"""Virality Predictor — predicts viral potential of content."""
from typing import Dict, Optional

class ViralityResult:
    __slots__ = ("virality_score", "shareability", "emotional_appeal", "novelty")
    def __init__(self):
        self.virality_score = 0.0
        self.shareability = 0.0
        self.emotional_appeal = 0.0
        self.novelty = 0.0
    def to_dict(self) -> dict:
        return {k: getattr(self, k) for k in self.__slots__}

class ViralityPredictor:
    EMOTIONAL_WORDS = {"amazing", "incredible", "shocking", "unbelievable", "must", "never", "always", "secret", "revealed", "exclusive"}
    def predict(self, text: str, engagement_data: Optional[Dict] = None) -> ViralityResult:
        result = ViralityResult()
        words = set(text.lower().split())
        result.emotional_appeal = min(1.0, len(words & self.EMOTIONAL_WORDS) / 3)
        result.shareability = min(1.0, (1.0 if "?" in text else 0.5) * (1.0 if len(text) < 300 else 0.7))
        result.novelty = min(1.0, len(set(text.lower().split())) / max(len(text.split()), 1))
        result.virality_score = round(
            result.emotional_appeal * 0.4 + result.shareability * 0.35 + result.novelty * 0.25, 3
        )
        return result
