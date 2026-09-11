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


def test_run_does_not_transcribe_when_recording_finalization_fails(
    manager: DictationManager,
) -> None:
    """An incomplete WAV file must not be sent to Whisper."""
    manager.recorder.check_microphone.return_value = (True, 0.5)
    manager.recorder.start_recording.return_value = "/tmp/test.wav"
    manager.recorder.stop_recording.return_value = False
    manager._run_progress = MagicMock()

    manager.run()

    manager.transcriber.transcribe_streaming.assert_not_called()
    manager.ui.show_error.assert_called_once_with("Failed to finalize recording")


def test_run_allows_copy_and_stdout_export_before_exit(
    manager: DictationManager,
) -> None:
    """Post-transcription utilities keep the latest dictation available."""
    manager.recorder.check_microphone.return_value = (True, 0.5)
    manager.recorder.start_recording.return_value = "/tmp/test.wav"
    manager.recorder.stop_recording.return_value = True
    manager.transcriber.transcribe_streaming.return_value = (True, "Hello world")
    manager.ui.show_actions.side_effect = ["c", "e", "s"]
    manager._run_progress = MagicMock()

    manager.run()

    manager.ui.copy_text.assert_called_once_with("Hello world")
    manager.ui.export_text.assert_called_once_with("Hello world")
    manager.history.add_entry.assert_called_once()


def test_save_transcription_writes_text_file(
    manager: DictationManager, tmp_path
) -> None:
    """A path without an extension is saved as a text file."""
    path = tmp_path / "dictation"

    manager._save_transcription("Hello world", str(path))

    assert path.with_suffix(".txt").read_text(encoding="utf-8") == "Hello world\n"
    manager.ui.show_success.assert_called_once()


def test_save_transcription_writes_markdown_file(
    manager: DictationManager, tmp_path
) -> None:
    """Markdown exports include a document title and the transcription."""
    path = tmp_path / "dictation.md"

    manager._save_transcription("Hello world", str(path))

    assert path.read_text(encoding="utf-8") == "# Dictation\n\nHello world\n"


def test_save_transcription_rejects_unsupported_extension(
    manager: DictationManager, tmp_path
) -> None:
    """Only text and Markdown destinations are accepted."""
    manager._save_transcription("Hello world", str(tmp_path / "dictation.pdf"))

    manager.ui.show_error.assert_called_once()


def test_save_transcription_preserves_existing_file(
    manager: DictationManager, tmp_path
) -> None:
    """Saving never overwrites an existing destination."""
    path = tmp_path / "dictation.txt"
    path.write_text("Existing text", encoding="utf-8")

    manager._save_transcription("Hello world", str(path))

    assert path.read_text(encoding="utf-8") == "Existing text"
    manager.ui.show_error.assert_called_once()


def test_save_transcription_handles_invalid_path(manager: DictationManager) -> None:
    """Invalid path normalization returns an error instead of terminating dictation."""
    manager._save_transcription("Hello world", "/")

    manager.ui.show_error.assert_called_once()


def test_run_exits_cleanly_when_plain_text_export_fails(
    manager: DictationManager,
) -> None:
    """A closed stdout pipe does not crash the interactive dictation loop."""
    manager.recorder.check_microphone.return_value = (True, 0.5)
    manager.recorder.start_recording.return_value = "/tmp/test.wav"
    manager.recorder.stop_recording.return_value = True
    manager.transcriber.transcribe_streaming.return_value = (True, "Hello world")
    manager.ui.show_actions.return_value = "e"
    manager.ui.export_text.return_value = False
    manager._run_progress = MagicMock()

    manager.run()

    manager.ui.export_text.assert_called_once_with("Hello world")
    assert manager.ui.show_actions.call_count == 1


def test_run_saves_early_stop_duration_in_history(manager: DictationManager) -> None:
    """History reflects the time recorded when Enter stops dictation early."""
    manager.recorder.check_microphone.return_value = (True, 0.5)
    manager.recorder.start_recording.return_value = "/tmp/test.wav"
    manager.recorder.stop_recording.return_value = True
    manager.transcriber.transcribe_streaming.return_value = (True, "Hello world")
    manager.ui.show_actions.return_value = "s"
    manager._run_progress = MagicMock(return_value=4)

    manager.run()

    assert manager.history.add_entry.call_args.kwargs["duration"] == 4
