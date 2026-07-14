"""
Ambiguity Detector — Sprint 3 (v3.0)

Detects ambiguous text that may have multiple interpretations.

Public API:
    detect(text) -> AmbiguityResult
    is_ambiguous(text) -> bool
    get_alternatives(text) -> List[str]

Version: 3.0.0
"""

from __future__ import annotations
import re
from typing import Dict, List


# Ambiguous words with multiple common meanings
_AMBIGUOUS_WORDS: Dict[str, List[str]] = {
    "apple": ["fruit", "technology_company"],
    "python": ["programming_language", "snake"],
    "java": ["programming_language", "island"],
    "rust": ["programming_language", "corrosion"],
    "go": ["programming_language", "movement"],
    "scala": ["programming_language", "staircase"],
    "crane": ["machine", "bird"],
    "bat": ["animal", "sports_equipment"],
    "bank": ["financial", "river_side"],
    "capital": ["money", "city"],
    "cell": ["phone", "biology"],
    "crash": ["accident", "computer_error"],
    "driver": ["software", "vehicle_operator"],
    "key": ["keyboard", "lock_opener", "important"],
    "light": ["not_heavy", "illumination"],
    "match": ["competition", "fire_starter"],
    "mercury": ["element", "planet"],
    "pitch": ["music", "sales", "sports"],
    "port": ["harbor", "software"],
    "ring": ["jewelry", "sound", "fight"],
    "scale": ["measurement", "fish_part"],
    "spring": ["season", "mechanical"],
    "stream": ["water", "data"],
    "table": ["furniture", "data_structure"],
    "trunk": ["tree_part", "car_storage", "elephant"],
    "value": ["worth", "programming"],
    "wave": ["ocean", "physics", "gesture"],
}

# Indicators of ambiguity
_HEDGE_WORDS = {"maybe", "perhaps", "might", "could", "possibly", "unclear",
                "ambiguous", "either", "both", "depends", "context"}
_VAGUE_WORDS = {"thing", "stuff", "something", "anything", "nothing",
                "kind", "sort", "basically", "actually", "literally"}


class AmbiguityResult:
    """Result of ambiguity detection."""

    __slots__ = ("text", "is_ambiguous", "ambiguity_score", "ambiguous_words",
                 "alternatives", "reasons", "confidence")

    def __init__(self) -> None:
        self.text: str = ""
        self.is_ambiguous: bool = False
        self.ambiguity_score: float = 0.0
        self.ambiguous_words: List[Dict] = []
        self.alternatives: List[str] = []
        self.reasons: List[str] = []
        self.confidence: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "is_ambiguous": self.is_ambiguous,
            "ambiguity_score": round(self.ambiguity_score, 3),
            "ambiguous_words": list(self.ambiguous_words),
            "alternatives": list(self.alternatives),
            "reasons": list(self.reasons),
            "confidence": round(self.confidence, 3),
        }


class AmbiguityDetector:
    """Detects ambiguous text and suggests alternatives.

    Usage::

        detector = AmbiguityDetector()
        result = detector.detect("I love apple pie and Apple computers")
        print(result.is_ambiguous, result.ambiguity_score)
    """

    def __init__(self) -> None:
        self._ambig_words = dict(_AMBIGUOUS_WORDS)

    def detect(self, text: str) -> AmbiguityResult:
        """Detect ambiguity in text."""
        result = AmbiguityResult()
        result.text = text

        if not text or not text.strip():
            return result

        words = self._tokenize(text)
        if not words:
            return result

        # Check for ambiguous words
        found_ambiguous: List[Dict] = []
        for word in words:
            if word in self._ambig_words:
                meanings = self._ambig_words[word]
                found_ambiguous.append({"word": word, "meanings": meanings})

        result.ambiguous_words = found_ambiguous

        # Check for hedge/vague words
        hedge_count = sum(1 for w in words if w in _HEDGE_WORDS)
        vague_count = sum(1 for w in words if w in _VAGUE_WORDS)

        # Score calculation
        ambig_score = len(found_ambiguous) / max(len(words), 1)
        hedge_score = min(0.3, hedge_count * 0.1)
        vague_score = min(0.2, vague_count * 0.05)

        result.ambiguity_score = round(min(1.0, ambig_score + hedge_score + vague_score), 3)
        result.is_ambiguous = result.ambiguity_score > 0.1

        # Generate alternatives
        if found_ambiguous:
            for item in found_ambiguous:
                result.alternatives.extend(
                    [f"{item['word']} ({m})" for m in item["meanings"]]
                )

        # Reasons
        if found_ambiguous:
            result.reasons.append(
                f"Found {len(found_ambiguous)} ambiguous word(s): "
                + ", ".join(w["word"] for w in found_ambiguous)
            )
        if hedge_count > 0:
            result.reasons.append(f"Contains {hedge_count} hedge word(s)")
        if vague_count > 0:
            result.reasons.append(f"Contains {vague_count} vague word(s)")

        # Confidence in ambiguity detection
        if result.ambiguity_score > 0.5:
            result.confidence = 0.9
        elif result.ambiguity_score > 0.2:
            result.confidence = 0.7
        elif result.ambiguity_score > 0:
            result.confidence = 0.5
        else:
            result.confidence = 0.85  # High confidence that it's NOT ambiguous

        return result

    def is_ambiguous(self, text: str) -> bool:
        return self.detect(text).is_ambiguous

    def get_alternatives(self, text: str) -> List[str]:
        return self.detect(text).alternatives

    def add_ambiguous_word(self, word: str, meanings: List[str]) -> None:
        self._ambig_words[word.lower()] = meanings

    def _tokenize(self, text: str) -> List[str]:
        return [w.lower() for w in re.findall(r"[a-zA-Z]+", text) if len(w) >= 2]
