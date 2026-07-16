"""Status Tracker — Track publish status through lifecycle."""
from __future__ import annotations
import time
from typing import Any, Dict, List

PUBLISH_STATUSES = ("pending", "uploading", "publishing", "published", "failed", "cancelled", "rollback")


class StatusRecord:
    """Single status change record."""

    __slots__ = ("status", "timestamp", "message")

    def __init__(self, status: str, message: str = "") -> None:
        self.status = status
        self.timestamp = time.time()
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "timestamp": self.timestamp,
            "message": self.message,
        }


class StatusTracker:
    """Track status transitions for a publish request."""

    def __init__(self, request_id: str = "") -> None:
        self.request_id = request_id
        self.current_status: str = "pending"
        self._history: List[StatusRecord] = []
        self._record("pending", "Tracker initialized")

    def update(self, status: str, message: str = "") -> None:
        if status not in PUBLISH_STATUSES:
            raise ValueError(f"Invalid status: {status}")
        self.current_status = status
        self._record(status, message)

    def get_history(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._history]

    def get_duration(self) -> float:
        if len(self._history) < 2:
            return 0.0
        return self._history[-1].timestamp - self._history[0].timestamp

    def is_terminal(self) -> bool:
        return self.current_status in ("published", "failed", "cancelled", "rollback")

    def is_success(self) -> bool:
        return self.current_status == "published"

    def transition_count(self) -> int:
        return len(self._history) - 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "current_status": self.current_status,
            "transitions": self.transition_count(),
            "is_terminal": self.is_terminal(),
            "duration_seconds": round(self.get_duration(), 3),
        }

    def _record(self, status: str, message: str) -> None:
        self._history.append(StatusRecord(status, message))
