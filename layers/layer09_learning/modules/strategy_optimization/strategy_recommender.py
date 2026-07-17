"""Strategy Recommender — Recommend strategies based on performance data."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile

_SR_COUNTER = itertools.count(1)


class StrategyRecommendation:
    """A recommended strategy action."""

    __slots__ = ("recommendation_id", "recommendation_type", "priority",
                 "strategy_id", "description", "expected_impact",
                 "confidence", "reasoning")

    def __init__(self, recommendation_type: str = "optimize", priority: str = "medium") -> None:
        self.recommendation_id: str = f"sr_{next(_SR_COUNTER)}"
        self.recommendation_type = recommendation_type
        self.priority = priority
        self.strategy_id: str = ""
        self.description: str = ""
        self.expected_impact: str = "low"
        self.confidence: float = 0.5
        self.reasoning: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "recommendation_type": self.recommendation_type,
            "priority": self.priority,
            "strategy_id": self.strategy_id,
            "description": self.description,
            "expected_impact": self.expected_impact,
            "confidence": round(self.confidence, 3),
        }


class StrategyRecommender:
    """Recommend strategy actions based on performance analysis."""

    def __init__(self) -> None:
        self._recommendations: List[StrategyRecommendation] = []

    def recommend(self, strategies: List[StrategyProfile]) -> List[StrategyRecommendation]:
        self._recommendations.clear()
        if not strategies:
            return self._recommendations
        self._recommend_scaling(strategies)
        self._recommend_optimization(strategies)
        self._recommend_deprecation(strategies)
        self._recommend_new_platforms(strategies)
        return list(self._recommendations)

    def _recommend_scaling(self, strategies: List[StrategyProfile]) -> None:
        for s in strategies:
            if s.effective_score > 0.7 and s.usage_count >= 3:
                rec = StrategyRecommendation("scale", "high")
                rec.strategy_id = s.strategy_id
                rec.description = f"Scale strategy '{s.name}' (score: {s.effective_score})"
                rec.expected_impact = "high"
                rec.confidence = min(1.0, s.effective_score)
                rec.reasoning = f"High effectiveness ({s.effective_score}) with sufficient data ({s.usage_count} uses)"
                self._recommendations.append(rec)

    def _recommend_optimization(self, strategies: List[StrategyProfile]) -> None:
        for s in strategies:
            if 0.3 <= s.effective_score <= 0.7 and s.usage_count >= 3:
                rec = StrategyRecommendation("optimize", "medium")
                rec.strategy_id = s.strategy_id
                rec.description = f"Optimize strategy '{s.name}' (score: {s.effective_score})"
                rec.expected_impact = "medium"
                rec.confidence = 0.6
                rec.reasoning = "Moderate performance with room for improvement"
                self._recommendations.append(rec)

    def _recommend_deprecation(self, strategies: List[StrategyProfile]) -> None:
        for s in strategies:
            if s.effective_score < 0.3 and s.usage_count >= 5:
                rec = StrategyRecommendation("deprecate", "medium")
                rec.strategy_id = s.strategy_id
                rec.description = f"Deprecate strategy '{s.name}' (score: {s.effective_score})"
                rec.expected_impact = "low"
                rec.confidence = 0.7
                rec.reasoning = f"Consistently low performance ({s.effective_score}) over {s.usage_count} uses"
                self._recommendations.append(rec)

    def _recommend_new_platforms(self, strategies: List[StrategyProfile]) -> None:
        high_platforms: Dict[str, List[float]] = {}
        for s in strategies:
            for p in s.target_platforms:
                high_platforms.setdefault(p, []).append(s.effective_score)
        best_platforms = [
            (p, sum(scores) / len(scores))
            for p, scores in high_platforms.items()
            if len(scores) >= 2
        ]
        best_platforms.sort(key=lambda x: x[1], reverse=True)
        for s in strategies:
            if not s.target_platforms and best_platforms:
                rec = StrategyRecommendation("expand", "medium")
                rec.strategy_id = s.strategy_id
                rec.description = f"Add top platforms: {', '.join(p for p, _ in best_platforms[:3])}"
                rec.expected_impact = "medium"
                rec.confidence = 0.6
                self._recommendations.append(rec)

    def get_recommendations(self, rec_type: str = "", priority: str = "") -> List[StrategyRecommendation]:
        result = self._recommendations
        if rec_type:
            result = [r for r in result if r.recommendation_type == rec_type]
        if priority:
            result = [r for r in result if r.priority == priority]
        return result

    @property
    def recommendation_count(self) -> int:
        return len(self._recommendations)
