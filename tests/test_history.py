"""Tests for history module."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from voice_to_text.history import (
    HistoryEntry,
    HistoryManager,
    get_xdg_config_dir,
    get_history_file_path,
    HistoryError,
    HistorySaveError,
    HistoryLoadError,
)


class TestHistoryEntry:
    def test_create(self):
        entry = HistoryEntry.create(language="en", duration=15, text="Hello world")
        
        assert entry.language == "en"
        assert entry.duration == 15
        assert entry.text == "Hello world"
        assert entry.timestamp is not None
    
    def test_create_empty_text(self):
        entry = HistoryEntry.create(language="es", duration=10, text="")
        
        assert entry.language == "es"
        assert entry.text == ""
    
    def test_asdict(self):
        entry = HistoryEntry(timestamp="2026-01-01T00:00:00", language="en", duration=15, text="Test")
        
        from dataclasses import asdict
        d = asdict(entry)
        
        assert d["timestamp"] == "2026-01-01T00:00:00"
        assert d["language"] == "en"
        assert d["duration"] == 15
        assert d["text"] == "Test"


class TestHistoryExceptions:
    def test_history_error_is_exception(self):
        assert issubclass(HistoryError, Exception)
    
    def test_history_save_error_is_history_error(self):
        assert issubclass(HistorySaveError, HistoryError)
    
    def test_history_load_error_is_history_error(self):
        assert issubclass(HistoryLoadError, HistoryError)
    
    def test_can_raise_history_error(self):
        with pytest.raises(HistoryError):
            raise HistoryError("test error")


class TestXDGPaths:
    def test_default_xdg_config_dir(self):
        with patch.dict(os.environ, {}, clear=True):
            if "XDG_CONFIG_HOME" in os.environ:
                del os.environ["XDG_CONFIG_HOME"]
            
            result = get_xdg_config_dir()
            
            assert result == Path.home() / ".config" / "voice-to-text"
    
    def test_custom_xdg_config_dir(self):
        with patch.dict(os.environ, {"XDG_CONFIG_HOME": "/custom/config"}):
            result = get_xdg_config_dir()
            
            assert result == Path("/custom/config") / "voice-to-text"
    
    def test_history_file_path(self):
        with patch("voice_to_text.history.get_xdg_config_dir", return_value=Path("/test/dir")):
            result = get_history_file_path()
            
            assert result == Path("/test/dir/history.json")


class TestHistoryManager:
    def test_init(self):
        manager = HistoryManager()
        
        assert manager._entries == []
    
    def test_add_entry(self):
        manager = HistoryManager()
        
        manager.add_entry(language="en", duration=15, text="Hello world")
        
        entries = manager.get_entries()
        assert len(entries) == 1
        assert entries[0].language == "en"
        assert entries[0].duration == 15
        assert entries[0].text == "Hello world"
    
    def test_add_entry_empty_text_skipped(self):
        manager = HistoryManager()
        
        manager.add_entry(language="en", duration=15, text="   ")
        
        assert len(manager.get_entries()) == 0
    
    def test_add_multiple_entries(self):
        manager = HistoryManager()
        
        manager.add_entry(language="en", duration=15, text="First")
        manager.add_entry(language="es", duration=10, text="Second")
        
        entries = manager.get_entries()
        assert len(entries) == 2
    
    def test_clear(self):
        manager = HistoryManager()
        manager.add_entry(language="en", duration=15, text="Test")
        
        manager.clear()
        
        assert len(manager.get_entries()) == 0
    
    def test_save_empty(self):
        manager = HistoryManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("voice_to_text.history.get_xdg_config_dir", return_value=Path(tmpdir)):
                manager._config_dir = Path(tmpdir)
                manager._history_file = Path(tmpdir) / "history.json"
                
                result = manager.save()
                
                assert result is True
                assert not (Path(tmpdir) / "history.json").exists()
    
    def test_save_creates_directory(self):
        manager = HistoryManager()
        manager.add_entry(language="en", duration=15, text="Test")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / "nested" / "config"
            manager._config_dir = config_dir
            manager._history_file = config_dir / "history.json"
            
            result = manager.save()
            
            assert result is True
            assert config_dir.exists()
            assert manager._history_file.exists()
    
    def test_save_and_load(self):
        manager = HistoryManager()
        manager.add_entry(language="en", duration=15, text="Test entry")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager._config_dir = Path(tmpdir)
            manager._history_file = Path(tmpdir) / "history.json"
            
            manager.save()
            
            with open(manager._history_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 1
            assert data[0]["language"] == "en"
            assert data[0]["text"] == "Test entry"
    
    def test_save_appends_to_existing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            
            existing = [{"timestamp": "2026-01-01T00:00:00", "language": "es", "duration": 10, "text": "Old"}]
            with open(history_file, 'w') as f:
                json.dump(existing, f)
            
            manager = HistoryManager()
            manager._config_dir = Path(tmpdir)
            manager._history_file = history_file
            manager.add_entry(language="en", duration=15, text="New")
            
            manager.save()
            
            with open(history_file, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]["text"] == "Old"
            assert data[1]["text"] == "New"
    
    def test_get_stats_empty(self):
        manager = HistoryManager()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            manager._history_file = Path(tmpdir) / "history.json"
            
            stats = manager.get_stats()
            
            assert stats["total"] == 0
            assert stats["languages"] == {}
            assert stats["total_duration"] == 0
    
    def test_get_stats_with_entries(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager()
            manager._history_file = Path(tmpdir) / "history.json"
            
            manager.add_entry(language="en", duration=15, text="Test 1")
            manager.add_entry(language="en", duration=10, text="Test 2")
            manager.add_entry(language="es", duration=20, text="Test 3")
            
            stats = manager.get_stats()
            
            assert stats["total"] == 3
            assert stats["languages"]["en"] == 2
            assert stats["languages"]["es"] == 1
            assert stats["total_duration"] == 45
    
    def test_load_all(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            
            existing = [
                {"timestamp": "2026-01-01T00:00:00", "language": "en", "duration": 15, "text": "Entry"}
            ]
            with open(history_file, 'w') as f:
                json.dump(existing, f)
            
            manager = HistoryManager()
            manager._history_file = history_file
            
            loaded = manager.load_all()
            
            assert len(loaded) == 1
            assert loaded[0]["text"] == "Entry"

    def test_clear_all_no_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = HistoryManager()
            manager._history_file = Path(tmpdir) / "history.json"
            manager.add_entry(language="en", duration=15, text="Test")
            
            result = manager.clear_all()
            
            assert result is True
            assert len(manager.get_entries()) == 0

    def test_clear_all_with_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            
            existing = [{"timestamp": "2026-01-01T00:00:00", "language": "en", "duration": 15, "text": "Entry"}]
            with open(history_file, 'w') as f:
                json.dump(existing, f)
            
            manager = HistoryManager()
            manager._history_file = history_file
            manager.add_entry(language="en", duration=10, text="New")
            
            result = manager.clear_all()
            
            assert result is True
            assert not history_file.exists()
            assert len(manager.get_entries()) == 0

    def test_clear_all_then_save_new(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            history_file = Path(tmpdir) / "history.json"
            
            existing = [{"timestamp": "2026-01-01T00:00:00", "language": "en", "duration": 15, "text": "Old"}]
            with open(history_file, 'w') as f:
                json.dump(existing, f)
            
            manager = HistoryManager()
            manager._history_file = history_file
            
            manager.clear_all()
            manager.add_entry(language="es", duration=20, text="New")
            manager.save()
            
            loaded = manager.load_all()
            assert len(loaded) == 1
            assert loaded[0]["text"] == "New"
            assert loaded[0]["language"] == "es"
