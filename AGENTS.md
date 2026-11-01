# Developer and Agent Guide

Shared instructions for contributors and coding agents. See [README.md](README.md)
for installation, user-facing features, configuration paths, and troubleshooting.
Keep those instructions there rather than duplicating them in agent-specific files.

## Development setup and commands

Run from the repository root with Python 3.10+:

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -e ".[dev]"
python -m voice_to_text
```

Install the package first with this `src/` layout; `python -m voice_to_text` is an
alternative entry point, not a way to skip installation. Use editable installation
for development.

```bash
# Tests
pytest
pytest tests/test_config.py
pytest tests/test_config.py::TestConfig::test_default_values
pytest --cov=src/voice_to_text --cov-report=term-missing

# Non-modifying checks
ruff check src/
black --check src/
isort --check-only src/
mypy src/

# Apply formatting / lint fixes when needed
black src/
isort src/
ruff check src/ --fix
```

Pre-commit is configured in `.pre-commit-config.yaml`, but is not included in the
`dev` extra. Install it separately in the development environment:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

Hooks include Black, isort, Ruff, mypy, Bandit, and file hygiene checks. They can
modify files; review the resulting diff. Tool settings and dependencies live in
`pyproject.toml`; hook versions and hook-specific arguments live in the pre-commit
configuration.

## Architecture

All application modules live in `src/voice_to_text/`.

| Module | Responsibility |
|--------|----------------|
| `cli.py` | Composition root: wires dependencies, dispatches menus, loads models lazily, and handles shutdown |
| `dictation.py` | Recording/transcription flow and dictation exports |
| `practice.py` | Lesson reading, recording, comparison, and feedback |
| `configurator.py` | Interactive settings management |
| `config.py` | Configuration dataclass, validation, and JSON persistence |
| `constants.py` | Shared limits, comparison defaults, and UI colors |
| `recorder.py` | ALSA `arecord` subprocess, temporary WAV audio, levels, and recorder exceptions |
| `transcriber.py` | faster-whisper model loading and transcription |
| `comparison.py` | Text normalization, matching, scoring, and word-error mapping |
| `phonetics.py` | English IPA hints using eng-to-ipa |
| `lessons.py` | Breaking News English scraping, published-level discovery, caching, and background preloading |
| `history.py` | Transcription history and persistence |
| `ui.py` | Rich rendering, prompts, clipboard, and nonblocking Enter-to-stop listener |
| `i18n.py` | English/Spanish UI strings and language labels |

`CLI` injects dependencies into `DictationManager`, `PracticeManager`, and
`ConfigManager`. Preserve constructor injection so tests can use mocks.

Lesson downloads use a single-worker `ThreadPoolExecutor`. The CLI polls preload
state and suppresses noisy loggers during background downloads. Preserve executor
shutdown and idempotent cleanup when changing exit paths. Recording must be stopped
and finalized successfully before audio is sent for transcription.

### Text comparison

The main ideas from the earlier improvement plan are implemented in `comparison.py`
and covered by `tests/test_comparison.py`. The current behavior is described below,
not the old proposal's API names or proposed configuration fields.

- `compare_with_method()` dispatches according to `Config.comparison_method`.
- `flexible` (default) searches around a moving transcript anchor, preferring
  exact matches before optional phonetic matches. The default window is ±4 tokens
  (`COMPARISON_WINDOW_SIZE`), not a configurable JSON field.
- `per_word` matches word presence regardless of order, consuming each matched
  transcript position once.
- `legacy` uses sequential `difflib` alignment.
- Normalization handles punctuation and English contractions. Preserve the mapping
  from normalized tokens to displayed words so error highlighting stays aligned.
- Simplified phonetic matching is a heuristic with safeguards for short words and
  partial-word matches; it is distinct from the IPA hints in `phonetics.py`.
- Scores are matched reference tokens divided by total reference tokens (0–1).
  Missing and extra words are reported separately; this is not acoustic assessment.

Only `comparison_method` is persisted as a comparison setting. Window size and
phonetic matching can be supplied to comparison APIs, but are not additional
settings in `Config`.

## Coding conventions

- Follow surrounding code; Python 3.10+, 88-character lines (Black/Ruff).
- Use type hints on function signatures and Google-style public docstrings.
- Use `snake_case` for modules/functions/variables, `PascalCase` for classes,
  `UPPER_SNAKE_CASE` for constants, and `_` prefixes for private methods.
- Sort imports with isort: standard library, third-party, then local imports.
- Prefer dataclasses for simple data containers.
- Use specific exceptions and meaningful messages; use existing recorder/history
  exception types where appropriate. Avoid broad catches for routine failures.
- Use module-level `logging.getLogger(__name__)`; keep diagnostic noise out of the
  interactive Rich UI, especially during background work.
- Put new shared constants in `constants.py`, configuration in `config.py`, and UI
  text in `i18n.py` with both English and Spanish translations. Use
  `get_text(key, lang)` instead of new hardcoded UI strings.
- Reuse the injected UI/console rather than introducing additional global consoles.

## Tests and change workflow

- Create a focused feature/fix/docs branch for changes.
- Keep tests in `tests/test_<module>.py`, classes named `Test<ModuleName>`, and
  descriptive `test_<behavior>` methods. Add regression tests for behavior changes.
- Preserve `tests/fixtures/breaking_news_homepage.md`: it is input data used by
  `tests/test_lessons.py`, not obsolete documentation.
- Run relevant tests and quality checks; report failures and unavailable tools
  accurately. Documentation-only edits do not require recording audio or
  downloading models/lessons.
- Add dependencies to `pyproject.toml` and reinstall the development extra when
  needed. Update these instructions if commands or architecture change.
- Keep README user-facing; keep shared development guidance in this file.
  Remove completed plans after retaining useful
  current behavior here; Git history preserves the original design.
- Use Conventional Commits prefixes (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`,
  `chore:`, etc.). Do not add a `Co-Authored-By: Claude ...` trailer.
- Do not commit or push without the user's request, and do not overwrite unrelated
  work.
