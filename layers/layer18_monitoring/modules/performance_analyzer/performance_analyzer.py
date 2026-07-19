"""PerformanceAnalyzer — analyze system performance metrics."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PerformanceSnapshot:
    __slots__ = ("timestamp", "metrics", "score", "grade", "metadata")

    def __init__(self, metrics: Dict[str, float]) -> None:
        self.timestamp = time.time()
        self.metrics = metrics
        self.score = self._calculate_score(metrics)
        self.grade = self._calculate_grade(self.score)
        self.metadata: Dict[str, Any] = {}

    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        if not metrics:
            return 0.0
        return round(sum(metrics.values()) / len(metrics) * 100, 1)

    def _calculate_grade(self, score: float) -> str:
        if score >= 90: return "A+"
        if score >= 80: return "A"
        if score >= 70: return "B"
        if score >= 60: return "C"
        if score >= 50: return "D"
        return "F"

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "score": self.score,
                "grade": self.grade, "metrics": self.metrics}


class PerformanceAnalyzer:
    def __init__(self) -> None:
        self._snapshots: List[PerformanceSnapshot] = []
        self._thresholds: Dict[str, Dict[str, float]] = {}

    def set_threshold(self, metric_name: str, min_val: float, max_val: float) -> None:
        self._thresholds[metric_name] = {"min": min_val, "max": max_val}

    def analyze(self, metrics: Dict[str, float]) -> PerformanceSnapshot:
        snapshot = PerformanceSnapshot(metrics)
        self._snapshots.append(snapshot)
        return snapshot

    def get_latest(self) -> Optional[PerformanceSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def get_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._snapshots[-limit:]]

    def check_violations(self, metrics: Dict[str, float]) -> List[Dict[str, Any]]:
        violations = []
        for name, value in metrics.items():
            threshold = self._thresholds.get(name)
            if threshold:
                if value < threshold["min"]:
                    violations.append({"metric": name, "value": value,
                                       "threshold_min": threshold["min"]})
                elif value > threshold["max"]:
                    violations.append({"metric": name, "value": value,
                                       "threshold_max": threshold["max"]})
        return violations

    def summary(self) -> Dict[str, Any]:
        if not self._snapshots:
            return {"snapshots": 0}
        scores = [s.score for s in self._snapshots]
        return {"snapshots": len(self._snapshots), "avg_score": round(sum(scores) / len(scores), 1),
                "latest_grade": self._snapshots[-1].grade}
