"""Cross-platform resource monitoring using optional psutil with safe fallbacks."""
from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional


class ResourceSnapshot:
    __slots__ = ("timestamp", "cpu_percent", "memory_percent", "memory_used_mb",
                 "memory_total_mb", "disk_percent", "disk_used_gb", "disk_total_gb",
                 "load_average", "metadata")

    def __init__(self) -> None:
        self.timestamp = time.time()
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.memory_used_mb = 0.0
        self.memory_total_mb = 0.0
        self.disk_percent = 0.0
        self.disk_used_gb = 0.0
        self.disk_total_gb = 0.0
        self.load_average: List[float] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "cpu_percent": self.cpu_percent,
                "memory_percent": self.memory_percent, "memory_used_mb": self.memory_used_mb,
                "memory_total_mb": self.memory_total_mb, "disk_percent": self.disk_percent,
                "disk_used_gb": self.disk_used_gb, "disk_total_gb": self.disk_total_gb}


class ResourceMonitor:
    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._history_size = history_size
        self._snapshots: List[ResourceSnapshot] = []
        self._thresholds: Dict[str, float] = {"cpu_percent": 90.0, "memory_percent": 85.0,
                                              "disk_percent": 90.0}

    def collect(self) -> ResourceSnapshot:
        snap = ResourceSnapshot()
        try:
            import psutil
            snap.cpu_percent = float(psutil.cpu_percent(interval=None))
            memory = psutil.virtual_memory()
            snap.memory_percent = float(memory.percent)
            snap.memory_used_mb = memory.used / 1024**2
            snap.memory_total_mb = memory.total / 1024**2
            disk = psutil.disk_usage(os.path.abspath(os.sep))
            snap.disk_percent = float(disk.percent)
            snap.disk_used_gb = disk.used / 1024**3
            snap.disk_total_gb = disk.total / 1024**3
            snap.load_average = list(getattr(psutil, "getloadavg", lambda: ())())
        except ImportError:
            snap.load_average = list(os.getloadavg()) if hasattr(os, "getloadavg") else []
        except (OSError, RuntimeError):
            pass
        self._snapshots.append(snap)
        if len(self._snapshots) > self._history_size:
            del self._snapshots[:-self._history_size]
        return snap

    def get_latest(self) -> Optional[ResourceSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def check_alerts(self) -> List[Dict[str, Any]]:
        latest = self.get_latest()
        if latest is None:
            return []
        alerts = []
        for key, value in (("cpu_percent", latest.cpu_percent),
                           ("memory_percent", latest.memory_percent),
                           ("disk_percent", latest.disk_percent)):
            if value >= self._thresholds[key]:
                alerts.append({"resource": key, "value": value, "threshold": self._thresholds[key]})
        return alerts

    def set_threshold(self, resource: str, threshold: float) -> None:
        if resource not in self._thresholds:
            raise KeyError(f"unknown resource: {resource}")
        if not 0 <= threshold <= 100:
            raise ValueError("threshold must be between 0 and 100")
        self._thresholds[resource] = threshold

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        if limit <= 0:
            raise ValueError("limit must be positive")
        return [s.to_dict() for s in self._snapshots[-limit:]]

    def summary(self) -> Dict[str, Any]:
        latest = self.get_latest()
        if latest is None:
            return {"snapshots": 0}
        return {"snapshots": len(self._snapshots), "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb}
