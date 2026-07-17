"""Feature Extractor — Extract features from content for engagement prediction."""
from __future__ import annotations
from typing import Any, Dict, List


class ContentFeatures:
    """Extracted features from a piece of content."""

    __slots__ = ("word_count", "sentence_count", "hashtag_count", "mention_count",
                 "emoji_count", "url_count", "question_count", "exclamation_count",
                 "avg_word_length", "readability_estimate", "has_hook", "has_cta",
                 "content_type", "platform")

    def __init__(self) -> None:
        self.word_count: int = 0
        self.sentence_count: int = 0
        self.hashtag_count: int = 0
        self.mention_count: int = 0
        self.emoji_count: int = 0
        self.url_count: int = 0
        self.question_count: int = 0
        self.exclamation_count: int = 0
        self.avg_word_length: float = 0.0
        self.readability_estimate: float = 0.0
        self.has_hook: bool = False
        self.has_cta: bool = False
        self.content_type: str = ""
        self.platform: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "hashtag_count": self.hashtag_count,
            "mention_count": self.mention_count,
            "emoji_count": self.emoji_count,
            "url_count": self.url_count,
            "question_count": self.question_count,
            "exclamation_count": self.exclamation_count,
            "avg_word_length": round(self.avg_word_length, 2),
            "readability_estimate": round(self.readability_estimate, 3),
            "has_hook": self.has_hook,
            "has_cta": self.has_cta,
            "content_type": self.content_type,
            "platform": self.platform,
        }


class FeatureExtractor:
    """Extract engagement-relevant features from content."""

    HOOK_WORDS = {"did you know", "here's the thing", "imagine", "what if",
                  "discover", "secret", "proven", "ultimate", "free", "exclusive"}
    CTA_WORDS = {"comment", "share", "follow", "subscribe", "click", "join",
                 "sign up", "get started", "try now", "learn more"}

    def extract(self, content: str, platform: str = "",
                content_type: str = "") -> ContentFeatures:
        features = ContentFeatures()
        features.platform = platform
        features.content_type = content_type

        if not content or not content.strip():
            return features

        words = content.split()
        features.word_count = len(words)
        features.sentence_count = max(1, content.count(".") + content.count("!") + content.count("?"))
        features.hashtag_count = content.count("#")
        features.mention_count = content.count("@")
        features.url_count = content.lower().count("http")
        features.question_count = content.count("?")
        features.exclamation_count = content.count("!")

        emojis = sum(1 for c in content if ord(c) > 0x2600 and ord(c) not in range(0x2E80, 0x2F00))
        features.emoji_count = emojis

        if words:
            features.avg_word_length = sum(len(w) for w in words) / len(words)

        features.readability_estimate = self._estimate_readability(features)
        features.has_hook = self._detect_hook(content)
        features.has_cta = self._detect_cta(content)

        return features

    def extract_batch(self, contents: List[str], platform: str = "",
                      content_type: str = "") -> List[ContentFeatures]:
        return [self.extract(c, platform, content_type) for c in contents]

    def _estimate_readability(self, f: ContentFeatures) -> float:
        score = 1.0
        if f.avg_word_length > 6:
            score -= 0.15
        avg_sent = f.word_count / max(1, f.sentence_count)
        if avg_sent > 20:
            score -= 0.2
        elif avg_sent < 5:
            score -= 0.1
        return round(max(0.0, min(1.0, score)), 3)

    def _detect_hook(self, content: str) -> bool:
        lower = content.lower()[:200]
        return any(h in lower for h in self.HOOK_WORDS)

    def _detect_cta(self, content: str) -> bool:
        lower = content.lower()
        return any(c in lower for c in self.CTA_WORDS)

    def to_feature_vector(self, features: ContentFeatures) -> List[float]:
        """Convert features to a numeric vector for model consumption."""
        return [
            float(features.word_count),
            float(features.sentence_count),
            float(features.hashtag_count),
            float(features.mention_count),
            float(features.emoji_count),
            float(features.url_count),
            float(features.question_count),
            float(features.exclamation_count),
            features.avg_word_length,
            features.readability_estimate,
            1.0 if features.has_hook else 0.0,
            1.0 if features.has_cta else 0.0,
        ]
