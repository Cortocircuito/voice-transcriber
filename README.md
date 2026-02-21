# Voice to Text

A simple voice-to-text (Speech to Text) tool using [faster-whisper](https://github.com/SYSTRAN/faster-whisper) for audio transcription.

## Features

- Real-time audio recording with configurable duration
- Fast transcription using faster-whisper
- Interactive menu with Spanish interface
- Configurable recording duration (custom seconds, default 15s)
- Multi-language transcription support (English, Spanish, French, German)
- Real-time countdown during recording
- Duration input validation
- Empty transcription detection

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

### Error Handling

- Invalid duration input → defaults to 15s
- Empty transcription → warns user "No se detectó ningún audio"

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
│   └── dictatesh        # Main script
├── whisper_venv/        # Python virtual environment
├── AGENTS.md            # Guidelines for AI agents
└── README.md
```

## Audio Configuration

The script uses `arecord` (ALSA) for audio capture:
- Format: S16_LE (16-bit signed little-endian)
- Sample rate: 16000 Hz
- Channels: 1 (mono)
- Device: `default`

If your microphone doesn't work, modify `RECORDING_DEVICE` in the script:
```bash
RECORDING_DEVICE="default"  # Change to your device, e.g., "hw:0,0"
```

## Supported Languages

The script supports:
- English (en)
- Spanish (es)
- French (fr)
- German (de)

Select language from the configuration menu or during recording.

## License

MIT License
