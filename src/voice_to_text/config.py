"""Configuration settings for voice-to-text."""

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


SUPPORTED_LANGUAGES: Dict[str, Tuple[str, str]] = {
    "1": ("en", "Inglés"),
    "2": ("es", "Español"),
    "3": ("fr", "Francés"),
    "4": ("de", "Alemán"),
}

DEFAULT_DURATION = 15
DEFAULT_LANGUAGE = "en"
DEFAULT_UI_LANGUAGE = "es"
SAMPLE_RATE = 16000
CHANNELS = 1
MIN_DURATION = 1
MAX_DURATION = 300
DEFAULT_DEVICE: Optional[str] = None


@dataclass
class Config:
    duration: int = DEFAULT_DURATION
    language: str = DEFAULT_LANGUAGE
    ui_language: str = DEFAULT_UI_LANGUAGE
    recording_device: Optional[str] = DEFAULT_DEVICE

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
