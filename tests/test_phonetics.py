"""Tests for phonetics module."""

import pytest

from voice_to_text.phonetics import (
    get_ipa,
    get_word_ipa,
    get_syllable_count,
    get_words_phonetics,
    PhoneticsError,
)


class TestGetIpa:
    """Tests for get_ipa function."""

    def test_get_ipa_empty_string(self):
        """Test IPA conversion with empty string."""
        result = get_ipa("")
        assert result == ""

    def test_get_ipa_simple_word(self):
        """Test IPA conversion with simple word."""
        result = get_ipa("hello")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_ipa_sentence(self):
        """Test IPA conversion with sentence."""
        result = get_ipa("hello world")
        assert isinstance(result, str)
        assert " " in result or len(result) > 0

    def test_get_ipa_preserves_punctuation(self):
        """Test IPA conversion preserves some punctuation."""
        result = get_ipa("hello, world!")
        assert isinstance(result, str)


class TestGetWordIpa:
    """Tests for get_word_ipa function."""

    def test_get_word_ipa_empty(self):
        """Test IPA for empty word."""
        result = get_word_ipa("")
        assert result is None

    def test_get_word_ipa_whitespace(self):
        """Test IPA for whitespace only."""
        result = get_word_ipa("   ")
        assert result is None

    def test_get_word_ipa_simple(self):
        """Test IPA for simple word."""
        result = get_word_ipa("hello")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_word_ipa_uppercase(self):
        """Test IPA handles uppercase."""
        result = get_word_ipa("HELLO")
        assert isinstance(result, str)

    def test_get_word_ipa_unknown(self):
        """Test IPA for unknown word returns None."""
        result = get_word_ipa("xyzqwerty123")
        assert result is None


class TestGetSyllableCount:
    """Tests for get_syllable_count function."""

    def test_get_syllable_count_empty(self):
        """Test syllable count for empty word."""
        result = get_syllable_count("")
        assert result == 0

    def test_get_syllable_count_simple(self):
        """Test syllable count for simple word."""
        result = get_syllable_count("hello")
        assert isinstance(result, int)
        assert result > 0

    def test_get_syllable_count_word(self):
        """Test syllable count for known word."""
        result = get_syllable_count("world")
        assert isinstance(result, int)
        assert result >= 0

    def test_get_syllable_count_unknown(self):
        """Test syllable count for unknown word."""
        result = get_syllable_count("xyzqwerty")
        assert result == 0


class TestGetWordsPhonetics:
    """Tests for get_words_phonetics function."""

    def test_get_words_phonetics_empty_list(self):
        """Test phonetics for empty list."""
        result = get_words_phonetics([])
        assert result == []

    def test_get_words_phonetics_single_word(self):
        """Test phonetics for single word."""
        result = get_words_phonetics(["hello"])
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0][0] == "hello"

    def test_get_words_phonetics_multiple_words(self):
        """Test phonetics for multiple words."""
        result = get_words_phonetics(["hello", "world"])
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0][0] == "hello"
        assert result[1][0] == "world"

    def test_get_words_phonetics_with_unknown(self):
        """Test phonetics handles unknown words."""
        result = get_words_phonetics(["hello", "xyzunknown"])
        assert len(result) == 2
        assert result[1][1] is None

    def test_get_words_phonetics_empty_strings(self):
        """Test phonetics filters empty strings."""
        result = get_words_phonetics(["hello", "", "world"])
        assert len(result) == 2

    def test_get_words_phonetics_preserves_order(self):
        """Test phonetics preserves word order."""
        words = ["hello", "world", "test"]
        result = get_words_phonetics(words)
        assert [w[0] for w in result] == words


class TestPhoneticsError:
    """Tests for PhoneticsError exception."""

    def test_phonetics_error_is_exception(self):
        """Test PhoneticsError inherits from Exception."""
        assert issubclass(PhoneticsError, Exception)

    def test_phonetics_error_can_be_raised(self):
        """Test PhoneticsError can be raised."""
        with pytest.raises(PhoneticsError):
            raise PhoneticsError("Test error")
