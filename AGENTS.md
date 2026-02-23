# AGENTS.md - Guidelines for AI Agents

This file provides guidelines for AI agents working on this codebase.

## Project Overview

Voice-to-text is a Python CLI application for speech transcription using faster-whisper. It provides an interactive terminal UI for dictation and lesson practice modes.

## Build, Lint, and Test Commands

### Running Tests

```bash
# Run all tests
pytest

# Run a single test file
pytest tests/test_config.py

# Run a single test
pytest tests/test_config.py::TestConfig::test_default_values

# Run with coverage
pytest --cov=src/voice_to_text --cov-report=term-missing
```

### Linting and Formatting

```bash
# Run ruff linter
ruff check src/

# Run ruff with auto-fix
ruff check src/ --fix

# Run black formatter
black src/

# Run isort import sorter
isort src/

# Run mypy type checker
mypy src/

# Run all pre-commit hooks
pre-commit run --all-files
```

### Running the Application

```bash
# Install the package
pip install -e .

# Run the CLI
voice-to-text

# Or run directly
python -m voice_to_text
```

## Code Style Guidelines

### General Rules

- **Line length**: 88 characters (configured in black/ruff)
- **Python version**: 3.10+
- **Type hints**: Use type hints for all function signatures
- **Docstrings**: Use Google-style docstrings for public functions

### Import Organization

Organize imports in the following order (use isort to enforce):

1. Standard library imports
2. Third-party imports
3. Local application imports

Within each group, alphabetize by module name.

```python
# Correct
import logging
import os
from typing import Optional

from rich.console import Console

from voice_to_text.config import Config
from voice_to_text.ui import UI
```

### Naming Conventions

- **Modules**: `snake_case` (e.g., `my_module.py`)
- **Classes**: `PascalCase` (e.g., `MyClass`)
- **Functions/variables**: `snake_case` (e.g., `my_function`, `my_variable`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_DURATION`)
- **Private methods**: prefix with `_` (e.g., `_private_method`)

### Type Hints

Always use type hints in function signatures:

```python
# Good
def my_function(name: str, value: int) -> Optional[str]:
    ...

# Avoid
def my_function(name, value):
    ...
```

### Custom Exceptions

Create custom exceptions inheriting from the appropriate base class:

```python
class RecorderError(Exception):
    """Base exception for recorder errors."""
    pass


class MicrophoneNotFoundError(RecorderError):
    """Raised when no microphone is found."""
    pass
```

### Error Handling

- Use specific exception types rather than catching generic `Exception`
- Provide meaningful error messages
- Use logging for errors that don't need to stop execution

```python
# Good
try:
    result = some_function()
except ValueError as e:
    logger.error(f"Invalid value: {e}")
    return None
```

### Logging

Use module-level loggers:

```python
logger = logging.getLogger(__name__)
```

Log levels:
- `logger.debug()` - Detailed information for debugging
- `logger.info()` - Confirmation that things work as expected
- `logger.warning()` - Something unexpected happened, but continue
- `logger.error()` - Serious problem, function couldn't perform task

### Class Structure

```python
class MyClass:
    """Short description of the class.

    Longer description if needed.
    """

    def __init__(
        self,
        param1: str,
        param2: int,
        optional_param: Optional[str] = None,
    ) -> None:
        self.param1 = param1
        self.param2 = param2
        self.optional_param = optional_param

    def public_method(self) -> str:
        """Description of what this method does.

        Returns:
            Description of return value.
        """
        return "result"

    def _private_method(self) -> None:
        """Internal method, not part of public API."""
        pass
```

### Dataclasses

Use dataclasses for simple data containers:

```python
from dataclasses import dataclass


@dataclass
class MyDataClass:
    name: str
    value: int
    optional_field: Optional[str] = None
```

### Testing Guidelines

- Test files go in `tests/` directory
- Name test files as `test_<module>.py`
- Test classes named `Test<ModuleName>`
- Test methods named `test_<description>`
- Use descriptive test names that explain what is being tested

```python
class TestConfig:
    def test_validate_duration_returns_value_when_valid(self):
        config = Config()
        assert config.validate_duration("30") == 30
```

### Rich Library Usage

The project uses Rich for terminal UI. Key patterns:

```python
from rich.console import Console
from rich.panel import Panel

console = Console()

# Print colored text
console.print("[bold red]Error:[/bold red] Something went wrong")

# Print a panel
console.print(Panel(content, title="Title"))
```

### Configuration

- All constants go in `src/voice_to_text/constants.py`
- Config class uses dataclass in `src/voice_to_text/config.py`
- Internationalization strings in `src/voice_to_text/i18n.py`

## Pre-commit Hooks

The project uses pre-commit. Install hooks with:

```bash
pip install -e ".[dev]"
pre-commit install
```

Hooks include:
- black (formatting)
- isort (import sorting)
- ruff (linting)
- mypy (type checking)
- bandit (security)

## Common Tasks

### Adding a New Feature

1. Create feature branch
2. Add code to appropriate module in `src/voice_to_text/`
3. Add tests in `tests/`
4. Run linters: `ruff check src/ && black src/ && mypy src/`
5. Run tests: `pytest`
6. Commit and push

### Adding Internationalization

1. Add translation keys to `src/voice_to_text/i18n.py`
2. Use `get_text("key", lang)` in code

### Adding a New Dependency

1. Add to `dependencies` in `pyproject.toml`
2. Run `pip install -e ".[dev]"` to update
3. Update this AGENTS.md if adding a new tool/command
