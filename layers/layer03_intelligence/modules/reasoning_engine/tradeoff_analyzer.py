"""Tradeoff Analyzer - Analyzes tradeoffs between competing objectives."""
from __future__ import annotations
from typing import Dict, List, Optional


class TradeoffDimension:
    """A single dimension of tradeoff analysis."""
    __slots__ = ("name", "value", "weight", "importance")

    def __init__(self, name: str = "", value: float = 0.0, weight: float = 1.0, importance: str = "medium"):
        self.name = name
        self.value = value
        self.weight = weight
        self.importance = importance

    def to_dict(self) -> Dict:
        return {"name": self.name, "value": round(self.value, 3),
                "weight": round(self.weight, 3), "importance": self.importance}


class TradeoffResult:
    """Result of tradeoff analysis."""
    __slots__ = ("dimensions", "overall_score", "best_option", "weakest_dimension",
                 "recommendations")

    def __init__(self) -> None:
        self.dimensions: List[TradeoffDimension] = []
        self.overall_score = 0.0
        self.best_option = ""
        self.weakest_dimension = ""
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "dimensions": [d.to_dict() for d in self.dimensions],
            "overall_score": round(self.overall_score, 3),
            "best_option": self.best_option,
            "weakest_dimension": self.weakest_dimension,
            "recommendations": list(self.recommendations),
        }


class TradeoffAnalyzer:
    """Analyzes tradeoffs across multiple competing dimensions."""

    def analyze(self, options: Dict[str, Dict[str, float]],
                weights: Optional[Dict[str, float]] = None) -> TradeoffResult:
        result = TradeoffResult()
        if not options:
            return result

        all_criteria = set()
        for scores in options.values():
            all_criteria.update(scores.keys())

        weights = weights or {c: 1.0 for c in all_criteria}
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        best_name = ""
        best_score = -1

        for option_name, scores in options.items():
            score = sum(scores.get(c, 0) * weights.get(c, 0) for c in all_criteria)
            if score > best_score:
                best_score = score
                best_name = option_name

        result.best_option = best_name
        result.overall_score = best_score

        # Find weakest dimension
        if best_name in options:
            best_scores = options[best_name]
            if best_scores:
                weakest = min(best_scores, key=best_scores.get)
                result.weakest_dimension = weakest
                result.recommendations.append(
                    f"Consider improving '{weakest}' (current: {best_scores[weakest]:.2f})"
                )

        return result
