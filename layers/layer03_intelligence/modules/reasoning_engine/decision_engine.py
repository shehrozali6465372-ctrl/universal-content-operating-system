"""Decision Engine — multi-factor decision making with scoring."""

from typing import Dict, List, Optional


class DecisionOption:
    def __init__(self, name: str, scores: Optional[Dict[str, float]] = None):
        self.name = name
        self.scores = scores or {}
        self.weighted_score = 0.0

    def to_dict(self) -> dict:
        return {"name": self.name, "scores": dict(self.scores), "weighted_score": self.weighted_score}


class DecisionEngine:
    def __init__(self, weights: Optional[Dict[str, float]] = None):
        self._weights = weights or {"relevance": 0.3, "confidence": 0.3, "opportunity": 0.2, "risk": 0.2}

    def decide(self, options: List[DecisionOption], context: Optional[Dict] = None) -> Optional[DecisionOption]:
        if not options:
            return None
        for opt in options:
            opt.weighted_score = sum(
                opt.scores.get(factor, 0.0) * weight
                for factor, weight in self._weights.items()
            )
        return max(options, key=lambda o: o.weighted_score)

    def rank(self, options: List[DecisionOption]) -> List[DecisionOption]:
        for opt in options:
            opt.weighted_score = sum(
                opt.scores.get(factor, 0.0) * weight
                for factor, weight in self._weights.items()
            )
        return sorted(options, key=lambda o: -o.weighted_score)

    def set_weights(self, weights: Dict[str, float]):
        self._weights = weights
