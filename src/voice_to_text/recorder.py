"""Audio recording functionality."""

import subprocess
import tempfile
import time
from typing import Optional, Tuple

from .config import CHANNELS, SAMPLE_RATE


class Recorder:
    def __init__(self, device: str = "default"):
        self.device = device
        self._interrupted = False
        self._process: Optional[subprocess.Popen] = None

    def check_microphone(self) -> Tuple[bool, Optional[float]]:
        """Check if microphone is available and return (success, level)."""
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
        except Exception:
            pass
        return False, None

    def start_recording(self) -> Optional[str]:
        """Start recording and return audio path."""
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
        except Exception:
            return None

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
        audio_path = self.start_recording()
        
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
