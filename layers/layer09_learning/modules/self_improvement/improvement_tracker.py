"""Improvement Tracker — Track improvement progress over time."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_IT_COUNTER = itertools.count(1)


class ImprovementSnapshot:
    """A snapshot of improvement metrics at a point in time."""

    __slots__ = ("snapshot_id", "timestamp", "score", "weaknesses_resolved",
                 "actions_completed", "active_experiments", "metadata")

    def __init__(self, score: float = 0.0) -> None:
        self.snapshot_id: str = f"ist_{next(_IT_COUNTER)}"
        self.timestamp: float = 0.0
        self.score = score
        self.weaknesses_resolved: int = 0
        self.actions_completed: int = 0
        self.active_experiments: int = 0
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "score": round(self.score, 3),
            "weaknesses_resolved": self.weaknesses_resolved,
            "actions_completed": self.actions_completed,
        }


class ImprovementTracker:
    """Track improvement progress over time with snapshots."""

    def __init__(self) -> None:
        self._snapshots: List[ImprovementSnapshot] = []

    def take_snapshot(self, score: float, weaknesses_resolved: int = 0,
                      actions_completed: int = 0, active_experiments: int = 0) -> ImprovementSnapshot:
        snap = ImprovementSnapshot(score)
        snap.timestamp = time.time()
        snap.weaknesses_resolved = weaknesses_resolved
        snap.actions_completed = actions_completed
        snap.active_experiments = active_experiments
        self._snapshots.append(snap)
        return snap

    def get_improvement_rate(self) -> float:
        if len(self._snapshots) < 2:
            return 0.0
        first = self._snapshots[0].score
        last = self._snapshots[-1].score
        if first == 0:
            return 0.0
        return round(((last - first) / abs(first)) * 100, 2)

    def get_trend(self) -> str:
        if len(self._snapshots) < 2:
            return "insufficient_data"
        scores = [s.score for s in self._snapshots[-5:]]
        if len(scores) >= 2:
            if scores[-1] > scores[0] * 1.05:
                return "improving"
            elif scores[-1] < scores[0] * 0.95:
                return "declining"
        return "stable"

    def get_best_score(self) -> float:
        if not self._snapshots:
            return 0.0
        return max(s.score for s in self._snapshots)

    def get_latest(self) -> ImprovementSnapshot | None:
        return self._snapshots[-1] if self._snapshots else None

    def get_snapshots(self, count: int = 0) -> List[ImprovementSnapshot]:
        if count > 0:
            return list(self._snapshots[-count:])
        return list(self._snapshots)

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)
