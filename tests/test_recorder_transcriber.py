"""Tests for voice_to_text package."""

from unittest.mock import MagicMock, patch

import pytest

from voice_to_text.config import Config, SUPPORTED_LANGUAGES
from voice_to_text.recorder import Recorder
from voice_to_text.transcriber import Transcriber


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


class TestRecorder:
    def test_init_default_device(self):
        recorder = Recorder()
        assert recorder.device == "default"
        assert recorder._interrupted is False

    def test_init_custom_device(self):
        recorder = Recorder(device="hw:0,0")
        assert recorder.device == "hw:0,0"

    @patch("voice_to_text.recorder.subprocess.run")
    def test_check_microphone_success(self, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        recorder = Recorder()
        result = recorder.check_microphone()

        assert result is True
        mock_run.assert_called_once()

    @patch("voice_to_text.recorder.subprocess.run")
    def test_check_microphone_failure(self, mock_run):
        mock_run.side_effect = Exception("Device not found")

        recorder = Recorder()
        result = recorder.check_microphone()

        assert result is False

    @patch("voice_to_text.recorder.subprocess.run")
    @patch("voice_to_text.recorder.time.sleep")
    @patch("voice_to_text.recorder.subprocess.Popen")
    def test_record_success(self, mock_popen, mock_sleep, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        recorder = Recorder()
        result = recorder.record(1)

        assert result is not None
        assert result.endswith(".wav")

    @patch("voice_to_text.recorder.subprocess.run")
    @patch("voice_to_text.recorder.time.sleep")
    @patch("voice_to_text.recorder.subprocess.Popen")
    def test_record_interrupted(self, mock_popen, mock_sleep, mock_run):
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        recorder = Recorder()
        result = recorder.record(5)

        assert result.endswith(".wav")

    def test_interrupt(self):
        recorder = Recorder()
        recorder._interrupted = False
        recorder.interrupt()
        assert recorder._interrupted is True


class TestTranscriber:
    def test_init_default_params(self):
        transcriber = Transcriber()
        assert transcriber.model_size == "base"
        assert transcriber.device == "cpu"
        assert transcriber.compute_type == "int8"
        assert transcriber._model is None

    def test_init_custom_params(self):
        transcriber = Transcriber(model_size="small", device="cuda", compute_type="float16")
        assert transcriber.model_size == "small"
        assert transcriber.device == "cuda"
        assert transcriber.compute_type == "float16"

    @patch("voice_to_text.transcriber.WhisperModel")
    def test_model_lazy_loading(self, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        transcriber = Transcriber()
        assert transcriber._model is None

        _ = transcriber.model

        mock_whisper.assert_called_once_with("base", device="cpu", compute_type="int8")

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_success(self, mock_unlink, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        config = Config(language="en")
        result = transcriber.transcribe("/tmp/test.wav", config)

        assert result is True
        mock_unlink.assert_called_once_with("/tmp/test.wav")

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_empty_result(self, mock_unlink, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_model.transcribe.return_value = ([], None)

        transcriber = Transcriber()
        config = Config(language="en")
        result = transcriber.transcribe("/tmp/test.wav", config)

        assert result is False

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_exception(self, mock_unlink, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_model.transcribe.side_effect = Exception("Model error")

        transcriber = Transcriber()
        config = Config(language="en")
        result = transcriber.transcribe("/tmp/test.wav", config)

        assert result is False

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_cleans_up_audio_file(self, mock_unlink, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.text = "Test"
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        config = Config()
        transcriber.transcribe("/tmp/audio.wav", config)

        mock_unlink.assert_called_once_with("/tmp/audio.wav")
