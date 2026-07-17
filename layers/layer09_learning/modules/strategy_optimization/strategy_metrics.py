"""Strategy Metrics — Track strategy optimization performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class StrategyMetrics:
    """Track metrics across strategy optimization cycles."""

    def __init__(self) -> None:
        self._total_optimizations: int = 0
        self._successful_optimizations: int = 0
        self._total_analyses: int = 0
        self._total_comparisons: int = 0
        self._total_recommendations: int = 0
        self._optimization_scores: List[float] = []
        self._improvement_rates: List[float] = []

    def record_optimization(self, score: float = 0.0, improved: bool = False) -> None:
        self._total_optimizations += 1
        if improved:
            self._successful_optimizations += 1
        if score > 0:
            self._optimization_scores.append(score)

    def record_analysis(self) -> None:
        self._total_analyses += 1

    def record_comparison(self, improvement_pct: float = 0.0) -> None:
        self._total_comparisons += 1
        if improvement_pct != 0:
            self._improvement_rates.append(improvement_pct)

    def record_recommendation(self, count: int = 1) -> None:
        self._total_recommendations += count

    def get_optimization_success_rate(self) -> float:
        if self._total_optimizations == 0:
            return 0.0
        return round(self._successful_optimizations / self._total_optimizations, 3)

    def get_avg_optimization_score(self) -> float:
        if not self._optimization_scores:
            return 0.0
        return round(sum(self._optimization_scores) / len(self._optimization_scores), 3)

    def get_avg_improvement_rate(self) -> float:
        if not self._improvement_rates:
            return 0.0
        return round(sum(self._improvement_rates) / len(self._improvement_rates), 2)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_optimizations": self._total_optimizations,
            "successful_optimizations": self._successful_optimizations,
            "optimization_success_rate": self.get_optimization_success_rate(),
            "total_analyses": self._total_analyses,
            "total_comparisons": self._total_comparisons,
            "total_recommendations": self._total_recommendations,
            "avg_optimization_score": self.get_avg_optimization_score(),
            "avg_improvement_rate": self.get_avg_improvement_rate(),
        }

    def reset(self) -> None:
        self._total_optimizations = 0
        self._successful_optimizations = 0
        self._total_analyses = 0
        self._total_comparisons = 0
        self._total_recommendations = 0
        self._optimization_scores.clear()
        self._improvement_rates.clear()
