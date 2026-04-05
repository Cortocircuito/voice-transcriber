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

### Recommended: User Install (Option 3)

This is the recommended method for end users. It avoids Python's externally-managed environment restrictions on Ubuntu 24.04+:

```bash
pip install -e . --user
```

**Update to new version:**
```bash
pip install -e . --user --force-reinstall
```

**Uninstall:**
```bash
pip uninstall voice-to-text
```

**Run:**
```bash
voice-to-text  # Command available globally from ~/.local/bin
```

---

### Alternative: pipx (Option 2)

Best for system-wide isolation. Requires pipx installed:

```bash
sudo apt install pipx
pipx install -e /path/to/voz_a_texto
```

**Update to new version:**
```bash
pipx reinstall voice-to-text
```

**Uninstall:**
```bash
pipx uninstall voice-to-text
```

**Run:**
```bash
voice-to-text  # Works globally
```

---

### Alternative: Virtual Environment (Option 1)

Best for development. Requires manual environment activation:

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

**Update to new version:**
```bash
source venv/bin/activate
pip install -e . --force-reinstall
```

**Uninstall:**
```bash
deactivate
rm -rf venv
```

**Run:**
```bash
source venv/bin/activate
voice-to-text
```

Or add to PATH permanently in `~/.bashrc`:
```bash
export PATH="/path/to/voz_a_texto/venv/bin:$PATH"
```

---

### With Development Dependencies

If you want to contribute or run tests, install dev dependencies:

```bash
pip install -e ".[dev]" --user
# Or with pipx:
pipx install -e /path/to/voz_a_texto[dev]
# Or with venv:
source venv/bin/activate && pip install -e ".[dev]"
```

## System Dependencies

### Linux (Ubuntu/Debian)

For the copy-to-clipboard feature, you need a clipboard tool. This is required for the `[C] Copy original` menu option:

**Wayland (default on Ubuntu 24.04+):**
```bash
sudo apt-get install wl-clipboard
```

**X11 (fallback):**
```bash
sudo apt-get install xclip
```

#### Clipboard Troubleshooting

The application uses `pyperclip` to access the clipboard, which relies on external tools:
- **Wayland**: Uses `wl-copy` and `wl-paste` from `wl-clipboard`
- **X11**: Uses `xclip` or `xsel`

**If the copy feature shows "Clipboard not available" error:**

1. **Verify clipboard tool is installed:**
   ```bash
   which wl-copy     # For Wayland
   which xclip       # For X11
   ```

2. **Check your display server:**
   ```bash
   echo $XDG_SESSION_TYPE  # Shows 'wayland' or 'x11'
   ```

3. **Installation method matters**: 
   - If you used **Option 1 (venv)** without activating, `pyperclip` won't find system tools
   - If you used **Option 3 (--user)** without proper PATH, command might not work
   - **Option 2 (pipx)** typically handles this best as it creates an isolated environment with proper PATH configuration

4. **Solution**: 
   - Ensure clipboard tool is installed for your display server
   - For venv: Always activate the environment before running
   - For --user install: Ensure `~/.local/bin` is in your PATH

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
| `--reading-speed` | Reading speed in WPM | 150 |
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

Settings can be configured via:
- **Interactive menu**: Change settings during runtime
- **Config file**: `~/.config/voice-to-text/config.json` (persists across sessions)
- **CLI arguments**: Override settings per session

Configurable options:
- Recording duration (1-300 seconds)
- Transcription language
- UI language
- Whisper model size
- Reading speed (words per minute)
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
