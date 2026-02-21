# AGENTS.md - Voice to Text Project

This document provides guidelines for AI agents working in this repository.

## Project Overview

A voice-to-text (Speech to Text) tool using faster-whisper for audio transcription. The project is a Python package with modular architecture following SOLID principles.

## Build/Lint/Test Commands

### Running the Application

```bash
# Run from source
python -m voice_to_text

# Run after installation
voice-to-text
```

### Installation

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies
pip install -e ".[dev]"
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=voice_to_text

# Run a single test file
pytest tests/test_config.py

# Run with verbose output
pytest -v
```

### Linting and Formatting

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

## Architecture

### Module Structure

```
voice_to_text/
├── __init__.py      # Package initialization, version
├── __main__.py      # Entry point (python -m voice_to_text)
├── cli.py           # CLI class - handles user interaction
├── config.py        # Config dataclass - settings management
├── recorder.py      # Recorder class - audio recording
└── transcriber.py   # Transcriber class - transcription
```

### Classes

| Class | Responsibility |
|-------|---------------|
| `Config` | Manages duration, language, and device settings |
| `Recorder` | Handles audio recording via arecord |
| `Transcriber` | Manages Whisper model and transcription |
| `CLI` | Command-line interface and user interaction |

## Code Style Guidelines

### Python Code

#### Imports

```python
# Standard library
import os
import sys

# Third-party packages
from faster_whisper import WhisperModel

# Local modules
from .config import Config
```

- Group imports: standard library, third-party, local
- Sort alphabetically within each group
- Use absolute imports for package modules
- Use explicit imports (avoid `from module import *`)

#### Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: 88 characters (black default)
- Use double quotes for strings
- Add trailing commas in multi-line collections

#### Types

- Use type hints for all function signatures:

```python
def transcribe(
    audio_path: str,
    config: Config,
) -> bool:
    ...
```

- Use `Optional[T]` for optional parameters
- Use `list[T]`, `dict[K, V]` instead of `List`, `Dict`

#### Naming Conventions

- Variables and functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

#### Error Handling

- Use specific exception types
- Provide meaningful error messages
- Use context managers for resource handling
- Never use bare `except:` clauses

#### Docstrings

- Use triple double quotes for docstrings
- Follow Google style

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `duration` | 15 | Recording duration in seconds (1-300) |
| `language` | en | Transcription language (en/es/fr/de) |
| `recording_device` | default | ALSA recording device |

## Supported Languages

| Code | Language |
|------|----------|
| en | English |
| es | Spanish |
| fr | French |
| de | German |

## Dependencies

Main Python packages:

- `faster-whisper` - Fast Whisper transcription
- `ctranslate2` - Transformer inference engine (dependency of faster-whisper)

Dev dependencies:

- `pytest` - Testing framework
- `black` - Code formatter
- `isort` - Import sorter
- `ruff` - Linter
- `mypy` - Type checker

## Notes

- The project uses Spanish for user-facing text
- Audio files are temporary and cleaned up after transcription
- Duration is validated (1-300 seconds)
- Empty transcription detection warns user
- Follow SOLID principles for new features
