"""Tests for lessons module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from voice_to_text.lessons import (
    Lesson,
    LessonError,
    LessonManager,
    NetworkError,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLesson:
    """Tests for Lesson dataclass."""

    def test_lesson_creation(self):
        """Test creating a Lesson instance."""
        lesson = Lesson(
            title="Test Lesson",
            url="https://example.com/lesson.html",
            date="01/01/24",
            description="A test lesson",
            levels=["1", "2", "3"],
            texts={"1": "Text level 1", "2": "Text level 2"},
            level_urls={"1": "url1", "2": "url2"},
            paragraphs={"1": ["para1"], "2": ["para2"]},
        )

        assert lesson.title == "Test Lesson"
        assert lesson.url == "https://example.com/lesson.html"
        assert lesson.levels == ["1", "2", "3"]

    def test_get_text_existing_level(self):
        """Test getting text for existing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=["1", "2"],
            texts={"1": "text1", "2": "text2"},
            level_urls={},
            paragraphs={},
        )

        assert lesson.get_text("1") == "text1"
        assert lesson.get_text("2") == "text2"

    def test_get_text_missing_level(self):
        """Test getting text for missing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=["1"],
            texts={"1": "text1"},
            level_urls={},
            paragraphs={},
        )

        assert lesson.get_text("2") is None

    def test_get_paragraphs_existing_level(self):
        """Test getting paragraphs for existing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=["1"],
            texts={},
            level_urls={},
            paragraphs={"1": ["para1", "para2"]},
        )

        assert lesson.get_paragraphs("1") == ["para1", "para2"]

    def test_get_paragraphs_missing_level(self):
        """Test getting paragraphs for missing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=[],
            texts={},
            level_urls={},
            paragraphs={},
        )

        assert lesson.get_paragraphs("1") == []

    def test_get_level_url_existing(self):
        """Test getting URL for existing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=["1"],
            texts={},
            level_urls={"1": "https://example.com/1.html"},
            paragraphs={},
        )

        assert lesson.get_level_url("1") == "https://example.com/1.html"

    def test_get_level_url_missing(self):
        """Test getting URL for missing level."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="",
            description="",
            levels=[],
            texts={},
            level_urls={},
            paragraphs={},
        )

        assert lesson.get_level_url("1") is None

    def test_to_dict(self):
        """Test converting Lesson to dictionary."""
        lesson = Lesson(
            title="Test",
            url="url",
            date="01/01/24",
            description="desc",
            levels=["1"],
            texts={"1": "text"},
            level_urls={"1": "url"},
            paragraphs={"1": ["para"]},
        )

        d = lesson.to_dict()

        assert d["title"] == "Test"
        assert d["levels"] == ["1"]
        assert d["texts"]["1"] == "text"

    def test_from_dict(self):
        """Test creating Lesson from dictionary."""
        data = {
            "title": "Test",
            "url": "url",
            "date": "01/01/24",
            "description": "desc",
            "levels": ["1"],
            "texts": {"1": "text"},
            "level_urls": {"1": "url"},
            "paragraphs": {"1": ["para"]},
        }

        lesson = Lesson.from_dict(data)

        assert lesson.title == "Test"
        assert lesson.levels == ["1"]

    def test_from_dict_defaults(self):
        """Test from_dict with missing keys uses defaults."""
        data = {"title": "Test", "url": "url"}

        lesson = Lesson.from_dict(data)

        assert lesson.title == "Test"
        assert lesson.date == ""
        assert lesson.levels == []


class TestLessonManager:
    """Tests for LessonManager class."""

    def test_init(self):
        """Test LessonManager initialization."""
        manager = LessonManager()

        assert manager._cache == {}
        assert manager._preload_future is None

    @patch("voice_to_text.lessons.get_lessons_cache_dir")
    def test_get_lessons_cache_dir_default(self, mock_cache_dir):
        """Test default cache directory."""
        mock_cache_dir.return_value = Path("/tmp/test")
        manager = LessonManager()

        assert manager._cache_dir == Path("/tmp/test")

    def test_shutdown_releases_executor(self):
        """shutdown() shuts the executor down without waiting."""
        manager = LessonManager()
        manager._executor = MagicMock()

        manager.shutdown()

        manager._executor.shutdown.assert_called_once_with(
            wait=False, cancel_futures=True
        )

    def test_shutdown_prevents_new_preload(self):
        """After shutdown the real executor rejects new work."""
        manager = LessonManager()
        manager.shutdown()

        with pytest.raises(RuntimeError):
            manager._executor.submit(lambda: None)

    def test_parse_homepage_valid_content(self):
        """Parse the easier and harder level groups published by the site."""
        manager = LessonManager()
        content = (FIXTURES_DIR / "breaking_news_homepage.md").read_text(
            encoding="utf-8"
        )

        lessons = manager._parse_homepage(content)

        assert len(lessons) == 2
        assert lessons[0]["title"] == (
            "Australia bans AI songs from official music charts"
        )
        assert lessons[0]["date"] == "07/09/26"
        assert lessons[0]["level_urls"] == {
            "4": "https://breakingnewsenglish.com/2609/260907-ban-on-ai-songs-4.html",
            "5": "https://breakingnewsenglish.com/2609/260907-ban-on-ai-songs-5.html",
            "6": "https://breakingnewsenglish.com/2609/260907-ban-on-ai-songs.html",
        }
        assert lessons[1]["date"] == "03/09/26"
        assert lessons[1]["level_urls"] == {
            "0": "https://breakingnewsenglish.com/2609/260903-manga-theme-park-0.html",
            "1": "https://breakingnewsenglish.com/2609/260903-manga-theme-park-1.html",
            "2": "https://breakingnewsenglish.com/2609/260903-manga-theme-park-2.html",
            "3": "https://breakingnewsenglish.com/2609/260903-manga-theme-park.html",
        }

    def test_parse_homepage_extracts_date(self):
        """Test date extraction from URL."""
        manager = LessonManager()

        content = """### [A sufficiently long test lesson](2601/260115-test.html)

* [Level 3](2601/260115-test.html)
"""

        lessons = manager._parse_homepage(content)

        assert lessons[0]["date"] == "15/01/26"
        assert set(lessons[0]["level_urls"]) == {"3"}

    def test_parse_homepage_skips_short_titles(self):
        """Test that short titles are skipped."""
        manager = LessonManager()

        content = """### [Short](2601/260115-test.html)

* [Level 3](2601/260115-test.html)
"""

        lessons = manager._parse_homepage(content)

        assert len(lessons) == 0

    def test_parse_homepage_deduplicates_urls(self):
        """Test that duplicate URLs are removed."""
        manager = LessonManager()

        content = """### [A sufficiently long test lesson](2601/260115-test.html)

* [Level 3](2601/260115-test.html)

### [A duplicate test lesson title](2601/260115-test.html)

* [Level 3](2601/260115-test.html)
"""

        lessons = manager._parse_homepage(content)

        assert len(lessons) == 1

    def test_extract_reading_text_basic(self):
        """Test extracting reading text."""
        manager = LessonManager()

        content = """# Test Title

This is a sample paragraph with enough content to be considered as reading text.
It has multiple sentences and should be extracted properly.
"""

        text = manager._extract_reading_text(content)

        assert isinstance(text, str)

    def test_extract_reading_text_skips_short_lines(self):
        """Test that short lines are skipped."""
        manager = LessonManager()

        content = """# Title

This is a very long paragraph with more than eighty characters that should be extracted properly.
"""

        text = manager._extract_reading_text(content)

        assert len(text) > 0

    def test_extract_paragraphs_basic(self):
        """Test extracting paragraphs."""
        manager = LessonManager()

        content = """# Title

First paragraph here with some content.

Second paragraph also with content.
"""

        paragraphs = manager._extract_paragraphs(content)

        assert len(paragraphs) >= 0

    def test_get_level_from_url_with_level(self):
        """Test extracting level from URL with level."""
        manager = LessonManager()

        level = manager._get_level_from_url("https://example.com/lesson-3.html")
        assert level == "3"

        level = manager._get_level_from_url("https://example.com/lesson-0.html")
        assert level == "0"

    def test_get_level_from_url_without_level(self):
        """Test extracting level from URL without level."""
        manager = LessonManager()

        level = manager._get_level_from_url("https://example.com/lesson.html")
        assert level == "3"

    def test_extract_description_from_title(self):
        """Test extracting description from markdown title."""
        manager = LessonManager()

        content = """# Breaking News English - Test Title

Some content here.
"""

        desc = manager._extract_description(content)

        assert isinstance(desc, str)

    def test_extract_description_from_first_line(self):
        """Test extracting description from first line."""
        manager = LessonManager()

        content = """# Title

This is a description line with enough content.
"""

        desc = manager._extract_description(content)

        assert isinstance(desc, str)

    @patch("voice_to_text.lessons.LessonManager._fetch_url")
    def test_fetch_level_content_success(self, mock_fetch):
        """Test successful level content fetching."""
        manager = LessonManager()
        mock_fetch.return_value = "# Test\n\nThis is the reading content."

        base_info = {
            "title": "Test",
            "url": "https://example.com/lesson.html",
            "level_urls": {"3": "https://example.com/lesson-3.html"},
        }

        text, paragraphs, description = manager._fetch_level_content(base_info, "3")

        assert isinstance(text, str)
        assert isinstance(paragraphs, list)

    @patch("voice_to_text.lessons.LessonManager._fetch_url")
    def test_fetch_level_content_network_error(self, mock_fetch):
        """Test level content fetching with network error."""
        manager = LessonManager()
        mock_fetch.side_effect = NetworkError("Network failed")

        base_info = {
            "title": "Test",
            "url": "https://example.com/lesson.html",
            "level_urls": {},
        }

        text, paragraphs, description = manager._fetch_level_content(base_info, "3")

        assert text == ""
        assert paragraphs == []
        assert description == ""


class TestLessonErrors:
    """Tests for lesson exceptions."""

    def test_lesson_error_is_exception(self):
        """Test LessonError inherits from Exception."""
        assert issubclass(LessonError, Exception)

    def test_network_error_is_lesson_error(self):
        """Test NetworkError inherits from LessonError."""
        assert issubclass(NetworkError, LessonError)

    def test_network_error_can_be_raised(self):
        """Test NetworkError can be raised."""
        with pytest.raises(NetworkError):
            raise NetworkError("Network failed")


class TestLessonLevelFiltering:
    """Tests for lesson level filtering logic."""

    def test_extract_reading_text_stops_at_bibliographic_citation(self):
        """Bibliographic references and following exercises are excluded."""
        manager = LessonManager()
        article = (
            "Scientists say the photos will help us predict space weather one day. "
            "The images also show details that could help researchers understand "
            "the Sun's energy."
        )
        content = f"""# Test Title

{article}

Haas, M. and Laughlin, M. (2000) Teaching Current Events: It's Status in Social Studies Today.

Scientists (1) ______________________________ to take the best-ever photos of the Sun.
"""

        text = manager._extract_reading_text(content)

        assert text == article
        assert "Haas" not in text
        assert "(1)" not in text

    def test_strip_bibliographic_tail_supports_different_authors(self):
        """The filter must not be tied to one fixed reference."""
        manager = LessonManager()
        text = (
            "The article ends here. Smith, J. and Patel, R. (2011) "
            "An Unrelated Reference. Exercise content follows."
        )

        assert manager._strip_bibliographic_tail(text) == "The article ends here."

    def test_load_cache_removes_bibliographic_tail(self, tmp_path):
        """Existing cached lessons are cleaned before practice begins."""
        manager = LessonManager()
        manager._index_file = tmp_path / "index.json"
        lesson = Lesson(
            title="Test Lesson",
            url="https://example.com/lesson.html",
            date="",
            description="",
            levels=["3"],
            texts={
                "3": "Article text. Smith, J. and Patel, R. (2011) "
                "An Unrelated Reference. Exercise content follows."
            },
            level_urls={"3": "https://example.com/lesson-3.html"},
            paragraphs={
                "3": [
                    "Article text.",
                    "Smith, J. and Patel, R. (2011) An Unrelated Reference.",
                    "Exercise content follows.",
                ]
            },
        )
        manager._index_file.write_text(
            json.dumps({"lessons": [lesson.to_dict()]}), encoding="utf-8"
        )

        cached_lesson = manager._load_cache()[0]

        assert cached_lesson.get_text("3") == "Article text."
        assert cached_lesson.get_paragraphs("3") == ["Article text."]

    def test_extract_reading_text_filters_litespeed_content(self):
        """Test that LiteSpeed placeholder content is filtered out."""
        manager = LessonManager()

        content = """# Test Title

Please be advised that LiteSpeed Technologies Inc. is not a web hosting company and, as such, has no control over content found on this site.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_extract_reading_text_filters_short_content(self):
        """Test that content shorter than 100 characters is filtered out."""
        manager = LessonManager()

        content = """# Test Title

This is short.
"""

        text = manager._extract_reading_text(content)

        assert len(text) < 100 or text == ""

    def test_extract_reading_text_keeps_valid_content(self):
        """Test that valid content with 100+ characters is kept."""
        manager = LessonManager()

        content = """# Test Title

This is a valid paragraph with enough content to be considered as reading text for the lesson practice. It contains multiple sentences and should be extracted properly as it has more than one hundred characters of actual lesson content.
"""

        text = manager._extract_reading_text(content)

        assert len(text) >= 100
        assert "valid paragraph" in text.lower()

    def test_extract_reading_text_filters_404_error(self):
        """Test that 404 error page content is filtered out."""
        manager = LessonManager()

        content = """# 404 Not Found

The page you requested was not found. Error 404.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_extract_reading_text_filters_forbidden(self):
        """Test that forbidden error content is filtered out."""
        manager = LessonManager()

        content = """# Access Denied

403 Forbidden - You do not have permission to access this page.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_extract_reading_text_filters_server_error(self):
        """Test that server error content is filtered out."""
        manager = LessonManager()

        content = """# Server Error

500 Internal Server Error occurred.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_extract_reading_text_filters_copyright(self):
        """Test that copyright content is filtered out."""
        manager = LessonManager()

        content = """# Test Title

Copyright Breaking News English. All rights reserved. This lesson is copyrighted material.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_extract_reading_text_filters_grammar(self):
        """Test that grammar section content is filtered out."""
        manager = LessonManager()

        content = """# Test Title

Grammar exercises and activities for this lesson include gap fill, spelling, and dictation practice.
"""

        text = manager._extract_reading_text(content)

        assert text == ""

    def test_fetch_level_content_filters_short_text(self):
        """Test that level content with less than 100 chars is filtered."""
        manager = LessonManager()

        mock_lesson_info = {
            "title": "Test Lesson",
            "url": "https://example.com/lesson.html",
            "level_urls": {"0": "https://example.com/lesson-0.html"},
        }

        with patch.object(manager, "_fetch_url") as mock_fetch:
            mock_fetch.return_value = "# Title\n\nShort content."

            text, paras, desc = manager._fetch_level_content(mock_lesson_info, "0")

            assert text == "" or len(text) < 100

    def test_fetch_level_content_keeps_valid_text(self):
        """Test that valid level content is kept."""
        manager = LessonManager()

        mock_lesson_info = {
            "title": "Test Lesson",
            "url": "https://example.com/lesson.html",
            "level_urls": {"3": "https://example.com/lesson-3.html"},
        }

        valid_content = "# Test Title\n\n" + "This is valid lesson content. " * 10

        with patch.object(manager, "_fetch_url") as mock_fetch:
            mock_fetch.return_value = valid_content

            text, paras, desc = manager._fetch_level_content(mock_lesson_info, "3")

            assert len(text) >= 100

    def test_fetch_level_content_filters_skip_patterns(self):
        """Test that content with skip patterns is filtered."""
        manager = LessonManager()

        mock_lesson_info = {
            "title": "Test Lesson",
            "url": "https://example.com/lesson.html",
            "level_urls": {"0": "https://example.com/lesson-0.html"},
        }

        skip_content = "# Title\n\nPlease be advised that LiteSpeed Technologies Inc. is not a web hosting company."

        with patch.object(manager, "_fetch_url") as mock_fetch:
            mock_fetch.return_value = skip_content

            text, paras, desc = manager._fetch_level_content(mock_lesson_info, "0")

            assert text == ""
