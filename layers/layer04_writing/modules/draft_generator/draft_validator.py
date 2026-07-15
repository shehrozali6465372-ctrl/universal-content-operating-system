"""Draft Validator — Validate generated drafts for quality and compliance."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


MIN_WORDS_PER_LENGTH = {"short": 30, "medium": 100, "long": 250}
MAX_WORDS_PER_LENGTH = {"short": 150, "medium": 400, "long": 800}


class DraftValidationResult:
    """Result of draft validation."""
    __slots__ = ("is_valid", "word_count", "sentence_count", "avg_word_length",
                 "issues", "score", "severity")

    def __init__(self) -> None:
        self.is_valid = True
        self.word_count = 0
        self.sentence_count = 0
        self.avg_word_length = 0.0
        self.issues: List[str] = []
        self.score = 100.0
        self.severity = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.is_valid,
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "avg_word_length": round(self.avg_word_length, 2),
            "issues": self.issues,
            "score": round(self.score, 1),
            "severity": self.severity,
        }


class DraftValidator:
    """Validates generated drafts for basic quality checks."""

    def __init__(self) -> None:
        self._check_count = 0

    def validate(self, draft: str, length: str = "medium", platform: str = "facebook",
                 rules: Optional[Dict[str, Any]] = None) -> DraftValidationResult:
        """Validate a draft for quality and compliance."""
        result = DraftValidationResult()
        rules = rules or {}

        # Word count
        words = draft.split()
        result.word_count = len(words)
        result.sentence_count = draft.count('.') + draft.count('!') + draft.count('?')

        # Avg word length
        if result.word_count > 0:
            result.avg_word_length = sum(len(w) for w in words) / result.word_count

        # Check min words
        min_words = MIN_WORDS_PER_LENGTH.get(length, 100)
        if result.word_count < min_words:
            result.issues.append(f"Too short: {result.word_count} words (minimum {min_words})")
            result.score -= 20

        # Check max words
        max_words = MAX_WORDS_PER_LENGTH.get(length, 800)
        if result.word_count > max_words:
            result.issues.append(f"Too long: {result.word_count} words (maximum {max_words})")
            result.score -= 10

        # Sentence length
        if result.sentence_count < 1:
            result.issues.append("No sentences detected")
            result.score -= 15

        # Repeated words check
        if result.word_count > 0:
            repeated = self._find_repeated_words(words)
            if repeated:
                result.issues.append(f"Repeated words: {', '.join(repeated[:3])}")
                result.score -= 5

        # URL check
        if "http" in draft or "www." in draft:
            result.issues.append("Draft contains URLs")

        # Custom rules
        if rules.get("no_profanity", False):
            profanity = self._detect_profanity(draft)
            if profanity:
                result.issues.append("Profanity detected")
                result.score -= 50

        if rules.get("min_word_count", 0) > 0 and result.word_count < rules.get("min_word_count"):
            result.issues.append(f"Below minimum word count ({rules['min_word_count']})")
            result.score -= 20

        # Severity
        if result.score < 40:
            result.severity = "high"
        elif result.score < 70:
            result.severity = "medium"

        result.is_valid = result.score >= 50
        self._check_count += 1
        return result

    def _find_repeated_words(self, words: List[str]) -> List[str]:
        seen: set = set()
        repeated: set = set()
        for w in words:
            w_lower = w.lower().strip(".,!?;:")
            if w_lower in seen:
                repeated.add(w_lower)
            seen.add(w_lower)
        return [w for w in repeated if len(w) > 3][:5]

    def _detect_profanity(self, text: str) -> bool:
        # Basic placeholder — should be replaced with real profanity list
        BAD_WORDS = {"fuck", "shit", "damn", "bitch", "ass", "bastard", "crap"}
        words = {w.lower().strip(".,!?;:") for w in text.split()}
        return len(words & BAD_WORDS) > 0

    @property
    def check_count(self) -> int:
        return self._check_count
