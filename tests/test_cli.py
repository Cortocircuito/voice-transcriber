"""Tests for CLI module."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest

from voice_to_text.cli import CLI
from voice_to_text.config import Config


class TestCLI:
    """Tests for CLI class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Config()
        config.ui_language = "en"
        config.language = "en"
        config.duration = 15
        return config

    @pytest.fixture
    def mock_recorder(self):
        """Create a mock recorder."""
        with patch("voice_to_text.cli.Recorder") as mock:
            recorder_instance = MagicMock()
            mock.return_value = recorder_instance
            yield recorder_instance

    @pytest.fixture
    def mock_transcriber(self):
        """Create a mock transcriber."""
        with patch("voice_to_text.cli.Transcriber") as mock:
            transcriber_instance = MagicMock()
            mock.return_value = transcriber_instance
            yield transcriber_instance

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI."""
        with patch("voice_to_text.cli.UI") as mock:
            ui_instance = MagicMock()
            ui_instance.console = MagicMock()
            mock.return_value = ui_instance
            yield ui_instance

    @pytest.fixture
    def mock_history(self):
        """Create a mock history manager."""
        with patch("voice_to_text.cli.HistoryManager") as mock:
            history_instance = MagicMock()
            history_instance.get_entries = MagicMock(return_value=[])
            mock.return_value = history_instance
            yield history_instance

    @pytest.fixture
    def mock_lesson_manager(self):
        """Create a mock lesson manager."""
        with patch("voice_to_text.cli.LessonManager") as mock:
            manager_instance = MagicMock()
            mock.return_value = manager_instance
            yield manager_instance

    def test_init_with_default_config(self):
        """Test CLI initialization with default config."""
        with (
            patch("voice_to_text.cli.Recorder") as mock_recorder,
            patch("voice_to_text.cli.Transcriber") as mock_transcriber,
            patch("voice_to_text.cli.UI") as mock_ui,
            patch("voice_to_text.cli.HistoryManager") as mock_history,
            patch("voice_to_text.cli.LessonManager") as mock_manager,
        ):
            cli = CLI()

            assert cli.config is not None

    def test_init_with_custom_config(self, mock_config):
        """Test CLI initialization with custom config."""
        with (
            patch("voice_to_text.cli.Recorder") as mock_recorder,
            patch("voice_to_text.cli.Transcriber") as mock_transcriber,
            patch("voice_to_text.cli.UI") as mock_ui,
            patch("voice_to_text.cli.HistoryManager") as mock_history,
            patch("voice_to_text.cli.LessonManager") as mock_manager,
        ):
            cli = CLI(mock_config)

            assert cli.config == mock_config

    def test_init_creates_managers(self, mock_config):
        """Test that CLI creates all managers."""
        with (
            patch("voice_to_text.cli.Recorder") as mock_recorder,
            patch("voice_to_text.cli.Transcriber") as mock_transcriber,
            patch("voice_to_text.cli.UI") as mock_ui,
            patch("voice_to_text.cli.HistoryManager") as mock_history,
            patch("voice_to_text.cli.LessonManager") as mock_manager,
        ):
            cli = CLI(mock_config)

            assert cli.recorder is not None
            assert cli.transcriber is not None
            assert cli.ui is not None
            assert cli.history is not None

    def test_cleanup_with_entries(self, mock_config, mock_history):
        """Test cleanup with history entries."""
        mock_history.get_entries = MagicMock(return_value=[{"text": "test"}])

        with (
            patch("voice_to_text.cli.Recorder"),
            patch("voice_to_text.cli.Transcriber"),
            patch("voice_to_text.cli.UI") as mock_ui,
            patch("voice_to_text.cli.LessonManager"),
        ):
            mock_ui_instance = MagicMock()
            mock_ui_instance.console = MagicMock()
            mock_ui.return_value = mock_ui_instance

            cli = CLI(mock_config)
            cli._cleanup()

            mock_history.save.assert_called_once()

    def test_cleanup_without_entries(self, mock_config, mock_history):
        """Test cleanup without history entries."""
        mock_history.get_entries = MagicMock(return_value=[])

        with (
            patch("voice_to_text.cli.Recorder"),
            patch("voice_to_text.cli.Transcriber"),
            patch("voice_to_text.cli.UI") as mock_ui,
            patch("voice_to_text.cli.LessonManager"),
        ):
            mock_ui_instance = MagicMock()
            mock_ui_instance.console = MagicMock()
            mock_ui.return_value = mock_ui_instance

            cli = CLI(mock_config)
            cli._cleanup()

            mock_history.save.assert_called_once()


class TestCLIArguments:
    """Tests for CLI argument parsing."""

    def test_main_default_args(self):
        """Test main with default arguments."""
        with (
            patch("voice_to_text.cli.CLI") as mock_cli_class,
            patch("voice_to_text.cli.Config") as mock_config_class,
        ):
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            with patch("sys.argv", ["voice-to-text"]):
                from voice_to_text.cli import main

                main()

            mock_cli_class.assert_called_once()
            mock_cli.run.assert_called_once_with(quick=False)

    def test_main_quick_args(self):
        """Test main with quick argument."""
        with (
            patch("voice_to_text.cli.CLI") as mock_cli_class,
            patch("voice_to_text.cli.Config") as mock_config_class,
        ):
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            with patch("sys.argv", ["voice-to-text", "--quick"]):
                from voice_to_text.cli import main

                main()

            mock_cli.run.assert_called_once_with(quick=True)

    def test_main_with_duration(self):
        """Test main with duration argument."""
        with (
            patch("voice_to_text.cli.CLI") as mock_cli_class,
            patch("voice_to_text.cli.Config") as mock_config_class,
        ):
            mock_config = MagicMock()
            mock_config_class.return_value = mock_config

            mock_cli = MagicMock()
            mock_cli_class.return_value = mock_cli

            with patch("sys.argv", ["voice-to-text", "--duration", "30"]):
                from voice_to_text.cli import main

                main()

            mock_config_class.assert_called_once_with(duration=30, language="en")
