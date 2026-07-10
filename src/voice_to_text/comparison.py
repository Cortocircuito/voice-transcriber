"""Text comparison for pronunciation analysis."""

import difflib
import re
from dataclasses import dataclass, field
from typing import Any

from .constants import COMPARISON_WINDOW_SIZE, DEFAULT_COMPARISON_METHOD

CONTRACTIONS = {
    "i'm": "i am",
    "i've": "i have",
    "i'll": "i will",
    "i'd": "i would",
    "you're": "you are",
    "you've": "you have",
    "you'll": "you will",
    "you'd": "you would",
    "he's": "he is",
    "he'll": "he will",
    "he'd": "he would",
    "she's": "she is",
    "she'll": "she will",
    "she'd": "she would",
    "it's": "it is",
    "it'll": "it will",
    "we're": "we are",
    "we've": "we have",
    "we'll": "we will",
    "we'd": "we would",
    "they're": "they are",
    "they've": "they have",
    "they'll": "they will",
    "they'd": "they would",
    "that's": "that is",
    "that'll": "that will",
    "who's": "who is",
    "who'll": "who will",
    "what's": "what is",
    "what'll": "what will",
    "where's": "where is",
    "where'll": "where will",
    "when's": "when is",
    "when'll": "when will",
    "why's": "why is",
    "why'll": "why will",
    "how's": "how is",
    "how'll": "how will",
    "isn't": "is not",
    "aren't": "are not",
    "wasn't": "was not",
    "weren't": "were not",
    "hasn't": "has not",
    "haven't": "have not",
    "hadn't": "had not",
    "doesn't": "does not",
    "don't": "do not",
    "didn't": "did not",
    "won't": "will not",
    "wouldn't": "would not",
    "shan't": "shall not",
    "shouldn't": "should not",
    "can't": "can not",
    "cannot": "can not",
    "couldn't": "could not",
    "mustn't": "must not",
    "mightn't": "might not",
    "needn't": "need not",
    "let's": "let us",
    "here's": "here is",
    "there's": "there is",
    "there'll": "there will",
}


@dataclass
class WordMatch:
    """Represents a word match result."""

    original: str
    transcribed: str
    is_match: bool
    index: int


@dataclass
class ComparisonResult:
    """Result of text comparison."""

    original_words: list[str] = field(default_factory=list)
    transcribed_words: list[str] = field(default_factory=list)
    matches: list[WordMatch] = field(default_factory=list)
    errors: list[tuple[int, str, str]] = field(default_factory=list)
    error_details: list[dict] = field(default_factory=list)
    trans_error_indices: set = field(default_factory=set)
    orig_error_indices: set = field(default_factory=set)
    accuracy: float = 0.0
    correct_count: int = 0
    total_count: int = 0
    missing_words: list[str] = field(default_factory=list)
    extra_words: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "accuracy": self.accuracy,
            "correct_count": self.correct_count,
            "total_count": self.total_count,
            "errors": self.errors,
            "missing_words": self.missing_words,
            "extra_words": self.extra_words,
        }


class TextComparator:
    """Compares original text with transcription."""

    # Phonetic groups: letters that sound similar in English
    PHONETIC_GROUPS = {
        "b": "B",
        "f": "F",
        "p": "P",
        "v": "V",
        "c": "K",
        "g": "K",
        "k": "K",
        "q": "K",
        "x": "K",
        "s": "S",
        "z": "S",
        "d": "D",
        "t": "D",
        "m": "M",
        "n": "N",
        "r": "R",
        "l": "R",  # r and l are phonetically similar
        "j": "J",
        "w": "W",
        "h": "W",  # w and h are silent or semivowels
    }
    VOWELS = set("aeiouy")

    @staticmethod
    def get_phonetic_code(word: str) -> str:
        """Generate a simplified phonetic code for a word.

        Implements a Soundex-like but simplified algorithm. Letters that
        sound similar receive the same code.

        Args:
            word: Word to convert

        Returns:
            Phonetic code (uppercase letters representing sounds)
        """
        if not word:
            return ""

        word = word.lower()
        if len(word) == 1:
            return word.upper()

        code = ""
        prev_phoneme = ""

        for i, char in enumerate(word):
            if char in TextComparator.VOWELS:
                # Vowels matter - preserve them partially, but do not emit
                # two consecutive vowel markers
                if not code.endswith("V"):
                    code += "V"
                prev_phoneme = "V"
                continue

            if char in TextComparator.PHONETIC_GROUPS:
                phoneme = TextComparator.PHONETIC_GROUPS[char]
                # Only add it if it differs from the previous phoneme
                if phoneme != prev_phoneme:
                    code += phoneme
                    prev_phoneme = phoneme
            else:
                prev_phoneme = ""

        # Remove consecutive duplicates
        result = ""
        prev = ""
        for c in code:
            if c != prev:
                result += c
            prev = c

        return result if result else word.upper()[:2]

    @staticmethod
    def is_phonetic_match(
        word1: str, word2: str, exact_match_required: bool = False
    ) -> bool:
        """Compare two words phonetically.

        Args:
            word1: First word
            word2: Second word
            exact_match_required: If True, require an exact match in addition
                to the phonetic one

        Returns:
            True if the words match exactly or phonetically
        """
        if not word1 or not word2:
            return False

        # Exact match (case-insensitive)
        if word1.lower() == word2.lower():
            return True

        if exact_match_required:
            return False

        # More flexible phonetic comparison
        code1 = TextComparator.get_phonetic_code(word1)
        code2 = TextComparator.get_phonetic_code(word2)

        if not code1 or not code2:
            return False

        # Check whether the phonetic codes are similar; difflib gives some slack
        return difflib.SequenceMatcher(None, code1, code2).ratio() > 0.6

    @staticmethod
    def normalize_word(word: str) -> str:
        """Normalize a single word.

        Args:
            word: Word to normalize

        Returns:
            Normalized word
        """
        word = word.lower().strip()
        word = re.sub(r"[^\w\s]", "", word)

        if word in CONTRACTIONS:
            word = CONTRACTIONS[word]

        return word

    @staticmethod
    def normalize_text(text: str) -> list[str]:
        """Normalize text into a list of words.

        Args:
            text: Text to normalize

        Returns:
            List of normalized words
        """
        text = text.lower()

        for contraction, expanded in CONTRACTIONS.items():
            text = text.replace(contraction, expanded)

        text = re.sub(r"[^\w\s]", " ", text)

        words = text.split()

        return [w for w in words if w]

    @staticmethod
    def get_original_words(text: str) -> list[str]:
        """Get original words preserving case and punctuation.

        Args:
            text: Original text

        Returns:
            List of original words
        """
        words = re.findall(r"\b[\w\'-]+\b", text)
        return words

    @staticmethod
    def _normalize_raw_word(word: str) -> list[str]:
        """Normalize a single raw word into its comparison token(s).

        A contraction expands to several tokens ("can't" -> ["can", "not"])
        and a hyphenated word splits too, mirroring :meth:`normalize_text` but
        for one raw word at a time so the caller can track which raw word each
        token came from.

        Args:
            word: A single raw word (as produced by ``get_original_words``)

        Returns:
            List of normalized tokens (possibly empty for pure punctuation)
        """
        lowered = word.lower().strip()
        if lowered in CONTRACTIONS:
            lowered = CONTRACTIONS[lowered]
        cleaned = re.sub(r"[^\w\s]", " ", lowered)
        return [token for token in cleaned.split() if token]

    @classmethod
    def _tokenize_aligned(cls, text: str) -> tuple[list[str], list[str], list[int]]:
        """Tokenize text keeping raw and normalized tokens aligned.

        Returns three parallel structures:

        - ``raw_words``: display tokens (case and punctuation preserved)
        - ``normalized_words``: comparison tokens (lowercased, punctuation
          stripped, contractions expanded)
        - ``norm_to_raw``: ``norm_to_raw[j]`` is the index of the raw word that
          produced normalized token ``j``. Because contractions and hyphenated
          words expand to several tokens, this map is what lets error/highlight
          indices computed in normalized space point back at the correct raw
          word (fixing the off-by-N drift after a contraction).

        Args:
            text: Text to tokenize

        Returns:
            Tuple of (raw_words, normalized_words, norm_to_raw)
        """
        raw_words = cls.get_original_words(text)
        normalized_words: list[str] = []
        norm_to_raw: list[int] = []
        for raw_idx, raw_word in enumerate(raw_words):
            for token in cls._normalize_raw_word(raw_word):
                normalized_words.append(token)
                norm_to_raw.append(raw_idx)
        return raw_words, normalized_words, norm_to_raw

    def compare_with_method(
        self,
        original: str,
        transcribed: str,
        method: str = DEFAULT_COMPARISON_METHOD,
        window_size: int = COMPARISON_WINDOW_SIZE,
        use_phonetic: bool = True,
    ) -> ComparisonResult:
        """Compare using the named strategy.

        Single dispatch point used by practice mode so the comparison
        algorithm is selectable via ``Config.comparison_method``.

        Args:
            original: Original lesson text to compare against
            transcribed: Transcribed text from speech
            method: One of ``COMPARISON_METHODS`` ("flexible", "per_word",
                "legacy"). Unknown values fall back to the flexible method.
            window_size: Search window for the flexible method
            use_phonetic: Allow phonetic matches in addition to exact ones

        Returns:
            ComparisonResult with detailed analysis
        """
        if method == "legacy":
            return self.compare(original, transcribed)
        if method == "per_word":
            return self.compare_per_word(
                original, transcribed, use_phonetic=use_phonetic
            )
        # "flexible" and any unknown value fall back to the flexible method.
        return self.compare_flexible(
            original,
            transcribed,
            window_size=window_size,
            use_phonetic=use_phonetic,
        )

    def compare(self, original: str, transcribed: str) -> ComparisonResult:
        """Compare original text with transcription.

        Args:
            original: Original text to compare against
            transcribed: Transcribed text from speech

        Returns:
            ComparisonResult with detailed analysis
        """
        # Aligned tokenization: raw words for display, normalized tokens for
        # matching, and a map from each normalized token back to its raw word.
        # difflib runs on the normalized tokens, so every raw lookup and error
        # index below is translated through the map to avoid the off-by-N drift
        # that contraction expansion ("I'm" -> "i am") used to introduce.
        original_words_raw, original_normalized, orig_to_raw = self._tokenize_aligned(
            original
        )
        (
            transcribed_words_raw,
            transcribed_normalized,
            trans_to_raw,
        ) = self._tokenize_aligned(transcribed)

        def orig_raw_idx(pos: int) -> int:
            return orig_to_raw[pos] if 0 <= pos < len(orig_to_raw) else -1

        def trans_raw_idx(pos: int) -> int:
            return trans_to_raw[pos] if 0 <= pos < len(trans_to_raw) else -1

        def orig_raw_word(pos: int) -> str:
            idx = orig_raw_idx(pos)
            return original_words_raw[idx] if idx >= 0 else ""

        def trans_raw_word(pos: int) -> str:
            idx = trans_raw_idx(pos)
            return transcribed_words_raw[idx] if idx >= 0 else ""

        matcher = difflib.SequenceMatcher(
            None, original_normalized, transcribed_normalized
        )

        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0

        def record_error(orig_pos: int, trans_pos: int, has_trans: bool) -> None:
            """Record an error keyed by raw word index (deduped per raw word)."""
            raw_idx = orig_raw_idx(orig_pos)
            orig_word = orig_raw_word(orig_pos)
            trans_word = trans_raw_word(trans_pos) if has_trans else ""
            if has_trans:
                t_idx = trans_raw_idx(trans_pos)
                if t_idx >= 0:
                    trans_error_indices.add(t_idx)
            if raw_idx >= 0:
                orig_error_indices.add(raw_idx)
            matches.append(
                WordMatch(
                    original=orig_word,
                    transcribed=trans_word,
                    is_match=False,
                    index=raw_idx,
                )
            )
            # A contraction spans several normalized tokens but one raw word;
            # list it once so "can't" is not reported twice.
            if raw_idx >= 0 and any(e[0] == raw_idx for e in errors):
                return
            error_msg = trans_word if trans_word else "(missing)"
            errors.append((raw_idx, orig_word, error_msg))
            error_details.append(
                {
                    "orig_idx": raw_idx,
                    "trans_idx": trans_raw_idx(trans_pos) if trans_word else None,
                    "expected": orig_word,
                    "got": error_msg,
                }
            )

        opcodes = matcher.get_opcodes()

        orig_pos = 0
        trans_pos = 0

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == "equal":
                for k in range(i2 - i1):
                    matches.append(
                        WordMatch(
                            original=orig_raw_word(orig_pos),
                            transcribed=trans_raw_word(trans_pos),
                            is_match=True,
                            index=orig_raw_idx(orig_pos),
                        )
                    )
                    correct_count += 1
                    orig_pos += 1
                    trans_pos += 1

            elif tag == "replace":
                orig_segment_len = i2 - i1
                trans_segment_len = j2 - j1

                for k in range(max(orig_segment_len, trans_segment_len)):
                    if k < orig_segment_len:
                        has_trans = k < trans_segment_len
                        record_error(orig_pos, trans_pos, has_trans)
                        orig_pos += 1

                    if k < trans_segment_len:
                        if k >= orig_segment_len:
                            t_idx = trans_raw_idx(trans_pos)
                            if t_idx >= 0:
                                trans_error_indices.add(t_idx)
                        trans_pos += 1

            elif tag == "delete":
                for k in range(i1, i2):
                    record_error(orig_pos, trans_pos, has_trans=False)
                    orig_pos += 1

            elif tag == "insert":
                for k in range(j1, j2):
                    t_idx = trans_raw_idx(trans_pos)
                    if t_idx >= 0:
                        trans_error_indices.add(t_idx)
                    trans_pos += 1

        total_count = len(original_normalized)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        missing_words = [orig for idx, orig, trans in errors if trans == "(missing)"]
        extra_words: list[str] = []

        return ComparisonResult(
            original_words=original_words_raw,
            transcribed_words=transcribed_words_raw,
            matches=matches,
            errors=errors,
            error_details=error_details,
            trans_error_indices=trans_error_indices,
            orig_error_indices=orig_error_indices,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
            missing_words=missing_words,
            extra_words=extra_words,
        )

    def compare_flexible(
        self,
        original: str,
        transcribed: str,
        window_size: int = 2,
        use_phonetic: bool = True,
    ) -> ComparisonResult:
        """Compare text with a flexible windowed search.

        For each word in the original text, search a range of positions in the
        transcription instead of requiring strict alignment.

        Args:
            original: Original text to compare against
            transcribed: Transcribed text
            window_size: Search window size (±words)
            use_phonetic: Use phonetic matching in addition to exact matching

        Returns:
            ComparisonResult with detailed analysis
        """
        # Aligned tokenization so raw display words and error indices line up
        # with the normalized tokens the window search runs on (see
        # _tokenize_aligned); without this, contractions drift the highlights.
        original_words_raw, original_normalized, orig_to_raw = self._tokenize_aligned(
            original
        )
        (
            transcribed_words_raw,
            transcribed_normalized,
            trans_to_raw,
        ) = self._tokenize_aligned(transcribed)

        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0

        # Tracks which transcribed positions have been matched
        matched_trans_positions: set[int] = set()

        # Anchor for the search window: the transcript position we expect the
        # next original word around. It advances to one past each match, so it
        # tracks reading progress instead of the original index. On a miss it
        # stays put, keeping the window over the same region for the next word
        # (handles runs of deletions without the anchor running ahead).
        expected_pos = 0

        for orig_idx, orig_word in enumerate(original_normalized):
            found_pos = -1

            # Bounded window on both sides of the anchor. This is what keeps a
            # word from matching an identical one far away in the transcript.
            window_start = max(0, expected_pos - window_size)
            window_end = min(
                len(transcribed_normalized), expected_pos + window_size + 1
            )

            # 1. Exact match within the window.
            for trans_idx in range(window_start, window_end):
                if trans_idx in matched_trans_positions:
                    continue

                if orig_word.lower() == transcribed_normalized[trans_idx].lower():
                    found_pos = trans_idx
                    matched_trans_positions.add(trans_idx)
                    break

            # 2. Phonetic match within the same window (not the whole transcript).
            if found_pos < 0 and use_phonetic:
                for trans_idx in range(window_start, window_end):
                    if trans_idx in matched_trans_positions:
                        continue

                    if self.is_phonetic_match(
                        orig_word, transcribed_normalized[trans_idx]
                    ):
                        found_pos = trans_idx
                        matched_trans_positions.add(trans_idx)
                        break

            if found_pos >= 0:
                expected_pos = found_pos + 1

            orig_raw_idx = orig_to_raw[orig_idx] if orig_idx < len(orig_to_raw) else -1
            orig_word_raw = (
                original_words_raw[orig_raw_idx] if orig_raw_idx >= 0 else orig_word
            )

            if found_pos >= 0:
                trans_raw_idx = (
                    trans_to_raw[found_pos] if found_pos < len(trans_to_raw) else -1
                )
                trans_word_raw = (
                    transcribed_words_raw[trans_raw_idx]
                    if trans_raw_idx >= 0
                    else transcribed_normalized[found_pos]
                )
                matches.append(
                    WordMatch(
                        original=orig_word_raw,
                        transcribed=trans_word_raw,
                        is_match=True,
                        index=orig_raw_idx,
                    )
                )
                correct_count += 1
            else:
                matches.append(
                    WordMatch(
                        original=orig_word_raw,
                        transcribed="",
                        is_match=False,
                        index=orig_raw_idx,
                    )
                )
                if orig_raw_idx >= 0:
                    orig_error_indices.add(orig_raw_idx)
                # One raw word can span several normalized tokens; list it once.
                if orig_raw_idx < 0 or not any(e[0] == orig_raw_idx for e in errors):
                    errors.append((orig_raw_idx, orig_word_raw, "(missing)"))
                    error_details.append(
                        {
                            "orig_idx": orig_raw_idx,
                            "trans_idx": None,
                            "expected": orig_word_raw,
                            "got": "(missing)",
                            "method": "flexible_window",
                        }
                    )

        # Extra words: transcribed raw words with no matched normalized token.
        extra_words: list[str] = []
        seen_extra_raw: set[int] = set()
        for trans_idx, trans_word in enumerate(transcribed_normalized):
            if trans_idx in matched_trans_positions:
                continue
            trans_raw_idx = (
                trans_to_raw[trans_idx] if trans_idx < len(trans_to_raw) else -1
            )
            if trans_raw_idx >= 0:
                trans_error_indices.add(trans_raw_idx)
                if trans_raw_idx in seen_extra_raw:
                    continue
                seen_extra_raw.add(trans_raw_idx)
                extra_words.append(transcribed_words_raw[trans_raw_idx])
            else:
                extra_words.append(trans_word)

        total_count = len(original_normalized)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        return ComparisonResult(
            original_words=original_words_raw,
            transcribed_words=transcribed_words_raw,
            matches=matches,
            errors=errors,
            error_details=error_details,
            trans_error_indices=trans_error_indices,
            orig_error_indices=orig_error_indices,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
            missing_words=[e[1] for e in errors if e[2] == "(missing)"],
            extra_words=extra_words,
        )

    def compare_per_word(
        self,
        original: str,
        transcribed: str,
        use_phonetic: bool = True,
    ) -> ComparisonResult:
        """Compare word by word without sequential alignment.

        For each word in the original text, check whether it exists at any
        position in the transcription. Order is not required.

        Args:
            original: Original text to compare against
            transcribed: Transcribed text
            use_phonetic: Use phonetic matching in addition to exact matching

        Returns:
            ComparisonResult with detailed analysis
        """
        # Aligned tokenization keeps raw display words and error indices in
        # sync with the normalized tokens (see _tokenize_aligned).
        original_words_raw, original_normalized, orig_to_raw = self._tokenize_aligned(
            original
        )
        (
            transcribed_words_raw,
            transcribed_normalized,
            trans_to_raw,
        ) = self._tokenize_aligned(transcribed)

        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0

        # Tracks which transcribed positions have been used
        used_trans_positions: set[int] = set()

        # For each original word, search any unused transcript position.
        for orig_idx, orig_word in enumerate(original_normalized):
            orig_raw_idx = orig_to_raw[orig_idx] if orig_idx < len(orig_to_raw) else -1
            orig_word_raw = (
                original_words_raw[orig_raw_idx] if orig_raw_idx >= 0 else orig_word
            )

            # Search any unused position
            found_pos = -1
            for trans_idx, trans_word in enumerate(transcribed_normalized):
                if trans_idx in used_trans_positions:
                    continue

                # Check for an exact or phonetic match
                is_match = orig_word.lower() == trans_word.lower() or (
                    use_phonetic and self.is_phonetic_match(orig_word, trans_word)
                )

                if is_match:
                    found_pos = trans_idx
                    used_trans_positions.add(trans_idx)
                    break

            if found_pos >= 0:
                trans_raw_idx = (
                    trans_to_raw[found_pos] if found_pos < len(trans_to_raw) else -1
                )
                trans_word_raw = (
                    transcribed_words_raw[trans_raw_idx]
                    if trans_raw_idx >= 0
                    else transcribed_normalized[found_pos]
                )
                matches.append(
                    WordMatch(
                        original=orig_word_raw,
                        transcribed=trans_word_raw,
                        is_match=True,
                        index=orig_raw_idx,
                    )
                )
                correct_count += 1
            else:
                matches.append(
                    WordMatch(
                        original=orig_word_raw,
                        transcribed="",
                        is_match=False,
                        index=orig_raw_idx,
                    )
                )
                if orig_raw_idx >= 0:
                    orig_error_indices.add(orig_raw_idx)
                if orig_raw_idx < 0 or not any(e[0] == orig_raw_idx for e in errors):
                    errors.append((orig_raw_idx, orig_word_raw, "(missing)"))
                    error_details.append(
                        {
                            "orig_idx": orig_raw_idx,
                            "trans_idx": None,
                            "expected": orig_word_raw,
                            "got": "(missing)",
                            "method": "per_word",
                        }
                    )

        # Extra words: transcribed raw words with no used normalized token.
        extra_words: list[str] = []
        seen_extra_raw: set[int] = set()
        for trans_idx, trans_word in enumerate(transcribed_normalized):
            if trans_idx in used_trans_positions:
                continue
            trans_raw_idx = (
                trans_to_raw[trans_idx] if trans_idx < len(trans_to_raw) else -1
            )
            if trans_raw_idx >= 0:
                trans_error_indices.add(trans_raw_idx)
                if trans_raw_idx in seen_extra_raw:
                    continue
                seen_extra_raw.add(trans_raw_idx)
                extra_words.append(transcribed_words_raw[trans_raw_idx])
            else:
                extra_words.append(trans_word)

        total_count = len(original_normalized)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        return ComparisonResult(
            original_words=original_words_raw,
            transcribed_words=transcribed_words_raw,
            matches=matches,
            errors=errors,
            error_details=error_details,
            trans_error_indices=trans_error_indices,
            orig_error_indices=orig_error_indices,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
            missing_words=[e[1] for e in errors if e[2] == "(missing)"],
            extra_words=extra_words,
        )

    def generate_display(
        self, result: ComparisonResult, ui_language: str = "en"
    ) -> str:
        """Generate a formatted display of the comparison.

        Args:
            result: Comparison result
            ui_language: UI language for formatting

        Returns:
            Formatted string for display
        """
        lines = []

        if result.errors:
            lines.append("")
            lines.append("  ❌ Mispronounced words:")
            for idx, orig, trans in result.errors[:10]:
                if trans == "(missing)":
                    lines.append(f'    • "{orig}" - missed')
                else:
                    lines.append(f'    • "{orig}" → "{trans}"')

            if len(result.errors) > 10:
                lines.append(f"    ... and {len(result.errors) - 10} more")
            lines.append("")

        return "\n".join(lines)

    def generate_rich_display(self, result: ComparisonResult) -> list[dict]:
        """Generate Rich-formatted segments for display.

        Args:
            result: Comparison result

        Returns:
            List of dicts with text and style
        """
        segments = []

        error_indices = {e[0] for e in result.errors}

        for i, word in enumerate(result.original_words):
            if i in error_indices:
                segments.append({"text": word, "style": "bold red"})
            else:
                segments.append({"text": word, "style": "green"})

            if i < len(result.original_words) - 1:
                segments.append({"text": " ", "style": ""})

        return segments
