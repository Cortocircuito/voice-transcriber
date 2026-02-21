"""Voice to Text - Speech transcription using faster-whisper."""

__version__ = "1.0.0"

from .cli import CLI
from .config import Config
from .recorder import Recorder
from .transcriber import Transcriber

__all__ = ["CLI", "Config", "Recorder", "Transcriber", "__version__"]
