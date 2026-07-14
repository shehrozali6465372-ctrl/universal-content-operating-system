"""Confidence Reasoner - Explains and reasons about confidence scores."""
from __future__ import annotations
from typing import Dict, List, Optional


class ConfidenceBreakdown:
    """Detailed breakdown of a confidence score."""
    __slots__ = ("overall", "components", "factors", "risk_level", "explanation")

    def __init__(self) -> None:
        self.overall = 0.0
        self.components: Dict[str, float] = {}
        self.factors: List[str] = []
        self.risk_level = "medium"
        self.explanation = ""

    def to_dict(self) -> Dict:
        return {
            "overall": round(self.overall, 3),
            "components": {k: round(v, 3) for k, v in self.components.items()},
            "factors": list(self.factors),
            "risk_level": self.risk_level,
            "explanation": self.explanation,
        }


class ConfidenceReasoner:
    """Reasons about confidence scores and provides explanations."""

    def reason(self, components: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> ConfidenceBreakdown:
        result = ConfidenceBreakdown()
        result.components = dict(components)

        if not components:
            return result

        weights = weights or {k: 1.0 for k in components}
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        result.overall = sum(components.get(k, 0) * weights.get(k, 0) for k in components)

        # Analyze factors
        high = [k for k, v in components.items() if v >= 0.7]
        low = [k for k, v in components.items() if v < 0.3]
        mid = [k for k, v in components.items() if 0.3 <= v < 0.7]

        if high:
            result.factors.append(f"Strong: {', '.join(high)}")
        if mid:
            result.factors.append(f"Moderate: {', '.join(mid)}")
        if low:
            result.factors.append(f"Weak: {', '.join(low)}")

        # Risk level
        if result.overall >= 0.7:
            result.risk_level = "low"
        elif result.overall >= 0.4:
            result.risk_level = "medium"
        else:
            result.risk_level = "high"

        # Explanation
        if result.overall >= 0.7:
            result.explanation = f"High confidence ({result.overall:.0%}) based on strong signals"
        elif result.overall >= 0.4:
            result.explanation = f"Moderate confidence ({result.overall:.0%}) - some uncertainty remains"
        else:
            result.explanation = f"Low confidence ({result.overall:.0%}) - significant uncertainty"

        return result
