"""ErrorTracker — track and categorize errors across the system."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from enum import Enum


class ErrorSeverity(str, Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"


class ErrorEntry:
    __slots__ = ("error_id", "error_type", "message", "severity", "source",
                 "stack_trace", "count", "first_seen", "last_seen", "metadata")

    def __init__(self, error_type: str, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 source: str = "") -> None:
        self.error_id = str(uuid.uuid4())[:12]
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.source = source
        self.stack_trace = ""
        self.count = 1
        self.first_seen = time.time()
        self.last_seen = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"error_id": self.error_id, "type": self.error_type,
                "message": self.message[:200], "severity": self.severity.value,
                "count": self.count, "first_seen": self.first_seen,
                "last_seen": self.last_seen}


class ErrorTracker:
    def __init__(self) -> None:
        self._errors: Dict[str, ErrorEntry] = {}
        self._history: List[Dict[str, Any]] = []

    def track(self, error_type: str, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM,
              source: str = "") -> ErrorEntry:
        key = f"{error_type}:{message[:100]}"
        if key in self._errors:
            self._errors[key].count += 1
            self._errors[key].last_seen = time.time()
            return self._errors[key]
        entry = ErrorEntry(error_type, message, severity, source)
        self._errors[key] = entry
        self._history.append(entry.to_dict())
        return entry

    def get_error(self, error_id: str) -> Optional[ErrorEntry]:
        for entry in self._errors.values():
            if entry.error_id == error_id:
                return entry
        return None

    def list_errors(self, severity: Optional[ErrorSeverity] = None) -> List[Dict[str, Any]]:
        entries = self._errors.values()
        if severity:
            entries = [e for e in entries if e.severity == severity]
        return [e.to_dict() for e in sorted(entries, key=lambda e: -e.count)]

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        sorted_errors = sorted(self._errors.values(), key=lambda e: -e.count)
        return [e.to_dict() for e in sorted_errors[:limit]]

    def clear(self) -> int:
        count = len(self._errors)
        self._errors.clear()
        return count

    def stats(self) -> Dict[str, Any]:
        total = sum(e.count for e in self._errors.values())
        by_severity = {}
        for e in self._errors.values():
            by_severity[e.severity.value] = by_severity.get(e.severity.value, 0) + 1
        return {"unique_errors": len(self._errors), "total_occurrences": total,
                "by_severity": by_severity}
