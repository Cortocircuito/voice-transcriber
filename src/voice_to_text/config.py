"""Configuration settings for voice-to-text."""

import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple, cast

from .constants import (
    COMPARISON_METHODS,
    CONFIG_FILE_NAME,
    DEFAULT_COMPARISON_METHOD as CONSTANTS_DEFAULT_COMPARISON_METHOD,
    MAX_DURATION as CONSTANTS_MAX_DURATION,
    MAX_READING_SPEED,
    MIN_DURATION as CONSTANTS_MIN_DURATION,
    MIN_READING_SPEED,
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

# Valid values used to sanitize a hand-edited config.json on load.
SUPPORTED_LANGUAGE_CODES = {code for code, _ in SUPPORTED_LANGUAGES.values()}
SUPPORTED_MODEL_SIZES = {model for model, _ in SUPPORTED_MODELS.values()}
SUPPORTED_UI_LANGUAGES = {"en", "es"}

DEFAULT_DURATION = 15
DEFAULT_LANGUAGE = "en"
DEFAULT_UI_LANGUAGE = "en"
DEFAULT_MODEL_SIZE = "base"
DEFAULT_READING_SPEED = 150
DEFAULT_COMPARISON_METHOD = CONSTANTS_DEFAULT_COMPARISON_METHOD
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
    comparison_method: str = DEFAULT_COMPARISON_METHOD

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

    @staticmethod
    def _valid_int(data: dict, key: str, lo: int, hi: int, default: int) -> int:
        """Return data[key] as an int in [lo, hi], else the default.

        Absent keys silently use the default; a present-but-invalid value
        (wrong type, out of range) falls back to the default with a warning so
        a hand-edited config.json cannot inject a bad value downstream.
        """
        if key not in data:
            return default
        value = data[key]
        if isinstance(value, bool):
            coerced = None
        else:
            try:
                coerced = int(value)
            except (TypeError, ValueError):
                coerced = None
        if coerced is not None and lo <= coerced <= hi:
            return coerced
        logger.warning(
            "Invalid '%s' in config (%r); using default %r", key, value, default
        )
        return default

    @staticmethod
    def _valid_choice(
        data: dict, key: str, choices: Iterable[str], default: str
    ) -> str:
        """Return data[key] if it is one of choices, else the default."""
        if key not in data:
            return default
        value = data[key]
        if value in choices:
            return cast(str, value)
        logger.warning(
            "Invalid '%s' in config (%r); using default %r", key, value, default
        )
        return default

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "Config":
        """Load config from JSON file.

        Values are validated field by field; anything missing or invalid
        (e.g. a hand-edited ``"model_size": "huge"`` or a negative duration)
        falls back to the default rather than propagating downstream.

        Args:
            path: Path to config file. If None, uses default location.

        Returns:
            Config instance with loaded, sanitized values.
        """
        if path is None:
            path = get_config_file_path()

        if not path.exists():
            return cls()

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                logger.warning(
                    "Config at %s is not a JSON object; using defaults", path
                )
                return cls()

            config = cls()
            config.duration = cls._valid_int(
                data, "duration", MIN_DURATION, MAX_DURATION, DEFAULT_DURATION
            )
            config.words_per_minute = cls._valid_int(
                data,
                "words_per_minute",
                MIN_READING_SPEED,
                MAX_READING_SPEED,
                DEFAULT_READING_SPEED,
            )
            config.language = cls._valid_choice(
                data, "language", SUPPORTED_LANGUAGE_CODES, DEFAULT_LANGUAGE
            )
            config.ui_language = cls._valid_choice(
                data, "ui_language", SUPPORTED_UI_LANGUAGES, DEFAULT_UI_LANGUAGE
            )
            config.model_size = cls._valid_choice(
                data, "model_size", SUPPORTED_MODEL_SIZES, DEFAULT_MODEL_SIZE
            )
            config.comparison_method = cls._valid_choice(
                data, "comparison_method", COMPARISON_METHODS, DEFAULT_COMPARISON_METHOD
            )
            if "recording_device" in data:
                device = data["recording_device"]
                if device is None or isinstance(device, str):
                    config.recording_device = device
                else:
                    logger.warning(
                        "Invalid 'recording_device' in config (%r); using default",
                        device,
                    )

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
                "comparison_method": self.comparison_method,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except IOError as e:
            logger.error(f"Failed to save config to {path}: {e}")
            return False
