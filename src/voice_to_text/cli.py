"""Command-line interface for voice-to-text."""

import argparse
import atexit
import re
import signal
import sys
import time
from typing import Optional

from rich.console import Console, Group
from rich.live import Live
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.text import Text

from .comparison import TextComparator
from .config import Config, SUPPORTED_LANGUAGES, SUPPORTED_MODELS, WORDS_PER_MINUTE, WORDS_PER_PAGE_MIN, WORDS_PER_PAGE_MAX
from .history import HistoryManager
from .i18n import get_text, get_language_label
from .lessons import LessonManager, NetworkError
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI


class CLI:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.recorder = Recorder(self.config.recording_device)
        self.transcriber = Transcriber(model_size=self.config.model_size)
        self.ui = UI(self.config)
        self.history = HistoryManager()
        self.lesson_manager = LessonManager()
        self.comparator = TextComparator()
        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Cleanup on exit - save history."""
        entries = self.history.get_entries()
        if entries:
            from rich.console import Console
            console = Console()
            console.print(f"\n[dim]💾 {get_text('history_saved', self.config.ui_language)}...[/dim]")
        self.history.save()

    def _signal_handler(self, signum, frame):
        self.recorder.interrupt()
        self._cleanup()
        self.ui.show_goodbye()
        sys.exit(0)

    def configure(self):
        """Handle configuration menu."""
        while True:
            stats = self.history.get_stats()
            total_entries = stats["total"] + len(self.history.get_entries())
            choice = self.ui.show_config(has_history=total_entries > 0)
            
            if choice == "1":
                new_duration = self.ui.prompt_duration()
                if new_duration:
                    validated = self.config.validate_duration(str(new_duration))
                    if validated != self.config.duration:
                        self.config.duration = validated
                        self.ui.show_success(f"{self.config.duration}s")
            elif choice == "2":
                lang_code = self.ui.show_language_selector()
                if lang_code:
                    self.config.language = lang_code
                    lang_label = get_language_label(lang_code, self.config.ui_language)
                    self.ui.show_success(lang_label)
            elif choice == "3":
                model_size = self.ui.show_model_selector()
                if model_size:
                    self.config.model_size = model_size
                    self.ui.show_success(self.config.get_model_label())
            elif choice == "4":
                if self.ui.confirm_clear_history(total_entries):
                    if self.history.clear_all():
                        self.ui.show_success(get_text("history_cleared", self.config.ui_language))
                    else:
                        self.ui.show_error("Failed to clear history")
            else:
                break

    def run_dictation(self):
        """Run the dictation loop."""
        while True:
            self.ui.show_recording_start()
            
            mic_ok, level = self.recorder.check_microphone()
            self.ui.show_mic_status(mic_ok)
            
            audio_path = self.recorder.start_recording()
            if not audio_path:
                self.ui.show_error("Failed to start recording")
                continue

            self._run_progress(self.config.duration)
            
            self.recorder.stop_recording()
            
            self.ui.show_transcribing()
            
            segments_displayed = []
            def on_segment(text: str):
                segments_displayed.append(text)
                self.ui.show_segment(text, len(segments_displayed))
            
            success, text = self.transcriber.transcribe_streaming(
                audio_path, self.config, on_segment=on_segment
            )
            
            if success and text.strip():
                self.history.add_entry(
                    language=self.config.language,
                    duration=self.config.duration,
                    text=text,
                )
            
            if not segments_displayed:
                self.ui.show_transcription(text if text else "")
            
            action = self.ui.show_actions()
            
            if action == "d":
                new_duration = self.ui.prompt_duration()
                if new_duration:
                    validated = self.config.validate_duration(str(new_duration))
                    if validated != self.config.duration:
                        self.config.duration = validated
            elif action == "i":
                lang_code = self.ui.show_language_selector()
                if lang_code:
                    self.config.language = lang_code
            elif action == "s":
                break

    def _run_progress(self, duration: int):
        """Run progress bar for recording with real-time audio level."""
        from rich.style import Style
        
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)
        console = Console()
        
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        task = progress.add_task(f"[cyan]{lang_label} • {duration}s", total=duration)
        
        def generate_display():
            elapsed = time.time() - start_time
            progress.update(task, completed=min(int(elapsed), duration))
            
            level = self.recorder.get_audio_level()
            level_bar = self._format_level_bar(level)
            
            if level > 0.7:
                color = "red"
            elif level > 0.4:
                color = "yellow"
            else:
                color = "green"
            
            level_display = Text()
            level_display.append("🎤 ")
            level_display.append("Level: ")
            level_display.append(level_bar, style=Style(color=color, bold=True))
            level_display.append(f"  {level*100:3.0f}%")
            
            return Group(progress, level_display)
        
        start_time = time.time()
        with Live(generate_display(), refresh_per_second=10, console=console) as live:
            while time.time() - start_time < duration:
                live.update(generate_display())
                time.sleep(0.1)

    def _format_level_bar(self, level: float, width: int = 20) -> str:
        """Format audio level as a visual bar."""
        filled = int(level * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _split_text_into_pages(self, text: str) -> list[tuple[str, int]]:
        """Split text into pages by paragraphs.
        
        Args:
            text: Full lesson text
            
        Returns:
            List of (page_text, word_count) tuples
        """
        import math
        
        paragraphs = re.split(r'\n\n+', text)
        
        pages = []
        current_page = []
        current_words = 0
        
        for para in paragraphs:
            para_words = len(para.split())
            para = para.strip()
            
            if not para:
                continue
            
            if current_words + para_words > WORDS_PER_PAGE_MAX and current_words > 0:
                pages.append(("\n".join(current_page), current_words))
                current_page = []
                current_words = 0
            
            current_page.append(para)
            current_words += para_words
        
        if current_page:
            pages.append(("\n".join(current_page), current_words))
        
        if not pages:
            pages = [(text, len(text.split()))]
        
        return pages

    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate estimated reading time in seconds.
        
        Args:
            word_count: Number of words
            
        Returns:
            Estimated time in seconds
        """
        import math
        minutes = word_count / WORDS_PER_MINUTE
        seconds = math.ceil(minutes * 60)
        return max(10, seconds)

    def run_lesson_practice(self):
        """Run the lesson practice mode."""
        lang = self.config.ui_language
        lessons = []
        is_offline = False
        
        self.ui.show_lessons_loading()
        
        try:
            lessons = self.lesson_manager.fetch_lessons(use_cache=True)
        except NetworkError:
            lessons = self.lesson_manager.get_cached_lessons()
            is_offline = True
            if not lessons:
                self.ui.show_error(get_text("lessons_error", lang))
                return
        
        while True:
            choice = self.ui.show_lessons_menu(lessons, is_offline)
            
            if choice is None:
                break
            
            if choice == -1:
                self.ui.show_lessons_loading()
                try:
                    lessons = self.lesson_manager.fetch_lessons(use_cache=False)
                    is_offline = False
                except NetworkError:
                    self.ui.show_error(get_text("lessons_error", lang))
                    lessons = self.lesson_manager.get_cached_lessons()
                    is_offline = True
                continue
            
            if choice < 0 or choice >= len(lessons):
                continue
            
            selected_lesson = lessons[choice]
            
            level = self.ui.show_level_selector(selected_lesson)
            if not level:
                continue
            
            paragraphs = selected_lesson.get_paragraphs(level)
            
            if not paragraphs:
                lesson_text = selected_lesson.get_text(level)
                if not lesson_text:
                    self.ui.show_error(get_text("lessons_error", lang))
                    continue
                paragraphs = self._split_into_paragraphs(lesson_text)
            
            if not paragraphs:
                self.ui.show_error(get_text("lessons_error", lang))
                continue
            
            while True:
                action = self._run_lesson_practice_loop(selected_lesson, paragraphs, level)
                
                if action == "new_lesson":
                    break
                elif action == "exit":
                    return
    
    def _split_into_paragraphs(self, text: str) -> list[tuple[str, int]]:
        """Split text into paragraphs.
        
        Args:
            text: Full text
            
        Returns:
            List of (paragraph_text, word_count) tuples
        """
        import re
        
        paras = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        
        result = []
        for para in paras:
            para = para.strip()
            if para:
                word_count = len(para.split())
                result.append((para, word_count))
        
        if not result:
            return [(text, len(text.split()))]
        
        return result
    
    def _group_paragraphs(self, paragraphs: list, per_page: int = 2) -> list:
        """Group paragraphs into pages.
        
        Args:
            paragraphs: List of (text, word_count) tuples
            per_page: Number of paragraphs per page
            
        Returns:
            List of (combined_text, total_words, start_para, end_para) tuples
        """
        pages = []
        total = len(paragraphs)
        
        for i in range(0, total, per_page):
            group = paragraphs[i:i + per_page]
            combined_text = "\n\n".join([p[0] for p in group])
            total_words = sum([p[1] for p in group])
            start_para = i + 1
            end_para = min(i + per_page, total)
            pages.append((combined_text, total_words, start_para, end_para))
        
        return pages

    def _run_lesson_practice_loop(self, lesson, paragraphs: list, level: str) -> str:
        """Run lesson practice with page-by-page (2 paragraphs) recording.
        
        Args:
            lesson: The selected lesson
            paragraphs: List of (paragraph_text, word_count) tuples
            level: The selected level
            
        Returns:
            Action: 'new_lesson', 'exit', or None
        """
        lang = self.config.ui_language
        
        pages = self._group_paragraphs(paragraphs, per_page=2)
        total_pages = len(pages)
        current_page = 0
        
        while current_page < total_pages:
            page_text, page_words, start_para, end_para = pages[current_page]
            page_duration = self._calculate_reading_time(page_words)
            
            action = self.ui.show_paragraph_page(
                text=page_text,
                level=level,
                start_paragraph=start_para,
                end_paragraph=end_para,
                total_paragraphs=len(paragraphs),
                estimated_duration=page_duration,
            )
            
            if action == "back":
                if current_page > 0:
                    current_page -= 1
                    continue
                else:
                    return "new_lesson"
            
            elif action == "duration":
                new_duration = self.ui.prompt_duration_change(
                    current_duration=self.config.duration,
                    calculated_duration=page_duration,
                )
                if new_duration:
                    self.config.duration = new_duration
                continue
            
            elif action == "next":
                current_page += 1
                continue
            
            elif action == "record":
                result = self._run_paragraph_recording(
                    lesson, page_text, level, page_duration, start_para, end_para, len(paragraphs)
                )
                
                if result == "next":
                    current_page += 1
                    continue
                elif result == "retry":
                    continue
                elif result == "new_lesson":
                    return "new_lesson"
                elif result == "exit":
                    return "exit"
        
        self.ui.show_lesson_complete()
        
        while True:
            action = self.ui.show_practice_actions()
            if action == "n":
                return "new_lesson"
            elif action == "s":
                return "exit"
            elif action == "r":
                current_page = 0
                break
        
        return "new_lesson"

    def _run_paragraph_recording(
        self,
        lesson,
        text: str,
        level: str,
        duration: int,
        start_paragraph: int,
        end_paragraph: int,
        total_paragraphs: int,
    ) -> str:
        """Run the recording for a page of paragraphs.
        
        Args:
            lesson: The selected lesson
            text: The combined paragraph text
            level: The selected level
            duration: Recording duration
            start_paragraph: Starting paragraph number
            end_paragraph: Ending paragraph number
            total_paragraphs: Total paragraphs
            
        Returns:
            Action string: 'next', 'retry', 'new_lesson', 'exit'
        """
        lang = self.config.ui_language
        
        self.ui.show_recording_start()
        
        mic_ok, _ = self.recorder.check_microphone()
        self.ui.show_mic_status(mic_ok)
        
        audio_path = self.recorder.start_recording()
        if not audio_path:
            self.ui.show_error("Failed to start recording")
            return "retry"
        
        self._run_progress(duration)
        
        self.recorder.stop_recording()
        
        self.ui.show_transcribing()
        
        success, transcribed = self.transcriber.transcribe_streaming(
            audio_path, self.config, on_segment=None
        )
        
        if not success or not transcribed:
            self.ui.show_warning(get_text("no_audio", lang))
            while True:
                action = self.ui.show_practice_actions()
                if action == "r":
                    return "retry"
                elif action == "n":
                    return "new_lesson"
                elif action == "s":
                    return "exit"
        
        result = self.comparator.compare(text, transcribed)
        
        self.ui.show_comparison(text, transcribed, result)
        
        if transcribed.strip():
            if start_paragraph == end_paragraph:
                para_range = f"P{start_paragraph}"
            else:
                para_range = f"P{start_paragraph}-{end_paragraph}"
            self.history.add_entry(
                language="en",
                duration=duration,
                text=f"[Practice: {lesson.title[:30]} {para_range}] {transcribed}",
            )
        
        while True:
            if end_paragraph < total_paragraphs:
                self.ui.show_paragraph_actions()
            else:
                self.ui.show_last_paragraph_actions()
            
            try:
                from rich.console import Console
                console = Console()
                action = console.input(f"[bold cyan]{get_text('option', lang)}:[/bold cyan] ")
                action = action.strip().lower()
            except (EOFError, KeyboardInterrupt):
                return "exit"
            
            if action == "r":
                return "retry"
            elif action == "n":
                return "next"
            elif action == "f":
                return "next"
            elif action == "s":
                return "exit"
    
    def _run_lesson_recording(self, lesson, text: str, level: str, duration: int) -> str:
        """Run the recording for lesson practice.
        
        Args:
            lesson: The selected lesson
            text: The lesson text
            level: The selected level
            duration: Recording duration
            
        Returns:
            Action string
        """
        lang = self.config.ui_language
        
        self.ui.show_recording_start()
        
        mic_ok, _ = self.recorder.check_microphone()
        self.ui.show_mic_status(mic_ok)
        
        audio_path = self.recorder.start_recording()
        if not audio_path:
            self.ui.show_error("Failed to start recording")
            return "continue"
        
        self._run_progress(duration)
        
        self.recorder.stop_recording()
        
        self.ui.show_transcribing()
        
        success, transcribed = self.transcriber.transcribe_streaming(
            audio_path, self.config, on_segment=None
        )
        
        if not success or not transcribed:
            self.ui.show_warning(get_text("no_audio", lang))
            return "continue"
        
        result = self.comparator.compare(text, transcribed)
        
        self.ui.show_comparison(text, transcribed, result)
        
        if transcribed.strip():
            self.history.add_entry(
                language="en",
                duration=duration,
                text=f"[Practice: {lesson.title[:30]}] {transcribed}",
            )
        
        while True:
            action = self.ui.show_practice_actions()
            if action == "r":
                return self._run_lesson_recording(lesson, text, level, duration)
            elif action == "n":
                return "new_lesson"
            elif action == "s":
                return "exit"

    def _run_lesson_session(self, lesson, text: str, level: str):
        """Run a single lesson practice session.
        
        Args:
            lesson: The selected lesson
            text: The lesson text
            level: The selected level
        """
        lang = self.config.ui_language
        
        self.ui.show_lesson_text(text, level)
        
        self.ui.show_recording_start()
        
        mic_ok, _ = self.recorder.check_microphone()
        self.ui.show_mic_status(mic_ok)
        
        audio_path = self.recorder.start_recording()
        if not audio_path:
            self.ui.show_error("Failed to start recording")
            return
        
        self._run_progress(self.config.duration)
        
        self.recorder.stop_recording()
        
        self.ui.show_transcribing()
        
        success, transcribed = self.transcriber.transcribe_streaming(
            audio_path, self.config, on_segment=None
        )
        
        if not success or not transcribed:
            self.ui.show_warning(get_text("no_audio", lang))
            return
        
        result = self.comparator.compare(text, transcribed)
        
        self.ui.show_comparison(text, transcribed, result)
        
        if transcribed.strip():
            self.history.add_entry(
                language="en",
                duration=self.config.duration,
                text=f"[Practice: {lesson.title[:30]}] {transcribed}",
            )

    def show_menu(self):
        """Show main menu."""
        while True:
            choice = self.ui.show_menu()
            
            if choice == "1":
                self.run_dictation()
            elif choice == "2":
                self.run_lesson_practice()
            elif choice == "3":
                self.configure()
            elif choice == "4":
                self.ui.show_goodbye()
                break

    def run(self, quick: bool = False):
        """Run the CLI application."""
        from rich.console import Console
        console = Console()
        
        console.print()
        console.print(f"[dim]{get_text('ready', self.config.ui_language)}[/dim]")
        
        self.lesson_manager.preload_lessons_async()
        
        self.transcriber.load_model()
        
        if quick:
            self.run_dictation()
            self.ui.show_goodbye()
        else:
            self.show_menu()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice to Text - Speech transcription")
    parser.add_argument(
        "--duration",
        type=int,
        default=15,
        help="Recording duration in seconds (default: 15)",
    )
    parser.add_argument(
        "--language",
        choices=["en", "es", "fr", "de"],
        default="en",
        help="Transcription language (default: en)",
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Start recording immediately (skip menu)",
    )
    
    args = parser.parse_args()
    
    config = Config(
        duration=args.duration,
        language=args.language,
    )
    
    cli = CLI(config)
    cli.run(quick=args.quick)


if __name__ == "__main__":
    main()
