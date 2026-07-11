"""Audio transcription functionality."""

import os
from typing import Callable, Optional, Tuple

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from faster_whisper import WhisperModel

from .config import Config
from .constants import COLOR_ACCENT, COLOR_DIM, COLOR_ERROR, COLOR_SUCCESS
from .i18n import get_text

# Fallback console used when no console is injected (e.g. in tests). The CLI
# passes the shared UI console so output honors quiet mode and Rich settings.
_default_console = Console()


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
    def __init__(
        self,
        model_size: Optional[str] = None,
        device: str = "cpu",
        compute_type: str = "int8",
        console: Optional[Console] = None,
    ):
        self._model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model: Optional[WhisperModel] = None
        self.console = console or _default_console

    def _print_error(self, message: str) -> None:
        """Print an error line to the injected console, prefixed and styled."""
        self.console.print(
            f"[{COLOR_ERROR}]{get_text('error_label')}: {message}[/{COLOR_ERROR}]"
        )

    @property
    def model_size(self) -> str:
        return self._model_size or "base"

    @property
    def model(self) -> WhisperModel:
        if self._model is None:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                progress.add_task(
                    f"[{COLOR_ACCENT}]{get_text('loading_model')} ({self.model_size})",
                    total=None,
                )
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
            self.console.print(
                f"[{COLOR_SUCCESS}]✓[/{COLOR_SUCCESS}] "
                f"[{COLOR_DIM}]{get_text('model_loaded')}[/{COLOR_DIM}]"
            )
        return self._model

    def transcribe(self, audio_path: str, config: Config) -> Tuple[bool, str]:
        """Transcribe audio file. Returns (success, text)."""
        return self.transcribe_streaming(audio_path, config)

    def transcribe_streaming(
        self,
        audio_path: str,
        config: Config,
        on_segment: Optional[Callable[[str], None]] = None,
    ) -> Tuple[bool, str]:
        """Transcribe audio file with optional streaming callback.

        Args:
            audio_path: Path to audio file
            config: Configuration
            on_segment: Optional callback called for each transcribed segment

        Returns:
            Tuple of (success, full_text)
        """
        lang = config.ui_language

        if not os.path.exists(audio_path):
            self._print_error(get_text("audio_not_found", lang))
            return False, ""

        if not os.path.getsize(audio_path) > 0:
            self._print_error(get_text("audio_empty", lang))
            return False, ""

        try:
            segments, info = self.model.transcribe(audio_path, language=config.language)

            text_parts = []
            for segment in segments:
                segment_text = segment.text.strip()
                if segment_text:
                    text_parts.append(segment_text)
                    if on_segment:
                        on_segment(segment_text)

            return True, "\n".join(text_parts)

        except ModelDownloadError:
            return False, ""
        except ModelLoadError:
            return False, ""
        except OSError as e:
            if "No space left" in str(e):
                self._print_error(get_text("disk_space_error", lang))
            elif "Permission denied" in str(e):
                self._print_error(get_text("model_cache_permission_error", lang))
            else:
                self._print_error(f"{get_text('transcription_os_error', lang)}: {e}")
            return False, ""
        except Exception as e:
            self._print_error(f"{get_text('transcribe_error', lang)}: {e}")
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
