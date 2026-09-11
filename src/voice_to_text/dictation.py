"""Dictation manager for voice-to-text."""

import re
import time
from math import ceil
from pathlib import Path

from rich.console import Console, Group
from rich.live import Live
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeRemainingColumn,
)
from rich.style import Style
from rich.text import Text

from .comparison import TextComparator
from .config import WORDS_PER_PAGE_MAX, Config
from .constants import COLOR_ACCENT, COLOR_SUCCESS
from .history import HistoryManager
from .i18n import get_language_label, get_text
from .recorder import Recorder, RecorderError
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

            mic_ok, _ = self.recorder.check_microphone()
            self.ui.show_mic_status(mic_ok)
            if not mic_ok:
                self.ui.show_error(get_text("mic_not_found", self.config.ui_language))
                return

            try:
                audio_path = self.recorder.start_recording()
            except RecorderError as e:
                self.ui.show_error(str(e))
                return
            if not audio_path:
                self.ui.show_error("Failed to start recording")
                continue

            try:
                recorded_duration = self._run_progress(self.config.duration)
            finally:
                recording_stopped = self.recorder.stop_recording()

            if not recording_stopped:
                self.ui.show_error("Failed to finalize recording")
                return

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
                    duration=recorded_duration,
                    text=text,
                )

            if not segments_displayed:
                self.ui.show_transcription(text if text else "")

            while True:
                action = self.ui.show_actions()

                if action == "c":
                    if text.strip():
                        self.ui.copy_text(text)
                    else:
                        self.ui.show_warning(
                            get_text("no_transcription", self.config.ui_language)
                        )
                    continue
                if action == "w":
                    if text.strip():
                        path = self.ui.prompt_transcription_path()
                        if path:
                            self._save_transcription(text, path)
                    else:
                        self.ui.show_warning(
                            get_text("no_transcription", self.config.ui_language)
                        )
                    continue
                if action == "e":
                    if text.strip():
                        if not self.ui.export_text(text):
                            return
                    else:
                        self.ui.show_warning(
                            get_text("no_transcription", self.config.ui_language)
                        )
                    continue
                if action == "d":
                    new_duration = self.ui.prompt_duration()
                    if new_duration:
                        validated = self.config.validate_duration(str(new_duration))
                        if validated != self.config.duration:
                            self.config.duration = validated
                    break
                if action == "i":
                    lang_code = self.ui.show_language_selector()
                    if lang_code:
                        self.config.language = lang_code
                    break
                if action == "s":
                    return
                break

    def _save_transcription(self, text: str, path_value: str) -> None:
        """Save a transcription as plain text or Markdown."""
        path: Path | None = None
        created = False
        try:
            path = Path(path_value).expanduser()
            if not path.suffix:
                path = path.with_suffix(".txt")
            if path.suffix.lower() not in {".txt", ".md"}:
                self.ui.show_error(
                    get_text("invalid_transcription_format", self.config.ui_language)
                )
                return

            content = text.rstrip() + "\n"
            if path.suffix.lower() == ".md":
                content = f"# Dictation\n\n{content}"

            with path.open("x", encoding="utf-8") as transcription_file:
                created = True
                transcription_file.write(content)
        except FileExistsError:
            self.ui.show_error(
                get_text("transcription_file_exists", self.config.ui_language)
            )
            return
        except (OSError, RuntimeError, ValueError) as e:
            if created and path:
                try:
                    path.unlink()
                except OSError:
                    pass
            self.ui.show_error(f"Failed to save transcription: {e}")
            return

        self.ui.show_success(
            get_text("transcription_saved", self.config.ui_language).format(path=path)
        )

    def _run_progress(self, duration: int) -> int:
        """Run recording progress and return the elapsed duration in seconds."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)

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

        def generate_display():
            elapsed = time.monotonic() - start_time
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
            level_display.append(f"  {level * 100:3.0f}%")

            return Group(progress, level_display)

        start_time = time.monotonic()
        with Live(generate_display(), refresh_per_second=10, console=console) as live:
            while True:
                elapsed = time.monotonic() - start_time
                if elapsed >= duration:
                    return duration
                if self.ui.recording_stop_requested():
                    return max(1, ceil(elapsed))
                live.update(generate_display())
                time.sleep(0.1)

    def _format_level_bar(self, level: float, width: int = 20) -> str:
        """Format audio level as a visual bar."""
        filled = int(level * width)
        bar = "█" * filled + "░" * (width - filled)
        return bar

    def _split_text_into_pages(self, text: str) -> list[tuple[str, int]]:
        """Split text into pages by paragraphs."""
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
