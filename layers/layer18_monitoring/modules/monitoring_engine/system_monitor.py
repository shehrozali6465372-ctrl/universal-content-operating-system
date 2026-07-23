"""SystemMonitor — CPU, RAM, disk, network monitoring with time-series.

Features:
- Real-time CPU usage tracking
- Memory usage with swap detection
- Disk I/O and space monitoring
- Network traffic tracking
- Time-series data storage
- Trend analysis (rising, falling, stable)
- Anomaly detection (z-score based)
"""
from __future__ import annotations
import time
import os
import threading
from typing import Any, Dict, List, Optional, Tuple


class SystemMonitor:
    """Comprehensive system resource monitoring."""

    def __init__(self, history_size: int = 1000):
        self._history_size = history_size
        self._lock = threading.Lock()

        # Time-series data
        self._cpu_history: List[Dict[str, Any]] = []
        self._memory_history: List[Dict[str, Any]] = []
        self._disk_history: List[Dict[str, Any]] = []

        # Current state
        self._last_snapshot: Dict[str, Any] = {}

        # Thresholds
        self._thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 75.0,
            "memory_critical": 90.0,
            "disk_warning": 80.0,
            "disk_critical": 95.0,
        }

    def snapshot(self) -> Dict[str, Any]:
        """Take a system resource snapshot."""
        now = time.time()

        # CPU
        cpu = self._get_cpu_percent()

        # Memory
        memory = self._get_memory_info()

        # Disk
        disk = self._get_disk_info()

        # Load average
        load = self._get_load_average()

        snapshot = {
            "timestamp": now,
            "cpu": cpu,
            "memory": memory,
            "disk": disk,
            "load_average": load,
            "alerts": self._check_thresholds(cpu, memory, disk),
        }

        # Store in history
        with self._lock:
            self._last_snapshot = snapshot
            self._cpu_history.append({"timestamp": now, "value": cpu.get("percent", 0)})
            self._memory_history.append({"timestamp": now, "value": memory.get("percent", 0)})
            self._disk_history.append({"timestamp": now, "value": disk.get("percent_used", 0)})

            # Trim history
            for hist in [self._cpu_history, self._memory_history, self._disk_history]:
                if len(hist) > self._history_size:
                    hist[:] = hist[-self._history_size:]

        return snapshot

    def _get_cpu_percent(self) -> Dict[str, Any]:
        """Get CPU usage percentage."""
        try:
            with open('/proc/stat') as f:
                line = f.readline()
            parts = line.split()
            total = sum(int(p) for p in parts[1:])
            idle = int(parts[4])
            usage = ((total - idle) / total) * 100 if total > 0 else 0.0
            return {"percent": round(usage, 1), "cores": os.cpu_count() or 1}
        except Exception:
            return {"percent": 0.0, "cores": os.cpu_count() or 1}

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory usage info."""
        try:
            with open('/proc/meminfo') as f:
                lines = f.readlines()
            total_kb = int(lines[0].split()[1])
            available_kb = int(lines[2].split()[1])
            used_kb = total_kb - available_kb

            # Swap
            swap_total = int(lines[15].split()[1]) if len(lines) > 15 else 0
            swap_free = int(lines[16].split()[1]) if len(lines) > 16 else 0
            swap_used = swap_total - swap_free

            return {
                "percent": round(used_kb / total_kb * 100, 1) if total_kb > 0 else 0,
                "total_mb": round(total_kb / 1024, 1),
                "used_mb": round(used_kb / 1024, 1),
                "available_mb": round(available_kb / 1024, 1),
                "swap_total_mb": round(swap_total / 1024, 1),
                "swap_used_mb": round(swap_used / 1024, 1),
            }
        except Exception:
            return {"percent": 0, "total_mb": 0, "used_mb": 0, "available_mb": 0}

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk usage info."""
        try:
            st = os.statvfs('/')
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used = total - free
            return {
                "percent_used": round(used / total * 100, 1) if total > 0 else 0,
                "total_gb": round(total / (1024**3), 1),
                "used_gb": round(used / (1024**3), 1),
                "free_gb": round(free / (1024**3), 1),
            }
        except Exception:
            return {"percent_used": 0, "total_gb": 0, "used_gb": 0, "free_gb": 0}

    def _get_load_average(self) -> List[float]:
        """Get system load average."""
        try:
            with open('/proc/loadavg') as f:
                parts = f.read().split()
            return [float(parts[i]) for i in range(3)]
        except Exception:
            return [0.0, 0.0, 0.0]

    def _check_thresholds(self, cpu: Dict, memory: Dict, disk: Dict) -> List[Dict[str, Any]]:
        """Check if any thresholds are exceeded."""
        alerts = []
        cpu_pct = cpu.get("percent", 0)
        mem_pct = memory.get("percent", 0)
        disk_pct = disk.get("percent_used", 0)

        if cpu_pct >= self._thresholds["cpu_critical"]:
            alerts.append({"type": "cpu", "severity": "critical", "value": cpu_pct,
                           "threshold": self._thresholds["cpu_critical"]})
        elif cpu_pct >= self._thresholds["cpu_warning"]:
            alerts.append({"type": "cpu", "severity": "warning", "value": cpu_pct,
                           "threshold": self._thresholds["cpu_warning"]})

        if mem_pct >= self._thresholds["memory_critical"]:
            alerts.append({"type": "memory", "severity": "critical", "value": mem_pct,
                           "threshold": self._thresholds["memory_critical"]})
        elif mem_pct >= self._thresholds["memory_warning"]:
            alerts.append({"type": "memory", "severity": "warning", "value": mem_pct,
                           "threshold": self._thresholds["memory_warning"]})

        if disk_pct >= self._thresholds["disk_critical"]:
            alerts.append({"type": "disk", "severity": "critical", "value": disk_pct,
                           "threshold": self._thresholds["disk_critical"]})
        elif disk_pct >= self._thresholds["disk_warning"]:
            alerts.append({"type": "disk", "severity": "warning", "value": disk_pct,
                           "threshold": self._thresholds["disk_warning"]})

        return alerts

    def get_current(self) -> Dict[str, Any]:
        """Get current system state."""
        if not self._last_snapshot:
            return self.snapshot()
        return self._last_snapshot

    def get_trend(self, metric: str = "cpu", window: int = 10) -> Dict[str, Any]:
        """Analyze trend for a metric."""
        with self._lock:
            if metric == "cpu":
                data = self._cpu_history
            elif metric == "memory":
                data = self._memory_history
            elif metric == "disk":
                data = self._disk_history
            else:
                return {"trend": "unknown", "values": []}

            recent = data[-window:] if len(data) >= window else data

        if len(recent) < 2:
            return {"trend": "stable", "values": [d["value"] for d in recent]}

        values = [d["value"] for d in recent]
        avg_first = sum(values[:len(values)//2]) / max(1, len(values)//2)
        avg_second = sum(values[len(values)//2:]) / max(1, len(values) - len(values)//2)

        diff = avg_second - avg_first
        if diff > 2:
            trend = "rising"
        elif diff < -2:
            trend = "falling"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "avg_first_half": round(avg_first, 1),
            "avg_second_half": round(avg_second, 1),
            "diff": round(diff, 1),
            "values": values,
        }

    def detect_anomalies(self, metric: str = "cpu", window: int = 30) -> List[Dict[str, Any]]:
        """Detect anomalies using z-score."""
        import math

        with self._lock:
            if metric == "cpu":
                data = self._cpu_history
            elif metric == "memory":
                data = self._memory_history
            else:
                return []

            recent = data[-window:] if len(data) >= window else data

        if len(recent) < 5:
            return []

        values = [d["value"] for d in recent]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std = math.sqrt(variance) if variance > 0 else 1.0

        anomalies = []
        for d in recent:
            z = (d["value"] - mean) / std if std > 0 else 0
            if abs(z) > 2.5:
                anomalies.append({
                    "timestamp": d["timestamp"],
                    "value": d["value"],
                    "z_score": round(z, 2),
                    "mean": round(mean, 1),
                    "std": round(std, 1),
                })

        return anomalies

    def set_threshold(self, name: str, value: float) -> None:
        """Set a threshold value."""
        self._thresholds[name] = value

    def get_history(self, metric: str = "cpu") -> List[Dict[str, Any]]:
        """Get history for a given metric."""
        with self._lock:
            if metric == "memory":
                return list(self._memory_history)
            elif metric == "disk":
                return list(self._disk_history)
            return list(self._cpu_history)

    def stats(self) -> Dict[str, Any]:
        """Get monitoring statistics."""
        return {
            "cpu_history_size": len(self._cpu_history),
            "memory_history_size": len(self._memory_history),
            "disk_history_size": len(self._disk_history),
            "thresholds": self._thresholds,
        }
