"""
Contradiction Detector — Sprint 4 (v4.0)

Detects semantic contradictions between texts at meaning level, not just lexical negation.

Public API:
    detect(text_a, text_b) -> ContradictionResult
    detect_batch(texts) -> List[ContradictionResult]
    has_contradiction(text_a, text_b, threshold) -> bool
    find_contradictions(texts) -> List[Tuple[int, int]]

Version: 4.0.0
"""

from __future__ import annotations
import re
from typing import Dict, List, Optional, Set, Tuple


# Negation patterns
_NEGATION_PREFIXES = {"un", "in", "im", "ir", "il", "dis", "non", "anti", "de", "mis"}
_NEGATION_WORDS = {"not", "no", "never", "neither", "nor", "nobody", "nothing",
                    "nowhere", "hardly", "barely", "scarcely", "without",
                    "nt", "nahi", "na", "nahin"}

# Opposite word pairs (semantic antonyms)
_ANTONYM_PAIRS: List[Tuple[str, str]] = [
    ("increase", "decrease"), ("increase", "decline"), ("increase", "drop"),
    ("grow", "shrink"),
    ("positive", "negative"), ("good", "bad"), ("great", "terrible"),
    ("success", "failure"), ("win", "lose"), ("profit", "loss"),
    ("high", "low"), ("more", "less"),
    ("best", "worst"), ("better", "worse"), ("strong", "weak"),
    ("fast", "slow"), ("hot", "cold"), ("old", "new"),
    ("start", "stop"), ("begin", "end"), ("open", "close"),
    ("love", "hate"), ("like", "dislike"), ("agree", "disagree"),
    ("increase", "reduce"), ("boost", "cut"), ("improve", "worsen"),
    ("rich", "poor"), ("safe", "dangerous"), ("easy", "difficult"),
    ("happy", "sad"), ("beautiful", "ugly"), ("clean", "dirty"),
    ("buy", "sell"), ("hire", "fire"), ("build", "destroy"),
    ("accept", "reject"), ("allow", "forbid"), ("enable", "disable"),
    ("morning", "night"), ("summer", "winter"), ("first", "last"),
]

# Build lookup for fast access
_ANTONYM_MAP: Dict[str, Set[str]] = {}
for _a, _b in _ANTONYM_PAIRS:
    _ANTONYM_MAP.setdefault(_a, set()).add(_b)
    _ANTONYM_MAP.setdefault(_b, set()).add(_a)


class ContradictionResult:
    """Result of contradiction detection between two texts."""

    __slots__ = ("text_a", "text_b", "is_contradictory", "confidence",
                 "contradiction_type", "evidence", "explanation")

    def __init__(self) -> None:
        self.text_a: str = ""
        self.text_b: str = ""
        self.is_contradictory: bool = False
        self.confidence: float = 0.0
        self.contradiction_type: str = "none"  # negation, antonym, factual, none
        self.evidence: List[str] = []
        self.explanation: str = ""

    def to_dict(self) -> Dict:
        return {
            "text_a": self.text_a,
            "text_b": self.text_b,
            "is_contradictory": self.is_contradictory,
            "confidence": round(self.confidence, 3),
            "contradiction_type": self.contradiction_type,
            "evidence": list(self.evidence),
            "explanation": self.explanation,
        }


class ContradictionDetector:
    """Detects semantic contradictions between texts.

    Usage::

        detector = ContradictionDetector()
        r = detector.detect("AI jobs are increasing", "AI jobs are declining")
        print(r.is_contradictory, r.confidence)
    """

    def __init__(self) -> None:
        self._antonym_map = dict(_ANTONYM_MAP)
        self._negation_words = set(_NEGATION_WORDS)

    def detect(self, text_a: str, text_b: str) -> ContradictionResult:
        """Detect contradictions between two texts."""
        result = ContradictionResult()
        result.text_a = text_a
        result.text_b = text_b

        if not text_a or not text_b:
            return result

        words_a = set(self._tokenize(text_a))
        words_b = set(self._tokenize(text_b))

        # 1. Check for direct negation
        neg_result = self._check_negation(words_a, words_b, text_a, text_b)
        if neg_result:
            return neg_result

        # 2. Check for antonym pairs
        ant_result = self._check_antonyms(words_a, words_b, text_a, text_b)
        if ant_result:
            return ant_result

        # 3. Check for directional contradictions (same topic, opposite direction)
        dir_result = self._check_directional(words_a, words_b, text_a, text_b)
        if dir_result:
            return dir_result

        return result

    def detect_batch(self, texts: List[str]) -> List[ContradictionResult]:
        """Detect contradictions among all pairs in a list of texts."""
        results: List[ContradictionResult] = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                r = self.detect(texts[i], texts[j])
                if r.is_contradictory:
                    results.append(r)
        return results

    def has_contradiction(self, text_a: str, text_b: str, threshold: float = 0.5) -> bool:
        """Quick check if two texts contradict above a threshold."""
        r = self.detect(text_a, text_b)
        return r.is_contradictory and r.confidence >= threshold

    def find_contradictions(self, texts: List[str], threshold: float = 0.5) -> List[Tuple[int, int]]:
        """Find indices of contradictory text pairs."""
        contradictions: List[Tuple[int, int]] = []
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                if self.has_contradiction(texts[i], texts[j], threshold):
                    contradictions.append((i, j))
        return contradictions

    def add_antonym_pair(self, word_a: str, word_b: str) -> None:
        """Add a custom antonym pair."""
        self._antonym_map.setdefault(word_a.lower(), set()).add(word_b.lower())
        self._antonym_map.setdefault(word_b.lower(), set()).add(word_a.lower())

    # ── Private ──────────────────────────────────────────────────────

    def _check_negation(self, words_a: Set[str], words_b: Set[str],
                        text_a: str, text_b: str) -> Optional[ContradictionResult]:
        """Check for negation-based contradictions."""
        neg_a = words_a & self._negation_words
        neg_b = words_b & self._negation_words

        # If one has negation and the other doesn't, and they share content words
        shared = words_a & words_b
        content_words = shared - self._negation_words - {"the", "a", "an", "is", "are", "was"}

        if content_words and bool(neg_a) != bool(neg_b):
            r = ContradictionResult()
            r.text_a = text_a
            r.text_b = text_b
            r.is_contradictory = True
            r.confidence = 0.7 + min(0.2, len(content_words) * 0.05)
            r.contradiction_type = "negation"
            r.evidence = [f"Negation detected: {neg_a or neg_b}"]
            r.explanation = (
                f"Text A {'contains' if neg_a else 'lacks'} negation while "
                f"Text B {'contains' if neg_b else 'lacks'} negation. "
                f"Shared content: {', '.join(list(content_words)[:5])}"
            )
            return r

        return None

    def _check_antonyms(self, words_a: Set[str], words_b: Set[str],
                        text_a: str, text_b: str) -> Optional[ContradictionResult]:
        """Check for antonym-based contradictions."""
        found_pairs: List[Tuple[str, str]] = []

        for word in words_a:
            antonyms = self._antonym_map.get(word, set())
            overlap = antonyms & words_b
            if overlap:
                for ant in overlap:
                    found_pairs.append((word, ant))

        if found_pairs:
            r = ContradictionResult()
            r.text_a = text_a
            r.text_b = text_b
            r.is_contradictory = True
            r.confidence = min(0.95, 0.6 + len(found_pairs) * 0.1)
            r.contradiction_type = "antonym"
            r.evidence = [f"'{a}' vs '{b}'" for a, b in found_pairs]
            r.explanation = (
                f"Found {len(found_pairs)} antonym pair(s): "
                + ", ".join(f"'{a}' ↔ '{b}'" for a, b in found_pairs[:3])
            )
            return r

        return None

    def _check_directional(self, words_a: Set[str], words_b: Set[str],
                           text_a: str, text_b: str) -> Optional[ContradictionResult]:
        """Check for directional contradictions (increase vs decrease on same topic)."""
        direction_up = {"increase", "rise", "grow", "boost", "improve", "more", "higher", "up", "gain"}
        direction_down = {"decrease", "decline", "fall", "shrink", "reduce", "less", "lower", "down", "drop", "lose"}

        up_a = words_a & direction_up
        down_a = words_a & direction_down
        up_b = words_b & direction_up
        down_b = words_b & direction_down

        # One says up, other says down
        if (up_a and down_b) or (down_a and up_b):
            shared_content = (words_a & words_b) - direction_up - direction_down - {"the", "a", "is", "are"}
            if shared_content or self._has_similar_topic(words_a, words_b):
                r = ContradictionResult()
                r.text_a = text_a
                r.text_b = text_b
                r.is_contradictory = True
                r.confidence = 0.75
                r.contradiction_type = "directional"
                r.evidence = [
                    f"Up: {up_a | up_b}",
                    f"Down: {down_a | down_b}",
                ]
                r.explanation = (
                    f"Opposite directional signals detected. "
                    f"Text A: {'↑' if up_a else '↓'}, Text B: {'↑' if up_b else '↓'}"
                )
                return r

        return None

    def _has_similar_topic(self, words_a: Set[str], words_b: Set[str]) -> bool:
        """Check if two word sets share enough topic overlap."""
        shared = words_a & words_b
        return len(shared) >= 2

    # Common word normalizations
    _FORM_MAP: Dict[str, str] = {
        "increasing": "increase", "decreasing": "decrease",
        "declining": "decline", "rising": "rise", "falling": "fall",
        "growing": "grow", "shrinking": "shrink", "boosting": "boost",
        "improving": "improve", "worsening": "worsen", "reducing": "reduce",
        "surging": "surge", "expanding": "expand", "dropping": "drop",
        "winning": "win", "losing": "lose", "succeeding": "succeed",
        "failing": "fail",
        "loving": "love", "hating": "hate", "starting": "start",
        "stopping": "stop", "opening": "open", "closing": "close",
        "building": "build", "destroying": "destroy", "accepting": "accept",
        "rejecting": "reject", "enabling": "enable", "disabling": "disable",
        "increases": "increase", "decreases": "decrease",
        "declines": "decline", "rises": "rise", "falls": "fall",
        "grows": "grow", "shrinks": "shrink", "boosts": "boost",
        "improves": "improve", "worsens": "worsen", "reduces": "reduce",
        "surges": "surge", "expands": "expand", "drops": "drop",
        "wins": "win", "loses": "lose", "succeeds": "succeed",
        "fails": "fail", "loves": "love", "hates": "hate",
        "increased": "increase", "decreased": "decrease",
        "declined": "decline", "rose": "rise", "fell": "fall",
        "grew": "grow", "shrank": "shrink", "boosted": "boost",
        "improved": "improve", "worsened": "worsen", "reduced": "reduce",
        "surged": "surge", "expanded": "expand", "dropped": "drop",
    }

    @staticmethod
    def _lemmatize(word: str) -> str:
        """Basic English lemmatizer using lookup + suffix stripping."""
        w = word.lower()
        if w in ContradictionDetector._FORM_MAP:
            return ContradictionDetector._FORM_MAP[w]
        for suffix, replacement in [
            ("ization", "ize"), ("isation", "ise"),
            ("fulness", "ful"), ("ousness", "ous"),
            ("ments", "ment"), ("ating", "ate"),
            ("ying", "y"), ("ing", ""), ("ness", ""),
            ("ment", ""), ("able", ""), ("ible", ""),
            ("tion", "t"), ("sion", "s"),
            ("ally", "al"), ("ely", "e"), ("ily", "y"),
            ("ies", "y"), ("ves", "f"),
            ("ated", "ate"), ("ened", "e"),
            ("ized", "ize"), ("ised", "ise"),
            ("less", ""), ("ful", ""),
            ("ous", ""), ("ive", ""),
            ("ers", "er"), ("est", ""),
            ("er", ""), ("ed", ""),
            ("ly", ""),
            ("s", ""),
        ]:
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                base = w[:-len(suffix)] + replacement
                if len(base) >= 3:
                    return base
        return w

    def _tokenize(self, text: str) -> List[str]:
        return [self._lemmatize(w) for w in re.findall(r"[a-zA-Z0-9\u0600-\u06FF]+", text)
                if len(w) >= 2]
