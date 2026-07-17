"""Calibration Metrics — Track calibration performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class CalibrationMetrics:
    """Track metrics across calibration operations."""

    def __init__(self) -> None:
        self._total_calibrations: int = 0
        self._total_evaluations: int = 0
        self._total_adjustments: int = 0
        self._total_benchmarks: int = 0
        self._mae_values: List[float] = []
        self._ece_values: List[float] = []

    def record_calibration(self, ece: float = 0.0) -> None:
        self._total_calibrations += 1
        if ece > 0:
            self._ece_values.append(ece)

    def record_evaluation(self, mae: float = 0.0) -> None:
        self._total_evaluations += 1
        if mae > 0:
            self._mae_values.append(mae)

    def record_adjustment(self) -> None:
        self._total_adjustments += 1

    def record_benchmark(self) -> None:
        self._total_benchmarks += 1

    def get_avg_mae(self) -> float:
        if not self._mae_values:
            return 0.0
        return round(sum(self._mae_values) / len(self._mae_values), 4)

    def get_avg_ece(self) -> float:
        if not self._ece_values:
            return 0.0
        return round(sum(self._ece_values) / len(self._ece_values), 4)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_calibrations": self._total_calibrations,
            "total_evaluations": self._total_evaluations,
            "total_adjustments": self._total_adjustments,
            "total_benchmarks": self._total_benchmarks,
            "avg_mae": self.get_avg_mae(),
            "avg_ece": self.get_avg_ece(),
        }

    def reset(self) -> None:
        self._total_calibrations = 0
        self._total_evaluations = 0
        self._total_adjustments = 0
        self._total_benchmarks = 0
        self._mae_values.clear()
        self._ece_values.clear()
