"""Lesson management for reading practice."""

import json
import logging
import os
import re
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

BASE_URL = "https://breakingnewsenglish.com"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class LessonError(Exception):
    """Base exception for lesson errors."""
    pass


class NetworkError(LessonError):
    """Raised when network request fails."""
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
        self._preload_future: Optional[Future] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
    
    def _fetch_url(self, url: str, timeout: int = 20) -> str:
        """Fetch content from URL with human-like behavior.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            HTML content as string
            
        Raises:
            NetworkError: If request fails
        """
        time.sleep(0.5 + (0.3 * (hash(url) % 3)))
        
        try:
            request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Accept-Encoding": "identity",
                    "Cache-Control": "max-age=0",
                    "Connection": "keep-alive",
                },
            )
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read()
                return content.decode("utf-8", errors="ignore")
        except urllib.error.HTTPError as e:
            raise NetworkError(f"HTTP {e.code} error fetching {url}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise NetworkError(f"Network error fetching {url}: {e.reason}") from e
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
        seen_urls = set()
        
        patterns = [
            r'<a[^>]+href="(\d{4}/\d{6}-[^"]+\.html)"[^>]*>([^<]+)</a>',
            r'<article[^>]*>.*?<h3><a href="([^"]+\.html)"[^>]*>([^<]+)</a></h3>',
            r'href="([^"]*\d{6}[^"]*\.html)"[^>]*>([^<]{20,}?)</a>',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, html, re.DOTALL | re.IGNORECASE):
                url_path, title = match.groups()
                
                if not url_path.startswith('http'):
                    if url_path.startswith('/'):
                        full_url = BASE_URL + url_path
                    else:
                        full_url = BASE_URL + "/" + url_path
                else:
                    full_url = url_path
                
                if not re.search(r'\d{6}-', full_url):
                    continue
                
                if full_url in seen_urls:
                    continue
                
                seen_urls.add(full_url)
                
                date_match = re.search(r'/(\d{4})/(\d{2})(\d{2})-', full_url)
                if date_match:
                    year, month, day = date_match.groups()
                    date_str = f"{day}/{month}/{year[2:]}"
                else:
                    date_str = ""
                
                title = re.sub(r'\s+', ' ', title).strip()
                title = re.sub(r'^\s*-\s*', '', title)
                
                if len(title) < 10:
                    continue
                
                lessons.append({
                    "title": title,
                    "url": full_url,
                    "date": date_str,
                })
        
        return lessons[:10]
    
    def _extract_reading_text(self, html: str) -> str:
        """Extract the main reading text from lesson HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Clean reading text
        """
        skip_patterns = [
            'copyright', 'lesson on', 'free worksheet', 'online activit',
            'breaking news english', 'esl lesson', 'download', 'subscribe',
            'twitter', 'facebook', 'instagram', 'bluesky', 'rss feed',
            'help this site', 'buy my', 'e-book', 'see a sample',
            'listen a minute', 'famous people', 'esl discussion',
            'business english', 'movie lesson', 'holiday lesson',
            'complete this table', 'spend one minute writing',
            'what do you know about', 'how exciting are they',
            'share what you wrote', 'change partners often',
            'to what degree are', 'who would you give',
            'write down all of the different words',
            'different words you associate with',
            'put the words into different categories',
            'share your words with your partner',
            'speed reading', '5-speed listening', 'grammar', 'dictation',
            'spelling', 'prepositions', 'jumble', 'no spaces',
            'gap fill', 'missing words', 'word pairs', 'match',
            'and talk about them', 'together, put the words',
        ]
        
        text_blocks = []
        
        content_patterns = [
            r'>([A-Z][^<]{150,}?[\.\!\?])<',
            r'<p[^>]*>([A-Z][^<]{100,}?[\.\!\?])</p>',
        ]
        
        seen_texts = set()
        
        for pattern in content_patterns:
            for match in re.finditer(pattern, html, re.IGNORECASE):
                text = match.group(1).strip()
                
                text = re.sub(r'\s+', ' ', text)
                text = re.sub(r'\([^)]+\)', '', text)
                text = re.sub(r'\[[^\]]+\]', '', text)
                text = re.sub(r'_{2,}', '', text)
                text = re.sub(r'\s+', ' ', text).strip()
                
                if len(text) < 80:
                    continue
                
                text_lower = text.lower()
                if any(skip in text_lower for skip in skip_patterns):
                    continue
                
                if text_lower.startswith('what do you') or text_lower.startswith('how '):
                    continue
                if text_lower.startswith('spend one minute') or text_lower.startswith('complete this'):
                    continue
                if text_lower.startswith('who would you') or text_lower.startswith('to what degree'):
                    continue
                
                normalized = ' '.join(text.split()[:10])
                if normalized in seen_texts:
                    continue
                seen_texts.add(normalized)
                
                text_blocks.append(text)
        
        if text_blocks:
            combined = ' '.join(text_blocks[:8])
            return combined
        
        return ""
    
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
                logger.info(f"Using {len(cached)} cached lessons")
                return cached
        
        try:
            logger.info("Fetching lessons from Breaking News English...")
            html = self._fetch_url(BASE_URL)
            lesson_infos = self._parse_homepage(html)
            
            logger.info(f"Found {len(lesson_infos)} lesson links")
            
            lessons = []
            for i, info in enumerate(lesson_infos[:6]):
                try:
                    logger.debug(f"Fetching lesson {i+1}/{min(6, len(lesson_infos))}: {info['title'][:40]}")
                    lesson_html = self._fetch_url(info["url"])
                    text = self._extract_reading_text(lesson_html)
                    
                    if text and len(text) > 100:
                        levels = ["2", "3"]
                        if "level 0" in lesson_html.lower() or "level-0" in lesson_html.lower():
                            levels = ["0", "1", "2"]
                        elif "level 4" in lesson_html.lower():
                            levels = ["4", "5"]
                        
                        description = self._extract_description(lesson_html)
                        
                        texts = {level: text for level in levels}
                        
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
                        logger.info(f"Loaded: {lesson.title[:50]} ({len(text)} chars, levels: {levels})")
                        
                except NetworkError as e:
                    logger.warning(f"Failed to fetch lesson: {e}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing lesson: {e}")
                    continue
            
            if lessons:
                self._save_cache(lessons)
                logger.info(f"Successfully loaded {len(lessons)} lessons")
            else:
                logger.warning("No lessons were extracted")
            
            return lessons
            
        except NetworkError as e:
            logger.error(f"Network error: {e}")
            if use_cache:
                cached = self._load_cache()
                if cached:
                    logger.info("Using cached lessons due to network error")
                    return cached
            raise
    
    def _extract_description(self, html: str) -> str:
        """Extract lesson description from HTML."""
        meta_pattern = r'<meta[^>]+name="description"[^>]+content="([^"]+)"'
        match = re.search(meta_pattern, html, re.IGNORECASE)
        if match:
            desc = match.group(1).strip()
            desc = re.sub(r'Breaking News English.*', '', desc, flags=re.IGNORECASE)
            return desc.strip()
        return ""
    
    def _save_cache(self, lessons: list[Lesson]) -> bool:
        """Save lessons to cache."""
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
        """Load lessons from cache."""
        if not self._index_file.exists():
            return []
        
        try:
            with open(self._index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            timestamp = data.get("timestamp", "")
            if timestamp:
                cache_time = datetime.fromisoformat(timestamp)
                age_hours = (datetime.now() - cache_time).total_seconds() / 3600
                if age_hours > 24:
                    logger.info("Cache is older than 24 hours")
                    return []
            
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
        """Clear the lesson cache."""
        try:
            if self._index_file.exists():
                self._index_file.unlink()
            self._cache.clear()
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def preload_lessons_async(self) -> None:
        """Start async preloading of lessons."""
        if self._preload_future is None or self._preload_future.done():
            self._preload_future = self._executor.submit(self._preload_task)
            logger.debug("Started async lesson preload")
    
    def _preload_task(self) -> list[Lesson]:
        """Background task to preload lessons."""
        try:
            return self.fetch_lessons(use_cache=True)
        except Exception as e:
            logger.error(f"Preload failed: {e}")
            return []
    
    def get_preloaded_lessons(self) -> list[Lesson]:
        """Get lessons, waiting for preload if necessary."""
        if self._preload_future is not None:
            try:
                return self._preload_future.result(timeout=30)
            except Exception:
                pass
        return self._load_cache()
