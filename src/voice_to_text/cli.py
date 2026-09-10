"""Command-line interface for voice-to-text."""

import argparse
import atexit
import logging
import signal
import sys
from typing import Callable, Optional

from .config import (
    MAX_DURATION,
    MAX_READING_SPEED,
    MIN_DURATION,
    MIN_READING_SPEED,
    Config,
)
from .configurator import ConfigManager
from .dictation import DictationManager
from .history import HistoryManager
from .i18n import get_text
from .lessons import LessonManager
from .practice import PracticeManager
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI

LESSONS_LOGGER = "voice_to_text.lessons"
EXTERNAL_LOGGERS = ["httpx", "httpcore", "urllib3", "faster_whisper"]


def _set_quiet_mode(quiet: bool) -> None:
    """Enable or disable quiet logging mode."""
    level = logging.CRITICAL + 1 if quiet else logging.INFO
    logging.root.setLevel(level)
    for logger_name in EXTERNAL_LOGGERS:
        logging.getLogger(logger_name).setLevel(level)


class CLI:
    _quiet_mode = False

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._cleaned_up = False
        self.recorder = Recorder(self.config.recording_device)
        self.ui = UI(self.config)
        self.transcriber = Transcriber(
            model_size=self.config.model_size, console=self.ui.console
        )
        self.history = HistoryManager()
        self.lesson_manager = LessonManager()

        self.dictation_manager = DictationManager(
            config=self.config,
            recorder=self.recorder,
            transcriber=self.transcriber,
            ui=self.ui,
            history=self.history,
        )

        self.practice_manager = PracticeManager(
            config=self.config,
            recorder=self.recorder,
            transcriber=self.transcriber,
            ui=self.ui,
            history=self.history,
            lesson_manager=self.lesson_manager,
        )

        self.config_manager = ConfigManager(
            config=self.config,
            ui=self.ui,
            history=self.history,
            transcriber=self.transcriber,
        )

        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Cleanup on exit - save history.

        Idempotent: the SIGINT handler calls this and then ``sys.exit(0)``,
        which fires the ``atexit`` handler that also calls it. Guard against
        the second run so history is not saved (and the message not printed)
        twice.
        """
        if self._cleaned_up:
            return
        self._cleaned_up = True
        # Stop any background lesson download so its worker thread does not
        # keep the interpreter alive at exit.
        self.recorder.stop_recording()
        self.lesson_manager.shutdown()
        entries = self.history.get_entries()
        if entries:
            self.ui.console.print(
                f"\n[dim]{get_text('history_saved', self.config.ui_language)}...[/dim]"
            )
        self.history.save()

    def _signal_handler(self, signum, frame):
        self.recorder.interrupt()
        self._cleanup()
        self.ui.show_goodbye()
        sys.exit(0)

    def _ensure_model_loaded(self) -> bool:
        """Load Whisper only when a transcription mode is selected."""
        model_loaded, message = self.transcriber.load_model()
        if not model_loaded:
            self.ui.show_error(message)
        return model_loaded

    def show_menu(self):
        """Show main menu."""
        shown_downloading = False
        while True:
            if self.lesson_manager.is_preloading():
                self.ui.show_lessons_download_progress()
                shown_downloading = True
            elif shown_downloading and self.lesson_manager.preload_succeeded():
                self.ui.show_lessons_download_complete()
                shown_downloading = False

            choice = self.ui.show_menu()

            if choice == "1":
                if self._ensure_model_loaded():
                    self.dictation_manager.run()
            elif choice == "2":
                if not self._ensure_model_loaded():
                    continue
                if self.lesson_manager.is_preloading():
                    self.ui.show_warning(
                        get_text("lessons_downloading", self.config.ui_language)
                    )
                elif not self.lesson_manager.get_cached_lessons():
                    if not self.lesson_manager.is_cache_expired():
                        # No cache at all
                        if self.ui.confirm_lesson_download():
                            CLI._quiet_mode = True
                            _set_quiet_mode(True)
                            self.lesson_manager.preload_lessons_async()
                    else:
                        # Cache exists but is expired
                        if self.ui.confirm_lesson_download(
                            prompt_key="lessons_outdated_prompt"
                        ):
                            CLI._quiet_mode = True
                            _set_quiet_mode(True)
                            self.lesson_manager.preload_lessons_async()
                        else:
                            stale = self.lesson_manager.get_stale_cached_lessons()
                            if stale:
                                self.ui.show_warning(
                                    get_text(
                                        "lessons_using_outdated",
                                        self.config.ui_language,
                                    )
                                )
                                _set_quiet_mode(False)
                                self.practice_manager.run(lessons=stale)
                                _set_quiet_mode(CLI._quiet_mode)
                else:
                    _set_quiet_mode(False)
                    self.practice_manager.run()
                    _set_quiet_mode(CLI._quiet_mode)
            elif choice == "3":
                self.config_manager.run()
            elif choice == "4":
                self.ui.show_goodbye()
                break

    def run(self, quick: bool = False):
        """Run the CLI application."""
        self.ui.console.print()
        self.ui.console.print(
            f"[dim]{get_text('ready', self.config.ui_language)}[/dim]"
        )

        if quick:
            if self._ensure_model_loaded():
                self.dictation_manager.run()
                self.ui.show_goodbye()
        else:
            self.show_menu()


def _bounded_int(minimum: int, maximum: int, name: str) -> Callable[[str], int]:
    """Build an argparse converter for an integer within an inclusive range."""

    def convert(value: str) -> int:
        try:
            number = int(value)
        except ValueError as e:
            raise argparse.ArgumentTypeError(f"{name} must be an integer") from e
        if not minimum <= number <= maximum:
            raise argparse.ArgumentTypeError(
                f"{name} must be between {minimum} and {maximum}"
            )
        return number

    return convert


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice to Text - Speech transcription")
    parser.add_argument(
        "--duration",
        type=_bounded_int(MIN_DURATION, MAX_DURATION, "duration"),
        default=None,
        help="Recording duration in seconds",
    )
    parser.add_argument(
        "--language",
        choices=["en", "es", "fr", "de"],
        default=None,
        help="Transcription language",
    )
    parser.add_argument(
        "--reading-speed",
        type=_bounded_int(MIN_READING_SPEED, MAX_READING_SPEED, "reading speed"),
        default=None,
        help="Reading speed in words per minute",
    )
    parser.add_argument(
        "--quick",
        "-q",
        action="store_true",
        help="Start recording immediately (skip menu)",
    )

    args = parser.parse_args()

    config = Config.load_from_file()

    if args.duration is not None:
        config.duration = args.duration
    if args.language is not None:
        config.language = args.language
    if args.reading_speed is not None:
        config.words_per_minute = args.reading_speed

    cli = CLI(config)
    cli.run(quick=args.quick)


if __name__ == "__main__":
    main()
