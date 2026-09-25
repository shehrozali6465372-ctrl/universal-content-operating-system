"""Decision Engine - Makes decisions by evaluating options against criteria."""
from __future__ import annotations
from math import isfinite
from threading import RLock
from typing import Dict, List, Optional


class DecisionOption:
    """A decision option with scores."""
    __slots__ = ("name", "scores", "metadata", "overall_score")

    def __init__(self, name: str = "", metadata: Optional[Dict] = None):
        self.name = name
        self.scores: Dict[str, float] = {}
        if metadata is not None and not isinstance(metadata, dict):
            raise TypeError("metadata must be a dict")
        self.metadata = dict(metadata or {})
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
        self._lock = RLock()

    def set_weights(self, weights: Dict[str, float]) -> None:
        if not isinstance(weights, dict) or any(not isinstance(v, (int, float)) or not isfinite(v) or v < 0 for v in weights.values()):
            raise ValueError("weights must be finite non-negative numbers")
        total = sum(weights.values())
        with self._lock:
            self._criteria_weights = {k: v / total for k, v in weights.items()} if total > 0 else {}

    def decide(self, options: List[DecisionOption], reasoning: bool = True) -> DecisionResult:
        if not isinstance(options, list):
            raise TypeError("options must be a list")
        with self._lock:
            return self._decide_locked(options, reasoning)

    def _decide_locked(self, options: List[DecisionOption], reasoning: bool = True) -> DecisionResult:
        result = DecisionResult()
        result.all_options = options

        if not options:
            return result

        for option in options:
            if not isinstance(option, DecisionOption):
                raise TypeError("options must contain DecisionOption instances")
            if any(not isinstance(v, (int, float)) or not isfinite(v) for v in option.scores.values()):
                raise ValueError("option scores must be finite numbers")
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
