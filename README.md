# Voice to Text

A Linux Python CLI for speech transcription with faster-whisper and an
interactive terminal UI. Dictate text or practice reading lessons from
[Breaking News English](https://breakingnewsenglish.com).

## Features

- **Dictation:** record audio, then transcribe it; press Enter to stop early.
- **Export:** copy a transcription, save it as `.txt` or `.md`, or print plain text.
- **Lesson practice:** read articles at their published difficulty levels (0–6),
  compare your transcription with the original, and see missing and extra words.
- **Languages:** English, Spanish, French, and German transcription; English and
  Spanish UI.
- **Models:** tiny, base, small, and medium Whisper models.
- **Offline lessons:** cached articles, background downloads, and manual refresh.
- **Settings and history:** persisted locally between sessions.

## Requirements

- Python 3.10+, Linux, and a microphone.
- ALSA `arecord` for recording (`alsa-utils` on Ubuntu/Debian).
- Internet access for initial model downloads and fetching new lessons.
- Optional system clipboard tool for copying text.

On Ubuntu/Debian:

```bash
sudo apt install alsa-utils python3-venv pipx
```

## Installation

Run these commands from a local checkout of this repository.

### For users: pipx

```bash
pipx ensurepath
pipx install .
voice-to-text
```

After `pipx ensurepath`, you may need to reopen your terminal. After updating the
checkout, reinstall with `pipx reinstall voice-to-text`. To uninstall:
`pipx uninstall voice-to-text`.

### For development: virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -e ".[dev]"
voice-to-text
```

Activate the environment in each new terminal. Editable installation means source
changes take effect without reinstalling; rerun the install command when
dependencies change. You can also launch with `python -m voice_to_text` after
installation.

Do not rely on `pip install --user` to bypass an `externally-managed-environment`
error: distributions using PEP 668 may block that too. Use pipx or a virtual
environment instead.

## Usage

```bash
voice-to-text                            # Interactive menu
voice-to-text --quick                    # Skip menu and start dictation
voice-to-text --duration 30 --language es
voice-to-text --help
```

The main menu offers **Record**, **Practice Reading**, **Configure**, and **Exit**.
Recording stops at the configured duration or when you press Enter in an
interactive terminal. Transcription starts after recording finishes; this is not
live speech-to-text during capture.

### Command-line options

| Option | Description | Default without saved settings |
|--------|-------------|--------------------------------|
| `--duration` | Recording duration, 1–300 seconds | 15 |
| `--language` | Transcription language: `en`, `es`, `fr`, `de` | `en` |
| `--reading-speed` | Reading speed, 20–300 WPM | 150 |
| `--quick`, `-q` | Start dictation without the main menu | false |

Explicit CLI values override saved settings at startup.

### Dictation actions

After transcription, use the action menu to:

- `[C]` copy the transcription to the clipboard.
- `[W]` write a `.txt` or `.md` file (no extension defaults to `.txt`). Existing
  files are never overwritten; the destination directory must already exist.
- `[E]` print the transcription as plain text to standard output. This is an
  interactive action, not a separate noninteractive export command.

### Lesson practice

Opening **Practice Reading** prompts you to download lessons when none are cached,
or to refresh an expired cache. Downloads run in the background; return to practice
once they finish. You can keep using stale cached lessons if you decline a refresh.
Only the levels published for each article are offered.

- `[1–N]`: select a lesson.
- `[P]` / `[N]`: previous/next page.
- `[R]`: refresh lessons.
- `[0]`: return to the main menu.

Practice supports `flexible` (default), `per_word`, and `legacy` comparison methods.
The score measures text matching, not an acoustic pronunciation assessment. See
[comparison behavior](AGENTS.md#text-comparison) for implementation details.

## Configuration and local data

Use **Configure** to change recording duration, transcription language, model size,
and reading speed, and confirm saving to persist changes. UI language
(`ui_language`: `en`/`es`), recording device (`recording_device`), and comparison
method (`comparison_method`: `flexible`/`per_word`/`legacy`) can be edited in
`config.json`; they do not have interactive selectors.

Local data lives in `${XDG_CONFIG_HOME:-~/.config}/voice-to-text/`:

- `config.json`: saved settings.
- `history.json`: transcription history.
- `lessons/`: cached lesson content.

## Clipboard troubleshooting

Copying text uses `pyperclip` and requires a tool accessible on `PATH`:

```bash
sudo apt install wl-clipboard  # Wayland: wl-copy / wl-paste
# Or, for X11:
sudo apt install xclip        # xsel is also supported
```

If copying fails, check `echo "$XDG_SESSION_TYPE"` and `command -v wl-copy`
or `command -v xclip`. Run the app inside your graphical session so the clipboard
tool can access the display. A Python virtual environment or pipx does not install
these system tools or fix display-session permissions.

## Development and documentation

[AGENTS.md](AGENTS.md) is the shared developer/agent guide: architecture, tests,
quality checks, and coding conventions.

Source code is in `src/voice_to_text/`; tests and their input fixtures are in
`tests/`. Markdown under `tests/fixtures/` is test data, not user documentation.

## License

MIT License
