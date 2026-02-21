"""Configuration settings for voice-to-text."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


SUPPORTED_LANGUAGES: Dict[str, Tuple[str, str]] = {
    "1": ("en", "Inglés"),
    "2": ("es", "Español"),
    "3": ("fr", "Francés"),
    "4": ("de", "Alemán"),
}

SUPPORTED_MODELS: Dict[str, Tuple[str, str]] = {
    "1": ("tiny", "≈75MB"),
    "2": ("base", "≈150MB"),
    "3": ("small", "≈500MB"),
    "4": ("medium", "≈1.5GB"),
}

DEFAULT_DURATION = 15
DEFAULT_LANGUAGE = "en"
DEFAULT_UI_LANGUAGE = "es"
DEFAULT_MODEL_SIZE = "base"
SAMPLE_RATE = 16000
CHANNELS = 1
MIN_DURATION = 1
MAX_DURATION = 300
DEFAULT_DEVICE: Optional[str] = None
DEFAULT_LEVEL_REFRESH_RATE = 0.1

WORDS_PER_MINUTE = 150
WORDS_PER_PAGE_MIN = 100
WORDS_PER_PAGE_MAX = 150


@dataclass
class Config:
    duration: int = DEFAULT_DURATION
    language: str = DEFAULT_LANGUAGE
    ui_language: str = DEFAULT_UI_LANGUAGE
    recording_device: Optional[str] = DEFAULT_DEVICE
    model_size: str = DEFAULT_MODEL_SIZE

    def validate_duration(self, value: str) -> int:
        try:
            dur = int(value)
            if MIN_DURATION <= dur <= MAX_DURATION:
                return dur
        except ValueError:
            pass
        return self.duration

    def get_language_label(self) -> str:
        for code, label in SUPPORTED_LANGUAGES.values():
            if code == self.language:
                return label
        return self.language

    def get_model_label(self) -> str:
        for code, (model, size) in SUPPORTED_MODELS.items():
            if model == self.model_size:
                return f"{model} ({size})"
        return self.model_size
