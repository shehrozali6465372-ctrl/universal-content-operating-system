"""Performance analysis using explicit metric semantics and bounded history."""
from __future__ import annotations

import threading
import time
from typing import Any, Dict, List, Optional


class PerformanceSnapshot:
    __slots__ = ("timestamp", "metrics", "score", "grade", "metadata")

    def __init__(self, metrics: Dict[str, float]) -> None:
        self.timestamp = time.time()
        self.metrics = {k: float(v) for k, v in metrics.items()}
        self.score = self._calculate_score(self.metrics)
        self.grade = self._calculate_grade(self.score)
        self.metadata: Dict[str, Any] = {}

    @staticmethod
    def _calculate_score(metrics: Dict[str, float]) -> float:
        if not metrics:
            return 0.0
        # Metrics are expected to be normalized to 0..1; reject invalid input rather than inventing semantics.
        if any(not 0.0 <= value <= 1.0 for value in metrics.values()):
            raise ValueError("performance metrics must be normalized to 0..1")
        return round(sum(metrics.values()) / len(metrics) * 100, 1)

    @staticmethod
    def _calculate_grade(score: float) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "score": self.score, "grade": self.grade,
                "metrics": dict(self.metrics)}


class PerformanceAnalyzer:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._snapshots: List[PerformanceSnapshot] = []
        self._thresholds: Dict[str, Dict[str, float]] = {}

    def set_threshold(self, metric_name: str, min_val: float, max_val: float) -> None:
        if not metric_name or min_val > max_val:
            raise ValueError("invalid performance threshold")
        self._thresholds[metric_name] = {"min": float(min_val), "max": float(max_val)}

    def analyze(self, metrics: Dict[str, float]) -> PerformanceSnapshot:
        snapshot = PerformanceSnapshot(metrics)
        with self._lock:
            self._snapshots.append(snapshot)
            if len(self._snapshots) > self._history_size:
                del self._snapshots[:-self._history_size]
        return snapshot

    def get_latest(self) -> Optional[PerformanceSnapshot]:
        with self._lock:
            return self._snapshots[-1] if self._snapshots else None

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            return [s.to_dict() for s in self._snapshots[-limit:]]

    def check_violations(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        violations = []
        for name, value in metrics.items():
            threshold = self._thresholds.get(name)
            if threshold and (value < threshold["min"] or value > threshold["max"]):
                violations.append({"metric": name, "value": value, "threshold_min": threshold["min"],
                                   "threshold_max": threshold["max"]})
        return violations

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            if not self._snapshots:
                return {"snapshots": 0}
            scores = [s.score for s in self._snapshots]
            return {"snapshots": len(scores), "avg_score": round(sum(scores) / len(scores), 1),
                    "latest_grade": self._snapshots[-1].grade}
