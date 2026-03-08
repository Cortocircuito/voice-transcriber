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

    # Grupos fonéticos: letras que suenan similar en inglés
    PHONETIC_GROUPS = {
        'b': 'B', 'f': 'F', 'p': 'P', 'v': 'V',
        'c': 'K', 'g': 'K', 'k': 'K', 'q': 'K', 'x': 'K',
        's': 'S', 'z': 'S',
        'd': 'D', 't': 'D',
        'm': 'M', 'n': 'N',
        'r': 'R', 'l': 'R',  # r y l son similares fonéticamente
        'j': 'J',
        'w': 'W', 'h': 'W',  # w y h son mudas o semivocales
    }
    VOWELS = set('aeiouy')

    @staticmethod
    def get_phonetic_code(word: str) -> str:
        """Genera código fonético simplificado para una palabra.

        Implementa un algoritmo similar a Soundex pero simplificado.
        Las letras que suenan similar reciben el mismo código.

        Args:
            word: Palabra a convertir

        Returns:
            Código fonético (letras mayúsculas representando sonidos)
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
                # Las vocales son importantes - las preservamos parcialmente
                # pero no连续 dos vocales
                if not code.endswith('V'):
                    code += 'V'
                prev_phoneme = "V"
                continue

            if char in TextComparator.PHONETIC_GROUPS:
                phoneme = TextComparator.PHONETIC_GROUPS[char]
                # Solo añadir si es diferente del fonema anterior
                if phoneme != prev_phoneme:
                    code += phoneme
                    prev_phoneme = phoneme
            else:
                prev_phoneme = ""

        # Eliminar duplicados consecutivos
        result = ""
        prev = ""
        for c in code:
            if c != prev:
                result += c
            prev = c

        return result if result else word.upper()[:2]

    @staticmethod
    def is_phonetic_match(word1: str, word2: str, exact_match_required: bool = False) -> bool:
        """Compara dos palabras fonéticamente.

        Args:
            word1: Primera palabra
            word2: Segunda palabra
            exact_match_required: Si True, requiere coincidencia exacta además de fonética

        Returns:
            True si las palabras coinciden exacta o fonéticamente
        """
        if not word1 or not word2:
            return False

        # Coincidencia exacta (ignorando mayúsculas/minúsculas)
        if word1.lower() == word2.lower():
            return True

        if exact_match_required:
            return False

        # Comparación fonética más flexible
        code1 = TextComparator.get_phonetic_code(word1)
        code2 = TextComparator.get_phonetic_code(word2)

        if not code1 or not code2:
            return False

        # Verificar si los códigos fonéticos son similares
        # Usamos difflib para mayor flexibilidad
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
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0
        
        opcodes = matcher.get_opcodes()
        
        orig_pos = 0
        trans_pos = 0
        
        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                for k in range(i2 - i1):
                    orig_word = original_words_raw[orig_pos] if orig_pos < len(original_words_raw) else ""
                    trans_word = transcribed_words_raw[trans_pos] if trans_pos < len(transcribed_words_raw) else ""
                    
                    matches.append(WordMatch(
                        original=orig_word,
                        transcribed=trans_word,
                        is_match=True,
                        index=orig_pos,
                    ))
                    correct_count += 1
                    orig_pos += 1
                    trans_pos += 1
                    
            elif tag == 'replace':
                orig_segment_len = i2 - i1
                trans_segment_len = j2 - j1
                
                for k in range(max(orig_segment_len, trans_segment_len)):
                    if k < orig_segment_len:
                        orig_word = original_words_raw[orig_pos] if orig_pos < len(original_words_raw) else ""
                        trans_word = transcribed_words_raw[trans_pos] if k < trans_segment_len and trans_pos < len(transcribed_words_raw) else ""
                        
                        orig_error_indices.add(orig_pos)
                        
                        if trans_word:
                            trans_error_indices.add(trans_pos)
                        
                        error_msg = trans_word if trans_word else "(missing)"
                        errors.append((orig_pos, orig_word, error_msg))
                        error_details.append({
                            "orig_idx": orig_pos,
                            "trans_idx": trans_pos if trans_word else None,
                            "expected": orig_word,
                            "got": error_msg,
                        })
                        
                        matches.append(WordMatch(
                            original=orig_word,
                            transcribed=trans_word,
                            is_match=False,
                            index=orig_pos,
                        ))
                        orig_pos += 1
                        
                    if k < trans_segment_len:
                        if k >= orig_segment_len:
                            trans_word = transcribed_words_raw[trans_pos] if trans_pos < len(transcribed_words_raw) else ""
                            trans_error_indices.add(trans_pos)
                        trans_pos += 1
                        
            elif tag == 'delete':
                for k in range(i1, i2):
                    orig_word = original_words_raw[orig_pos] if orig_pos < len(original_words_raw) else ""
                    
                    orig_error_indices.add(orig_pos)
                    errors.append((orig_pos, orig_word, "(missing)"))
                    error_details.append({
                        "orig_idx": orig_pos,
                        "trans_idx": None,
                        "expected": orig_word,
                        "got": "(missing)",
                    })
                    
                    matches.append(WordMatch(
                        original=orig_word,
                        transcribed="",
                        is_match=False,
                        index=orig_pos,
                    ))
                    orig_pos += 1
                    
            elif tag == 'insert':
                for k in range(j1, j2):
                    trans_word = transcribed_words_raw[trans_pos] if trans_pos < len(transcribed_words_raw) else ""
                    trans_error_indices.add(trans_pos)
                    trans_pos += 1
        
        total_count = len(original_normalized)
        accuracy = correct_count / total_count if total_count > 0 else 0.0

        missing_words = [orig for idx, orig, trans in errors if trans == "(missing)"]
        extra_words = []

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
        """Compara texto con búsqueda flexible en ventana.

        Para cada palabra del texto original, busca en un rango de posiciones
        en la transcripción en lugar de requerir alineación estricta.

        Args:
            original: Texto original a comparar
            transcribed: Texto transcrito
            window_size: Tamaño de la ventana de búsqueda (±palabras)
            use_phonetic: Usar coincidencia fonética además de exacta

        Returns:
            ComparisonResult con análisis detallado
        """
        original_words_raw = self.get_original_words(original)
        transcribed_words_raw = self.get_original_words(transcribed)

        original_normalized = self.normalize_text(original)
        transcribed_normalized = self.normalize_text(transcribed)

        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0

        # Tracks which transcribed positions have been matched
        matched_trans_positions: set[int] = set()

        for orig_idx, orig_word in enumerate(original_normalized):
            # Primero buscar coincidencia exacta en la ventana
            found_pos = -1
            found_type = None  # 'exact' or 'phonetic'

            search_start = max(0, orig_idx - window_size)

            # 1. Buscar coincidencia exacta en la ventana
            for trans_idx in range(search_start, len(transcribed_normalized)):
                if trans_idx in matched_trans_positions:
                    continue

                if orig_word.lower() == transcribed_normalized[trans_idx].lower():
                    found_pos = trans_idx
                    found_type = 'exact'
                    matched_trans_positions.add(trans_idx)
                    break

            # 2. Si no hay coincidencia exacta, buscar fonética en todo el texto
            if found_pos < 0 and use_phonetic:
                for trans_idx in range(len(transcribed_normalized)):
                    if trans_idx in matched_trans_positions:
                        continue

                    if self.is_phonetic_match(orig_word, transcribed_normalized[trans_idx]):
                        found_pos = trans_idx
                        found_type = 'phonetic'
                        matched_trans_positions.add(trans_idx)
                        break

            orig_word_raw = original_words_raw[orig_idx] if orig_idx < len(original_words_raw) else orig_word

            if found_pos >= 0:
                trans_word_raw = (
                    transcribed_words_raw[found_pos]
                    if found_pos < len(transcribed_words_raw)
                    else transcribed_normalized[found_pos]
                )
                matches.append(WordMatch(
                    original=orig_word_raw,
                    transcribed=trans_word_raw,
                    is_match=True,
                    index=orig_idx,
                ))
                correct_count += 1
            else:
                matches.append(WordMatch(
                    original=orig_word_raw,
                    transcribed="",
                    is_match=False,
                    index=orig_idx,
                ))
                orig_error_indices.add(orig_idx)
                errors.append((orig_idx, orig_word_raw, "(missing)"))
                error_details.append({
                    "orig_idx": orig_idx,
                    "trans_idx": None,
                    "expected": orig_word_raw,
                    "got": "(missing)",
                    "method": "flexible_window",
                })

        # Identificar palabras extra (en transcripción pero no matched)
        extra_words = []
        for trans_idx, trans_word in enumerate(transcribed_normalized):
            if trans_idx not in matched_trans_positions:
                trans_word_raw = (
                    transcribed_words_raw[trans_idx]
                    if trans_idx < len(transcribed_words_raw)
                    else trans_word
                )
                extra_words.append(trans_word_raw)
                trans_error_indices.add(trans_idx)

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
        """Compara palabra por palabra sin alineación secuencial.

        Para cada palabra del texto original, verifica si existe en
        cualquier posición de la transcripción. No requiere orden.

        Args:
            original: Texto original a comparar
            transcribed: Texto transcrito
            use_phonetic: Usar coincidencia fonética además de exacta

        Returns:
            ComparisonResult con análisis detallado
        """
        original_words_raw = self.get_original_words(original)
        transcribed_words_raw = self.get_original_words(transcribed)

        original_normalized = self.normalize_text(original)
        transcribed_normalized = self.normalize_text(transcribed)

        matches: list[WordMatch] = []
        errors: list[tuple[int, str, str]] = []
        error_details: list[dict] = []
        orig_error_indices: set[int] = set()
        trans_error_indices: set[int] = set()
        correct_count = 0

        # Tracks which transcribed positions have been used
        used_trans_positions: set[int] = set()

        # Para cada palabra original, buscar en cualquier posición
        for orig_idx, orig_word in enumerate(original_normalized):
            orig_word_raw = (
                original_words_raw[orig_idx]
                if orig_idx < len(original_words_raw)
                else orig_word
            )

            # Buscar en cualquier posición no usada
            found_pos = -1
            for trans_idx, trans_word in enumerate(transcribed_normalized):
                if trans_idx in used_trans_positions:
                    continue

                # Verificar coincidencia exacta o fonética
                is_match = (
                    orig_word.lower() == trans_word.lower() or
                    (use_phonetic and self.is_phonetic_match(orig_word, trans_word))
                )

                if is_match:
                    found_pos = trans_idx
                    used_trans_positions.add(trans_idx)
                    break

            if found_pos >= 0:
                trans_word_raw = (
                    transcribed_words_raw[found_pos]
                    if found_pos < len(transcribed_words_raw)
                    else transcribed_normalized[found_pos]
                )
                matches.append(WordMatch(
                    original=orig_word_raw,
                    transcribed=trans_word_raw,
                    is_match=True,
                    index=orig_idx,
                ))
                correct_count += 1
            else:
                matches.append(WordMatch(
                    original=orig_word_raw,
                    transcribed="",
                    is_match=False,
                    index=orig_idx,
                ))
                orig_error_indices.add(orig_idx)
                errors.append((orig_idx, orig_word_raw, "(missing)"))
                error_details.append({
                    "orig_idx": orig_idx,
                    "trans_idx": None,
                    "expected": orig_word_raw,
                    "got": "(missing)",
                    "method": "per_word",
                })

        # Palabras extra (en transcripción pero no usadas)
        extra_words = []
        for trans_idx, trans_word in enumerate(transcribed_normalized):
            if trans_idx not in used_trans_positions:
                trans_word_raw = (
                    transcribed_words_raw[trans_idx]
                    if trans_idx < len(transcribed_words_raw)
                    else trans_word
                )
                extra_words.append(trans_word_raw)
                trans_error_indices.add(trans_idx)

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
