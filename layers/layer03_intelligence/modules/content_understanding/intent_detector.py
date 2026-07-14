"""
Intent Detector
Classifies the intent/purpose of content.
"""

from typing import Dict, List


# Intent patterns: keywords mapped to intent types
INTENT_PATTERNS: Dict[str, List[str]] = {
    "informative": ["how", "what", "why", "guide", "learn", "explain", "tutorial", "tip"],
    "promotional": ["buy", "discount", "offer", "sale", "deal", "free", "limited", "premium"],
    "engagement": ["question", "poll", "guess", "think", "opinion", "agree", "comment", "share"],
    "news": ["breaking", "announce", "launch", "release", "update", "report", "develop"],
    "educational": ["course", "learn", "study", "research", "teach", "training", "skill"],
    "entertainment": ["funny", "meme", "joke", "humor", "laugh", "viral", "trending"],
    "inspirational": ["motivation", "success", "achieve", "dream", "goal", "inspire", "growth"],
    "emotional": ["feel", "love", "heart", "emotional", "touching", "amazing", "beautiful"],
}


class IntentResult:
    """Result of intent detection."""

    __slots__ = ("primary_intent", "confidence", "all_intents")

    def __init__(self, primary_intent: str = "unknown", confidence: float = 0.0):
        self.primary_intent = primary_intent
        self.confidence = confidence
        self.all_intents: Dict[str, float] = {}

    def to_dict(self) -> dict:
        return {
            "primary_intent": self.primary_intent,
            "confidence": self.confidence,
            "all_intents": dict(self.all_intents),
        }


class IntentDetector:
    """Detects the intent/purpose of content."""

    def __init__(self, min_confidence: float = 0.1):
        self.min_confidence = min_confidence
        self._patterns = dict(INTENT_PATTERNS)

    def detect(self, text: str) -> IntentResult:
        """Detect the primary intent of the text."""
        words = set(text.lower().split())
        scores: Dict[str, float] = {}

        for intent, keywords in self._patterns.items():
            matches = len(words.intersection(set(keywords)))
            if matches > 0:
                scores[intent] = round(matches / len(keywords), 3)

        if not scores:
            return IntentResult("unknown", 0.0)

        primary = max(scores, key=scores.get)
        result = IntentResult(primary, scores[primary])
        result.all_intents = dict(sorted(scores.items(), key=lambda x: -x[1]))
        return result

    def detect_batch(self, texts: List[str]) -> List[IntentResult]:
        """Detect intent for multiple texts."""
        return [self.detect(t) for t in texts]

    def get_dominant_intent(self, texts: List[str]) -> IntentResult:
        """Get the most common intent across multiple texts."""
        results = self.detect_batch(texts)
        intent_counts: Dict[str, List[float]] = {}
        for r in results:
            if r.primary_intent not in intent_counts:
                intent_counts[r.primary_intent] = []
            intent_counts[r.primary_intent].append(r.confidence)

        if not intent_counts:
            return IntentResult("unknown", 0.0)

        dominant = max(intent_counts, key=lambda k: len(intent_counts[k]))
        avg_conf = sum(intent_counts[dominant]) / len(intent_counts[dominant])
        return IntentResult(dominant, round(avg_conf, 3))

    def add_pattern(self, intent: str, keywords: List[str]):
        """Add or update intent patterns."""
        self._patterns[intent] = keywords
