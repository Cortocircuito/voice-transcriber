# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Voice-to-text CLI application for speech transcription using faster-whisper, with an interactive Rich terminal UI. Two main modes: dictation (record → transcribe) and lesson practice (read aloud lessons scraped from Breaking News English, then compare transcription against the original text). Linux-only recording via ALSA `arecord`.

See AGENTS.md for detailed code style conventions (type hints, docstrings, exceptions, logging, Rich patterns).

## Commands

```bash
# Dev setup (venv at ./venv)
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Tests
pytest                                          # all tests
pytest tests/test_config.py                     # one file
pytest tests/test_config.py::TestConfig::test_default_values  # one test
pytest --cov=src/voice_to_text --cov-report=term-missing

# Lint / format / type-check
ruff check src/ --fix
black src/
isort src/
mypy src/
pre-commit run --all-files   # black, isort, ruff, mypy, bandit

# Run
python -m voice_to_text      # without install
voice-to-text                # installed entry point (voice_to_text:main)
```

## Architecture

All source lives in `src/voice_to_text/` (setuptools src layout).

**Composition root:** `cli.py` — the `CLI` class constructs and wires everything: `Config`, `Recorder`, `Transcriber`, `UI`, `HistoryManager`, `LessonManager`, then injects them into three mode managers that own the main-menu flows:

- `DictationManager` (`dictation.py`) — record and transcribe free speech
- `PracticeManager` (`practice.py`) — lesson reading practice; uses `comparison.py` to diff the transcription against the lesson text and `phonetics.py` (eng-to-ipa) for IPA hints
- `ConfigManager` (`configurator.py`) — interactive settings menu

Mode managers receive their dependencies via constructor injection; tests rely on this to pass mocks.

**Key subsystems:**

- `recorder.py` — spawns `arecord` as a subprocess, streams audio to a temp WAV file while computing levels for the progress UI. All recorder errors are custom exceptions (`ArecordNotFoundError`, `MicrophoneNotFoundError`, ...).
- `transcriber.py` — faster-whisper wrapper; model size (tiny/base/small/medium) and language come from `Config`.
- `lessons.py` — scrapes breakingnewsenglish.com with `scrapesome`, parses 7 difficulty levels per lesson. Caches to disk with expiry, and supports background preloading via a single-worker `ThreadPoolExecutor` (`preload_lessons_async` / `is_preloading` / `preload_succeeded`); `cli.py` polls this state to show download progress in the menu.
- `comparison.py` — word-level diff (difflib) with normalization (contractions, punctuation) producing per-word accuracy results for practice mode.
- `ui.py` — all Rich console rendering; `i18n.py` holds UI strings via `get_text(key, lang)` (English/Spanish); `constants.py` holds all constants.

**Persistence:** everything user-facing lives under `~/.config/voice-to-text/` — `config.json`, `history.json`, and `lessons/` cache. History is saved on exit via `atexit`/SIGINT handlers registered in `CLI`.

**Logging quiet mode:** during background lesson downloads, `cli.py::_set_quiet_mode` silences root and external loggers (httpx, faster_whisper, ...) so log noise doesn't corrupt the Rich UI. Keep this in mind when adding logging around lesson downloads.

## Notes

- New UI text must be added to `i18n.py` with both language keys, not hardcoded.
- `plans/` holds design documents (e.g. the improved comparison algorithm plan).

## Git Commits

- Do not add a `Co-Authored-By: Claude ...` trailer to commit messages in this repository.
- Use Conventional Commits style prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, ...) matching the existing commit history.
