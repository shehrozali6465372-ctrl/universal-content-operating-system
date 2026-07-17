"""Rollback Manager — Manage rollback of failed improvements."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_RM_COUNTER = itertools.count(1)


class RollbackPoint:
    """A saved state that can be restored."""

    __slots__ = ("point_id", "label", "snapshot", "created_at",
                 "restorable", "reason")

    def __init__(self, label: str = "") -> None:
        self.point_id: str = f"rbp_{next(_RM_COUNTER)}"
        self.label = label
        self.snapshot: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.restorable: bool = True
        self.reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "point_id": self.point_id,
            "label": self.label,
            "restorable": self.restorable,
            "reason": self.reason,
        }


class RollbackManager:
    """Manage rollback points for failed improvements."""

    def __init__(self) -> None:
        self._points: List[RollbackPoint] = []
        self._rollback_count: int = 0

    def save_point(self, label: str, snapshot: Dict[str, Any],
                   reason: str = "") -> RollbackPoint:
        point = RollbackPoint(label)
        point.snapshot = dict(snapshot)
        point.reason = reason
        self._points.append(point)
        return point

    def rollback(self, point_id: str) -> Optional[Dict[str, Any]]:
        point = self.get_point(point_id)
        if point and point.restorable:
            point.restorable = False
            self._rollback_count += 1
            return dict(point.snapshot)
        return None

    def get_point(self, point_id: str) -> Optional[RollbackPoint]:
        for p in self._points:
            if p.point_id == point_id:
                return p
        return None

    def get_points(self, restorable_only: bool = False) -> List[RollbackPoint]:
        if restorable_only:
            return [p for p in self._points if p.restorable]
        return list(self._points)

    def get_latest(self) -> Optional[RollbackPoint]:
        return self._points[-1] if self._points else None

    @property
    def rollback_count(self) -> int:
        return self._rollback_count

    @property
    def point_count(self) -> int:
        return len(self._points)
