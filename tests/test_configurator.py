"""Tests for configuration manager runtime changes."""

from unittest.mock import MagicMock

from voice_to_text.config import Config
from voice_to_text.configurator import ConfigManager


def test_model_selection_replaces_the_transcriber_model() -> None:
    """Changing model size applies to the transcriber used by both modes."""
    config = Config()
    ui = MagicMock()
    ui.show_config.side_effect = ["3", "0"]
    ui.show_model_selector.return_value = "small"
    ui.confirm_save_config.return_value = False
    history = MagicMock()
    history.get_stats.return_value = {"total": 0}
    history.get_entries.return_value = []
    transcriber = MagicMock()
    manager = ConfigManager(config, ui, history, transcriber)

    manager.run()

    assert config.model_size == "small"
    transcriber.set_model_size.assert_called_once_with("small")
