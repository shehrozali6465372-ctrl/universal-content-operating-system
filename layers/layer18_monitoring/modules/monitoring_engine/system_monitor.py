"""Production system resource monitoring with bounded history and safe fallbacks."""
from __future__ import annotations

import math
import os
import threading
import time
from typing import Any, Dict, List, Optional


class SystemMonitor:
    """Collect CPU, memory, disk and load metrics safely on Linux-like hosts."""

    def __init__(self, history_size: int = 1000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._history_size = history_size
        self._lock = threading.RLock()
        self._cpu_history: List[Dict[str, Any]] = []
        self._memory_history: List[Dict[str, Any]] = []
        self._disk_history: List[Dict[str, Any]] = []
        self._last_snapshot: Dict[str, Any] = {}
        self._previous_cpu: Optional[tuple[int, int]] = None
        self._thresholds: Dict[str, float] = {
            "cpu_warning": 70.0, "cpu_critical": 90.0,
            "memory_warning": 75.0, "memory_critical": 90.0,
            "disk_warning": 80.0, "disk_critical": 95.0,
        }

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        cpu = self._get_cpu_percent()
        memory = self._get_memory_info()
        disk = self._get_disk_info()
        snapshot = {
            "timestamp": now,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "load_average": self._get_load_average(),
            "alerts": self._check_thresholds(cpu, memory, disk),
        }
        with self._lock:
            self._last_snapshot = snapshot
            self._append(self._cpu_history, {"timestamp": now, "value": cpu["percent"]})
            self._append(self._memory_history, {"timestamp": now, "value": memory["percent"]})
            self._append(self._disk_history, {"timestamp": now, "value": disk["percent_used"]})
        return snapshot

    def _append(self, history: List[Dict[str, Any]], value: Dict[str, Any]) -> None:
        history.append(value)
        if len(history) > self._history_size:
            del history[:-self._history_size]

    def _get_cpu_percent(self) -> Dict[str, Any]:
        try:
            with open("/proc/stat", encoding="utf-8") as handle:
                fields = handle.readline().split()
            if len(fields) < 5:
                raise ValueError("invalid /proc/stat")
            values = [int(v) for v in fields[1:]]
            total = sum(values)
            idle = values[3] + (values[4] if len(values) > 4 else 0)
            current = (total, idle)
            with self._lock:
                previous = self._previous_cpu
                self._previous_cpu = current
            if previous is None:
                percent = 0.0
            else:
                total_delta = total - previous[0]
                idle_delta = idle - previous[1]
                percent = (1 - idle_delta / total_delta) * 100 if total_delta > 0 else 0.0
            return {"percent": round(max(0.0, min(100.0, percent)), 1), "cores": os.cpu_count() or 1}
        except (OSError, ValueError, IndexError):
            return {"percent": 0.0, "cores": os.cpu_count() or 1}

    def _get_memory_info(self) -> Dict[str, Any]:
        try:
            values: Dict[str, int] = {}
            with open("/proc/meminfo", encoding="utf-8") as handle:
                for line in handle:
                    key, raw = line.split(":", 1)
                    values[key] = int(raw.split()[0])
            total = values.get("MemTotal", 0)
            available = values.get("MemAvailable", values.get("MemFree", 0))
            swap_total = values.get("SwapTotal", 0)
            swap_free = values.get("SwapFree", 0)
            used = max(0, total - available)
            return {
                "percent": round(used / total * 100, 1) if total else 0.0,
                "total_mb": round(total / 1024, 1),
                "used_mb": round(used / 1024, 1),
                "available_mb": round(available / 1024, 1),
                "swap_total_mb": round(swap_total / 1024, 1),
                "swap_used_mb": round(max(0, swap_total - swap_free) / 1024, 1),
            }
        except (OSError, ValueError):
            return {"percent": 0.0, "total_mb": 0.0, "used_mb": 0.0, "available_mb": 0.0,
                    "swap_total_mb": 0.0, "swap_used_mb": 0.0}

    def _get_disk_info(self) -> Dict[str, Any]:
        try:
            stat = os.statvfs("/")
            total = stat.f_blocks * stat.f_frsize
            free = stat.f_bavail * stat.f_frsize
            used = max(0, total - free)
            return {
                "percent_used": round(used / total * 100, 1) if total else 0.0,
                "total_gb": round(total / 1024**3, 1),
                "used_gb": round(used / 1024**3, 1),
                "free_gb": round(free / 1024**3, 1),
            }
        except OSError:
            return {"percent_used": 0.0, "total_gb": 0.0, "used_gb": 0.0, "free_gb": 0.0}

    def _get_load_average(self) -> List[float]:
        try:
            with open("/proc/loadavg", encoding="utf-8") as handle:
                return [float(v) for v in handle.read().split()[:3]]
        except (OSError, ValueError):
            try:
                return [float(v) for v in os.getloadavg()]
            except (AttributeError, OSError):
                return [0.0, 0.0, 0.0]

    def _check_thresholds(self, cpu: Dict[str, Any], memory: Dict[str, Any],
                          disk: Dict[str, Any]) -> List[Dict[str, Any]]:
        checks = (
            ("cpu", cpu["percent"], "cpu_warning", "cpu_critical"),
            ("memory", memory["percent"], "memory_warning", "memory_critical"),
            ("disk", disk["percent_used"], "disk_warning", "disk_critical"),
        )
        alerts: List[Dict[str, Any]] = []
        for resource, value, warning_key, critical_key in checks:
            if value >= self._thresholds[critical_key]:
                alerts.append({"type": resource, "severity": "critical", "value": value,
                                "threshold": self._thresholds[critical_key]})
            elif value >= self._thresholds[warning_key]:
                alerts.append({"type": resource, "severity": "warning", "value": value,
                                "threshold": self._thresholds[warning_key]})
        return alerts

    def get_current(self) -> Dict[str, Any]:
        with self._lock:
            snapshot = dict(self._last_snapshot)
        return snapshot if snapshot else self.snapshot()

    def get_trend(self, metric: str = "cpu", window: int = 10) -> Dict[str, Any]:
        if window <= 0:
            raise ValueError("window must be positive")
        with self._lock:
            data = {"cpu": self._cpu_history, "memory": self._memory_history,
                    "disk": self._disk_history}.get(metric)
            recent = list(data[-window:]) if data is not None else []
        if data is None:
            return {"trend": "unknown", "values": []}
        if len(recent) < 2:
            return {"trend": "stable", "values": [d["value"] for d in recent]}
        values = [d["value"] for d in recent]
        midpoint = len(values) // 2
        first = sum(values[:midpoint]) / midpoint
        second = sum(values[midpoint:]) / (len(values) - midpoint)
        diff = second - first
        trend = "rising" if diff > 2 else "falling" if diff < -2 else "stable"
        return {"trend": trend, "avg_first_half": round(first, 1),
                "avg_second_half": round(second, 1), "diff": round(diff, 1), "values": values}

    def detect_anomalies(self, metric: str = "cpu", window: int = 30) -> List[Dict[str, Any]]:
        if window <= 0:
            raise ValueError("window must be positive")
        with self._lock:
            data = {"cpu": self._cpu_history, "memory": self._memory_history}.get(metric)
            recent = list(data[-window:]) if data is not None else []
        if data is None or len(recent) < 5:
            return []
        values = [d["value"] for d in recent]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        std = math.sqrt(variance)
        if std == 0:
            return []
        return [{"timestamp": d["timestamp"], "value": d["value"],
                 "z_score": round((d["value"] - mean) / std, 2),
                 "mean": round(mean, 1), "std": round(std, 1)}
                for d in recent if abs((d["value"] - mean) / std) > 2.5]

    def set_threshold(self, name: str, value: float) -> None:
        if name not in self._thresholds:
            raise KeyError(f"unknown threshold: {name}")
        if not 0 <= value <= 100:
            raise ValueError("threshold must be between 0 and 100")
        with self._lock:
            self._thresholds[name] = value

    def get_history(self, metric: str = "cpu") -> List[Dict[str, Any]]:
        with self._lock:
            data = {"cpu": self._cpu_history, "memory": self._memory_history,
                    "disk": self._disk_history}.get(metric)
            if data is None:
                raise KeyError(f"unknown metric: {metric}")
            return list(data)

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {"cpu_history_size": len(self._cpu_history),
                    "memory_history_size": len(self._memory_history),
                    "disk_history_size": len(self._disk_history),
                    "thresholds": dict(self._thresholds)}
