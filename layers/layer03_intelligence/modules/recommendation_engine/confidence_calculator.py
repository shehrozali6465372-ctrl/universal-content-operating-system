"""Confidence Calculator - Calculates recommendation confidence with breakdown."""
from __future__ import annotations
from typing import Dict


class RecConfidence:
    __slots__ = ("overall", "components", "risk_level", "explanation")
    def __init__(self) -> None:
        self.overall = 0.0
        self.components: Dict[str, float] = {}
        self.risk_level = "medium"
        self.explanation = ""
    def to_dict(self) -> Dict:
        return {"overall": round(self.overall, 3), "components": {k: round(v, 3) for k, v in self.components.items()},
                "risk_level": self.risk_level, "explanation": self.explanation}


class ConfidenceCalculator:
    def __init__(self, weights: Dict[str, float] = None) -> None:
        self._weights = weights or {"trend": 0.25, "audience": 0.2, "competition": 0.2, "knowledge": 0.2, "novelty": 0.15}

    def calculate(self, signals: Dict[str, float]) -> RecConfidence:
        result = RecConfidence()
        result.components = dict(signals)
        if not signals:
            return result

        total = sum(signals.get(k, 0) * self._weights.get(k, 0.1) for k in signals)
        w_sum = sum(self._weights.get(k, 0.1) for k in signals)
        result.overall = total / w_sum if w_sum > 0 else 0.5

        if result.overall >= 0.7: result.risk_level = "low"
        elif result.overall >= 0.4: result.risk_level = "medium"
        else: result.risk_level = "high"

        weak = [k for k, v in signals.items() if v < 0.3]
        if weak:
            result.explanation = f"Confidence: {result.overall:.0%}. Weak: {', '.join(weak)}"
        else:
            result.explanation = f"Confidence: {result.overall:.0%}. All signals acceptable."
        return result
