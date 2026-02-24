"""Command-line interface for voice-to-text."""

import argparse
import atexit
import logging
import signal
import sys
from typing import Optional

from .config import Config
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
        self.recorder = Recorder(self.config.recording_device)
        self.transcriber = Transcriber(model_size=self.config.model_size)
        self.ui = UI(self.config)
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
        )

        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)
        atexit.register(self._cleanup)

    def _cleanup(self):
        """Cleanup on exit - save history."""
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
                self.dictation_manager.run()
            elif choice == "2":
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

        cached_lessons = self.lesson_manager.get_cached_lessons()
        if not cached_lessons:
            if self.ui.confirm_lesson_download():
                CLI._quiet_mode = True
                _set_quiet_mode(True)
                self.lesson_manager.preload_lessons_async()

        self.transcriber.load_model()

        if quick:
            self.dictation_manager.run()
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
        "--quick",
        "-q",
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
