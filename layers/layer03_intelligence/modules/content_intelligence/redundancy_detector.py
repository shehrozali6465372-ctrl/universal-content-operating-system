"""Redundancy Detector - Detects repetitive content."""
from __future__ import annotations
from typing import Dict, List


class RedundancyResult:
    __slots__ = ("redundancy_score", "repetitive_phrases", "unique_ratio", "recommendations")

    def __init__(self) -> None:
        self.redundancy_score = 0.0
        self.repetitive_phrases: List[str] = []
        self.unique_ratio = 1.0
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict:
        return {"redundancy_score": round(self.redundancy_score, 3),
                "repetitive_phrases": list(self.repetitive_phrases),
                "unique_ratio": round(self.unique_ratio, 3),
                "recommendations": list(self.recommendations)}


class RedundancyDetector:
    def detect(self, content: str, window: int = 3) -> RedundancyResult:
        result = RedundancyResult()
        words = content.lower().split()
        if len(words) < window:
            return result

        # Find repeated n-grams
        ngrams: Dict[str, int] = {}
        for i in range(len(words) - window + 1):
            gram = " ".join(words[i:i + window])
            ngrams[gram] = ngrams.get(gram, 0) + 1

        repeated = {g: c for g, c in ngrams.items() if c > 1}
        result.repetitive_phrases = list(repeated.keys())[:5]
        result.redundancy_score = min(1.0, sum(repeated.values()) / max(len(words), 1))
        result.unique_ratio = 1.0 - result.redundancy_score

        if result.redundancy_score > 0.3:
            result.recommendations.append("Reduce repetitive phrases")
        return result
