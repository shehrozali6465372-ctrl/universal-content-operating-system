"""Content Confidence - Confidence scoring for content analysis."""
from __future__ import annotations
from typing import Dict


class ContentConfidenceResult:
    __slots__ = ("overall", "components", "risk_level", "explanation")

    def __init__(self) -> None:
        self.overall = 0.0
        self.components: Dict[str, float] = {}
        self.risk_level = "medium"
        self.explanation = ""

    def to_dict(self) -> Dict:
        return {"overall": round(self.overall, 3),
                "components": {k: round(v, 3) for k, v in self.components.items()},
                "risk_level": self.risk_level, "explanation": self.explanation}


class ContentConfidence:
    def calculate(self, scores: Dict[str, float]) -> ContentConfidenceResult:
        result = ContentConfidenceResult()
        result.components = dict(scores)
        if not scores:
            return result

        weights = {"quality": 0.25, "readability": 0.15, "engagement": 0.2,
                   "novelty": 0.15, "relevance": 0.15, "virality": 0.1}
        total = sum(scores.get(k, 0) * weights.get(k, 0.1) for k in scores)
        weight_sum = sum(weights.get(k, 0.1) for k in scores)
        result.overall = total / weight_sum if weight_sum > 0 else 0.5

        if result.overall >= 0.7: result.risk_level = "low"
        elif result.overall >= 0.4: result.risk_level = "medium"
        else: result.risk_level = "high"

        weak = [k for k, v in scores.items() if v < 0.4]
        if weak:
            result.explanation = f"Confidence: {result.overall:.0%}. Weak areas: {', '.join(weak)}"
        else:
            result.explanation = f"Confidence: {result.overall:.0%}. All dimensions acceptable."
        return result
