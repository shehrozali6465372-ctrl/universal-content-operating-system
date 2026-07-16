"""Publish Audit — Audit trail for all publish operations."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_AUDIT_COUNTER = itertools.count(1)


class AuditEntry:
    """Single audit log entry."""

    __slots__ = ("entry_id", "action", "platform", "request_id",
                 "post_id", "success", "duration_ms", "details", "timestamp")

    def __init__(self, action: str = "", platform: str = "") -> None:
        self.entry_id: str = f"audit_{next(_AUDIT_COUNTER)}"
        self.action = action
        self.platform = platform
        self.request_id: str = ""
        self.post_id: str = ""
        self.success = False
        self.duration_ms: float = 0.0
        self.details: Dict[str, Any] = {}
        self.timestamp: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "action": self.action,
            "platform": self.platform,
            "request_id": self.request_id,
            "post_id": self.post_id,
            "success": self.success,
            "duration_ms": round(self.duration_ms, 2),
            "timestamp": self.timestamp,
            "details": self.details,
        }


class PublishAudit:
    """Audit trail for publishing operations."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def log(
        self,
        action: str,
        platform: str = "",
        request_id: str = "",
        post_id: str = "",
        success: bool = False,
        duration_ms: float = 0.0,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEntry:
        entry = AuditEntry(action, platform)
        entry.request_id = request_id
        entry.post_id = post_id
        entry.success = success
        entry.duration_ms = duration_ms
        entry.details = details or {}
        self._entries.append(entry)
        return entry

    def get_entries(
        self,
        platform: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[AuditEntry]:
        results = self._entries
        if platform:
            results = [e for e in results if e.platform == platform]
        if action:
            results = [e for e in results if e.action == action]
        return results

    def get_success_rate(self) -> float:
        if not self._entries:
            return 0.0
        successful = sum(1 for e in self._entries if e.success)
        return round(successful / len(self._entries), 3)

    def get_stats(self) -> Dict[str, Any]:
        if not self._entries:
            return {"total": 0}
        durations = [e.duration_ms for e in self._entries if e.duration_ms > 0]
        return {
            "total": len(self._entries),
            "successful": sum(1 for e in self._entries if e.success),
            "failed": sum(1 for e in self._entries if not e.success),
            "success_rate": self.get_success_rate(),
            "avg_duration_ms": round(sum(durations) / max(1, len(durations)), 2),
            "platforms": list(set(e.platform for e in self._entries if e.platform)),
        }

    @property
    def entry_count(self) -> int:
        return len(self._entries)
