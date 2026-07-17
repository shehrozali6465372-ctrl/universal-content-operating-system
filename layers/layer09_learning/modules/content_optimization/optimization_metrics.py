"""Optimization Metrics — Track optimization performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class OptimizationMetrics:
    """Track metrics across content optimization operations."""

    def __init__(self) -> None:
        self._total_optimizations: int = 0
        self._total_suggestions: int = 0
        self._total_variants: int = 0
        self._accepted_variants: int = 0
        self._improvement_scores: List[float] = []
        self._acceptance_scores: List[float] = []

    def record_optimization(self, improvement: float = 0.0, accepted: bool = False) -> None:
        self._total_optimizations += 1
        self._total_variants += 1
        if improvement > 0:
            self._improvement_scores.append(improvement)
        if accepted:
            self._accepted_variants += 1

    def record_suggestions(self, count: int = 0) -> None:
        self._total_suggestions += count

    def record_variant(self) -> None:
        self._total_variants += 1

    def get_acceptance_rate(self) -> float:
        if self._total_variants == 0:
            return 0.0
        return round(self._accepted_variants / self._total_variants, 3)

    def get_avg_improvement(self) -> float:
        if not self._improvement_scores:
            return 0.0
        return round(sum(self._improvement_scores) / len(self._improvement_scores), 3)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_optimizations": self._total_optimizations,
            "total_suggestions": self._total_suggestions,
            "total_variants": self._total_variants,
            "accepted_variants": self._accepted_variants,
            "acceptance_rate": self.get_acceptance_rate(),
            "avg_improvement": self.get_avg_improvement(),
        }

    def reset(self) -> None:
        self._total_optimizations = 0
        self._total_suggestions = 0
        self._total_variants = 0
        self._accepted_variants = 0
        self._improvement_scores.clear()
        self._acceptance_scores.clear()
