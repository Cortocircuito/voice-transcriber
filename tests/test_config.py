"""Tests for voice_to_text package."""

import json
import pytest
from pathlib import Path

from voice_to_text.config import Config, SUPPORTED_LANGUAGES, get_config_file_path
from voice_to_text.i18n import get_text, get_language_label


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.duration == 15
        assert config.language == "en"
        assert config.ui_language == "en"
        assert config.recording_device is None
        assert config.model_size == "base"
        assert config.words_per_minute == 150
        assert config.comparison_method == "flexible"

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
        assert config.get_language_label() == "English"
        config.language = "es"
        assert config.get_language_label() == "Spanish"

    def test_get_model_label(self):
        config = Config()
        config.model_size = "tiny"
        assert "tiny" in config.get_model_label()
        config.model_size = "base"
        assert "base" in config.get_model_label()


class TestI18n:
    def test_get_text_english(self):
        assert get_text("menu_record", "en") == "Record"
        assert get_text("menu_exit", "en") == "Exit"

    def test_get_language_label(self):
        assert get_language_label("en", "en") == "English"
        assert get_language_label("es", "en") == "Spanish"


class TestConfigFile:
    def test_get_config_file_path(self):
        path = get_config_file_path()
        assert path.name == "config.json"
        assert "voice-to-text" in str(path)

    def test_load_from_file_defaults(self, tmp_path):
        config = Config.load_from_file(tmp_path / "config.json")
        assert config.duration == 15
        assert config.language == "en"
        assert config.words_per_minute == 150

    def test_load_from_file_with_values(self, tmp_path):
        config_file = tmp_path / "config.json"
        data = {
            "duration": 30,
            "language": "es",
            "words_per_minute": 100,
        }
        with open(config_file, "w") as f:
            json.dump(data, f)

        config = Config.load_from_file(config_file)
        assert config.duration == 30
        assert config.language == "es"
        assert config.words_per_minute == 100

    def test_load_from_file_partial_values(self, tmp_path):
        config_file = tmp_path / "config.json"
        data = {"duration": 45}
        with open(config_file, "w") as f:
            json.dump(data, f)

        config = Config.load_from_file(config_file)
        assert config.duration == 45
        assert config.language == "en"
        assert config.words_per_minute == 150

    def test_load_from_file_comparison_method(self, tmp_path):
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump({"comparison_method": "per_word"}, f)

        config = Config.load_from_file(config_file)
        assert config.comparison_method == "per_word"

    def test_load_from_file_invalid_comparison_method(self, tmp_path):
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump({"comparison_method": "bogus"}, f)

        config = Config.load_from_file(config_file)
        assert config.comparison_method == "flexible"

    def test_load_from_file_invalid_json(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text("invalid json")

        config = Config.load_from_file(config_file)
        assert config.duration == 15

    def test_save_to_file(self, tmp_path):
        config = Config(
            duration=30,
            language="es",
            words_per_minute=100,
        )
        config_file = tmp_path / "config.json"

        result = config.save_to_file(config_file)
        assert result is True
        assert config_file.exists()

        with open(config_file) as f:
            data = json.load(f)
        assert data["duration"] == 30
        assert data["language"] == "es"
        assert data["words_per_minute"] == 100
        assert data["comparison_method"] == "flexible"


class TestConfigValidation:
    """load_from_file sanitizes hand-edited / invalid values."""

    def _write(self, tmp_path, data):
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump(data, f)
        return config_file

    def test_duration_out_of_range_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"duration": -5}))
        assert cfg.duration == 15
        cfg = Config.load_from_file(self._write(tmp_path, {"duration": 10000}))
        assert cfg.duration == 15

    def test_duration_wrong_type_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"duration": "abc"}))
        assert cfg.duration == 15
        # A JSON bool must not be silently coerced to 0/1.
        cfg = Config.load_from_file(self._write(tmp_path, {"duration": True}))
        assert cfg.duration == 15

    def test_words_per_minute_out_of_range_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"words_per_minute": 5}))
        assert cfg.words_per_minute == 150
        cfg = Config.load_from_file(self._write(tmp_path, {"words_per_minute": 9999}))
        assert cfg.words_per_minute == 150

    def test_invalid_language_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"language": "xx"}))
        assert cfg.language == "en"

    def test_invalid_ui_language_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"ui_language": "fr"}))
        assert cfg.ui_language == "en"

    def test_invalid_model_size_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"model_size": "huge"}))
        assert cfg.model_size == "base"

    def test_valid_values_are_kept(self, tmp_path):
        cfg = Config.load_from_file(
            self._write(
                tmp_path,
                {
                    "duration": 42,
                    "words_per_minute": 200,
                    "language": "fr",
                    "ui_language": "es",
                    "model_size": "small",
                    "comparison_method": "per_word",
                },
            )
        )
        assert cfg.duration == 42
        assert cfg.words_per_minute == 200
        assert cfg.language == "fr"
        assert cfg.ui_language == "es"
        assert cfg.model_size == "small"
        assert cfg.comparison_method == "per_word"

    def test_recording_device_string_kept_none_kept(self, tmp_path):
        cfg = Config.load_from_file(
            self._write(tmp_path, {"recording_device": "hw:1,0"})
        )
        assert cfg.recording_device == "hw:1,0"
        cfg = Config.load_from_file(self._write(tmp_path, {"recording_device": None}))
        assert cfg.recording_device is None

    def test_recording_device_wrong_type_uses_default(self, tmp_path):
        cfg = Config.load_from_file(self._write(tmp_path, {"recording_device": 5}))
        assert cfg.recording_device is None

    def test_non_object_json_uses_defaults(self, tmp_path):
        config_file = tmp_path / "config.json"
        with open(config_file, "w") as f:
            json.dump([1, 2, 3], f)
        cfg = Config.load_from_file(config_file)
        assert cfg.duration == 15
        assert cfg.language == "en"

    def test_one_invalid_field_does_not_drop_valid_ones(self, tmp_path):
        cfg = Config.load_from_file(
            self._write(tmp_path, {"duration": -1, "language": "de"})
        )
        assert cfg.duration == 15  # invalid -> default
        assert cfg.language == "de"  # valid -> kept
