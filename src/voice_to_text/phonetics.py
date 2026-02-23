"""Phonetic transcription module using IPA."""

import logging
from typing import Optional

import eng_to_ipa as ipa

logger = logging.getLogger(__name__)


class PhoneticsError(Exception):
    """Base exception for phonetics errors."""
    pass


def get_ipa(text: str) -> str:
    """Convert text to International Phonetic Alphabet (IPA).

    Args:
        text: English text to convert

    Returns:
        IPA transcription of the text. Unknown words are marked with *.
    """
    if not text:
        return ""

    result = ipa.convert(text)
    return result


def get_word_ipa(word: str) -> Optional[str]:
    """Get IPA transcription for a single word.

    Args:
        word: Single English word

    Returns:
        IPA transcription or None if word cannot be transcribed
    """
    if not word:
        return None

    word = word.strip()
    if not word:
        return None

    result = ipa.convert(word)

    if "*" in result:
        return None

    return result


def get_syllable_count(word: str) -> int:
    """Get the number of syllables in a word.

    Args:
        word: English word

    Returns:
        Number of syllables (0 if word not found)
    """
    if not word:
        return 0

    try:
        syllables = ipa.syllable_count(word)
        return syllables if syllables else 0
    except Exception:
        return 0


def get_words_phonetics(words: list[str]) -> list[tuple[str, Optional[str]]]:
    """Get IPA phonetics for a list of words, preserving order.

    Args:
        words: List of words to get phonetics for

    Returns:
        List of tuples (word, ipa) where ipa is None if not found in dictionary
    """
    result: list[tuple[str, Optional[str]]] = []

    for word in words:
        word_clean = word.strip()
        if not word_clean:
            continue

        word_lower = word_clean.lower()
        ipa_result = ipa.convert(word_lower)

        if "*" in ipa_result:
            result.append((word_clean, None))
        else:
            result.append((word_clean, ipa_result))

    return result
