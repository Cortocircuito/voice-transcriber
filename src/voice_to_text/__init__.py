"""Voice to Text - Speech transcription using faster-whisper."""

import logging
import sys

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s: %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from .cli import CLI, main
from .config import Config
from .configurator import ConfigManager
from .dictation import DictationManager
from .i18n import get_text, get_language_label
from .practice import PracticeManager
from .recorder import Recorder
from .transcriber import Transcriber
from .ui import UI

__all__ = [
    "CLI",
    "Config",
    "ConfigManager",
    "DictationManager",
    "PracticeManager",
    "Recorder",
    "Transcriber",
    "UI",
    "main",
    "get_text",
    "get_language_label",
    "__version__",
]
