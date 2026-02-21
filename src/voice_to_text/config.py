"""Configuration settings for voice-to-text."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .constants import (
    MAX_DURATION as CONSTANTS_MAX_DURATION,
    MIN_DURATION as CONSTANTS_MIN_DURATION,
    WORDS_PER_MINUTE,
    WORDS_PER_PAGE_MAX,
    WORDS_PER_PAGE_MIN,
)


SUPPORTED_LANGUAGES: Dict[str, Tuple[str, str]] = {
    "1": ("en", "English"),
    "2": ("es", "Spanish"),
    "3": ("fr", "French"),
    "4": ("de", "German"),
}

SUPPORTED_MODELS: Dict[str, Tuple[str, str]] = {
    "1": ("tiny", "≈75MB"),
    "2": ("base", "≈150MB"),
    "3": ("small", "≈500MB"),
    "4": ("medium", "≈1.5GB"),
}

DEFAULT_DURATION = 15
DEFAULT_LANGUAGE = "en"
DEFAULT_UI_LANGUAGE = "en"
DEFAULT_MODEL_SIZE = "base"
SAMPLE_RATE = 16000
CHANNELS = 1
MIN_DURATION = CONSTANTS_MIN_DURATION
MAX_DURATION = CONSTANTS_MAX_DURATION
DEFAULT_DEVICE: Optional[str] = None
DEFAULT_LEVEL_REFRESH_RATE = 0.1

WORDS_PER_MINUTE = WORDS_PER_MINUTE
WORDS_PER_PAGE_MIN = WORDS_PER_PAGE_MIN
WORDS_PER_PAGE_MAX = WORDS_PER_PAGE_MAX


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
