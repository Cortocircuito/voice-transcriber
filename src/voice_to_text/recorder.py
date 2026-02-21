"""Audio recording functionality."""

import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional

from .config import CHANNELS, SAMPLE_RATE


class Recorder:
    def __init__(self, device: str = "default"):
        self.device = device
        self._interrupted = False

    def check_microphone(self) -> bool:
        print("🎤 Mic: ", end="", flush=True)
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
                print("✅")
                return True
        except Exception:
            pass
        print("⚠️")
        return False

    def record(self, duration: int) -> Optional[str]:
        self._interrupted = False
        self.check_microphone()
        print("Iniciando... ¡HABLA AHORA!")

        audio_path = tempfile.mktemp(suffix=".wav")

        try:
            proc = subprocess.Popen(
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

            for i in range(duration, 0, -1):
                if self._interrupted:
                    proc.terminate()
                    proc.wait()
                    return None
                print(f"\rRestante: {i} s", end="", flush=True)
                time.sleep(1)
            print()

            proc.terminate()
            proc.wait()
            return audio_path

        except Exception as e:
            print(f"Error grabando: {e}")
            return None

    def interrupt(self):
        self._interrupted = True
        print("\nInterrumpido.")
