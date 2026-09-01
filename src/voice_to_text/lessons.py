"""Lesson management for reading practice."""

import json
import logging
import os
import re
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, cast
from urllib.parse import urljoin

from scrapesome import sync_scraper

logger = logging.getLogger(__name__)

BASE_URL = "https://breakingnewsenglish.com"

# The lesson pages append a bibliographic reference after the article, followed
# by exercises and other site content. The reference is not part of the text to
# practise reading aloud.
BIBLIOGRAPHIC_CITATION_PATTERN = re.compile(
    r"\b[A-Z][A-Za-z'-]+,\s*(?:[A-Z]\.\s*)+"
    r"(?:(?:and|&)\s+[A-Z][A-Za-z'-]+,\s*(?:[A-Z]\.\s*)+)?"
    r"\(\d{4}[a-z]?\)"
)


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
    level_urls: dict[str, str]
    paragraphs: dict[str, list[str]]

    def get_text(self, level: str) -> Optional[str]:
        """Get the text for a specific level."""
        return self.texts.get(level)

    def get_paragraphs(self, level: str) -> list[str]:
        """Get paragraphs for a specific level."""
        return self.paragraphs.get(level, [])

    def get_level_url(self, level: str) -> Optional[str]:
        """Get the URL for a specific level."""
        return self.level_urls.get(level)

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
            level_urls=data.get("level_urls", {}),
            paragraphs=data.get("paragraphs", {}),
        )


class LessonManager:
    """Manages lesson fetching, caching, and retrieval."""

    def __init__(self):
        self._cache_dir = get_lessons_cache_dir()
        self._index_file = self._cache_dir / "index.json"
        self._cache: dict[str, Lesson] = {}
        self._preload_future: Optional[Future] = None
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._preload_complete: bool = False
        self._preload_succeeded: bool = False

    def _fetch_url(self, url: str, timeout: int = 20) -> str:
        """Fetch content from URL using scrapesome.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds

        Returns:
            Markdown content as string

        Raises:
            NetworkError: If request fails
        """
        try:
            result: Any = sync_scraper(
                url,
                output_format_type="markdown",
                timeout=timeout,
            )
            if isinstance(result, dict):
                return cast(str, result.get("data", ""))
            return cast(str, result)
        except Exception as e:
            raise NetworkError(f"Error fetching {url}: {e}") from e

    def _parse_homepage(self, content: str) -> list[dict[str, Any]]:
        """Parse homepage to extract lesson info.

        Args:
            content: Markdown content of homepage

        Returns:
            List of lesson info dictionaries
        """
        lessons: list[dict[str, Any]] = []
        seen_urls: set[str] = set()

        lesson_heading_pattern = re.compile(
            r'^###\s+\[([^\]]+)\]\((\S+?\.html)(?:\s+"[^"]*")?\)\s*$',
            re.MULTILINE,
        )
        level_link_pattern = re.compile(
            r'\[Level\s*([0-6])\]\((\S+?\.html)(?:\s+"[^"]*")?\)',
            re.IGNORECASE,
        )
        heading_matches = list(lesson_heading_pattern.finditer(content))

        for index, match in enumerate(heading_matches):
            title = match.group(1).strip()
            full_url = urljoin(f"{BASE_URL}/", match.group(2).strip())

            if full_url in seen_urls:
                continue

            date_match = re.search(r"/(\d{2})(\d{2})(\d{2})-[^/]+\.html$", full_url)
            if date_match:
                year, month, day = date_match.groups()
                date_str = f"{day}/{month}/{year}"
            else:
                date_str = ""

            title = re.sub(r"\s+", " ", title).strip()
            title = re.sub(r"^\s*-\s*", "", title)

            if len(title) < 10:
                continue

            level_urls: dict[str, str] = {}
            section_end = (
                heading_matches[index + 1].start()
                if index + 1 < len(heading_matches)
                else len(content)
            )
            section = content[match.end() : section_end]
            for level_match in level_link_pattern.finditer(section):
                level = level_match.group(1)
                level_url = urljoin(f"{BASE_URL}/", level_match.group(2).strip())
                suffixed_url = f"{full_url[:-5]}-{level}.html"
                if level_url not in {full_url, suffixed_url}:
                    continue
                level_urls[level] = level_url

            if not level_urls:
                continue

            seen_urls.add(full_url)

            lessons.append(
                {
                    "title": title,
                    "url": full_url,
                    "date": date_str,
                    "level_urls": level_urls,
                }
            )

        return lessons[:10]

    def _extract_reading_text(self, content: str) -> str:
        """Extract the main reading text from lesson markdown.

        Args:
            content: Markdown content

        Returns:
            Clean reading text
        """
        skip_patterns = [
            "copyright",
            "lesson on",
            "free worksheet",
            "online activit",
            "breaking news english",
            "esl lesson",
            "download",
            "subscribe",
            "twitter",
            "facebook",
            "instagram",
            "bluesky",
            "rss feed",
            "help this site",
            "buy my",
            "e-book",
            "see a sample",
            "listen a minute",
            "famous people",
            "esl discussion",
            "business english",
            "movie lesson",
            "holiday lesson",
            "complete this table",
            "spend one minute writing",
            "what do you know about",
            "how exciting are they",
            "share what you wrote",
            "change partners often",
            "to what degree are",
            "who would you give",
            "write down all of the different words",
            "different words you associate with",
            "put the words into different categories",
            "share your words with your partner",
            "speed reading",
            "5-speed listening",
            "grammar",
            "dictation",
            "spelling",
            "prepositions",
            "jumble",
            "no spaces",
            "gap fill",
            "missing words",
            "word pairs",
            "match",
            "and talk about them",
            "together, put the words",
            "litespeed",
            "not a web hosting",
            "has no control over content",
            "404 not found",
            "page not found",
            "error 404",
            "access denied",
            "forbidden",
            "server error",
            "403 forbidden",
            "access to this resource",
            "server is denied",
            "proudly powered",
            "litespeed web server",
        ]

        text_blocks = []
        seen_texts = set()

        lines = content.split("\n")
        for line in lines:
            line = line.strip()

            if line.startswith("#") or line.startswith("["):
                continue

            line = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", line)
            line = re.sub(r"[\*\_]{2,}", "", line)
            line = re.sub(r"\s+", " ", line).strip()

            line_without_tail = self._strip_bibliographic_tail(line)
            has_bibliographic_tail = line_without_tail != line
            line = line_without_tail

            if not line:
                if has_bibliographic_tail:
                    break
                continue

            if line.startswith("*"):
                if has_bibliographic_tail:
                    break
                continue

            if len(line) < 80:
                if has_bibliographic_tail:
                    text_blocks.append(line)
                    break
                continue

            text_lower = line.lower()
            if any(skip in text_lower for skip in skip_patterns):
                continue

            if text_lower.startswith("what do you") or text_lower.startswith("how "):
                continue
            if text_lower.startswith("spend one minute") or text_lower.startswith(
                "complete this"
            ):
                continue
            if text_lower.startswith("who would you") or text_lower.startswith(
                "to what degree"
            ):
                continue

            normalized = " ".join(line.split()[:10])
            if normalized in seen_texts:
                if has_bibliographic_tail:
                    break
                continue
            seen_texts.add(normalized)

            text_blocks.append(line)
            if has_bibliographic_tail:
                break

        if text_blocks:
            combined = " ".join(text_blocks[:8])
            return self._strip_bibliographic_tail(combined)

        return ""

    def _strip_bibliographic_tail(self, text: str) -> str:
        """Remove a bibliography entry and all following non-article content."""
        match = BIBLIOGRAPHIC_CITATION_PATTERN.search(text)
        if not match:
            return text
        return text[: match.start()].rstrip()

    def _extract_paragraphs(self, content: str) -> list[str]:
        """Extract paragraphs from the article content.

        Args:
            content: Markdown content

        Returns:
            List of paragraph strings
        """
        paragraphs = []

        blocks = re.split(r"\n\s*\n", content)

        for block in blocks:
            block = block.strip()

            if block.startswith("#") or block.startswith("["):
                continue

            text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", block)
            text = re.sub(r"[\*\_]{2,}", "", text)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) < 20:
                continue

            skip_patterns = [
                "try the same news story",
                "sources",
                "make sure you try",
                "paragraph",
                "level",
                "listen",
                "fill",
                "match",
                "litespeed",
                "not a web hosting",
                "has no control over content",
                "404 not found",
                "page not found",
                "error 404",
                "access denied",
                "forbidden",
                "server error",
                "403 forbidden",
                "access to this resource",
                "server is denied",
                "proudly powered",
                "litespeed web server",
                "copyright",
            ]
            text_without_tail = self._strip_bibliographic_tail(text)
            if text_without_tail != text:
                if text_without_tail:
                    paragraphs.append(text_without_tail)
                break

            text_lower = text.lower()
            if any(skip in text_lower for skip in skip_patterns):
                continue

            paragraphs.append(text)

        if not paragraphs:
            full_text = self._extract_reading_text(content)
            if full_text:
                paras = re.split(r"(?<=[.!?])\s+", full_text)
                paragraphs = [p.strip() for p in paras if len(p.strip()) > 20]

        return paragraphs

    def _clean_cached_lesson(self, lesson: Lesson) -> Lesson:
        """Remove bibliography tails from a lesson saved by an earlier version."""
        lesson.texts = {
            level: self._strip_bibliographic_tail(text)
            for level, text in lesson.texts.items()
        }

        cleaned_paragraphs: dict[str, list[str]] = {}
        for level, paragraphs in lesson.paragraphs.items():
            cleaned: list[str] = []
            for paragraph in paragraphs:
                paragraph_without_tail = self._strip_bibliographic_tail(paragraph)
                if paragraph_without_tail:
                    cleaned.append(paragraph_without_tail)
                if paragraph_without_tail != paragraph:
                    break
            cleaned_paragraphs[level] = cleaned
        lesson.paragraphs = cleaned_paragraphs

        return lesson

    def _get_level_from_url(self, url: str) -> str:
        """Extract level from URL.

        Args:
            url: Lesson URL

        Returns:
            Level string (0-6)
        """
        match = re.search(r"-(\d+)\.html$", url)
        if match:
            return match.group(1)

        return "3"

    def _fetch_level_content(
        self, base_info: dict, level: str
    ) -> tuple[str, list[str], str]:
        """Fetch content for a specific level.

        Args:
            base_info: Base lesson info dict
            level: Level to fetch

        Returns:
            Tuple of (text, paragraphs, description)
        """
        level_urls = base_info.get("level_urls")
        if isinstance(level_urls, dict):
            url = level_urls.get(level, base_info["url"])
        else:
            url = base_info["url"]

        try:
            content = self._fetch_url(url)
            text = self._extract_reading_text(content)
            paragraphs = self._extract_paragraphs(content)
            description = self._extract_description(content)

            if not text and paragraphs:
                text = " ".join(paragraphs)

            return text, paragraphs, description
        except NetworkError:
            return "", [], ""

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
            content = self._fetch_url(BASE_URL)
            lesson_infos = self._parse_homepage(content)

            logger.info(f"Found {len(lesson_infos)} lesson links")

            lessons = []
            for i, info in enumerate(lesson_infos[:6]):
                try:
                    logger.debug(
                        f"Fetching lesson {i + 1}/{min(6, len(lesson_infos))}: {info['title'][:40]}"
                    )

                    level_urls_raw = info.get("level_urls")
                    level_urls: dict[str, str]
                    if not isinstance(level_urls_raw, dict):
                        level_urls = {"3": info["url"]}
                    else:
                        level_urls = level_urls_raw
                    levels = sorted(level_urls.keys(), key=lambda x: int(x))

                    texts = {}
                    paragraphs = {}
                    description = ""

                    for level in levels:
                        text, paras, desc = self._fetch_level_content(info, level)
                        if text and len(text) >= 100:
                            texts[level] = text
                            paragraphs[level] = paras
                            if desc and not description:
                                description = desc

                    if texts:
                        # Filter level_urls to only include valid levels
                        valid_level_urls = {
                            k: v for k, v in level_urls.items() if k in texts
                        }
                        lesson = Lesson(
                            title=info["title"],
                            url=info["url"],
                            date=info["date"],
                            description=description,
                            levels=list(texts.keys()),
                            texts=texts,
                            level_urls=valid_level_urls,
                            paragraphs=paragraphs,
                        )
                        lessons.append(lesson)
                        self._cache[info["url"]] = lesson
                        logger.info(
                            f"Loaded: {lesson.title[:50]} ({len(texts)} levels: {levels})"
                        )

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

    def _extract_description(self, content: str) -> str:
        """Extract lesson description from markdown content."""
        match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        if match:
            title = match.group(1).strip()
            title = re.sub(r"Breaking News English.*", "", title, flags=re.IGNORECASE)
            return title.strip()

        lines = content.split("\n")
        for line in lines[:5]:
            line = line.strip()
            if line and not line.startswith("#") and len(line) > 20:
                line = re.sub(r"Breaking News English.*", "", line, flags=re.IGNORECASE)
                return line.strip()

        return ""

    def _save_cache(self, lessons: list[Lesson]) -> bool:
        """Save lessons to cache."""
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            data = {
                "timestamp": datetime.now().isoformat(),
                "lessons": [lesson.to_dict() for lesson in lessons],
            }

            temp_file = self._index_file.with_suffix(".tmp")
            with open(temp_file, "w", encoding="utf-8") as f:
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
            with open(self._index_file, "r", encoding="utf-8") as f:
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
                lesson = self._clean_cached_lesson(Lesson.from_dict(item))
                lessons.append(lesson)
                self._cache[lesson.url] = lesson

            return lessons

        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []

    def get_cached_lessons(self) -> list[Lesson]:
        """Get all cached lessons."""
        return self._load_cache()

    def is_cache_expired(self) -> bool:
        """Check if the cache exists but is older than 24 hours.

        Returns:
            True if cache file exists and is expired, False otherwise.
        """
        if not self._index_file.exists():
            return False
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            timestamp = data.get("timestamp", "")
            if not timestamp:
                return False
            cache_time = datetime.fromisoformat(timestamp)
            age_hours = (datetime.now() - cache_time).total_seconds() / 3600
            return age_hours > 24
        except Exception:
            return False

    def get_stale_cached_lessons(self) -> list[Lesson]:
        """Load cached lessons regardless of age (bypasses 24h expiry check).

        Returns:
            List of cached lessons, or empty list if no cache file exists.
        """
        if not self._index_file.exists():
            return []
        try:
            with open(self._index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            lessons = []
            for item in data.get("lessons", []):
                lesson = self._clean_cached_lesson(Lesson.from_dict(item))
                lessons.append(lesson)
                self._cache[lesson.url] = lesson
            return lessons
        except Exception as e:
            logger.error(f"Failed to load stale cache: {e}")
            return []

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
            self._preload_complete = False
            self._preload_succeeded = False
            self._preload_future = self._executor.submit(self._preload_task)
            logger.debug("Started async lesson preload")

    def _preload_task(self) -> list[Lesson]:
        """Background task to preload lessons."""
        try:
            lessons = self.fetch_lessons(use_cache=True)
            self._preload_complete = True
            self._preload_succeeded = len(lessons) > 0
            return lessons
        except Exception as e:
            logger.error(f"Preload failed: {e}")
            self._preload_complete = True
            self._preload_succeeded = False
            return []

    def is_preloading(self) -> bool:
        """Check if preload is still running."""
        if self._preload_future is None:
            return False
        return not self._preload_complete

    def preload_succeeded(self) -> bool:
        """Check if preload completed successfully with lessons."""
        return self._preload_complete and self._preload_succeeded

    def get_preloaded_lessons(self) -> list[Lesson]:
        """Get lessons, waiting for preload if necessary."""
        if self._preload_future is not None:
            try:
                result = self._preload_future.result(timeout=30)
                return cast(list[Lesson], result)
            except Exception:
                pass
        return self._load_cache()

    def shutdown(self) -> None:
        """Release the preload executor without blocking exit.

        The executor's worker thread is non-daemon, so without this the
        interpreter joins it at exit and hangs while a background download is
        in flight. ``cancel_futures`` drops any not-yet-started work; a request
        already running still finishes, but it is bounded by the fetch timeout.
        """
        self._executor.shutdown(wait=False, cancel_futures=True)
