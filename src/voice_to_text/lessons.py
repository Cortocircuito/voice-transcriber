"""Lesson management for reading practice."""

import json
import logging
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://breakingnewsenglish.com"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"


class LessonError(Exception):
    """Base exception for lesson errors."""
    pass


class NetworkError(LessonError):
    """Raised when network request fails."""
    pass


class ParseError(LessonError):
    """Raised when parsing fails."""
    pass


def get_lessons_cache_dir() -> Path:
    """Get the cache directory for lessons."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "voice-to-text" / "lessons"
    return Path.home() / ".config" / "voice-to-text" / "lessons"


@dataclass
class Lesson:
    """A reading practice lesson."""
    title: str
    url: str
    date: str
    description: str
    levels: list[str]
    texts: dict[str, str]
    
    def get_text(self, level: str) -> Optional[str]:
        """Get the text for a specific level."""
        return self.texts.get(level)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lesson":
        """Create from dictionary."""
        return cls(
            title=data.get("title", ""),
            url=data.get("url", ""),
            date=data.get("date", ""),
            description=data.get("description", ""),
            levels=data.get("levels", []),
            texts=data.get("texts", {}),
        )


class LessonManager:
    """Manages lesson fetching, caching, and retrieval."""
    
    def __init__(self):
        self._cache_dir = get_lessons_cache_dir()
        self._index_file = self._cache_dir / "index.json"
        self._cache: dict[str, Lesson] = {}
    
    def _fetch_url(self, url: str, timeout: int = 10) -> str:
        """Fetch content from URL.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            HTML content as string
            
        Raises:
            NetworkError: If request fails
        """
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": USER_AGENT},
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", errors="ignore")
        except urllib.error.URLError as e:
            raise NetworkError(f"Network error fetching {url}: {e}") from e
        except Exception as e:
            raise NetworkError(f"Error fetching {url}: {e}") from e
    
    def _parse_homepage(self, html: str) -> list[dict[str, str]]:
        """Parse homepage to extract lesson info.
        
        Args:
            html: HTML content of homepage
            
        Returns:
            List of lesson info dictionaries
        """
        lessons = []
        
        title_pattern = r'<a[^>]+href="(/(\d{4})/(\d{6})-([^"]+)\.html)"[^>]*>([^<]+)</a>'
        
        for match in re.finditer(title_pattern, html, re.IGNORECASE):
            url_path, year, date_code, slug, title = match.groups()
            
            full_url = f"{BASE_URL}{url_path}"
            
            date_str = date_code[:2] + "/" + date_code[2:4] + "/" + year[2:]
            
            lessons.append({
                "title": title.strip(),
                "url": full_url,
                "date": date_str,
                "slug": slug,
            })
        
        seen = set()
        unique_lessons = []
        for lesson in lessons:
            if lesson["url"] not in seen:
                seen.add(lesson["url"])
                unique_lessons.append(lesson)
        
        return unique_lessons[:10]
    
    def _parse_lesson_page(self, html: str, url: str) -> dict[str, str]:
        """Parse a lesson page to extract texts for all levels.
        
        Args:
            html: HTML content of lesson page
            url: URL of the lesson
            
        Returns:
            Dictionary mapping level to text
        """
        texts = {}
        
        level_patterns = [
            (r'<a[^>]+href="[^"]*-(\d)\.html[^"]*"[^>]*>Level\s*\1', None),
            (r'Level\s*(\d)', None),
        ]
        
        levels_found = set()
        for pattern, _ in level_patterns:
            for match in re.finditer(pattern, html, re.IGNORECASE):
                level = match.group(1)
                if level.isdigit():
                    levels_found.add(level)
        
        if not levels_found:
            levels_found = {"2", "3"}
        
        for level in levels_found:
            level_url = url.replace(".html", f"-{level}.html")
            try:
                level_html = self._fetch_url(level_url)
                text = self._extract_text(level_html)
                if text:
                    texts[level] = text
            except NetworkError:
                continue
        
        if not texts:
            text = self._extract_text(html)
            if text:
                texts["2"] = text
        
        return texts
    
    def _extract_text(self, html: str) -> str:
        """Extract readable text from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Extracted and cleaned text
        """
        text = html
        
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
        
        text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
        text = re.sub(r'</p>', '\n\n', text, flags=re.IGNORECASE)
        text = re.sub(r'<[^>]+>', ' ', text)
        
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&amp;', '&', text)
        text = re.sub(r'&lt;', '<', text)
        text = re.sub(r'&gt;', '>', text)
        text = re.sub(r'&quot;', '"', text)
        text = re.sub(r'&#39;', "'", text)
        
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        patterns = [
            r'The Reading / Listening.*?(?=\n\n|\Z)',
            r'Copyright.*?Banville',
            r'Breaking News English',
            r'Home.*?Help This Site',
            r'MY e-BOOK',
            r'SEE MORE\.\.\.',
            r'Try (easier|harder) levels',
            r'Download this',
            r'Listen A Minute',
            r'ESL Discussions',
            r'Famous People Lessons',
            r'ESL Holiday Lessons',
            r'Business English Materials',
            r'Lessons On Movies',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def fetch_lessons(self, use_cache: bool = True) -> list[Lesson]:
        """Fetch lessons from website or cache.
        
        Args:
            use_cache: Whether to use cached lessons if available
            
        Returns:
            List of Lesson objects
        """
        if use_cache:
            cached = self._load_cache()
            if cached:
                return cached
        
        try:
            html = self._fetch_url(BASE_URL)
            lesson_infos = self._parse_homepage(html)
            
            lessons = []
            for info in lesson_infos[:5]:
                try:
                    lesson_html = self._fetch_url(info["url"])
                    texts = self._parse_lesson_page(lesson_html, info["url"])
                    
                    if texts:
                        levels = sorted(texts.keys())
                        description = self._extract_description(lesson_html)
                        
                        lesson = Lesson(
                            title=info["title"],
                            url=info["url"],
                            date=info["date"],
                            description=description,
                            levels=levels,
                            texts=texts,
                        )
                        lessons.append(lesson)
                        self._cache[info["url"]] = lesson
                except (NetworkError, ParseError) as e:
                    logger.warning(f"Failed to fetch lesson {info['url']}: {e}")
                    continue
            
            if lessons:
                self._save_cache(lessons)
            
            return lessons
            
        except NetworkError:
            if use_cache:
                return self._load_cache()
            raise
    
    def _extract_description(self, html: str) -> str:
        """Extract lesson description from HTML."""
        meta_pattern = r'<meta[^>]+name="description"[^>]+content="([^"]+)"'
        match = re.search(meta_pattern, html, re.IGNORECASE)
        if match:
            return match.group(1).strip()
        
        return ""
    
    def _save_cache(self, lessons: list[Lesson]) -> bool:
        """Save lessons to cache.
        
        Args:
            lessons: List of lessons to cache
            
        Returns:
            True if save was successful
        """
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            
            data = {
                "timestamp": datetime.now().isoformat(),
                "lessons": [lesson.to_dict() for lesson in lessons],
            }
            
            temp_file = self._index_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            temp_file.replace(self._index_file)
            logger.debug(f"Cached {len(lessons)} lessons")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False
    
    def _load_cache(self) -> list[Lesson]:
        """Load lessons from cache.
        
        Returns:
            List of cached lessons
        """
        if not self._index_file.exists():
            return []
        
        try:
            with open(self._index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            lessons = []
            for item in data.get("lessons", []):
                lesson = Lesson.from_dict(item)
                lessons.append(lesson)
                self._cache[lesson.url] = lesson
            
            return lessons
            
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []
    
    def get_cached_lessons(self) -> list[Lesson]:
        """Get all cached lessons."""
        return self._load_cache()
    
    def clear_cache(self) -> bool:
        """Clear the lesson cache.
        
        Returns:
            True if clearing was successful
        """
        try:
            if self._index_file.exists():
                self._index_file.unlink()
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
