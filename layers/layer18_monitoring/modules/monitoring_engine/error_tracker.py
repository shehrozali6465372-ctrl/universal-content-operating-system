"""Thread-safe bounded error tracking with deterministic fingerprints."""
from __future__ import annotations

import hashlib
import threading
import time
from typing import Any, Dict, List, Optional


class ErrorTracker:
    def __init__(self, history_size: int = 5000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._history_size = history_size
        self._lock = threading.RLock()
        self._errors: List[Dict[str, Any]] = []
        self._groups: Dict[str, Dict[str, Any]] = {}
        self._total_errors = 0

    def record(self, error_type: str, message: str, module: str = "unknown",
               severity: str = "error", stack_trace: str = "",
               metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not error_type.strip() or not message.strip():
            raise ValueError("error_type and message are required")
        if severity not in {"warning", "error", "critical"}:
            raise ValueError("severity must be warning, error, or critical")
        now = time.time()
        fingerprint = hashlib.sha256(
            f"{error_type}:{module}:{message[:100]}".encode("utf-8")
        ).hexdigest()[:16]
        error = {"timestamp": now, "error_type": error_type, "message": message[:500],
                 "module": module, "severity": severity, "stack_trace": stack_trace[:1000],
                 "fingerprint": fingerprint, "metadata": dict(metadata or {})}
        with self._lock:
            self._errors.append(error)
            if len(self._errors) > self._history_size:
                del self._errors[:-self._history_size]
            self._total_errors += 1
            group = self._groups.setdefault(fingerprint, {
                "fingerprint": fingerprint, "error_type": error_type, "message": message[:200],
                "module": module, "severity": severity, "count": 0, "first_seen": now, "last_seen": now})
            group["count"] += 1
            group["last_seen"] = now
        return dict(error)

    def get_recent(self, limit: int = 50, module: Optional[str] = None,
                   severity: Optional[str] = None) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        with self._lock:
            errors = list(self._errors)
        if module:
            errors = [e for e in errors if e["module"] == module]
        if severity:
            errors = [e for e in errors if e["severity"] == severity]
        return [dict(e) for e in errors[-limit:]]

    def get_top_errors(self, top_k: int = 10) -> List[Dict[str, Any]]:
        if top_k <= 0:
            raise ValueError("top_k must be positive")
        with self._lock:
            groups = [dict(g) for g in self._groups.values()]
        groups.sort(key=lambda g: (-g["count"], g["fingerprint"]))
        return groups[:top_k]

    def get_errors_by_module(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for error in self._errors:
                counts[error["module"]] = counts.get(error["module"], 0) + 1
            return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def get_errors_by_type(self) -> Dict[str, int]:
        with self._lock:
            counts: Dict[str, int] = {}
            for error in self._errors:
                counts[error["error_type"]] = counts.get(error["error_type"], 0) + 1
            return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))

    def get_error_rate(self, window_seconds: float = 300) -> Dict[str, Any]:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        cutoff = time.time() - window_seconds
        with self._lock:
            count = sum(e["timestamp"] >= cutoff for e in self._errors)
        return {"window_seconds": window_seconds, "error_count": count,
                "error_rate_per_minute": round(count / (window_seconds / 60), 2)}

    def get_trend(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        if window_hours <= 0:
            raise ValueError("window_hours must be positive")
        cutoff = time.time() - window_hours * 3600
        with self._lock:
            recent = list(e for e in self._errors if e["timestamp"] >= cutoff)
        buckets = {hour: 0 for hour in range(window_hours)}
        for error in recent:
            hour = min(window_hours - 1, max(0, int((error["timestamp"] - cutoff) / 3600)))
            buckets[hour] += 1
        return [{"hour": hour, "count": buckets[hour]} for hour in range(window_hours)]

    def clear(self) -> None:
        with self._lock:
            self._errors.clear(); self._groups.clear(); self._total_errors = 0

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            severity_counts: Dict[str, int] = {}
            for error in self._errors:
                severity_counts[error["severity"]] = severity_counts.get(error["severity"], 0) + 1
            return {"total_errors": self._total_errors, "unique_error_groups": len(self._groups),
                    "errors_in_history": len(self._errors), "severity_breakdown": severity_counts}
