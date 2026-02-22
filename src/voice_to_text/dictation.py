"""Dictation manager for voice-to-text."""

import re
import time
from typing import Callable, Optional

from rich.console import Console, Group
from rich.live import Live
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn
from rich.style import Style
from rich.text import Text

from .comparison import TextComparator
from .config import Config, WORDS_PER_PAGE_MAX, WORDS_PER_PAGE_MIN
from .constants import COLOR_ACCENT, COLOR_SUCCESS
from .history import HistoryManager
from .i18n import get_language_label, get_text
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI

console = Console()


class DictationManager:
    """Manages dictation mode."""

    def __init__(
        self,
        config: Config,
        recorder: Recorder,
        transcriber: Transcriber,
        ui: UI,
        history: HistoryManager,
    ):
        self.config = config
        self.recorder = recorder
        self.transcriber = transcriber
        self.ui = ui
        self.history = history
        self.comparator = TextComparator()

    def run(self) -> None:
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

    def _run_progress(self, duration: int) -> None:
        """Run progress bar for recording with real-time audio level."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style=COLOR_SUCCESS, finished_style=COLOR_SUCCESS),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        )
        task = progress.add_task(f"[{COLOR_ACCENT}]{lang_label} • {duration}s", total=duration)

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
        """Split text into pages by paragraphs."""
        import math

        paragraphs = re.split(r"\n\n+", text)

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
