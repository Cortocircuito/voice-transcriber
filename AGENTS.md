# AGENTS.md - Voice to Text Project

This document provides guidelines for AI agents working in this repository.

## 🤖 Agent Documentation

This AGENTS.md file contains guidelines specifically for AI agents working on this voice-to-text project.

## Project Overview

A voice-to-text (Speech to Text) tool using faster-whisper for audio transcription. The project is a Python package with modular architecture following SOLID principles. Features a beautiful terminal UI built with Rich library and full internationalization support.

## Build/Lint/Test Commands

### Running the Application

```bash
# Spanish UI (default)
python -m voice_to_text

# English UI
python -m voice_to_text --lang en

# With custom settings
python -m voice_to_text --lang en --duration 30 --language es
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

## Git Commit Messages

### Format

Use conventional commits format:

```
<type>: <subject>

[optional body]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `refactor` | Code refactoring |
| `test` | Adding/updating tests |
| `chore` | Maintenance, deps, build |

### Rules

- Use lowercase after the colon
- Keep subject line under 72 characters
- Use imperative mood ("add feature" not "added feature")
- Reference issues when applicable (e.g., "fix #123")
- Add body for complex changes

### Examples

```
feat: add lesson practice mode with pronunciation comparison

fix: add missing imports in ui.py

docs: update README with new features

refactor: simplify transcription error handling
```

## Architecture

### Module Structure

```
voice_to_text/
├── __init__.py      # Package initialization, version
├── __main__.py      # Entry point (python -m voice_to_text)
├── cli.py           # CLI class - handles user interaction
├── comparison.py    # Text comparison for pronunciation analysis
├── config.py        # Config dataclass - settings management
├── history.py       # Transcription history manager
├── i18n.py          # Internationalization - translations
├── lessons.py       # Lesson fetching & management from web
├── recorder.py      # Recorder class - audio recording
├── transcriber.py   # Transcriber class - transcription
└── ui.py            # UI class - Rich console components
```

### Classes

| Class | Responsibility |
|-------|---------------|
| `Config` | Manages duration, language, ui_language, and device settings |
| `Recorder` | Handles audio recording via arecord |
| `Transcriber` | Manages Whisper model and transcription |
| `CLI` | Command-line interface and user interaction |
| `UI` | Rich console components for beautiful output |
| `LessonManager` | Fetches and caches lessons from Breaking News English |
| `Lesson` | Dataclass representing a lesson with levels and paragraphs |
| `TextComparator` | Compares transcribed text with original for accuracy |

### Key Features

- **Internationalization**: Full i18n support via `i18n.py` with Spanish/English translations
- **Rich UI**: Beautiful terminal output with panels, progress bars, and colors
- **Modular Design**: Each class has a single responsibility
- **Lesson Practice**: Paragraph-by-paragraph reading practice with pronunciation feedback

## Code Style Guidelines

### Python Code

#### Imports

```python
# Standard library
import os
import sys

# Third-party packages
from rich.console import Console
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
) -> Tuple[bool, str]:
    ...
```

- Use `Optional[T]` for optional parameters
- Use `Tuple[A, B]` for return tuples
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
| `ui_language` | es | UI language (en/es) |
| `recording_device` | default | ALSA recording device |

## Supported Languages

### Transcription Languages

| Code | Language |
|------|----------|
| en | English |
| es | Spanish |
| fr | French |
| de | German |

### UI Languages

| Code | Language |
|------|----------|
| es | Spanish |
| en | English |

## Dependencies

Main Python packages:

- `faster-whisper` - Fast Whisper transcription
- `rich` - Beautiful terminal UI
- `ctranslate2` - Transformer inference engine (dependency of faster-whisper)

Dev dependencies:

- `pytest` - Testing framework
- `black` - Code formatter
- `isort` - Import sorter
- `ruff` - Linter
- `mypy` - Type checker

## UI Components (Rich)

The `ui.py` module provides these UI components:

| Method | Description |
|--------|-------------|
| `show_menu()` | Bordered menu panel with options |
| `show_recording_start()` | Recording start message |
| `show_progress()` | Animated progress bar |
| `show_transcription()` | Result panel with border |
| `show_mic_status()` | Microphone status indicator |
| `show_config()` | Configuration menu panel |
| `show_language_selector()` | Language selection table |
| `show_lessons_menu()` | Lesson selection menu |
| `show_level_selector()` | Level selection for lessons |
| `show_paragraph_page()` | Single paragraph display with navigation |
| `show_comparison()` | Pronunciation comparison results |
| `show_practice_actions()` | Post-recording action prompts |

## Audio Recording

The `Recorder` class uses `arecord` (ALSA) for audio capture:

- Format: S16_LE (16-bit signed little-endian)
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Device: `default` (configurable via `recording_device`)

## Lesson Practice System

### LessonManager

The `LessonManager` class fetches lessons from Breaking News English:

- Parses homepage to extract available lessons and their level URLs
- Fetches content for each level (0-6)
- Caches lessons locally in `~/.config/voice-to-text/lessons/index.json`
- Provides async preloading for faster startup

### Lesson Dataclass

| Field | Type | Description |
|-------|------|-------------|
| `title` | str | Lesson title |
| `url` | str | Main lesson URL |
| `date` | str | Publication date |
| `description` | str | Lesson description |
| `levels` | list[str] | Available levels (e.g., ["0", "1", "2"]) |
| `texts` | dict[str, str] | Full text per level |
| `level_urls` | dict[str, str] | URLs for each level |
| `paragraphs` | dict[str, list[str]] | Paragraphs per level |

### TextComparator

The `TextComparator` class analyzes pronunciation:

- Normalizes text (expands contractions, removes punctuation)
- Uses difflib for sequence matching
- Returns accuracy percentage and list of errors
- Highlights mispronounced words

### Paragraph Flow

1. User selects lesson from menu
2. User selects difficulty level (0-6)
3. For each paragraph:
   - Display paragraph with estimated reading time
   - User presses R to record
   - App records and transcribes
   - Show accuracy comparison
   - User can retry or continue to next paragraph
4. After all paragraphs: show completion message

## Internationalization (i18n)

The `i18n.py` module provides:

- `get_text(key, lang)` - Get translated text
- `get_language_label(lang_code, ui_lang)` - Get language name in UI language
- `TRANSLATIONS` - Dictionary of all translations

## Notes

- The project uses Spanish for user-facing text by default
- UI language can be changed with `--lang en` flag
- Audio files are temporary and cleaned up after transcription
- Duration is validated (1-300 seconds)
- Empty transcription detection warns user
- Follow SOLID principles for new features
