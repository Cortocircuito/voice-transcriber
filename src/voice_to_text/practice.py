"""Practice manager for lesson practice mode."""

import math
import re

from .comparison import TextComparator
from .config import Config, WORDS_PER_MINUTE
from .constants import COLOR_ACCENT, COLOR_SUCCESS
from .history import HistoryManager
from .i18n import get_text
from .lessons import Lesson, LessonManager, NetworkError
from .phonetics import get_ipa
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI


class PracticeManager:
    """Manages lesson practice mode."""

    def __init__(
        self,
        config: Config,
        recorder: Recorder,
        transcriber: Transcriber,
        ui: UI,
        history: HistoryManager,
        lesson_manager: LessonManager,
    ):
        self.config = config
        self.recorder = recorder
        self.transcriber = transcriber
        self.ui = ui
        self.history = history
        self.lesson_manager = lesson_manager
        self.comparator = TextComparator()

    def run(self) -> None:
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

        page = 0

        while True:
            choice = self.ui.show_lessons_menu(
                lessons, page=page, per_page=5, is_offline=is_offline
            )

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
                page = 0
                continue

            if choice == -2:
                page += 1
                continue

            if choice == -3:
                page = max(0, page - 1)
                continue

            if choice < 0 or choice >= len(lessons):
                continue

            selected_lesson = lessons[choice]

            level = self.ui.show_level_selector(selected_lesson)
            if not level:
                continue

            lesson_text = selected_lesson.get_text(level)
            if not lesson_text:
                self.ui.show_error(get_text("lessons_error", lang))
                continue
            paragraphs = self._split_into_paragraphs(lesson_text)

            if not paragraphs:
                self.ui.show_error(get_text("lessons_error", lang))
                continue

            while True:
                action = self._run_lesson_practice_loop(
                    selected_lesson, paragraphs, level
                )

                if action == "new_lesson":
                    break
                elif action == "main_menu":
                    return
                elif action == "exit":
                    return

    def _split_into_paragraphs(self, text: str) -> list[tuple[str, int]]:
        """Split text into paragraphs."""
        paras = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)

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
        """Group paragraphs into pages with phonetics."""
        pages = []
        total = len(paragraphs)

        for i in range(0, total, per_page):
            group = paragraphs[i : i + per_page]
            combined_text = "\n\n".join([p[0] for p in group])
            total_words = sum([p[1] for p in group])
            start_para = i + 1
            end_para = min(i + per_page, total)

            phonetic_text = get_ipa(combined_text)

            pages.append((combined_text, total_words, start_para, end_para, phonetic_text))

        return pages

    def _calculate_reading_time(self, word_count: int) -> int:
        """Calculate estimated reading time in seconds."""
        minutes = word_count / WORDS_PER_MINUTE
        seconds = math.ceil(minutes * 60)
        return max(10, seconds)

    def _run_lesson_practice_loop(
        self,
        lesson: Lesson,
        paragraphs: list,
        level: str,
    ) -> str:
        """Run lesson practice with page-by-page recording."""
        pages = self._group_paragraphs(paragraphs, per_page=2)
        total_pages = len(pages)
        current_page = 0
        page_durations: dict[int, int] = {}

        while current_page < total_pages:
            page_text, page_words, start_para, end_para, phonetic_text = pages[current_page]
            page_duration = self._calculate_reading_time(page_words)
            current_duration = page_durations.get(current_page, page_duration)

            action = self.ui.show_paragraph_page(
                text=page_text,
                phonetic_text=phonetic_text,
                level=level,
                start_paragraph=start_para,
                end_paragraph=end_para,
                total_paragraphs=len(paragraphs),
                estimated_duration=page_duration,
                current_duration=current_duration,
            )

            if action == "prev":
                if current_page > 0:
                    current_page -= 1
                continue

            elif action == "back":
                return "new_lesson"

            elif action == "main_menu":
                return "main_menu"

            elif action == "duration":
                new_duration = self.ui.prompt_duration_change(
                    current_duration=current_duration,
                    calculated_duration=page_duration,
                )
                if new_duration:
                    current_duration = new_duration
                    page_durations[current_page] = new_duration
                continue

            elif action == "next":
                current_page += 1
                continue

            elif action == "record":
                result = self._run_paragraph_recording(
                    lesson,
                    page_text,
                    current_duration,
                    start_para,
                    end_para,
                    len(paragraphs),
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
        lesson: Lesson,
        text: str,
        duration: int,
        start_paragraph: int,
        end_paragraph: int,
        total_paragraphs: int,
    ) -> str:
        """Run the recording for a page of paragraphs."""
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
                language=self.config.language,
                duration=duration,
                text=f"[Practice: {lesson.title[:30]} {para_range}] {transcribed}",
            )

        while True:
            if end_paragraph < total_paragraphs:
                self.ui.show_paragraph_actions()
            else:
                self.ui.show_last_paragraph_actions()

            try:
                action = self.ui.console.input(
                    f"[bold {COLOR_ACCENT}]{get_text('option', lang)}:[/bold {COLOR_ACCENT}] "
                )
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

        return "exit"

    def _run_progress(self, duration: int) -> None:
        """Run progress bar for recording."""
        import time

        from rich.console import Console
        from rich.live import Live
        from rich.progress import (
            BarColumn,
            Progress,
            SpinnerColumn,
            TextColumn,
            TimeRemainingColumn,
        )

        lang = self.config.ui_language
        from .i18n import get_language_label

        lang_label = get_language_label(self.config.language, lang)
        console = Console()

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=COLOR_SUCCESS, finished_style=COLOR_SUCCESS),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        task = progress.add_task(
            f"[{COLOR_ACCENT}]{lang_label} • {duration}s", total=duration
        )

        start_time = time.time()
        with Live(progress, refresh_per_second=10, console=console):
            while time.time() - start_time < duration:
                progress.update(task, completed=int(time.time() - start_time))
                time.sleep(0.1)
