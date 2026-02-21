"""Tests for voice_to_text package."""

from voice_to_text.config import Config, SUPPORTED_LANGUAGES


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.duration == 15
        assert config.language == "en"
        assert config.recording_device == "default"

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
