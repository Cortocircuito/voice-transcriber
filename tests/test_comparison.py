"""Tests for text comparison module."""

import pytest

from voice_to_text.comparison import (
    TextComparator,
    ComparisonResult,
    WordMatch,
)


class TestTextComparator:
    """Tests for TextComparator class."""

    def test_normalize_word_basic(self):
        """Test basic word normalization."""
        comparator = TextComparator()
        assert comparator.normalize_word("Hello") == "hello"
        assert comparator.normalize_word("WORLD") == "world"

    def test_normalize_word_punctuation(self):
        """Test word normalization removes punctuation."""
        comparator = TextComparator()
        assert comparator.normalize_word("hello,") == "hello"
        assert comparator.normalize_word("world.") == "world"
        assert comparator.normalize_word("'test'") == "test"

    def test_normalize_word_contractions(self):
        """Test contraction expansion in normalization."""
        comparator = TextComparator()
        assert comparator.normalize_word("can't") == "cant"
        assert comparator.normalize_word("won't") == "wont"
        assert comparator.normalize_word("i'm") == "im"

    def test_normalize_text_basic(self):
        """Test text normalization."""
        comparator = TextComparator()
        result = comparator.normalize_text("Hello world")
        assert result == ["hello", "world"]

    def test_normalize_text_contractions(self):
        """Test text normalization with contractions."""
        comparator = TextComparator()
        result = comparator.normalize_text("I can't go")
        assert result == ["i", "can", "not", "go"]

    def test_normalize_text_punctuation(self):
        """Test text normalization removes punctuation."""
        comparator = TextComparator()
        result = comparator.normalize_text("Hello, world!")
        assert result == ["hello", "world"]

    def test_get_original_words_basic(self):
        """Test extracting original words."""
        comparator = TextComparator()
        words = comparator.get_original_words("Hello world")
        assert words == ["Hello", "world"]

    def test_get_original_words_punctuation(self):
        """Test extracting words with punctuation."""
        comparator = TextComparator()
        words = comparator.get_original_words("Hello, world!")
        assert words == ["Hello", "world"]

    def test_get_original_words_apostrophes(self):
        """Test extracting words with apostrophes."""
        comparator = TextComparator()
        words = comparator.get_original_words("It's a test")
        assert words == ["It's", "a", "test"]

    def test_compare_identical_texts(self):
        """Test comparing identical texts."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello world")

        assert result.accuracy == 1.0
        assert result.correct_count == 2
        assert result.total_count == 2
        assert len(result.errors) == 0

    def test_compare_completely_different(self):
        """Test comparing completely different texts."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "foo bar")

        assert result.accuracy == 0.0
        assert result.correct_count == 0
        assert result.total_count == 2

    def test_compare_partial_match(self):
        """Test comparing partially matching texts."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello there")

        assert result.accuracy > 0.0
        assert result.correct_count == 1
        assert result.total_count == 2

    def test_compare_missing_words(self):
        """Test comparing with missing words."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello")

        assert "world" in result.missing_words

    def test_compare_extra_words(self):
        """Test comparing with extra words."""
        comparator = TextComparator()
        result = comparator.compare("hello", "hello world foo")

        assert result.trans_error_indices is not None

    def test_compare_contractions(self):
        """Test comparing texts with contractions."""
        comparator = TextComparator()
        result = comparator.compare("I can't go", "i can not go")

        assert result.accuracy == 1.0

    def test_compare_case_insensitive(self):
        """Test that comparison is case insensitive."""
        comparator = TextComparator()
        result = comparator.compare("HELLO WORLD", "hello world")

        assert result.accuracy == 1.0

    def test_compare_empty_original(self):
        """Test comparing with empty original text."""
        comparator = TextComparator()
        result = comparator.compare("", "hello world")

        assert result.total_count == 0
        assert result.accuracy == 0.0

    def test_compare_empty_transcribed(self):
        """Test comparing with empty transcribed text."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "")

        assert result.total_count == 2
        assert result.accuracy == 0.0

    def test_compare_empty_both(self):
        """Test comparing with both texts empty."""
        comparator = TextComparator()
        result = comparator.compare("", "")

        assert result.total_count == 0

    def test_generate_display_no_errors(self):
        """Test display generation with no errors."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello world")
        display = comparator.generate_display(result)

        assert isinstance(display, str)

    def test_generate_display_with_errors(self):
        """Test display generation with errors."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello")
        display = comparator.generate_display(result)

        assert "Mispronounced" in display or "missing" in display.lower()

    def test_generate_rich_display(self):
        """Test Rich display generation."""
        comparator = TextComparator()
        result = comparator.compare("hello world", "hello world")
        segments = comparator.generate_rich_display(result)

        assert isinstance(segments, list)
        assert len(segments) > 0
        assert "text" in segments[0]
        assert "style" in segments[0]


class TestComparisonResult:
    """Tests for ComparisonResult dataclass."""

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ComparisonResult(
            original_words=["hello", "world"],
            transcribed_words=["hello", "world"],
            accuracy=1.0,
            correct_count=2,
            total_count=2,
            errors=[],
            missing_words=[],
            extra_words=[],
        )

        d = result.to_dict()

        assert d["accuracy"] == 1.0
        assert d["correct_count"] == 2
        assert d["total_count"] == 2


class TestWordMatch:
    """Tests for WordMatch dataclass."""

    def test_word_match_creation(self):
        """Test WordMatch creation."""
        match = WordMatch(
            original="hello",
            transcribed="hello",
            is_match=True,
            index=0,
        )

        assert match.original == "hello"
        assert match.is_match is True
        assert match.index == 0
