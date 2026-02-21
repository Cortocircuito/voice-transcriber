"""Command-line interface for voice-to-text."""

import signal
import sys
from typing import Optional

from .config import Config, SUPPORTED_LANGUAGES
from .recorder import Recorder
from .transcriber import Transcriber


class CLI:
    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self.recorder = Recorder(self.config.recording_device)
        self.transcriber = Transcriber()
        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        self.recorder.interrupt()

    def configure(self):
        print()
        print(f"--- CONFIGURACIÓN (D:{self.config.duration}s | L:{self.config.get_language_label()}) ---")
        print("1) Duración (segundos)")
        print("2) Idioma (1:en 2:es 3:fr 4:de)")

        choice = input("Opción: ").strip()

        if choice == "1":
            new_dur = input(f"Segundos [{self.config.duration}]: ").strip()
            if new_dur:
                self.config.duration = self.config.validate_duration(new_dur)
        elif choice == "2":
            lang_opt = input("1)Inglés 2)Español 3)Francés 4)Alemán: ").strip()
            if lang_opt in SUPPORTED_LANGUAGES:
                self.config.language = SUPPORTED_LANGUAGES[lang_opt][0]

    def run_dictation(self):
        while True:
            print()
            print(f"--- GRABANDO ({self.config.duration}s, {self.config.get_language_label()}) ---")

            audio_path = self.recorder.record(self.config.duration)
            if audio_path is None:
                continue

            self.transcriber.transcribe(audio_path, self.config)

            print("D)uración | I)dioma | S)alir")
            try:
                action = input("Continuar: ").strip().lower()
            except EOFError:
                break

            if action == "d":
                new_dur = input(f"Segundos [{self.config.duration}]: ").strip()
                if new_dur:
                    self.config.duration = self.config.validate_duration(new_dur)
            elif action == "i":
                lang_opt = input("1)en 2)es 3:fr 4:de: ").strip()
                if lang_opt in SUPPORTED_LANGUAGES:
                    self.config.language = SUPPORTED_LANGUAGES[lang_opt][0]
            elif action == "s":
                break

    def show_menu(self):
        while True:
            print()
            print("=== MENÚ ===")
            print("1) Grabar")
            print(f"2) Configurar (D:{self.config.duration}s L:{self.config.get_language_label()})")
            print("3) Salir")

            try:
                opt = input("Opción: ").strip()
            except EOFError:
                break

            if opt == "1":
                self.run_dictation()
            elif opt == "2":
                self.configure()
            elif opt == "3":
                print("¡Hasta luego!")
                break

    def run(self):
        print("Entorno activado. Ctrl+C para salir.")
        self.show_menu()
