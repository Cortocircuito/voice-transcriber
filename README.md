# Voice to Text

A beautiful voice-to-text (Speech to Text) tool using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for audio transcription.

## 📚 Human Documentation

This README.md file contains user-facing documentation for humans using the voice-to-text application.

## Features

- 🎤 Real-time audio recording with configurable duration
- 📊 Real-time audio level meter during recording
- ⚡ Fast transcription using faster-whisper
- 📝 Partial transcription display (line-by-line streaming)
- 🌍 Multi-language UI (Spanish/English)
- 🗣️ Multi-language transcription (English, Spanish, French, German)
- 🚀 Quick mode with `--quick` flag (skip menu, start recording immediately)
- 💾 Auto-save transcription history on exit (JSON format)
- 🎨 Beautiful terminal UI with panels and colors
- ✅ Duration input validation
- ⚠️ Empty transcription detection
- 📚 Lesson Practice Mode - Practice reading with real news articles
- 🔤 Paragraph-by-paragraph pronunciation practice
- 📖 Real-time accuracy feedback with word highlighting
- 🧪 Fully tested codebase

## Requirements

- Python 3.10+
- ALSA (for audio recording via `arecord`)
- Linux (tested on Ubuntu)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cortocircuito/voice-transcriber.git
cd voice-transcriber
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install the package:
```bash
pip install -e .
```

## Usage

### Spanish UI (default)
```bash
python -m voice_to_text
```

### English UI
```bash
python -m voice_to_text --lang en
```

### With custom settings
```bash
python -m voice_to_text --lang en --duration 30 --language es
```

### Quick mode (skip menu, start recording immediately)
```bash
python -m voice_to_text --quick
# or
python -m voice_to_text -q
```

### CLI Arguments

| Argument | Short | Description | Default |
|----------|-------|-------------|---------|
| `--lang` | | UI language (es/en) | es |
| `--duration` | | Recording duration in seconds | 15 |
| `--language` | | Transcription language (en/es/fr/de) | en |
| `--quick` | `-q` | Start recording immediately (skip menu) | false |

## Lesson Practice Mode

The app includes a **Lesson Practice Mode** that lets you practice reading English with real news articles from [Breaking News English](https://breakingnewsenglish.com).

### Features:
- 📚 Browse lessons from breaking news stories
- 📖 Multiple difficulty levels (0-6)
- 🔤 Practice reading paragraph by paragraph
- ⏱️ Auto-calculated reading time per paragraph
- 🎯 Real-time pronunciation feedback with accuracy score
- 🔍 Highlights mispronounced words

### Usage:
```
[1] 🎙️  Grabar
[2] 📚  Practice Reading
[3] ⚙️  Configurar
[4] 🚪 Salir
```

Select a lesson → Choose difficulty level → Read paragraph by paragraph → Get instant feedback!

### How it works:
1. Select a news lesson from the list
2. Choose your difficulty level (0=Beginner to 6=Advanced)
3. Read each paragraph aloud when prompted
4. The app transcribes your speech and compares it to the original
5. See your accuracy score and which words need work
6. Move to the next paragraph or try again

## Screenshots

### Main Menu (Spanish)
```
╭─────────────────────────────── 🎤 VOZ A TEXTO ───────────────────────────────╮
│                                                                              │
│    [1]     🎙️  Grabar                                                        │
│    [2]     ⚙️   Configurar                                                   │
│    [3]     🚪 Salir                                                          │
│                                                                              │
╰─────────────────────── Duración: 15s │ Idioma: Inglés ───────────────────────╯
```

### Main Menu (English)
```
╭────────────────────────────── 🎤 VOICE TO TEXT ──────────────────────────────╮
│                                                                              │
│    [1]     🎙️  Record                                                        │
│    [2]     ⚙️   Configure                                                    │
│    [3]     🚪 Exit                                                           │
│                                                                              │
╰───────────────────── Duration: 15s │ Language: English ──────────────────────╯
```

### Recording with Progress Bar and Audio Level
```
╭──────────────────────────────────────────────╮
│              🎙️  GRABANDO                     │
│              ¡HABLA AHORA!                    │
╰──────────────────────────────────────────────╯
🎤 Mic: ✅ Listo
   Inglés • 15s  ████████████░░░░░░░░  67%  5s
🎤 Level: ████████████████░░░░  72%
```

### Transcription Result
```
╭──────────────────────────────────────────────╮
│     ✅ TRANSCRIPCIÓN (Inglés)                 │
├──────────────────────────────────────────────┤
│                                              │
│   Hello, this is a test of the voice         │
│   to text application working perfectly.     │
│                                              │
╰──────────────────────────────────────────────╯
```

## Project Structure

```
voice-transcriber/
├── src/
│   └── voice_to_text/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Entry point
│       ├── cli.py           # Command-line interface
│       ├── comparison.py    # Text comparison for pronunciation
│       ├── config.py        # Configuration management
│       ├── history.py       # Transcription history
│       ├── i18n.py          # Internationalization
│       ├── lessons.py       # Lesson fetching & management
│       ├── recorder.py      # Audio recording
│       ├── transcriber.py   # Transcription logic
│       └── ui.py            # UI components (Rich)
├── tests/
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_history.py
│   └── test_recorder_transcriber.py
├── pyproject.toml           # Project metadata
├── README.md
└── LICENSE
```

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Formatting
```bash
black .
isort .
```

### Linting
```bash
ruff check .
mypy .
```

## Supported Languages

| Code | Language |
|------|----------|
| en | English |
| es | Spanish |
| fr | French |
| de | German |

## Audio Configuration

The application uses `arecord` (ALSA) for audio capture:
- Format: S16_LE (16-bit signed little-endian)
- Sample rate: 16000 Hz
- Channels: 1 (mono)

If your microphone doesn't work, you can configure it programmatically:
```python
from voice_to_text import Config, CLI

config = Config(recording_device="hw:0,0")
cli = CLI(config)
cli.run()
```

## Transcription History

Transcriptions are automatically saved on exit to:
```
~/.config/voice-to-text/history.json
```

History format:
```json
[
  {
    "timestamp": "2026-02-21T15:30:00.000000",
    "language": "en",
    "duration": 15,
    "text": "Your transcribed text..."
  }
]
```

Lesson practice entries are marked with `[Practice: Lesson Name]`:
```json
[
  {
    "timestamp": "2026-02-21T15:30:00.000000",
    "language": "en",
    "duration": 30,
    "text": "[Practice: Japan wins its first...] Your transcribed text..."
  }
]
```

You can also use `XDG_CONFIG_HOME` to customize the location:
```bash
export XDG_CONFIG_HOME=~/.my-config
```

## Lesson Cache

Lessons from Breaking News English are cached locally:
```
~/.config/voice-to-text/lessons/index.json
```

Cache is valid for 24 hours. Use the refresh option in the lesson menu to update.

## Dependencies

| Package | Purpose |
|---------|---------|
| `faster-whisper` | Fast Whisper transcription |
| `rich` | Beautiful terminal UI |

## License

MIT License
