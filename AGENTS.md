# AGENTS.md - Voice to Text Project

This document provides guidelines for AI agents working in this repository.

## Project Overview

A voice-to-text (Speech to Text) tool using faster-whisper for audio transcription. The project uses Bash scripts for the main application logic and a Python virtual environment for the whisper dependencies.

## Build/Lint/Test Commands

### Running the Application

```bash
# Run the main dictation script
./STT/dictado.sh
```

### Virtual Environment

```bash
# Activate the virtual environment
source whisper_venv/bin/activate

# Deactivate
deactivate
```

### Manual Transcription

```bash
# Activate venv first, then:
faster-whisper <audio_file> --language en -o <output_file>
```

### Testing

This project currently has no automated tests. When adding Python code, use pytest:

```bash
# Run all tests
pytest
```

### Linting and Formatting

For Python code, use these tools:

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Lint with ruff
ruff check .

# Type check with mypy
mypy .
```

For Bash scripts:

```bash
# Check bash syntax
bash -n STT/dictado.sh
```

## Code Style Guidelines

### Shell Scripts (Bash)

- Use `#!/bin/bash` shebang
- Use snake_case for variables and functions: `DURATION`, `run_dictation()`
- Use UPPER_CASE for constants and global variables
- Quote all variable expansions: `"$VARIABLE"`
- Use `[[ ]]` for conditionals instead of `[ ]` or `test`
- Use `$()` for command substitution instead of backticks
- Add descriptive comments in Spanish (project convention)
- Organize code into logical sections with comment headers:
  ```bash
  # --- Section Name ---
  ```
- Use functions for reusable logic
- Always check return codes with `||` for error handling
- Use `case` statements for menu selections

### Python Code

When adding Python modules to this project:

#### Imports

```python
# Standard library
import os
import sys

# Third-party packages
import numpy as np
from faster_whisper import WhisperModel

# Local modules
from .module import function
```

- Group imports: standard library, third-party, local
- Sort alphabetically within each group
- Use absolute imports for project modules
- Use explicit imports (avoid `from module import *`)

#### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (black default)
- Use double quotes for strings
- Add trailing commas in multi-line collections

#### Types

- Use type hints for all function signatures:

```python
def transcribe_audio(
    audio_path: str,
    language: str = "en",
) -> tuple[str, float]:
    ...
```

- Use `Optional[T]` for optional parameters
- Use `Union[A, B]` or `A | B` for multiple types
- Use `list[T]`, `dict[K, V]` instead of `List`, `Dict`

#### Naming Conventions

- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`
- Module-level dunder names: `__all__`, `__version__`

#### Error Handling

- Use specific exception types
- Provide meaningful error messages
- Use context managers for resource handling:

```python
try:
    with open(file_path, "r") as f:
        content = f.read()
except FileNotFoundError:
    logger.error(f"File not found: {file_path}")
    raise
```

- Never use bare `except:` clauses
- Log errors appropriately before re-raising

#### Docstrings

- Use triple double quotes for docstrings
- Follow Google style:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short description of function.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Description of return value.

    Raises:
        ValueError: If param2 is negative.
    """
```

## Project Structure

```
voz_a_texto/
├── STT/
│   └── dictatesh        # Main dictation script
├── whisper_venv/        # Python virtual environment
├── comando.wav         # Temporary audio file (generated)
├── transcripcion_bruta.txt   # Raw transcription output
└── texto_puro_final.txt  # Cleaned transcription text
```

## Configuration Variables

Main variables in `STT/dictado.sh`:

| Variable | Default | Description |
|----------|---------|-------------|
| `DURATION` | 15 | Recording duration in seconds (1-300) |
| `LANGUAGE` | en | Transcription language (en/es/fr/de) |
| `RECORDING_DEVICE` | default | ALSA recording device |

## Supported Languages

| Code | Language |
|------|----------|
| en | English |
| es | Spanish |
| fr | French |
| de | German |

## Key Functions

| Function | Description |
|----------|-------------|
| `validate_duration()` | Validates duration input (1-300 seconds) |
| `check_mic_level()` | Tests microphone connectivity |
| `clean_transcription()` | Filters raw transcription output |
| `record_audio()` | Records audio with countdown |
| `transcribe()` | Transcribes audio using faster-whisper |
| `configure_settings()` | Configure duration and language |

## Dependencies

Main Python packages in the virtual environment:

- `faster-whisper` - Fast Whisper transcription
- `ctranslate2` - Transformer inference engine
- `numpy` - Numerical computing
- `onnxruntime` - ONNX model runtime

## Audio Recording

The scripts use `arecord` (ALSA) for audio capture:

- Format: S16_LE (16-bit signed little-endian)
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Device: `default` (configurable via `RECORDING_DEVICE`)

## Notes

- The project uses Spanish for user-facing text and comments
- Audio files are temporary and cleaned up after each session
- Language and duration are configurable via menu
- Duration input is validated (1-300 seconds)
- Empty transcription detection warns user
- Modify `RECORDING_DEVICE` if the default microphone doesn't work
