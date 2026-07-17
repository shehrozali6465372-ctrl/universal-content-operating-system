"""Evaluator — Evaluate quality predictions against actual outcomes."""
from __future__ import annotations
from typing import Any, Dict, List


class EvaluationResult:
    """Result of evaluating quality predictions."""

    __slots__ = ("metric", "predicted", "actual", "error",
                 "absolute_error", "squared_error", "direction")

    def __init__(self, metric: str = "") -> None:
        self.metric = metric
        self.predicted: float = 0.0
        self.actual: float = 0.0
        self.error: float = 0.0
        self.absolute_error: float = 0.0
        self.squared_error: float = 0.0
        self.direction: str = "accurate"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "predicted": round(self.predicted, 4),
            "actual": round(self.actual, 4),
            "error": round(self.error, 4),
            "absolute_error": round(self.absolute_error, 4),
            "direction": self.direction,
        }


class Evaluator:
    """Evaluate quality prediction accuracy against actual outcomes."""

    def __init__(self) -> None:
        self._results: List[EvaluationResult] = []

    def evaluate(self, predicted: Dict[str, float],
                 actual: Dict[str, float]) -> List[EvaluationResult]:
        results = []
        all_metrics = set(list(predicted.keys()) + list(actual.keys()))
        for metric in all_metrics:
            p = predicted.get(metric, 0.0)
            a = actual.get(metric, 0.0)
            r = EvaluationResult(metric)
            r.predicted = p
            r.actual = a
            r.error = round(a - p, 4)
            r.absolute_error = round(abs(r.error), 4)
            r.squared_error = round(r.error ** 2, 4)
            if r.error > 0.05:
                r.direction = "underpredicted"
            elif r.error < -0.05:
                r.direction = "overpredicted"
            else:
                r.direction = "accurate"
            results.append(r)
            self._results.append(r)
        return results

    def get_mae(self) -> float:
        if not self._results:
            return 0.0
        return round(sum(r.absolute_error for r in self._results) / len(self._results), 4)

    def get_rmse(self) -> float:
        if not self._results:
            return 0.0
        import math
        return round(math.sqrt(sum(r.squared_error for r in self._results) / len(self._results)), 4)

    def get_direction_summary(self) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for r in self._results:
            summary[r.direction] = summary.get(r.direction, 0) + 1
        return summary

    def get_results(self) -> List[EvaluationResult]:
        return list(self._results)

    @property
    def evaluation_count(self) -> int:
        return len(self._results)
