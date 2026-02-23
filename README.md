# Voice to Text

A Python CLI application for speech transcription using faster-whisper. Provides an interactive terminal UI for dictation and lesson practice modes.

## Features

- **Dictation Mode**: Record and transcribe your voice in real-time
- **Lesson Practice**: Practice reading with lessons from Breaking News English
- **Multiple Languages**: Support for English, Spanish, French, and German
- **Model Options**: Choose from tiny, base, small, or medium Whisper models
- **Text Comparison**: Compare your transcription with the original text
- **Progress Tracking**: Visual progress bars during recording

## Requirements

- Python 3.10+
- Linux with ALSA audio (arecord)
- Microphone

## Installation

```bash
pip install -e .
```

Or install with development dependencies:

```bash
pip install -e ".[dev]"
```

## Usage

### Interactive Menu

```bash
voice-to-text
```

### Quick Start (Immediate Recording)

```bash
voice-to-text --quick
```

### With Custom Settings

```bash
voice-to-text --duration 30 --language es
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--duration` | Recording duration in seconds | 15 |
| `--language` | Transcription language (en/es/fr/de) | en |
| `--quick`, `-q` | Start recording immediately | false |

## Menu Options

1. **Record** - Start dictation mode
2. **Practice Reading** - Practice with lesson articles
3. **Configure** - Change settings
4. **Exit** - Quit application

## Configuration

Settings are stored in a dataclass and include:
- Recording duration (1-300 seconds)
- Transcription language
- UI language
- Whisper model size
- Recording device

## Development

### Running Tests

```bash
pytest
```

### Linting

```bash
ruff check src/
black src/
mypy src/
```

### Pre-commit Hooks

```bash
pip install -e ".[dev]"
pre-commit install
```

## Project Structure

```
src/voice_to_text/
├── cli.py           # Command-line interface
├── config.py        # Configuration dataclass
├── configurator.py  # Settings management
├── dictation.py     # Dictation mode
├── history.py      # Transcription history
├── i18n.py          # Internationalization
├── lessons.py       # Lesson fetching & parsing
├── practice.py      # Lesson practice mode
├── recorder.py      # Audio recording
├── transcriber.py   # Speech transcription
└── ui.py            # Terminal UI
```

## License

MIT License
