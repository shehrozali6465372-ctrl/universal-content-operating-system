"""Performance Comparator — Compare previous vs current performance."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer09_learning.modules.learning_engine.learning_signal import LearningSignal


class ComparisonResult:
    """Result of comparing two performance periods."""

    __slots__ = ("metric_name", "previous_value", "current_value",
                 "change", "change_pct", "direction", "significance")

    def __init__(self, metric_name: str = "") -> None:
        self.metric_name = metric_name
        self.previous_value: float = 0.0
        self.current_value: float = 0.0
        self.change: float = 0.0
        self.change_pct: float = 0.0
        self.direction: str = "stable"
        self.significance: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "previous_value": round(self.previous_value, 4),
            "current_value": round(self.current_value, 4),
            "change": round(self.change, 4),
            "change_pct": round(self.change_pct, 2),
            "direction": self.direction,
            "significance": self.significance,
        }


class PerformanceComparator:
    """Compare performance between two periods."""

    SIGNIFICANCE_THRESHOLDS = {
        "high": 20.0,
        "medium": 10.0,
        "low": 5.0,
    }

    def __init__(self) -> None:
        self._comparisons: List[ComparisonResult] = []
        self._comparison_count = 0

    def compare(
        self,
        metric_name: str,
        previous_value: float,
        current_value: float,
    ) -> ComparisonResult:
        result = ComparisonResult(metric_name)
        result.previous_value = previous_value
        result.current_value = current_value
        result.change = current_value - previous_value

        if previous_value != 0:
            result.change_pct = (result.change / abs(previous_value)) * 100
        else:
            result.change_pct = 100.0 if current_value > 0 else 0.0

        abs_pct = abs(result.change_pct)
        if abs_pct >= self.SIGNIFICANCE_THRESHOLDS["high"]:
            result.significance = "high"
        elif abs_pct >= self.SIGNIFICANCE_THRESHOLDS["medium"]:
            result.significance = "medium"
        else:
            result.significance = "low"

        if result.change_pct > 5:
            result.direction = "growth"
        elif result.change_pct < -5:
            result.direction = "decline"
        else:
            result.direction = "stable"

        self._comparisons.append(result)
        self._comparison_count += 1
        return result

    def compare_signals(
        self,
        previous_signals: List[LearningSignal],
        current_signals: List[LearningSignal],
    ) -> List[ComparisonResult]:
        prev_map = {s.metric_name: s.value for s in previous_signals}
        curr_map = {s.metric_name: s.value for s in current_signals}
        all_metrics = set(list(prev_map.keys()) + list(curr_map.keys()))
        results = []
        for metric in all_metrics:
            r = self.compare(metric, prev_map.get(metric, 0.0), curr_map.get(metric, 0.0))
            results.append(r)
        return results

    def get_growth_metrics(self) -> List[ComparisonResult]:
        return [c for c in self._comparisons if c.direction == "growth"]

    def get_decline_metrics(self) -> List[ComparisonResult]:
        return [c for c in self._comparisons if c.direction == "decline"]

    def get_comparisons(self) -> List[ComparisonResult]:
        return list(self._comparisons)

    @property
    def comparison_count(self) -> int:
        return self._comparison_count
