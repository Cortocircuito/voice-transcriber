"""Audio transcription functionality."""

import os
from pathlib import Path
from typing import Optional, Tuple

from rich.console import Console

from faster_whisper import WhisperModel

from .config import Config

console = Console()


class TranscriberError(Exception):
    """Base exception for transcriber errors."""
    pass


class ModelDownloadError(TranscriberError):
    """Raised when model download fails."""
    pass


class ModelLoadError(TranscriberError):
    """Raised when model fails to load."""
    pass


class TranscriptionError(TranscriberError):
    """Raised when transcription fails."""
    pass


class Transcriber:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            console.print(f"[dim]⏳ Loading Whisper model ({self.model_size})...[/dim]")
            try:
                self._model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type,
                )
            except OSError as e:
                if "No such file or directory" in str(e) or "404" in str(e):
                    raise ModelDownloadError(
                        f"Failed to download model '{self.model_size}'. "
                        f"Please check your internet connection and try again. Error: {e}"
                    ) from e
                if "Permission denied" in str(e):
                    raise ModelLoadError(
                        f"Permission denied while loading model. Check cache directory permissions. Error: {e}"
                    ) from e
                raise ModelLoadError(f"Failed to load model: {e}") from e
            except Exception as e:
                raise ModelLoadError(f"Failed to load Whisper model: {e}") from e
        return self._model

    def transcribe(self, audio_path: str, config: Config) -> Tuple[bool, str]:
        """Transcribe audio file. Returns (success, text)."""
        if not os.path.exists(audio_path):
            console.print("[red]Error: Audio file not found[/red]")
            return False, ""

        if not os.path.getsize(audio_path) > 0:
            console.print("[red]Error: Audio file is empty[/red]")
            return False, ""

        try:
            segments, info = self.model.transcribe(audio_path, language=config.language)
            text = "\n".join(segment.text.strip() for segment in segments)
            return True, text

        except ModelDownloadError:
            return False, ""
        except ModelLoadError:
            return False, ""
        except OSError as e:
            if "No space left" in str(e):
                console.print("[red]Error: Not enough disk space to load model[/red]")
            elif "Permission denied" in str(e):
                console.print("[red]Error: Permission denied accessing model cache[/red]")
            else:
                console.print(f"[red]Error: OS error during transcription: {e}[/red]")
            return False, ""
        except Exception as e:
            console.print(f"[red]Error transcribing: {e}[/red]")
            return False, ""
        finally:
            try:
                os.unlink(audio_path)
            except Exception:
                pass

    def load_model(self) -> Tuple[bool, str]:
        """Pre-load the model. Returns (success, message)."""
        try:
            _ = self.model
            return True, f"Model {self.model_size} loaded successfully"
        except ModelDownloadError as e:
            return False, f"Download failed: {e}"
        except ModelLoadError as e:
            return False, f"Load failed: {e}"
        except Exception as e:
            return False, f"Error: {e}"
