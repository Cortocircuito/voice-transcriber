"""Tests for practice module."""

from unittest.mock import MagicMock, patch

import pytest

from voice_to_text.practice import PracticeManager
from voice_to_text.config import Config


class TestPracticeManager:
    """Tests for PracticeManager class."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config."""
        config = Config()
        config.ui_language = "en"
        config.language = "en"
        return config

    @pytest.fixture
    def mock_recorder(self):
        """Create a mock recorder."""
        recorder = MagicMock()
        recorder.check_microphone = MagicMock(return_value=(True, 0.5))
        recorder.start_recording = MagicMock(return_value="/tmp/test.wav")
        recorder.stop_recording = MagicMock()
        return recorder

    @pytest.fixture
    def mock_transcriber(self):
        """Create a mock transcriber."""
        transcriber = MagicMock()
        transcriber.transcribe_streaming = MagicMock(
            return_value=(True, "transcribed text")
        )
        return transcriber

    @pytest.fixture
    def mock_ui(self):
        """Create a mock UI."""
        ui = MagicMock()
        return ui

    @pytest.fixture
    def mock_history(self):
        """Create a mock history manager."""
        history = MagicMock()
        return history

    @pytest.fixture
    def mock_lesson_manager(self):
        """Create a mock lesson manager."""
        manager = MagicMock()
        return manager

    def test_init(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test PracticeManager initialization."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        assert manager.config == mock_config
        assert manager.recorder == mock_recorder
        assert manager.transcriber == mock_transcriber
        assert manager.ui == mock_ui

    def test_split_into_paragraphs_basic(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test splitting text into paragraphs."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        text = "This is first sentence. This is second sentence."
        result = manager._split_into_paragraphs(text)

        assert isinstance(result, list)
        assert len(result) > 0

    def test_split_into_paragraphs_single_sentence(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test splitting single sentence."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        text = "This is a single sentence."
        result = manager._split_into_paragraphs(text)

        assert len(result) == 1
        assert result[0][1] > 0

    def test_split_into_paragraphs_empty(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test splitting empty text."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        result = manager._split_into_paragraphs("")

        assert len(result) == 1

    def test_group_paragraphs_basic(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test grouping paragraphs into pages."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        paragraphs = [
            ("First paragraph here.", 3),
            ("Second paragraph here.", 3),
            ("Third paragraph here.", 3),
            ("Fourth paragraph here.", 3),
        ]

        result = manager._group_paragraphs(paragraphs, per_page=2)

        assert len(result) == 2

    def test_group_paragraphs_single_page(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test grouping with single page."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        paragraphs = [
            ("First paragraph.", 3),
        ]

        result = manager._group_paragraphs(paragraphs, per_page=2)

        assert len(result) == 1

    def test_calculate_reading_time(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test reading time calculation."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        result = manager._calculate_reading_time(60)

        assert result >= 10
        assert isinstance(result, int)

    def test_calculate_reading_time_zero(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test reading time with zero words."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        result = manager._calculate_reading_time(0)

        assert result >= 10

    def test_calculate_reading_time_many_words(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Test reading time with many words."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )

        result = manager._calculate_reading_time(300)

        assert result > 10
