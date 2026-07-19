"""ScoringEngine — multi-factor scoring and ranking."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ScoreFactor:
    __slots__ = ("name", "weight", "value", "metadata")

    def __init__(self, name: str, weight: float = 1.0, value: float = 0.0) -> None:
        self.name = name
        self.weight = weight
        self.value = value
        self.metadata: Dict[str, Any] = {}


class ScoringEngine:
    def __init__(self) -> None:
        self._factors: Dict[str, ScoreFactor] = {}
        self._weights: Dict[str, float] = {}

    def add_factor(self, name: str, weight: float = 1.0) -> None:
        self._factors[name] = ScoreFactor(name, weight)
        self._weights[name] = weight

    def set_weight(self, name: str, weight: float) -> None:
        self._weights[name] = weight
        if name in self._factors:
            self._factors[name].weight = weight

    def score(self, values: Dict[str, float]) -> float:
        total_weight = sum(self._weights.get(k, 1.0) for k in values if k in self._weights or True)
        weighted_sum = sum(values.get(k, 0) * self._weights.get(k, 1.0) for k in values)
        return round(weighted_sum / max(total_weight, 0.01), 4)

    def rank(self, items: List[Dict[str, Any]], score_key: str = "score") -> List[Dict[str, Any]]:
        return sorted(items, key=lambda x: -x.get(score_key, 0))

    def normalize(self, values: List[float]) -> List[float]:
        if not values:
            return []
        min_v = min(values)
        max_v = max(values)
        if max_v == min_v:
            return [0.5] * len(values)
        return [round((v - min_v) / (max_v - min_v), 4) for v in values]

    def list_factors(self) -> List[Dict[str, Any]]:
        return [{"name": f.name, "weight": f.weight} for f in self._factors.values()]
