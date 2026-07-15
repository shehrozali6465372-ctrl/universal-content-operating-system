"""Readability Analyzer - Analyzes text readability and complexity."""
from __future__ import annotations
import re
from typing import Dict, List


class ReadabilityResult:
    """Readability analysis result."""
    __slots__ = ("flesch_score", "grade_level", "reading_time_seconds",
                 "word_count", "sentence_count", "avg_words_per_sentence",
                 "complexity", "recommendations")

    def __init__(self) -> None:
        self.flesch_score = 0.0
        self.grade_level = 0.0
        self.reading_time_seconds = 0.0
        self.word_count = 0
        self.sentence_count = 0
        self.avg_words_per_sentence = 0.0
        self.complexity = "moderate"
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "flesch_score": round(self.flesch_score, 1),
            "grade_level": round(self.grade_level, 1),
            "reading_time_seconds": round(self.reading_time_seconds, 1),
            "word_count": self.word_count, "sentence_count": self.sentence_count,
            "avg_words_per_sentence": round(self.avg_words_per_sentence, 1),
            "complexity": self.complexity,
            "recommendations": list(self.recommendations),
        }


class ReadabilityAnalyzer:
    """Analyzes text readability using simplified Flesch-Kincaid metrics."""

    def analyze(self, text: str) -> ReadabilityResult:
        result = ReadabilityResult()
        if not text.strip():
            return result

        sentences = [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]
        words = text.split()
        syllables = sum(self._count_syllables(w) for w in words)

        result.word_count = len(words)
        result.sentence_count = len(sentences)
        result.avg_words_per_sentence = len(words) / max(len(sentences), 1)
        result.reading_time_seconds = len(words) / 3.5

        if len(sentences) > 0 and len(words) > 0:
            result.flesch_score = (
                206.835 - 1.015 * result.avg_words_per_sentence - 84.6 * syllables / len(words)
            )
            result.flesch_score = max(0, min(100, result.flesch_score))
            result.grade_level = 0.39 * result.avg_words_per_sentence + 11.8 * syllables / len(words) - 15.59
            result.grade_level = max(0, result.grade_level)

        if result.flesch_score >= 70: result.complexity = "easy"
        elif result.flesch_score >= 50: result.complexity = "moderate"
        elif result.flesch_score >= 30: result.complexity = "difficult"
        else: result.complexity = "very_difficult"

        if result.avg_words_per_sentence > 20:
            result.recommendations.append("Shorten sentences (avg > 20 words)")
        if result.complexity in ("difficult", "very_difficult"):
            result.recommendations.append("Simplify language for broader audience")
        if result.word_count < 50:
            result.recommendations.append("Content may be too short")

        return result

    def _count_syllables(self, word: str) -> int:
        word = word.lower().strip()
        if len(word) <= 3: return 1
        vowels = "aeiouy"
        count = 0
        prev_vowel = False
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not prev_vowel:
                count += 1
            prev_vowel = is_vowel
        if word.endswith("e"): count -= 1
        return max(1, count)
