"""Voice to Text - Speech transcription using faster-whisper."""

__version__ = "1.1.0"

from .cli import CLI, main
from .config import Config
from .i18n import get_text, get_language_label
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI

__all__ = [
    "CLI",
    "Config",
    "Recorder",
    "Transcriber",
    "UI",
    "main",
    "get_text",
    "get_language_label",
    "__version__",
]
