"""Audio transcription functionality."""

import os
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from .config import Config


class Transcriber:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            print(f"Cargando modelo Whisper ({self.model_size})...")
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
        return self._model

    def transcribe(self, audio_path: str, config: Config) -> bool:
        try:
            segments, _ = self.model.transcribe(audio_path, language=config.language)
            text = "\n".join(segment.text.strip() for segment in segments)

            if not text:
                print("-" * 35)
                print("⚠️ No se detectó ningún audio. ¿Hablaste durante la grabación?")
                print("-" * 35)
                return False

            print("-" * 35)
            print(f"✅ Transcripción ({config.get_language_label()}):")
            print(text)
            print("-" * 35)
            return True

        except Exception as e:
            print(f"Error transcribiendo: {e}")
            return False
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass
