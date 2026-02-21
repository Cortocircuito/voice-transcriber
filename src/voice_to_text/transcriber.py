"""Audio transcription functionality."""

import os
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

from faster_whisper import WhisperModel

from .config import Config

console = Console()


class Transcriber:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            console.print(f"[dim]⏳ Loading Whisper model ({self.model_size})...[/dim]")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str, config: Config) -> Tuple[bool, str]:
        """Transcribe audio file. Returns (success, text)."""
        try:
            segments, _ = self.model.transcribe(audio_path, language=config.language)
            text = "\n".join(segment.text.strip() for segment in segments)
            return True, text

        except Exception as e:
            console.print(f"[red]Error transcribing: {e}[/red]")
            return False, ""
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def load_model(self) -> bool:
        """Pre-load the model."""
        try:
            _ = self.model
            return True
        except Exception:
            return False
