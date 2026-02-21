"""Transcription history management."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class HistoryError(Exception):
    """Base exception for history errors."""
    pass


class HistorySaveError(HistoryError):
    """Raised when saving history fails."""
    pass


class HistoryLoadError(HistoryError):
    """Raised when loading history fails."""
    pass


def get_xdg_config_dir() -> Path:
    """Get XDG config directory for the application."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "voice-to-text"
    return Path.home() / ".config" / "voice-to-text"


def get_history_file_path() -> Path:
    """Get the path to the history file."""
    return get_xdg_config_dir() / "history.json"


@dataclass
class HistoryEntry:
    """A single transcription history entry."""
    timestamp: str
    language: str
    duration: int
    text: str
    
    @classmethod
    def create(cls, language: str, duration: int, text: str) -> "HistoryEntry":
        """Create a new history entry with current timestamp."""
        return cls(
            timestamp=datetime.now().isoformat(),
            language=language,
            duration=duration,
            text=text,
        )


class HistoryManager:
    """Manages transcription history."""
    
    def __init__(self):
        self._entries: list[HistoryEntry] = []
        self._config_dir = get_xdg_config_dir()
        self._history_file = get_history_file_path()
    
    def add_entry(self, language: str, duration: int, text: str) -> None:
        """Add a new transcription to history.
        
        Args:
            language: Language code of the transcription
            duration: Recording duration in seconds
            text: Transcribed text
        """
        if text.strip():
            entry = HistoryEntry.create(language, duration, text)
            self._entries.append(entry)
    
    def get_entries(self) -> list[HistoryEntry]:
        """Get all in-memory history entries.
        
        Returns:
            Copy of the entries list
        """
        return self._entries.copy()
    
    def clear(self) -> None:
        """Clear in-memory history."""
        self._entries.clear()
    
    def clear_all(self) -> bool:
        """Clear all history (in-memory and from file).
        
        Returns:
            True if clearing was successful, False otherwise
        """
        self._entries.clear()
        
        if not self._history_file.exists():
            return True
        
        try:
            self._history_file.unlink()
            logger.debug(f"Deleted history file: {self._history_file}")
            return True
        except PermissionError as e:
            logger.error(f"Permission denied deleting history: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error deleting history: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting history: {e}")
            return False
    
    def save(self) -> bool:
        """Save history to JSON file.
        
        Returns:
            True if save was successful, False otherwise
        """
        if not self._entries:
            return True
        
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            existing_entries = self._load_existing()
            
            all_entries = existing_entries + [asdict(e) for e in self._entries]
            
            temp_file = self._history_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            
            temp_file.replace(self._history_file)
            
            logger.debug(f"Saved {len(self._entries)} entries to {self._history_file}")
            self._entries.clear()
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied saving history: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error saving history: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving history: {e}")
            return False
    
    def _load_existing(self) -> list[dict[str, Any]]:
        """Load existing history entries from file.
        
        Returns:
            List of history entry dictionaries
        """
        if not self._history_file.exists():
            return []
        
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                logger.warning(f"History file contains invalid format: {type(data)}")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in history file: {e}")
            return []
        except PermissionError as e:
            logger.error(f"Permission denied reading history: {e}")
            return []
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return []
    
    def load_all(self) -> list[dict[str, Any]]:
        """Load all history from file.
        
        Returns:
            List of all history entries
        """
        return self._load_existing()
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the history.
        
        Returns:
            Dictionary with total count, languages breakdown, and total duration
        """
        all_entries = self._load_existing() + [asdict(e) for e in self._entries]
        
        if not all_entries:
            return {"total": 0, "languages": {}, "total_duration": 0}
        
        languages: dict[str, int] = {}
        total_duration = 0
        
        for entry in all_entries:
            lang = entry.get("language", "unknown")
            languages[lang] = languages.get(lang, 0) + 1
            total_duration += entry.get("duration", 0)
        
        return {
            "total": len(all_entries),
            "languages": languages,
            "total_duration": total_duration,
        }
