"""Voice to Text - Speech transcription using faster-whisper."""

import logging
import sys

__version__ = "1.0.0"

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s: %(levelname)s - %(message)s",
    stream=sys.stderr,
)

from .cli import CLI, main  # noqa: E402
from .config import Config  # noqa: E402
from .configurator import ConfigManager  # noqa: E402
from .dictation import DictationManager  # noqa: E402
from .i18n import get_text, get_language_label  # noqa: E402
from .practice import PracticeManager  # noqa: E402
from .recorder import Recorder  # noqa: E402
from .transcriber import Transcriber  # noqa: E402
from .ui import UI  # noqa: E402

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
