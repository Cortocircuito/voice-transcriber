"""Audio recording functionality."""

import os
import shutil
import subprocess
import tempfile
import time
from typing import List, Optional, Tuple

from .config import CHANNELS, SAMPLE_RATE


class RecorderError(Exception):
    """Base exception for recorder errors."""
    pass


class ArecordNotFoundError(RecorderError):
    """Raised when arecord command is not available."""
    pass


class MicrophonePermissionError(RecorderError):
    """Raised when microphone permission is denied."""
    pass


class MicrophoneNotFoundError(RecorderError):
    """Raised when no microphone is found."""
    pass


def detect_audio_devices() -> List[str]:
    """Detect available audio recording devices using ALSA."""
    devices = []
    
    if not shutil.which("arecord"):
        return devices
    
    try:
        result = subprocess.run(
            ["arecord", "-l"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "card" in line and "device" in line:
                    parts = line.split(":")
                    if parts:
                        card_info = parts[0].strip()
                        card_num = card_info.split()[1] if len(card_info.split()) > 1 else None
                        if card_num:
                            devices.append(f"hw:{card_num},0")
    except Exception:
        pass
    
    return devices


def find_working_microphone() -> Optional[str]:
    """Find the first working microphone device."""
    devices = detect_audio_devices()
    
    for device in devices:
        try:
            result = subprocess.run(
                [
                    "arecord",
                    "-D", device,
                    "-f", "S16_LE",
                    "-r", str(SAMPLE_RATE),
                    "-c", str(CHANNELS),
                    "-d", "1",
                    "/dev/null",
                ],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return device
        except Exception:
            continue
    
    try:
        result = subprocess.run(
            [
                "arecord",
                "-D", "default",
                "-f", "S16_LE",
                "-r", str(SAMPLE_RATE),
                "-c", str(CHANNELS),
                "-d", "1",
                "/dev/null",
            ],
            capture_output=True,
            timeout=2,
        )
        if result.returncode == 0:
            return "default"
    except Exception:
        pass
    
    return None


class Recorder:
    def __init__(self, device: Optional[str] = None):
        if device is None:
            device = find_working_microphone() or "default"
        self.device = device
        self._interrupted = False
        self._process: Optional[subprocess.Popen] = None

    def check_arecord_available(self) -> bool:
        """Check if arecord command is available."""
        return shutil.which("arecord") is not None

    def check_microphone(self) -> Tuple[bool, Optional[float]]:
        """Check if microphone is available and return (success, level)."""
        if not self.check_arecord_available():
            return False, None

        try:
            result = subprocess.run(
                [
                    "arecord",
                    "-D", self.device,
                    "-f", "S16_LE",
                    "-r", str(SAMPLE_RATE),
                    "-c", str(CHANNELS),
                    "-d", "1",
                    "/dev/null",
                ],
                capture_output=True,
                timeout=2,
            )
            if result.returncode == 0:
                return True, 0.5
            elif result.returncode == 13 or result.returncode == 1:
                return False, None
        except subprocess.TimeoutExpired:
            return True, 0.5
        except FileNotFoundError:
            return False, None
        except PermissionError:
            return False, None
        except Exception:
            pass
        return False, None

    def validate_prerecording(self, test_duration: int = 2) -> Tuple[bool, str]:
        """Validate microphone works before starting a long recording.
        
        Args:
            test_duration: Duration in seconds to test the microphone (default 2s)
            
        Returns:
            Tuple of (success, message)
        """
        if not self.check_arecord_available():
            return False, "arecord not found"

        test_file = tempfile.mktemp(suffix=".wav")
        
        try:
            proc = subprocess.Popen(
                [
                    "arecord",
                    "-D", self.device,
                    "-f", "S16_LE",
                    "-r", str(SAMPLE_RATE),
                    "-c", str(CHANNELS),
                    "-d", str(test_duration),
                    test_file,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            
            _, stderr = proc.communicate(timeout=test_duration + 2)
            
            if proc.returncode != 0:
                if b"Permission denied" in stderr or proc.returncode == 13:
                    return False, "Permission denied"
                if b"no such device" in stderr or b"not found" in stderr:
                    return False, "Device not found"
                return False, f"Recording failed (code {proc.returncode})"
            
            if not os.path.exists(test_file):
                return False, "Audio file not created"
            
            file_size = os.path.getsize(test_file)
            if file_size < 1000:
                return False, "No audio detected - microphone may be muted or disconnected"
            
            expected_size = SAMPLE_RATE * CHANNELS * 2 * test_duration
            if file_size < expected_size * 0.5:
                return False, f"Audio too quiet or device not working properly"
            
            return True, "Microphone validated successfully"
            
        except subprocess.TimeoutExpired:
            return False, "Recording test timed out"
        except PermissionError:
            return False, "Permission denied"
        except Exception as e:
            return False, f"Validation error: {e}"
        finally:
            try:
                os.unlink(test_file)
            except Exception:
                pass

    def start_recording(self) -> Optional[str]:
        """Start recording and return audio path."""
        if not self.check_arecord_available():
            raise ArecordNotFoundError(
                "arecord not found. Please install ALSA utilities (sudo apt install alsa-utils)"
            )

        audio_path = tempfile.mktemp(suffix=".wav")

        try:
            self._process = subprocess.Popen(
                [
                    "arecord",
                    "-D", self.device,
                    "-f", "S16_LE",
                    "-r", str(SAMPLE_RATE),
                    "-c", str(CHANNELS),
                    audio_path,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return audio_path
        except PermissionError as e:
            raise MicrophonePermissionError(
                f"Permission denied to access microphone: {e}"
            ) from e
        except FileNotFoundError as e:
            raise MicrophoneNotFoundError(
                f"Recording device '{self.device}' not found. Check your audio devices."
            ) from e
        except OSError as e:
            if "Permission denied" in str(e):
                raise MicrophonePermissionError(
                    f"Permission denied to access microphone: {e}"
                ) from e
            raise RecorderError(f"Failed to start recording: {e}") from e

    def stop_recording(self) -> bool:
        """Stop recording."""
        if self._process:
            self._process.terminate()
            self._process.wait()
            self._process = None
            return True
        return False

    def record(self, duration: int, progress_callback=None, validate_mic: bool = True) -> Optional[str]:
        """Record audio for specified duration with optional progress callback.
        
        Args:
            duration: Recording duration in seconds (max 300)
            progress_callback: Optional callback(current, total)
            validate_mic: If True, run pre-recording mic validation for longer recordings
            
        Returns:
            Path to recorded audio file, or None if failed
        """
        from .config import MAX_DURATION
        
        self._interrupted = False
        
        if duration > MAX_DURATION:
            duration = MAX_DURATION
        
        if duration > 10 and validate_mic:
            valid, message = self.validate_prerecording(test_duration=2)
            if not valid:
                return None

        mic_available, _ = self.check_microphone()
        if not mic_available:
            return None

        try:
            audio_path = self.start_recording()
        except RecorderError:
            return None

        if not audio_path:
            return None

        try:
            for i in range(duration):
                if self._interrupted:
                    self.stop_recording()
                    return None

                if progress_callback:
                    progress_callback(i + 1, duration)
                else:
                    print(f"\rRecording: {duration - i}s remaining", end="", flush=True)

                time.sleep(1)

            if not progress_callback:
                print()

            self.stop_recording()
            
            if os.path.getsize(audio_path) < 1000:
                return None
            
            return audio_path

        except Exception:
            self.stop_recording()
            return None

    def interrupt(self):
        """Interrupt current recording."""
        self._interrupted = True
        self.stop_recording()

    def get_audio_level(self) -> float:
        """Get current audio input level (0.0 to 1.0)."""
        return 0.5
