"""Compatibility error tracker with bounded state."""
from __future__ import annotations

import threading
import time
import uuid
from enum import Enum
from typing import Any, Dict, List, Optional


class ErrorSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorEntry:
    __slots__ = (
        "error_id", "error_type", "message", "severity", "source",
        "stack_trace", "count", "first_seen", "last_seen", "metadata",
    )

    def __init__(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        source: str = "",
    ) -> None:
        self.error_id = str(uuid.uuid4())
        self.error_type = error_type
        self.message = message
        self.severity = severity
        self.source = source
        self.stack_trace = ""
        self.count = 1
        self.first_seen = time.time()
        self.last_seen = self.first_seen
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "error_id": self.error_id,
            "type": self.error_type,
            "message": self.message[:200],
            "severity": self.severity.value,
            "source": self.source,
            "count": self.count,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
        }


class ErrorTracker:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._lock = threading.RLock()
        self._history_size = history_size
        self._errors: Dict[str, ErrorEntry] = {}
        self._history: List[Dict[str, Any]] = []

    def track(
        self,
        error_type: str,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        source: str = "",
    ) -> ErrorEntry:
        if not error_type.strip() or not message.strip():
            raise ValueError("error_type and message are required")
        key = f"{error_type}:{message[:100]}"
        with self._lock:
            entry = self._errors.get(key)
            if entry:
                entry.count += 1
                entry.last_seen = time.time()
                return entry
            entry = ErrorEntry(error_type, message, severity, source)
            self._errors[key] = entry
            self._history.append(entry.to_dict())
            if len(self._history) > self._history_size:
                del self._history[:-self._history_size]
            return entry

    def get_error(self, error_id: str) -> Optional[ErrorEntry]:
        with self._lock:
            return next(
                (entry for entry in self._errors.values() if entry.error_id == error_id),
                None,
            )

    def list_errors(
        self, severity: Optional[ErrorSeverity] = None
    ) -> List[Dict[str, Any]]:
        with self._lock:
            entries = list(self._errors.values())
            if severity is not None:
                entries = [entry for entry in entries if entry.severity == severity]
            return [entry.to_dict() for entry in entries]

    def get_top_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            entries = sorted(
                self._errors.values(), key=lambda entry: (-entry.count, entry.error_id)
            )
            return [entry.to_dict() for entry in entries[:limit]]

    def clear(self) -> int:
        with self._lock:
            count = len(self._errors)
            self._errors.clear()
            return count

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "unique_errors": len(self._errors),
                "total_occurrences": sum(entry.count for entry in self._errors.values()),
                "by_severity": {
                    severity.value: sum(
                        entry.severity == severity for entry in self._errors.values()
                    )
                    for severity in ErrorSeverity
                },
            }
