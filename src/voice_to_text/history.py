"""Transcription history management."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict


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
        self._entries: List[HistoryEntry] = []
        self._config_dir = get_xdg_config_dir()
        self._history_file = get_history_file_path()
    
    def add_entry(self, language: str, duration: int, text: str):
        """Add a new transcription to history."""
        if text.strip():
            entry = HistoryEntry.create(language, duration, text)
            self._entries.append(entry)
    
    def get_entries(self) -> List[HistoryEntry]:
        """Get all history entries."""
        return self._entries.copy()
    
    def clear(self):
        """Clear in-memory history."""
        self._entries.clear()
    
    def save(self) -> bool:
        """Save history to JSON file."""
        if not self._entries:
            return True
        
        try:
            self._config_dir.mkdir(parents=True, exist_ok=True)
            
            existing_entries = self._load_existing()
            
            all_entries = existing_entries + [asdict(e) for e in self._entries]
            
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump(all_entries, f, ensure_ascii=False, indent=2)
            
            self._entries.clear()
            return True
        except Exception:
            return False
    
    def _load_existing(self) -> List[dict]:
        """Load existing history entries from file."""
        if not self._history_file.exists():
            return []
        
        try:
            with open(self._history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    
    def load_all(self) -> List[dict]:
        """Load all history from file."""
        return self._load_existing()
    
    def get_stats(self) -> dict:
        """Get statistics about the history."""
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
