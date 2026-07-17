"""Strategy Comparator — Compare strategy performance between versions."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile


class StrategyComparisonResult:
    """Result of comparing two strategy versions."""

    __slots__ = ("metric_name", "baseline_value", "candidate_value",
                 "change", "change_pct", "winner", "significance")

    def __init__(self, metric_name: str = "") -> None:
        self.metric_name = metric_name
        self.baseline_value: float = 0.0
        self.candidate_value: float = 0.0
        self.change: float = 0.0
        self.change_pct: float = 0.0
        self.winner: str = "tie"
        self.significance: str = "low"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric_name": self.metric_name,
            "baseline_value": round(self.baseline_value, 4),
            "candidate_value": round(self.candidate_value, 4),
            "change": round(self.change, 4),
            "change_pct": round(self.change_pct, 2),
            "winner": self.winner,
            "significance": self.significance,
        }


class StrategyComparator:
    """Compare two strategy profiles across multiple metrics."""

    SIGNIFICANCE_THRESHOLDS = {"high": 20.0, "medium": 10.0, "low": 5.0}

    def __init__(self) -> None:
        self._results: List[StrategyComparisonResult] = []

    def compare(self, baseline: StrategyProfile, candidate: StrategyProfile) -> List[StrategyComparisonResult]:
        self._results.clear()
        metrics = [
            ("success_rate", baseline.success_rate, candidate.success_rate),
            ("avg_engagement", baseline.avg_engagement, candidate.avg_engagement),
            ("avg_reach", baseline.avg_reach, candidate.avg_reach),
            ("avg_conversion", baseline.avg_conversion, candidate.avg_conversion),
            ("effective_score", baseline.effective_score, candidate.effective_score),
        ]
        for name, b_val, c_val in metrics:
            result = StrategyComparisonResult(name)
            result.baseline_value = b_val
            result.candidate_value = c_val
            result.change = c_val - b_val
            if b_val != 0:
                result.change_pct = (result.change / abs(b_val)) * 100
            else:
                result.change_pct = 100.0 if c_val > 0 else 0.0
            if result.change_pct > 2:
                result.winner = "candidate"
            elif result.change_pct < -2:
                result.winner = "baseline"
            else:
                result.winner = "tie"
            abs_pct = abs(result.change_pct)
            if abs_pct >= self.SIGNIFICANCE_THRESHOLDS["high"]:
                result.significance = "high"
            elif abs_pct >= self.SIGNIFICANCE_THRESHOLDS["medium"]:
                result.significance = "medium"
            else:
                result.significance = "low"
            self._results.append(result)
        return list(self._results)

    def get_overall_winner(self, baseline: StrategyProfile, candidate: StrategyProfile) -> str:
        results = self.compare(baseline, candidate)
        candidate_wins = sum(1 for r in results if r.winner == "candidate")
        baseline_wins = sum(1 for r in results if r.winner == "baseline")
        if candidate_wins > baseline_wins:
            return "candidate"
        elif baseline_wins > candidate_wins:
            return "baseline"
        return "tie"

    def get_significant_differences(self) -> List[StrategyComparisonResult]:
        return [r for r in self._results if r.significance in ("high", "medium")]

    def get_results(self) -> List[StrategyComparisonResult]:
        return list(self._results)
