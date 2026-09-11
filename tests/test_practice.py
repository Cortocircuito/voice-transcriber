"""Tests for practice module."""

from contextlib import contextmanager
from unittest.mock import MagicMock

import pytest

from voice_to_text.config import Config
from voice_to_text.lessons import Lesson
from voice_to_text.practice import PracticeManager
from voice_to_text.recorder import RecorderError


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

    def test_lesson_completion_retry_restarts_the_lesson(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """The completion retry action must not return to lesson selection."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        lesson = Lesson(
            title="Lesson",
            url="https://example.com",
            date="2026-01-01",
            description="Description",
            levels=["0"],
            texts={"0": "One sentence."},
            level_urls={},
            paragraphs={},
        )
        mock_ui.show_paragraph_page.return_value = "next"
        mock_ui.show_practice_actions.return_value = "r"

        result = manager._run_lesson_practice_loop(lesson, [("One sentence.", 2)], "0")

        assert result == "retry"

    def test_paragraph_recording_retries_without_starting_when_microphone_fails(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Practice does not try to record after a failed microphone check."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        mock_recorder.check_microphone.return_value = (False, None)
        lesson = MagicMock(title="Lesson")

        result = manager._run_paragraph_recording(lesson, "Text", 10, 1, 1, 1)

        assert result == "retry"
        mock_recorder.start_recording.assert_not_called()

    def test_paragraph_recording_retries_when_starting_fails(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Recorder exceptions return to the practice retry action."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        mock_recorder.start_recording.side_effect = RecorderError("Device busy")
        lesson = MagicMock(title="Lesson")

        result = manager._run_paragraph_recording(lesson, "Text", 10, 1, 1, 1)

        assert result == "retry"
        mock_ui.show_error.assert_called_once_with("Device busy")

    def test_paragraph_recording_does_not_transcribe_when_finalization_fails(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Practice retries instead of scoring an incomplete WAV file."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        mock_recorder.stop_recording.return_value = False
        manager._run_progress = MagicMock()
        lesson = MagicMock(title="Lesson")

        result = manager._run_paragraph_recording(lesson, "Text", 10, 1, 1, 1)

        assert result == "retry"
        mock_transcriber.transcribe_streaming.assert_not_called()
        mock_ui.show_error.assert_called_once_with("Failed to finalize recording")

    def test_paragraph_recording_saves_early_stop_duration(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Practice history stores the duration from an Enter-stopped recording."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        manager._run_progress = MagicMock(return_value=4)
        mock_ui.console.input.return_value = "s"
        lesson = MagicMock(title="Lesson")

        assert manager._run_paragraph_recording(lesson, "Text", 10, 1, 1, 1) == "exit"

        assert mock_history.add_entry.call_args.kwargs["duration"] == 4

    def test_progress_stops_when_enter_is_requested(
        self,
        mock_config,
        mock_recorder,
        mock_transcriber,
        mock_ui,
        mock_history,
        mock_lesson_manager,
    ):
        """Practice progress exits immediately when the listener sees Enter."""
        manager = PracticeManager(
            mock_config,
            mock_recorder,
            mock_transcriber,
            mock_ui,
            mock_history,
            mock_lesson_manager,
        )
        mock_recorder.get_audio_level.return_value = 0.5

        @contextmanager
        def stop_listener():
            yield lambda: True

        mock_ui.recording_stop_listener.side_effect = stop_listener

        assert manager._run_progress(10) == 1
