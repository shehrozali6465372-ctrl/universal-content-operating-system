"""AutomationMonitor — Track running tasks, workers, resource usage."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional


class AutomationMonitor:
    """Monitor automation health and performance."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._snapshots: List[Dict[str, Any]] = []
        self._max_snapshots: int = 1000
        self._warnings: List[Dict[str, Any]] = []
        self._errors: List[Dict[str, Any]] = []

    def record_snapshot(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._snapshots.append({
                "timestamp": time.time(),
                "data": data,
            })
            if len(self._snapshots) > self._max_snapshots:
                self._snapshots = self._snapshots[-self._max_snapshots:]

    def record_warning(self, message: str, source: str = "") -> None:
        with self._lock:
            self._warnings.append({
                "message": message,
                "source": source,
                "timestamp": time.time(),
            })

    def record_error(self, message: str, source: str = "",
                     error: str = "") -> None:
        with self._lock:
            self._errors.append({
                "message": message,
                "source": source,
                "error": error,
                "timestamp": time.time(),
            })

    def get_status(self, workers_stats: Dict[str, Any],
                   pipeline_stats: Dict[str, Any],
                   safety_stats: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "healthy" if not self._errors[-5:] else "degraded",
            "workers": workers_stats,
            "pipeline": pipeline_stats,
            "safety": safety_stats,
            "warnings": len(self._warnings),
            "errors": len(self._errors),
            "recent_errors": [e for e in self._errors[-5:]],
        }

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "snapshots": len(self._snapshots),
                "warnings": len(self._warnings),
                "errors": len(self._errors),
            }
