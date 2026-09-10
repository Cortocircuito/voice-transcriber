"""Tests for dictation manager recording failures."""

from unittest.mock import MagicMock

import pytest

from voice_to_text.config import Config
from voice_to_text.dictation import DictationManager
from voice_to_text.recorder import RecorderError


@pytest.fixture
def manager() -> DictationManager:
    """Create a dictation manager with isolated collaborators."""
    return DictationManager(
        config=Config(),
        recorder=MagicMock(),
        transcriber=MagicMock(),
        ui=MagicMock(),
        history=MagicMock(),
    )


def test_run_returns_without_recording_when_microphone_is_unavailable(
    manager: DictationManager,
) -> None:
    """A failed microphone check must not start recording."""
    manager.recorder.check_microphone.return_value = (False, None)

    manager.run()

    manager.recorder.start_recording.assert_not_called()
    manager.transcriber.transcribe_streaming.assert_not_called()
    manager.ui.show_error.assert_called_once()


def test_run_returns_when_recording_start_fails(manager: DictationManager) -> None:
    """Recorder exceptions are shown to the user instead of escaping the CLI."""
    manager.recorder.check_microphone.return_value = (True, 0.5)
    manager.recorder.start_recording.side_effect = RecorderError("Device busy")

    manager.run()

    manager.transcriber.transcribe_streaming.assert_not_called()
    manager.ui.show_error.assert_called_once_with("Device busy")
