"""Configuration settings for voice-to-text."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

from .constants import (
    CONFIG_FILE_NAME,
    MAX_DURATION as CONSTANTS_MAX_DURATION,
    MIN_DURATION as CONSTANTS_MIN_DURATION,
    WORDS_PER_MINUTE,
    WORDS_PER_PAGE_MAX,
    WORDS_PER_PAGE_MIN,
)

logger = logging.getLogger(__name__)


def get_xdg_config_dir() -> Path:
    """Get XDG config directory for the application."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "voice-to-text"
    return Path.home() / ".config" / "voice-to-text"


def get_config_file_path() -> Path:
    """Get the path to the config file."""
    return get_xdg_config_dir() / CONFIG_FILE_NAME


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
DEFAULT_READING_SPEED = 150
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
    words_per_minute: int = DEFAULT_READING_SPEED

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

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "Config":
        """Load config from JSON file.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            Config instance with loaded values.
        """
        if path is None:
            path = get_config_file_path()

        if not path.exists():
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            config = cls()
            if "duration" in data:
                config.duration = data["duration"]
            if "language" in data:
                config.language = data["language"]
            if "ui_language" in data:
                config.ui_language = data["ui_language"]
            if "recording_device" in data:
                config.recording_device = data["recording_device"]
            if "model_size" in data:
                config.model_size = data["model_size"]
            if "words_per_minute" in data:
                config.words_per_minute = data["words_per_minute"]

            return config
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config from {path}: {e}")
            return cls()

    def save_to_file(self, path: Optional[Path] = None) -> bool:
        """Save config to JSON file.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            True if saved successfully, False otherwise.
        """
        if path is None:
            path = get_config_file_path()

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "duration": self.duration,
                "language": self.language,
                "ui_language": self.ui_language,
                "recording_device": self.recording_device,
                "model_size": self.model_size,
                "words_per_minute": self.words_per_minute,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save config to {path}: {e}")
            return False
