"""Tests for UI module."""

from unittest.mock import MagicMock, patch

import pytest

from voice_to_text.ui import UI
from voice_to_text.config import Config


class TestUI:
    """Tests for UI class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Config()
        config.ui_language = "en"
        return config

    def test_init(self, mock_config):
        """Test UI initialization."""
        with patch("voice_to_text.ui.Console"):
            ui = UI(mock_config)
            assert ui.config == mock_config

    def test_create_panel(self, mock_config):
        """Test panel creation."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui._create_panel("Test content", title="Test Title")
            assert result is not None

    def test_menu_table(self, mock_config):
        """Test menu table creation."""
        with patch("voice_to_text.ui.Console"):
            ui = UI(mock_config)
            items = [("[1]", "Option 1"), ("[2]", "Option 2")]
            result = ui._menu_table(items)
            assert result is not None

    def test_prompt_duration_change(self, mock_config):
        """Test duration change prompt."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="30")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 30

    def test_prompt_duration_change_empty(self, mock_config):
        """Test duration change with empty input."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 15

    def test_prompt_duration_change_invalid(self, mock_config):
        """Test duration change with invalid input."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="abc")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 15

    def test_confirm_clear_history_no_entries(self, mock_config):
        """Test confirm clear history with no entries."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.confirm_clear_history(0)

            assert result is False

    def test_prompt_duration_valid(self, mock_config):
        """Test prompt duration with valid input."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="30")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result == 30

    def test_prompt_duration_empty(self, mock_config):
        """Test prompt duration with empty input."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result is None

    def test_prompt_duration_invalid(self, mock_config):
        """Test prompt duration with invalid input."""
        with patch("voice_to_text.ui.Console") as mock_console:
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="abc")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result is None
