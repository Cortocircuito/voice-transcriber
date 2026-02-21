"""Tests for voice_to_text package."""

from unittest.mock import MagicMock, patch

import pytest

from voice_to_text.config import Config, SUPPORTED_LANGUAGES
from voice_to_text.recorder import (
    ArecordNotFoundError,
    MicrophoneNotFoundError,
    MicrophonePermissionError,
    Recorder,
    RecorderError,
)
from voice_to_text.transcriber import (
    ModelDownloadError,
    ModelLoadError,
    Transcriber,
    TranscriberError,
)


class TestConfig:
    def test_default_values(self):
        config = Config()
        assert config.duration == 15
        assert config.language == "en"
        assert config.ui_language == "en"
        assert config.recording_device is None
        assert config.model_size == "base"

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


class TestRecorder:
    @patch("voice_to_text.recorder.find_working_microphone")
    def test_init_default_device(self, mock_find):
        mock_find.return_value = "default"
        recorder = Recorder()
        assert recorder.device == "default"
        assert recorder._interrupted is False

    def test_init_custom_device(self):
        recorder = Recorder(device="hw:0,0")
        assert recorder.device == "hw:0,0"

    @patch("voice_to_text.recorder.find_working_microphone")
    @patch("voice_to_text.recorder.subprocess.run")
    def test_check_microphone_success(self, mock_run, mock_find):
        mock_find.return_value = "default"
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        recorder = Recorder()
        success, level = recorder.check_microphone()

        assert success is True
        assert level == 0.5
        mock_run.assert_called_once()

    @patch("voice_to_text.recorder.find_working_microphone")
    @patch("voice_to_text.recorder.subprocess.run")
    def test_check_microphone_failure(self, mock_run, mock_find):
        mock_find.return_value = "default"
        mock_run.side_effect = Exception("Device not found")

        recorder = Recorder()
        success, level = recorder.check_microphone()

        assert success is False
        assert level is None

    @patch("voice_to_text.recorder.subprocess.Popen")
    def test_start_recording(self, mock_popen):
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc

        recorder = Recorder(device="default")
        result = recorder.start_recording()

        assert result is not None
        assert result.endswith(".wav")

    def test_interrupt(self):
        recorder = Recorder()
        recorder._interrupted = False
        recorder.interrupt()
        assert recorder._interrupted is True

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.os.path.getsize")
    @patch("voice_to_text.recorder.os.path.exists")
    @patch("voice_to_text.recorder.os.unlink")
    def test_validate_prerecording_success(self, mock_unlink, mock_exists, mock_getsize, mock_popen):
        mock_exists.return_value = True
        mock_getsize.return_value = 64000

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_proc

        recorder = Recorder(device="default")
        success, message = recorder.validate_prerecording(test_duration=1)

        assert success is True

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.os.path.exists")
    @patch("voice_to_text.recorder.os.unlink")
    def test_validate_prerecording_file_too_small(self, mock_unlink, mock_exists, mock_popen):
        mock_exists.return_value = True

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (b"", b"")
        mock_popen.return_value = mock_proc

        with patch("voice_to_text.recorder.os.path.getsize", return_value=100):
            recorder = Recorder(device="default")
            success, message = recorder.validate_prerecording(test_duration=1)

            assert success is False
            assert "No audio detected" in message or "quiet" in message.lower()

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.os.path.exists")
    @patch("voice_to_text.recorder.os.unlink")
    def test_validate_prerecording_permission_denied(self, mock_unlink, mock_exists, mock_popen):
        mock_exists.return_value = False

        mock_proc = MagicMock()
        mock_proc.returncode = 13
        mock_proc.communicate.return_value = (b"", b"Permission denied")
        mock_popen.return_value = mock_proc

        recorder = Recorder(device="default")
        success, message = recorder.validate_prerecording(test_duration=1)

        assert success is False

    @patch("voice_to_text.recorder.find_working_microphone")
    @patch.object(Recorder, "validate_prerecording")
    @patch("voice_to_text.recorder.time.sleep")
    @patch("voice_to_text.recorder.os.path.getsize")
    @patch("voice_to_text.recorder.os")
    def test_record_with_validation_long_duration(self, mock_os, mock_getsize, mock_sleep, mock_validate, mock_find):
        mock_find.return_value = "default"
        mock_validate.return_value = (True, "OK")
        mock_getsize.return_value = 64000
        mock_os.path.getsize.return_value = 64000
        mock_os.path.exists.return_value = True

        with patch("voice_to_text.recorder.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc

            with patch("voice_to_text.recorder.subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                recorder = Recorder()
                result = recorder.record(duration=15, validate_mic=False)

                assert result is not None

    @patch("voice_to_text.recorder.find_working_microphone")
    @patch("voice_to_text.recorder.time.sleep")
    @patch("voice_to_text.recorder.os.path.getsize")
    @patch("voice_to_text.recorder.os")
    def test_record_short_duration_skips_validation(self, mock_os, mock_getsize, mock_sleep, mock_find):
        mock_find.return_value = "default"
        mock_getsize.return_value = 64000
        mock_os.path.getsize.return_value = 64000
        mock_os.path.exists.return_value = True

        with patch("voice_to_text.recorder.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc

            with patch("voice_to_text.recorder.subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                recorder = Recorder()
                result = recorder.record(duration=5, validate_mic=False)

                assert result is not None

    @patch("voice_to_text.recorder.find_working_microphone")
    @patch("voice_to_text.recorder.os.path.getsize")
    @patch("voice_to_text.recorder.os")
    def test_record_empty_file_returns_none(self, mock_os, mock_getsize, mock_find):
        mock_find.return_value = "default"
        mock_getsize.return_value = 0
        mock_os.path.getsize.return_value = 0
        mock_os.path.exists.return_value = True

        with patch("voice_to_text.recorder.subprocess.Popen") as mock_popen:
            mock_proc = MagicMock()
            mock_popen.return_value = mock_proc

            with patch("voice_to_text.recorder.subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                recorder = Recorder()
                result = recorder.record(duration=1, validate_mic=False)

                assert result is None


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
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_success(self, mock_unlink, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.text = "Hello world"
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        config = Config(language="en")
        success, text = transcriber.transcribe("/tmp/test.wav", config)

        assert success is True
        assert text == "Hello world"
        mock_unlink.assert_called_once_with("/tmp/test.wav")

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_empty_result(self, mock_unlink, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_model.transcribe.return_value = ([], None)

        transcriber = Transcriber()
        config = Config(language="en")
        success, text = transcriber.transcribe("/tmp/test.wav", config)

        assert success is True
        assert text == ""

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_exception(self, mock_unlink, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_model.transcribe.side_effect = Exception("Model error")

        transcriber = Transcriber()
        config = Config(language="en")
        success, text = transcriber.transcribe("/tmp/test.wav", config)

        assert success is False
        assert text == ""

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    @patch("voice_to_text.transcriber.os.unlink")
    def test_transcribe_cleans_up_audio_file(self, mock_unlink, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        mock_segment = MagicMock()
        mock_segment.text = "Test"
        mock_model.transcribe.return_value = ([mock_segment], None)

        transcriber = Transcriber()
        config = Config()
        transcriber.transcribe("/tmp/audio.wav", config)

        mock_unlink.assert_called_once_with("/tmp/audio.wav")


class TestRecorderErrorHandling:
    def test_recorder_error_exception(self):
        with pytest.raises(RecorderError):
            raise RecorderError("Test error")

    def test_arecord_not_found_error(self):
        with pytest.raises(ArecordNotFoundError):
            raise ArecordNotFoundError("arecord not found")

    def test_microphone_not_found_error(self):
        with pytest.raises(MicrophoneNotFoundError):
            raise MicrophoneNotFoundError("No microphone found")

    def test_microphone_permission_error(self):
        with pytest.raises(MicrophonePermissionError):
            raise MicrophonePermissionError("Permission denied")

    @patch("voice_to_text.recorder.shutil.which")
    def test_check_arecord_available_true(self, mock_which):
        mock_which.return_value = "/usr/bin/arecord"
        recorder = Recorder()
        assert recorder.check_arecord_available() is True

    @patch("voice_to_text.recorder.shutil.which")
    def test_check_arecord_available_false(self, mock_which):
        mock_which.return_value = None
        recorder = Recorder()
        assert recorder.check_arecord_available() is False

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.shutil.which")
    def test_start_recording_arecord_not_found(self, mock_which, mock_popen):
        mock_which.return_value = None
        recorder = Recorder()
        with pytest.raises(ArecordNotFoundError):
            recorder.start_recording()

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.shutil.which")
    def test_start_recording_device_not_found(self, mock_which, mock_popen):
        mock_which.return_value = "/usr/bin/arecord"
        mock_popen.side_effect = FileNotFoundError("Device not found")
        recorder = Recorder()
        with pytest.raises(MicrophoneNotFoundError):
            recorder.start_recording()

    @patch("voice_to_text.recorder.subprocess.Popen")
    @patch("voice_to_text.recorder.shutil.which")
    def test_start_recording_permission_denied(self, mock_which, mock_popen):
        mock_which.return_value = "/usr/bin/arecord"
        mock_popen.side_effect = PermissionError("Permission denied")
        recorder = Recorder()
        with pytest.raises(MicrophonePermissionError):
            recorder.start_recording()


class TestTranscriberErrorHandling:
    def test_transcriber_error_exception(self):
        with pytest.raises(TranscriberError):
            raise TranscriberError("Test error")

    def test_model_download_error(self):
        with pytest.raises(ModelDownloadError):
            raise ModelDownloadError("Download failed")

    def test_model_load_error(self):
        with pytest.raises(ModelLoadError):
            raise ModelLoadError("Load failed")

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    def test_transcribe_file_not_found(self, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = False
        mock_getsize.return_value = 1000

        transcriber = Transcriber()
        config = Config()
        success, text = transcriber.transcribe("/tmp/nonexistent.wav", config)

        assert success is False
        assert text == ""

    @patch("voice_to_text.transcriber.WhisperModel")
    @patch("voice_to_text.transcriber.os.path.exists")
    @patch("voice_to_text.transcriber.os.path.getsize")
    def test_transcribe_empty_file(self, mock_getsize, mock_exists, mock_whisper):
        mock_exists.return_value = True
        mock_getsize.return_value = 0

        transcriber = Transcriber()
        config = Config()
        success, text = transcriber.transcribe("/tmp/empty.wav", config)

        assert success is False
        assert text == ""

    @patch("voice_to_text.transcriber.WhisperModel")
    def test_load_model_success(self, mock_whisper):
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        transcriber = Transcriber()
        success, message = transcriber.load_model()

        assert success is True

    @patch("voice_to_text.transcriber.WhisperModel")
    def test_load_model_download_error(self, mock_whisper):
        mock_whisper.side_effect = OSError("No such file or directory")

        transcriber = Transcriber()
        success, message = transcriber.load_model()

        assert success is False
        assert "Download" in message
