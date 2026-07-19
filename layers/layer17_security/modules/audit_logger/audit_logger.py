"""AuditLogger — security event logging and tracking."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class AuditSeverity(str, Enum):
    INFO = "info"; WARNING = "warning"; ERROR = "error"; CRITICAL = "critical"


class AuditEvent:
    __slots__ = ("event_id", "event_type", "severity", "message", "source",
                 "user_id", "ip_address", "timestamp", "metadata")

    def __init__(self, event_type: str, severity: AuditSeverity, message: str,
                 source: str = "") -> None:
        self.event_id = str(uuid.uuid4())[:12]
        self.event_type = event_type
        self.severity = severity
        self.message = message
        self.source = source
        self.user_id = ""
        self.ip_address = ""
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"event_id": self.event_id, "event_type": self.event_type,
                "severity": self.severity.value, "message": self.message,
                "timestamp": self.timestamp}


class AuditLogger:
    def __init__(self, max_entries: int = 10000) -> None:
        self._events: List[AuditEvent] = []
        self._max_entries = max_entries

    def log(self, event_type: str, severity: AuditSeverity, message: str,
            source: str = "", user_id: str = "", ip_address: str = "") -> AuditEvent:
        event = AuditEvent(event_type, severity, message, source)
        event.user_id = user_id
        event.ip_address = ip_address
        self._events.append(event)
        if len(self._events) > self._max_entries:
            self._events = self._events[-self._max_entries:]
        return event

    def query(self, event_type: Optional[str] = None,
              severity: Optional[AuditSeverity] = None,
              user_id: Optional[str] = None,
              limit: int = 100) -> List[Dict[str, Any]]:
        results = self._events
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if severity:
            results = [e for e in results if e.severity == severity]
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        return [e.to_dict() for e in results[-limit:]]

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> int:
        count = len(self._events)
        self._events.clear()
        return count
