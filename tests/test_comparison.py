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


class TestPhoneticMatching:
    """Tests for phonetic matching."""

    def test_phonetic_code_basic(self):
        """Test basic phonetic code generation."""
        comparator = TextComparator()
        # Palabras que suenan diferente deberían tener códigos diferentes
        code_cat = comparator.get_phonetic_code("cat")
        code_dog = comparator.get_phonetic_code("dog")
        assert code_cat != code_dog

    def test_phonetic_code_similar_sounds(self):
        """Test that similar sounding words have same or similar codes."""
        comparator = TextComparator()
        # cat y cut suenan similar
        code_cat = comparator.get_phonetic_code("cat")
        code_cut = comparator.get_phonetic_code("cut")
        assert code_cat == code_cut

    def test_phonetic_match_cat_cut(self):
        """Test phonetic matching for cat/cut."""
        comparator = TextComparator()
        assert comparator.is_phonetic_match("cat", "cut") is True

    def test_phonetic_match_hello_hi(self):
        """Test phonetic matching for hello/hi."""
        comparator = TextComparator()
        assert comparator.is_phonetic_match("hello", "hi") is True

    def test_phonetic_match_case_insensitive(self):
        """Test phonetic matching is case insensitive."""
        comparator = TextComparator()
        assert comparator.is_phonetic_match("CAT", "cut") is True
        assert comparator.is_phonetic_match("cat", "CUT") is True

    def test_exact_match_takes_precedence(self):
        """Test that exact matches work regardless of phonetic."""
        comparator = TextComparator()
        assert comparator.is_phonetic_match("hello", "hello") is True


class TestFlexibleComparison:
    """Tests for flexible window comparison."""

    def test_flexible_identical_texts(self):
        """Test flexible comparison with identical texts."""
        comparator = TextComparator()
        result = comparator.compare_flexible("hello world", "hello world")
        assert result.accuracy == 1.0
        assert result.correct_count == 2

    def test_flexible_word_duplication(self):
        """Test flexible comparison handles word duplication."""
        comparator = TextComparator()
        # Usuario dice "the the" en vez de "the"
        result = comparator.compare_flexible("the cat sat", "the the cat sat")
        # Debería encontrar todas las palabras
        assert result.accuracy == 1.0
        assert result.correct_count == 3

    def test_flexible_word_offset(self):
        """Test flexible comparison handles word offset."""
        comparator = TextComparator()
        # Palabra desplazada por una palabra extra
        result = comparator.compare_flexible(
            "hello world test",
            "hello there world test",
            window_size=2
        )
        # "world" y "test" deberían encontrarse
        assert result.accuracy == 1.0

    def test_flexible_with_phonetic(self):
        """Test flexible comparison with phonetic matching."""
        comparator = TextComparator()
        result = comparator.compare_flexible(
            "hello world",
            "hi world",
            window_size=2,
            use_phonetic=True
        )
        # "hello" y "hi" deberían coincidir fonéticamente
        assert result.accuracy == 1.0

    def test_flexible_missing_word(self):
        """Test flexible comparison detects missing words."""
        comparator = TextComparator()
        result = comparator.compare_flexible("hello world", "hello")
        assert result.accuracy < 1.0
        assert "world" in result.missing_words


class TestPerWordComparison:
    """Tests for per-word comparison (no alignment)."""

    def test_per_word_identical(self):
        """Test per-word comparison with identical texts."""
        comparator = TextComparator()
        result = comparator.compare_per_word("hello world", "hello world")
        assert result.accuracy == 1.0

    def test_per_word_different_order(self):
        """Test per-word comparison with different word order."""
        comparator = TextComparator()
        # Orden diferente
        result = comparator.compare_per_word(
            "the cat sat on the mat",
            "mat sat cat the on the"
        )
        # Todas las palabras están presentes
        assert result.accuracy == 1.0
        assert result.correct_count == 6

    def test_per_word_partial_match(self):
        """Test per-word comparison with partial match."""
        comparator = TextComparator()
        result = comparator.compare_per_word(
            "hello world",
            "hello"
        )
        assert result.accuracy == 0.5
        assert result.correct_count == 1
        assert "world" in result.missing_words

    def test_per_word_with_phonetic(self):
        """Test per-word comparison with phonetic matching."""
        comparator = TextComparator()
        result = comparator.compare_per_word(
            "the cat sat",
            "the cut sat",
            use_phonetic=True
        )
        # "cat" y "cut" deberían coincidir fonéticamente
        assert result.accuracy == 1.0

    def test_per_word_extra_words(self):
        """Test per-word comparison detects extra words."""
        comparator = TextComparator()
        result = comparator.compare_per_word(
            "hello world",
            "hello world extra"
        )
        assert "extra" in result.extra_words
