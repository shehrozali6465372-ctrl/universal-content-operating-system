"""Decision Engine - Makes decisions by evaluating options against criteria."""
from __future__ import annotations
from typing import Dict, List, Optional


class DecisionOption:
    """A decision option with scores."""
    __slots__ = ("name", "scores", "metadata", "overall_score")

    def __init__(self, name: str = "", metadata: Optional[Dict] = None):
        self.name = name
        self.scores: Dict[str, float] = {}
        self.metadata = metadata or {}
        self.overall_score = 0.0

    def to_dict(self) -> Dict:
        return {"name": self.name, "scores": {k: round(v, 3) for k, v in self.scores.items()},
                "overall_score": round(self.overall_score, 3), "metadata": dict(self.metadata)}


class DecisionResult:
    """Result of decision making."""
    __slots__ = ("chosen_option", "all_options", "reasoning", "confidence", "alternatives")

    def __init__(self) -> None:
        self.chosen_option: Optional[DecisionOption] = None
        self.all_options: List[DecisionOption] = []
        self.reasoning: List[str] = []
        self.confidence = 0.0
        self.alternatives: List[DecisionOption] = []

    def to_dict(self) -> Dict:
        return {
            "chosen": self.chosen_option.to_dict() if self.chosen_option else None,
            "alternatives": [o.to_dict() for o in self.alternatives[:3]],
            "reasoning": list(self.reasoning),
            "confidence": round(self.confidence, 3),
            "total_options": len(self.all_options),
        }


class DecisionEngine:
    """Makes decisions by weighted scoring of options."""

    def __init__(self) -> None:
        self._criteria_weights: Dict[str, float] = {}

    def set_weights(self, weights: Dict[str, float]) -> None:
        total = sum(weights.values())
        self._criteria_weights = {k: v / total for k, v in weights.items()} if total > 0 else weights

    def decide(self, options: List[DecisionOption], reasoning: bool = True) -> DecisionResult:
        result = DecisionResult()
        result.all_options = options

        if not options:
            return result

        for option in options:
            weighted = 0.0
            total_weight = 0.0
            for criterion, score in option.scores.items():
                w = self._criteria_weights.get(criterion, 1.0 / max(len(option.scores), 1))
                weighted += score * w
                total_weight += w
            option.overall_score = weighted / total_weight if total_weight > 0 else 0.0

        sorted_options = sorted(options, key=lambda o: o.overall_score, reverse=True)
        result.chosen_option = sorted_options[0]
        result.alternatives = sorted_options[1:]

        if len(sorted_options) > 1:
            gap = sorted_options[0].overall_score - sorted_options[1].overall_score
            result.confidence = min(1.0, 0.5 + gap * 2)
        else:
            result.confidence = 0.5

        if reasoning:
            result.reasoning.append(
                f"Chose '{sorted_options[0].name}' with score {sorted_options[0].overall_score:.3f}"
            )
            if self._criteria_weights:
                top_criterion = max(sorted_options[0].scores, key=lambda c: sorted_options[0].scores[c] * self._criteria_weights.get(c, 1.0))
                result.reasoning.append(f"Strongest factor: {top_criterion}")

        return result

    def decide_simple(self, options: Dict[str, float]) -> str:
        if not options:
            return ""
        return max(options, key=options.get)
