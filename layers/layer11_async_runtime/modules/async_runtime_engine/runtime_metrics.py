"""RuntimeMetrics — Track runtime performance metrics."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class RuntimeMetrics:
    """Track tasks, latency, throughput, errors, and resources."""

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}
        self._latencies: List[float] = []
        self._max_latency_history: int = 1000

    def increment(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) + value

    def decrement(self, name: str, value: int = 1) -> None:
        self._counters[name] = self._counters.get(name, 0) - value

    def set_gauge(self, name: str, value: float) -> None:
        self._gauges[name] = value

    def record_latency(self, name: str, latency_ms: float) -> None:
        self._latencies.append(latency_ms)
        if len(self._latencies) > self._max_latency_history:
            self._latencies = self._latencies[-self._max_latency_history:]
        self._gauges[f"last_{name}_latency_ms"] = latency_ms

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def get_uptime(self) -> float:
        return round(time.time() - self._start_time, 1)

    def get_throughput(self) -> float:
        uptime = self.get_uptime()
        if uptime <= 0:
            return 0.0
        completed = self._counters.get("tasks_completed", 0)
        return round(completed / uptime, 2)

    def get_avg_latency(self) -> float:
        if not self._latencies:
            return 0.0
        return round(sum(self._latencies) / len(self._latencies), 2)

    def get_error_rate(self) -> float:
        total = self._counters.get("tasks_completed", 0) + self._counters.get("tasks_failed", 0)
        if total == 0:
            return 0.0
        return round(self._counters.get("tasks_failed", 0) / total, 4)

    def to_dict(self) -> Dict[str, Any]:
        return {"uptime": self.get_uptime(), "counters": dict(self._counters),
                "gauges": dict(self._gauges), "throughput": self.get_throughput(),
                "avg_latency_ms": self.get_avg_latency(), "error_rate": self.get_error_rate()}

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._latencies.clear()
        self._start_time = time.time()
