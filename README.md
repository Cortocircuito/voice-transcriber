# Voice to Text

A simple voice-to-text (Speech to Text) tool using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for audio transcription.

## Features

- Real-time audio recording with configurable duration
- Fast transcription using faster-whisper
- Interactive menu with Spanish interface
- Configurable recording duration (10s, 15s, 30s)
- Real-time countdown during recording

## Requirements

- Python 3.10+
- ALSA (for audio recording via `arecord`)
- Linux (tested on Ubuntu)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/voz_a_texto.git
cd voz_a_texto
```

2. Create and activate a virtual environment:
```bash
python -m venv whisper_venv
source whisper_venv/bin/activate
```

3. Install dependencies:
```bash
pip install faster-whisper
```

## Usage

Run the main dictation script:
```bash
./STT/dictado.sh
```

### Controls

- Select recording duration: 10s (Corto), 15s (Medio), 30s (Largo)
- Press `S` to return to menu
- Press `1`, `2`, or `3` during recording to change duration
- Press `Ctrl+C` to exit

### Manual Transcription

You can also transcribe an existing audio file:
```bash
source whisper_venv/bin/activate
faster-whisper audio_file.wav --language en -o output.txt
```

## Project Structure

```
voz_a_texto/
├── STT/
│   ├── dictado.sh        # Main script (with real-time countdown)
│   └── dictado-old.sh    # Previous version (without countdown)
├── whisper_venv/         # Python virtual environment
├── AGENTS.md             # Guidelines for AI agents
└── README.md
```

## Audio Configuration

The script uses `arecord` (ALSA) for audio capture:
- Format: S16_LE (16-bit signed little-endian)
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Device: `default`

If your microphone doesn't work, modify `DISPOSITIVO_GRABACION` in the script:
```bash
DISPOSITIVO_GRABACION="default"  # Change to your device, e.g., "hw:0,0"
```

## Supported Languages

The transcription language is set to English (`--language en`). To transcribe in another language, modify the `faster-whisper` command in the script:

```bash
faster-whisper "$ARCHIVO_AUDIO" --language es -o "$ARCHIVO_BRUTO"  # Spanish
faster-whisper "$ARCHIVO_AUDIO" --language fr -o "$ARCHIVO_BRUTO"  # French
```

See [faster-whisper documentation](https://github.com/SYSTRAN/faster-whisper) for supported languages.

## License

MIT License
