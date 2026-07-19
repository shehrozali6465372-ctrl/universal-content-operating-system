"""ResourceMonitor — monitor CPU, memory, disk, network resources."""
from __future__ import annotations
import time
import os
from typing import Any, Dict, List, Optional


class ResourceSnapshot:
    __slots__ = ("timestamp", "cpu_percent", "memory_percent", "memory_used_mb",
                 "memory_total_mb", "disk_percent", "disk_used_gb", "disk_total_gb",
                 "load_average", "metadata")

    def __init__(self) -> None:
        self.timestamp = time.time()
        self.cpu_percent: float = 0.0
        self.memory_percent: float = 0.0
        self.memory_used_mb: float = 0.0
        self.memory_total_mb: float = 0.0
        self.disk_percent: float = 0.0
        self.disk_used_gb: float = 0.0
        self.disk_total_gb: float = 0.0
        self.load_average: List[float] = []
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "cpu_percent": self.cpu_percent,
                "memory_percent": self.memory_percent,
                "disk_percent": self.disk_percent}


class ResourceMonitor:
    def __init__(self) -> None:
        self._snapshots: List[ResourceSnapshot] = []
        self._thresholds: Dict[str, float] = {
            "cpu_percent": 90.0, "memory_percent": 85.0, "disk_percent": 90.0}

    def collect(self) -> ResourceSnapshot:
        snap = ResourceSnapshot()
        try:
            with open('/proc/loadavg') as f:
                parts = f.read().split()
                snap.load_average = [float(parts[i]) for i in range(3)]
        except Exception:
            snap.load_average = [0.0, 0.0, 0.0]
        try:
            with open('/proc/meminfo') as f:
                lines = f.readlines()
                total = int(lines[0].split()[1]) / 1024
                available = int(lines[2].split()[1]) / 1024
                snap.memory_total_mb = round(total, 1)
                snap.memory_used_mb = round(total - available, 1)
                snap.memory_percent = round((total - available) / total * 100, 1) if total > 0 else 0
        except Exception:
            pass
        self._snapshots.append(snap)
        return snap

    def get_latest(self) -> Optional[ResourceSnapshot]:
        return self._snapshots[-1] if self._snapshots else None

    def check_alerts(self) -> List[Dict[str, Any]]:
        alerts = []
        latest = self.get_latest()
        if not latest:
            return alerts
        if latest.cpu_percent >= self._thresholds["cpu_percent"]:
            alerts.append({"resource": "cpu", "value": latest.cpu_percent,
                           "threshold": self._thresholds["cpu_percent"]})
        if latest.memory_percent >= self._thresholds["memory_percent"]:
            alerts.append({"resource": "memory", "value": latest.memory_percent,
                           "threshold": self._thresholds["memory_percent"]})
        return alerts

    def set_threshold(self, resource: str, threshold: float) -> None:
        self._thresholds[resource] = threshold

    def get_history(self, limit: int = 60) -> List[Dict[str, Any]]:
        return [s.to_dict() for s in self._snapshots[-limit:]]

    def summary(self) -> Dict[str, Any]:
        if not self._snapshots:
            return {"snapshots": 0}
        latest = self._snapshots[-1]
        return {"snapshots": len(self._snapshots), "memory_percent": latest.memory_percent,
                "memory_used_mb": latest.memory_used_mb}
