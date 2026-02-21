"""Text comparison for pronunciation analysis."""

import difflib
import re
from dataclasses import dataclass, field
from typing import Any


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
    
    @staticmethod
    def normalize_word(word: str) -> str:
        """Normalize a single word.
        
        Args:
            word: Word to normalize
            
        Returns:
            Normalized word
        """
        word = word.lower().strip()
        word = re.sub(r'[^\w\s]', '', word)
        
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
        
        text = re.sub(r'[^\w\s]', ' ', text)
        
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
        words = re.findall(r'\b[\w\'-]+\b', text)
        return words
    
    def compare(self, original: str, transcribed: str) -> ComparisonResult:
        """Compare original text with transcription.
        
        Args:
            original: Original text to compare against
            transcribed: Transcribed text from speech
            
        Returns:
            ComparisonResult with detailed analysis
        """
        original_words_raw = self.get_original_words(original)
        transcribed_words_raw = self.get_original_words(transcribed)
        
        original_normalized = self.normalize_text(original)
        transcribed_normalized = self.normalize_text(transcribed)
        
        matcher = difflib.SequenceMatcher(None, original_normalized, transcribed_normalized)
        
        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        correct_count = 0
        
        opcodes = matcher.get_opcodes()
        
        orig_idx = 0
        trans_idx = 0
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for k in range(i2 - i1):
                    orig_word = original_words_raw[orig_idx] if orig_idx < len(original_words_raw) else ""
                    trans_word = transcribed_words_raw[trans_idx] if trans_idx < len(transcribed_words_raw) else ""
                    
                    matches.append(WordMatch(
                        original=orig_word,
                        transcribed=trans_word,
                        is_match=True,
                        index=orig_idx,
                    ))
                    correct_count += 1
                    orig_idx += 1
                    trans_idx += 1
                    
            elif tag == 'replace':
                orig_segment = original_normalized[i1:i2]
                trans_segment = transcribed_normalized[j1:j2]
                
                for k, orig_word in enumerate(orig_segment):
                    orig_word_raw = original_words_raw[orig_idx] if orig_idx < len(original_words_raw) else ""
                    trans_word_raw = transcribed_words_raw[trans_idx] if trans_idx < len(transcribed_words_raw) else ""
                    
                    matches.append(WordMatch(
                        original=orig_word_raw,
                        transcribed=trans_word_raw if k == 0 else "",
                        is_match=False,
                        index=orig_idx,
                    ))
                    errors.append((orig_idx, orig_word_raw, trans_word_raw if k == 0 else "(missing)"))
                    orig_idx += 1
                    
                if len(trans_segment) > len(orig_segment):
                    for k in range(len(orig_segment), len(trans_segment)):
                        trans_idx += 1
                        
            elif tag == 'delete':
                for k in range(i1, i2):
                    orig_word_raw = original_words_raw[orig_idx] if orig_idx < len(original_words_raw) else ""
                    matches.append(WordMatch(
                        original=orig_word_raw,
                        transcribed="",
                        is_match=False,
                        index=orig_idx,
                    ))
                    errors.append((orig_idx, orig_word_raw, "(missing)"))
                    orig_idx += 1
                    
            elif tag == 'insert':
                for k in range(j1, j2):
                    trans_idx += 1
        
        total_count = len(original_normalized)
        accuracy = correct_count / total_count if total_count > 0 else 0.0
        
        missing_words = [orig for idx, orig, trans in errors if trans == "(missing)"]
        extra_words = []
        
        return ComparisonResult(
            original_words=original_words_raw,
            transcribed_words=transcribed_words_raw,
            matches=matches,
            errors=errors,
            accuracy=accuracy,
            correct_count=correct_count,
            total_count=total_count,
            missing_words=missing_words,
            extra_words=extra_words,
        )
    
    def generate_display(self, result: ComparisonResult, ui_language: str = "en") -> str:
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
                    lines.append(f"    • \"{orig}\" - missed")
                else:
                    lines.append(f"    • \"{orig}\" → \"{trans}\"")
            
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
