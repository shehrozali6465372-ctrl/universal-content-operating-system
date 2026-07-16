"""Incident Logger — Log failures with context and timeline."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.failure_recovery.failure_detector import FailureRecord

_INCIDENT_COUNTER = itertools.count(1)


class IncidentEntry:
    """Single incident log entry."""

    __slots__ = (
        "incident_id", "failure", "context", "timeline",
        "recovery_action", "resolved", "resolution_time",
    )

    def __init__(self, failure: FailureRecord) -> None:
        self.incident_id: str = f"INC-{next(_INCIDENT_COUNTER):04d}"
        self.failure = failure
        self.context: Dict[str, Any] = {}
        self.timeline: List[Dict[str, Any]] = []
        self.recovery_action: str = ""
        self.resolved: bool = False
        self.resolution_time: float = 0.0
        self._add_timeline("detected", f"Failure detected: {failure.error_type}")

    def add_event(self, event: str, detail: str = "") -> None:
        self._add_timeline(event, detail)

    def mark_resolved(self) -> None:
        self.resolved = True
        self.resolution_time = time.time()
        self._add_timeline("resolved", "Incident resolved")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_id": self.incident_id,
            "failure_id": self.failure.failure_id,
            "error_type": self.failure.error_type,
            "severity": self.failure.severity,
            "platform": self.failure.platform,
            "resolved": self.resolved,
            "timeline_events": len(self.timeline),
            "context": self.context,
        }

    def _add_timeline(self, event: str, detail: str) -> None:
        self.timeline.append({
            "event": event,
            "detail": detail,
            "timestamp": time.time(),
        })


class IncidentLogger:
    """Log and track all incidents during publishing."""

    def __init__(self) -> None:
        self._incidents: List[IncidentEntry] = []

    def log_incident(self, failure: FailureRecord) -> IncidentEntry:
        entry = IncidentEntry(failure)
        self._incidents.append(entry)
        return entry

    def get_incidents(
        self,
        platform: Optional[str] = None,
        resolved: Optional[bool] = None,
    ) -> List[IncidentEntry]:
        results = self._incidents
        if platform:
            results = [i for i in results if i.failure.platform == platform]
        if resolved is not None:
            results = [i for i in results if i.resolved == resolved]
        return results

    def get_unresolved(self) -> List[IncidentEntry]:
        return self.get_incidents(resolved=False)

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._incidents)
        resolved = sum(1 for i in self._incidents if i.resolved)
        by_type: Dict[str, int] = {}
        by_severity: Dict[str, int] = {}
        for inc in self._incidents:
            by_type[inc.failure.error_type] = by_type.get(inc.failure.error_type, 0) + 1
            by_severity[inc.failure.severity] = by_severity.get(inc.failure.severity, 0) + 1
        return {
            "total": total,
            "resolved": resolved,
            "unresolved": total - resolved,
            "resolution_rate": round(resolved / max(1, total), 3),
            "by_type": by_type,
            "by_severity": by_severity,
        }

    @property
    def incident_count(self) -> int:
        return len(self._incidents)
