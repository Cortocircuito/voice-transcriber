"""Tests for UI module."""

import signal
from unittest.mock import MagicMock, call, patch

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
        with patch("voice_to_text.ui.Console"), patch("voice_to_text.ui.signal"):
            ui = UI(mock_config)
            assert ui.config == mock_config

    def test_init_redraw_fn_starts_none(self, mock_config):
        """_redraw_fn is None after construction."""
        with patch("voice_to_text.ui.Console"), patch("voice_to_text.ui.signal"):
            ui = UI(mock_config)
            assert ui._redraw_fn is None

    def test_setup_resize_handler_registers_sigwinch(self, mock_config):
        """_setup_resize_handler registers a SIGWINCH handler on Unix."""
        with patch("voice_to_text.ui.Console"):
            mock_signal = MagicMock()
            mock_signal.SIGWINCH = signal.SIGWINCH
            mock_signal.getsignal.return_value = None
            with patch("voice_to_text.ui.signal", mock_signal):
                UI(mock_config)
                mock_signal.signal.assert_called_once_with(
                    signal.SIGWINCH, mock_signal.signal.call_args[0][1]
                )

    def test_setup_resize_handler_skips_on_no_sigwinch(self, mock_config):
        """_setup_resize_handler does nothing when SIGWINCH is absent (Windows)."""
        with patch("voice_to_text.ui.Console"):
            # spec includes 'signal' so we can assert on it, but not 'SIGWINCH'
            mock_signal = MagicMock(spec=["signal", "getsignal"])
            with patch("voice_to_text.ui.signal", mock_signal):
                UI(mock_config)
                mock_signal.signal.assert_not_called()

    def test_resize_handler_calls_redraw_fn_when_set(self, mock_config):
        """SIGWINCH handler clears screen and calls _redraw_fn when one is set."""
        captured_handler = {}

        def fake_signal(sig, handler):
            captured_handler["fn"] = handler

        with patch("voice_to_text.ui.Console") as mock_console_cls:
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console_cls.return_value = console_instance

            mock_signal = MagicMock()
            mock_signal.SIGWINCH = signal.SIGWINCH
            mock_signal.getsignal.return_value = None
            mock_signal.signal.side_effect = fake_signal

            with patch("voice_to_text.ui.signal", mock_signal):
                ui = UI(mock_config)

        redraw = MagicMock()
        ui._redraw_fn = redraw
        captured_handler["fn"](signal.SIGWINCH, None)

        console_instance.clear.assert_called_once()
        redraw.assert_called_once()

    def test_resize_handler_skips_redraw_when_no_fn(self, mock_config):
        """SIGWINCH handler does not call clear when _redraw_fn is None."""
        captured_handler = {}

        def fake_signal(sig, handler):
            captured_handler["fn"] = handler

        with patch("voice_to_text.ui.Console") as mock_console_cls:
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console_cls.return_value = console_instance

            mock_signal = MagicMock()
            mock_signal.SIGWINCH = signal.SIGWINCH
            mock_signal.getsignal.return_value = None
            mock_signal.signal.side_effect = fake_signal

            with patch("voice_to_text.ui.signal", mock_signal):
                ui = UI(mock_config)

        assert ui._redraw_fn is None
        captured_handler["fn"](signal.SIGWINCH, None)
        console_instance.clear.assert_not_called()

    def test_resize_handler_chains_old_handler(self, mock_config):
        """SIGWINCH handler calls the previously registered handler."""
        captured_handler = {}
        old_handler = MagicMock()

        def fake_signal(sig, handler):
            captured_handler["fn"] = handler

        with patch("voice_to_text.ui.Console") as mock_console_cls:
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console_cls.return_value = console_instance

            mock_signal = MagicMock()
            mock_signal.SIGWINCH = signal.SIGWINCH
            mock_signal.getsignal.return_value = old_handler
            mock_signal.signal.side_effect = fake_signal

            with patch("voice_to_text.ui.signal", mock_signal):
                UI(mock_config)

        captured_handler["fn"](signal.SIGWINCH, None)
        old_handler.assert_called_once_with(signal.SIGWINCH, None)

    def test_show_menu_clears_redraw_fn_after_input(self, mock_config):
        """show_menu sets _redraw_fn before input and clears it afterwards."""
        with (
            patch("voice_to_text.ui.Console") as mock_console_cls,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="4")
            mock_console_cls.return_value = console_instance

            ui = UI(mock_config)
            result = ui.show_menu()

            assert result == "4"
            assert ui._redraw_fn is None

    def test_show_config_clears_redraw_fn_after_input(self, mock_config):
        """show_config clears _redraw_fn after input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console_cls,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="6")
            mock_console_cls.return_value = console_instance

            ui = UI(mock_config)
            ui.show_config()

            assert ui._redraw_fn is None

    def test_create_panel(self, mock_config):
        """Test panel creation."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui._create_panel("Test content", title="Test Title")
            assert result is not None

    def test_menu_table(self, mock_config):
        """Test menu table creation."""
        with patch("voice_to_text.ui.Console"), patch("voice_to_text.ui.signal"):
            ui = UI(mock_config)
            items = [("[1]", "Option 1"), ("[2]", "Option 2")]
            result = ui._menu_table(items)
            assert result is not None

    def test_prompt_duration_change(self, mock_config):
        """Test duration change prompt."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="30")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 30
            assert ui._redraw_fn is None

    def test_prompt_duration_change_empty(self, mock_config):
        """Test duration change with empty input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 15

    def test_prompt_duration_change_invalid(self, mock_config):
        """Test duration change with invalid input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="abc")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration_change(15, 30)

            assert result == 15

    def test_confirm_clear_history_no_entries(self, mock_config):
        """Test confirm clear history with no entries."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.confirm_clear_history(0)

            assert result is False

    def test_prompt_duration_valid(self, mock_config):
        """Test prompt duration with valid input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="30")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result == 30

    def test_prompt_duration_empty(self, mock_config):
        """Test prompt duration with empty input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result is None

    def test_prompt_duration_invalid(self, mock_config):
        """Test prompt duration with invalid input."""
        with (
            patch("voice_to_text.ui.Console") as mock_console,
            patch("voice_to_text.ui.signal"),
        ):
            console_instance = MagicMock()
            console_instance.width = 80
            console_instance.input = MagicMock(return_value="abc")
            mock_console.return_value = console_instance

            ui = UI(mock_config)
            result = ui.prompt_duration()

            assert result is None
