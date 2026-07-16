"""Readability Analyzer — Measure content readability and complexity."""
from __future__ import annotations
from typing import Any, Dict, List


class ReadabilityResult:
    """Readability analysis result."""
    __slots__ = ("flesch_score", "grade_level", "reading_time_seconds",
                 "word_count", "sentence_count", "avg_sentence_length",
                 "avg_word_length", "readability_level", "issues")

    def __init__(self) -> None:
        self.flesch_score = 0.0
        self.grade_level = 0.0
        self.reading_time_seconds = 0.0
        self.word_count = 0
        self.sentence_count = 0
        self.avg_sentence_length = 0.0
        self.avg_word_length = 0.0
        self.readability_level = ""
        self.issues: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "flesch_score": round(self.flesch_score, 1),
            "grade_level": round(self.grade_level, 1),
            "reading_time_seconds": round(self.reading_time_seconds, 1),
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "avg_sentence_length": round(self.avg_sentence_length, 1),
            "readability_level": self.readability_level,
            "issues": self.issues,
        }


class ReadabilityAnalyzer:
    """Analyzes text readability using simplified Flesch-Kincaid."""

    def __init__(self) -> None:
        self._analysis_count = 0

    def analyze(self, text: str) -> ReadabilityResult:
        """Analyze text readability."""
        result = ReadabilityResult()
        words = text.split()
        result.word_count = len(words)

        sentences = max(text.count('.') + text.count('!') + text.count('?'), 1)
        result.sentence_count = sentences
        result.avg_sentence_length = result.word_count / sentences
        result.avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        result.reading_time_seconds = result.word_count / 4  # ~200 wpm

        # Simplified Flesch
        result.flesch_score = max(0, min(100,
            206.835 - 1.015 * result.avg_sentence_length - 84.6 * (sum(len(w) for w in words) / max(len(words), 1) / 5)
        ))

        # Grade level (simplified)
        result.grade_level = max(0,
            0.39 * result.avg_sentence_length + 11.8 * (sum(len(w) for w in words) / max(len(words), 1) / 5) - 15.59
        )

        # Level
        if result.flesch_score >= 80:
            result.readability_level = "easy"
        elif result.flesch_score >= 60:
            result.readability_level = "moderate"
        elif result.flesch_score >= 40:
            result.readability_level = "difficult"
        else:
            result.readability_level = "very_difficult"

        # Issues
        if result.avg_sentence_length > 25:
            result.issues.append("Sentences too long — aim for under 20 words")
        if result.word_count < 50:
            result.issues.append("Content may be too short for meaningful analysis")

        self._analysis_count += 1
        return result

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
