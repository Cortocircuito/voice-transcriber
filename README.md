# Voice to Text

A Python CLI application for speech transcription using faster-whisper. Provides an interactive terminal UI for dictation and lesson practice modes.

## Features

- **Dictation Mode**: Record and transcribe your voice in real-time
- **Lesson Practice**: Practice reading with lessons from Breaking News English (7 levels)
- **Multiple Languages**: Support for English, Spanish, French, and German
- **Model Options**: Choose from tiny, base, small, or medium Whisper models
- **Text Comparison**: Compare your transcription with the original text
- **Progress Tracking**: Visual progress bars during recording
- **Smart Download**: Prompts to download lessons on first run with async background loading
- **Quiet Mode**: Clean UI during lesson download with optional verbose logging in Practice mode

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

On first run, if no lessons are cached, you'll be prompted to download lessons from Breaking News English. Lessons are downloaded asynchronously and available while you use the app.

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

## Lesson Practice

Lessons are fetched from [Breaking News English](https://breakingnewsenglish.com) and include:

- **7 Difficulty Levels**: From level 0 (easiest) to level 6 (hardest)
- **Smart Filtering**: Automatically filters out invalid/error content
- **Offline Support**: Lessons are cached locally for offline use
- **Refresh**: Option to refresh and fetch latest lessons

### Lesson Navigation

- `[1-N]` - Select a lesson
- `[P]` / `[N]` - Previous/Next page
- `[R]` - Refresh lessons
- `[0]` - Back to main menu

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
