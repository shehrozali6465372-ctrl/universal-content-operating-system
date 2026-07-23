"""ErrorTracker — Track, classify, and analyze errors.

Features:
- Error recording with stack traces
- Error classification (by type, severity, module)
- Frequency analysis
- Error grouping (deduplication)
- Error trends over time
- Top errors ranking
"""
from __future__ import annotations
import time
import hashlib
import threading
from typing import Any, Dict, List, Optional


class ErrorTracker:
    """Track and analyze errors across the system."""

    def __init__(self, history_size: int = 5000):
        self._history_size = history_size
        self._lock = threading.Lock()

        # Error storage
        self._errors: List[Dict[str, Any]] = []
        self._groups: Dict[str, Dict[str, Any]] = {}  # fingerprint → group

        # Stats
        self._total_errors = 0

    def record(self, error_type: str, message: str, module: str = "unknown",
               severity: str = "error", stack_trace: str = "",
               metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Record an error.

        Args:
            error_type: Exception class name
            message: Error message
            module: Source module
            severity: error, warning, critical
            stack_trace: Full stack trace
            metadata: Additional context

        Returns:
            Error record
        """
        now = time.time()
        fingerprint = hashlib.md5(f"{error_type}:{module}:{message[:100]}".encode()).hexdigest()[:12]

        error = {
            "timestamp": now,
            "error_type": error_type,
            "message": message[:500],
            "module": module,
            "severity": severity,
            "stack_trace": stack_trace[:1000],
            "fingerprint": fingerprint,
            "metadata": metadata or {},
        }

        with self._lock:
            self._errors.append(error)
            self._total_errors += 1

            # Trim
            if len(self._errors) > self._history_size:
                self._errors = self._errors[-self._history_size:]

            # Update groups
            if fingerprint not in self._groups:
                self._groups[fingerprint] = {
                    "fingerprint": fingerprint,
                    "error_type": error_type,
                    "message": message[:200],
                    "module": module,
                    "severity": severity,
                    "count": 0,
                    "first_seen": now,
                    "last_seen": now,
                }
            group = self._groups[fingerprint]
            group["count"] += 1
            group["last_seen"] = now

        return error

    def get_recent(self, limit: int = 50, module: str = None,
                   severity: str = None) -> List[Dict[str, Any]]:
        """Get recent errors with optional filters."""
        with self._lock:
            errors = list(self._errors)

        if module:
            errors = [e for e in errors if e["module"] == module]
        if severity:
            errors = [e for e in errors if e["severity"] == severity]

        return errors[-limit:]

    def get_top_errors(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """Get most frequent error groups."""
        with self._lock:
            groups = list(self._groups.values())

        groups.sort(key=lambda g: g["count"], reverse=True)
        return groups[:top_k]

    def get_errors_by_module(self) -> Dict[str, int]:
        """Count errors by module."""
        with self._lock:
            errors = list(self._errors)

        counts: Dict[str, int] = {}
        for e in errors:
            module = e["module"]
            counts[module] = counts.get(module, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_errors_by_type(self) -> Dict[str, int]:
        """Count errors by type."""
        with self._lock:
            errors = list(self._errors)

        counts: Dict[str, int] = {}
        for e in errors:
            etype = e["error_type"]
            counts[etype] = counts.get(etype, 0) + 1
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))

    def get_error_rate(self, window_seconds: float = 300) -> Dict[str, Any]:
        """Get error rate in a time window."""
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            recent = [e for e in self._errors if e["timestamp"] >= cutoff]

        return {
            "window_seconds": window_seconds,
            "error_count": len(recent),
            "error_rate_per_minute": round(len(recent) / (window_seconds / 60), 2),
        }

    def get_trend(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """Get error trend over time (hourly buckets)."""
        now = time.time()
        cutoff = now - (window_hours * 3600)

        with self._lock:
            recent = [e for e in self._errors if e["timestamp"] >= cutoff]

        # Bucket by hour
        buckets: Dict[int, int] = {}
        for e in recent:
            hour = int((e["timestamp"] - cutoff) / 3600)
            buckets[hour] = buckets.get(hour, 0) + 1

        return [{"hour": h, "count": buckets.get(h, 0)} for h in range(window_hours)]

    def clear(self) -> None:
        """Clear all errors."""
        with self._lock:
            self._errors.clear()
            self._groups.clear()
            self._total_errors = 0

    def stats(self) -> Dict[str, Any]:
        """Get error tracker statistics."""
        with self._lock:
            severity_counts = {}
            for e in self._errors:
                s = e["severity"]
                severity_counts[s] = severity_counts.get(s, 0) + 1

        return {
            "total_errors": self._total_errors,
            "unique_error_groups": len(self._groups),
            "errors_in_history": len(self._errors),
            "severity_breakdown": severity_counts,
        }
