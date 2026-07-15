"""Performance Tracker - Tracks content performance over time."""
from __future__ import annotations
import time
from typing import Dict, List


class PerformanceSnapshot:
    __slots__ = ("post_id", "timestamp", "metrics", "cumulative_score")
    def __init__(self, post_id: str = ""):
        self.post_id = post_id
        self.timestamp = time.time()
        self.metrics: Dict[str, float] = {}
        self.cumulative_score = 0.0
    def to_dict(self) -> Dict:
        return {"post_id": self.post_id, "timestamp": self.timestamp,
                "metrics": {k: round(v, 4) for k, v in self.metrics.items()},
                "score": round(self.cumulative_score, 3)}


class PerformanceTracker:
    def __init__(self, max_snapshots: int = 500) -> None:
        self._snapshots: List[PerformanceSnapshot] = []
        self._max = max_snapshots

    def record(self, post_id: str, metrics: Dict[str, float]) -> PerformanceSnapshot:
        snap = PerformanceSnapshot(post_id)
        snap.metrics = dict(metrics)
        snap.cumulative_score = sum(metrics.values()) / max(len(metrics), 1)
        self._snapshots.append(snap)
        if len(self._snapshots) > self._max:
            self._snapshots = self._snapshots[-self._max:]
        return snap

    def get_for_post(self, post_id: str) -> List[PerformanceSnapshot]:
        return [s for s in self._snapshots if s.post_id == post_id]

    def get_best_performing(self, n: int = 5) -> List[PerformanceSnapshot]:
        return sorted(self._snapshots, key=lambda s: s.cumulative_score, reverse=True)[:n]

    def get_worst_performing(self, n: int = 5) -> List[PerformanceSnapshot]:
        return sorted(self._snapshots, key=lambda s: s.cumulative_score)[:n]

    def get_average_score(self) -> float:
        if not self._snapshots: return 0.0
        return sum(s.cumulative_score for s in self._snapshots) / len(self._snapshots)

    def get_trend(self) -> str:
        if len(self._snapshots) < 3: return "insufficient_data"
        recent = [s.cumulative_score for s in self._snapshots[-3:]]
        older = [s.cumulative_score for s in self._snapshots[:-3]] or [0]
        r_avg = sum(recent) / len(recent)
        o_avg = sum(older) / len(older)
        if r_avg > o_avg * 1.1: return "improving"
        elif r_avg < o_avg * 0.9: return "declining"
        return "stable"

    def count(self) -> int:
        return len(self._snapshots)
