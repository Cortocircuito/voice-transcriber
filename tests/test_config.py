"""Tests for voice_to_text package."""

import pytest

from voice_to_text.config import Config, SUPPORTED_LANGUAGES
from voice_to_text.i18n import get_text, get_language_label


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.duration == 15
        assert config.language == "en"
        assert config.ui_language == "es"
        assert config.recording_device is None

    def test_validate_duration_valid(self):
        config = Config()
        assert config.validate_duration("30") == 30
        assert config.validate_duration("1") == 1
        assert config.validate_duration("300") == 300

    def test_validate_duration_invalid(self):
        config = Config()
        assert config.validate_duration("0") == 15
        assert config.validate_duration("-1") == 15
        assert config.validate_duration("301") == 15
        assert config.validate_duration("abc") == 15

    def test_get_language_label(self):
        config = Config()
        config.language = "en"
        assert config.get_language_label() == "Inglés"
        config.language = "es"
        assert config.get_language_label() == "Español"


class TestI18n:
    def test_get_text_spanish(self):
        assert get_text("menu_record", "es") == "Grabar"
        assert get_text("menu_exit", "es") == "Salir"

    def test_get_text_english(self):
        assert get_text("menu_record", "en") == "Record"
        assert get_text("menu_exit", "en") == "Exit"

    def test_get_language_label(self):
        assert get_language_label("en", "es") == "Inglés"
        assert get_language_label("en", "en") == "English"
        assert get_language_label("es", "en") == "Spanish"
