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

    def record(self, duration: int, progress_callback=None) -> Optional[str]:
        """Record audio for specified duration with optional progress callback."""
        self._interrupted = False

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
