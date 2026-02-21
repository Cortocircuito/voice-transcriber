# Voice to Text

A simple voice-to-text (Speech to Text) tool using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for audio transcription.

## Features

- Real-time audio recording with configurable duration
- Fast transcription using faster-whisper
- Multi-language transcription support (English, Spanish, French, German)
- Real-time countdown during recording
- Duration input validation
- Empty transcription detection
- Modular and testable Python codebase

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

Or install from requirements:
```bash
pip install -r requirements.txt
```

## Usage

### As a command-line tool

```bash
python -m voice_to_text
```

Or after installation:
```bash
voice-to-text
```

### Menu

```
=== MENÚ ===
1) Grabar
2) Configurar (D:15s L:Inglés)
3) Salir
```

### Controls

- **1** - Start recording
- **2** - Configure duration and language
- **D** - Change duration during recording
- **I** - Change language during recording
- **S** - Return to menu
- **Ctrl+C** - Exit

### Configuration

- **Duration**: Enter custom seconds (default: 15s, valid: 1-300)
- **Language**: 1)English 2)Spanish 3)French 4)German

## Project Structure

```
voice-transcriber/
├── src/
│   └── voice_to_text/
│       ├── __init__.py      # Package initialization
│       ├── __main__.py      # Entry point
│       ├── cli.py           # Command-line interface
│       ├── config.py        # Configuration management
│       ├── recorder.py      # Audio recording
│       └── transcriber.py   # Transcription logic
├── tests/
│   ├── __init__.py
│   └── test_config.py       # Unit tests
├── pyproject.toml           # Project metadata
├── requirements.txt         # Dependencies
├── README.md
└── LICENSE
```

## Development

### Running Tests

```bash
pytest
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

If your microphone doesn't work, modify the `recording_device` in `Config`:
```python
from voice_to_text import Config
config = Config(recording_device="hw:0,0")
```

## License

MIT License
