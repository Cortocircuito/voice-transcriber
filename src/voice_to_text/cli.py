"""Command-line interface for voice-to-text."""

import argparse
import signal
import sys
from typing import Optional

from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeRemainingColumn

from .config import Config, SUPPORTED_LANGUAGES, SUPPORTED_MODELS
from .i18n import get_text, get_language_label
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI


class CLI:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.recorder = Recorder(self.config.recording_device)
        self.transcriber = Transcriber(model_size=self.config.model_size)
        self.ui = UI(self.config)
        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.recorder.interrupt()
        self.ui.show_goodbye()
        sys.exit(0)

    def configure(self):
        """Handle configuration menu."""
        while True:
            choice = self.ui.show_config()
            
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
            
            success, text = self.transcriber.transcribe(audio_path, self.config)
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
        """Run progress bar for recording."""
        lang = self.config.ui_language
        lang_label = get_language_label(self.config.language, lang)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
        ) as progress:
            task = progress.add_task(
                f"[cyan]{lang_label} • {duration}s",
                total=duration,
            )
            for _ in range(duration):
                import time
                time.sleep(1)
                progress.update(task, advance=1)

    def show_menu(self):
        """Show main menu."""
        while True:
            choice = self.ui.show_menu()
            
            if choice == "1":
                self.run_dictation()
            elif choice == "2":
                self.configure()
            elif choice == "3":
                self.ui.show_goodbye()
                break

    def run(self):
        """Run the CLI application."""
        console = self.ui.console if hasattr(self.ui, 'console') else None
        from rich.console import Console
        console = Console()
        
        console.print()
        console.print(f"[dim]{get_text('ready', self.config.ui_language)}[/dim]")
        
        self.transcriber.load_model()
        self.show_menu()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Voice to Text - Speech transcription")
    parser.add_argument(
        "--lang",
        choices=["es", "en"],
        default="es",
        help="UI language (es/en)",
    )
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
    
    args = parser.parse_args()
    
    config = Config(
        duration=args.duration,
        language=args.language,
        ui_language=args.lang,
    )
    
    cli = CLI(config)
    cli.run()


if __name__ == "__main__":
    main()
