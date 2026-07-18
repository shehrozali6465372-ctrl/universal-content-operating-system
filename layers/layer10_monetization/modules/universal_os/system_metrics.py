"""SystemMetrics — Track uptime, success rate, latency, learning rate, revenue."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class SystemMetrics:
    """Track system-wide metrics: uptime, success rate, latency, revenue."""

    def __init__(self) -> None:
        self._start_time: float = time.time()
        self._metrics: List[Dict[str, Any]] = []
        self._counters: Dict[str, int] = {}
        self._gauges: Dict[str, float] = {}

    def increment(self, counter_name: str, value: int = 1) -> None:
        self._counters[counter_name] = self._counters.get(counter_name, 0) + value

    def decrement(self, counter_name: str, value: int = 1) -> None:
        self._counters[counter_name] = self._counters.get(counter_name, 0) - value

    def set_gauge(self, gauge_name: str, value: float) -> None:
        self._gauges[gauge_name] = value

    def record_event(self, event_type: str, value: float = 0.0,
                     tags: Dict[str, str] = None) -> None:
        self._metrics.append({"type": event_type, "value": value,
                               "timestamp": time.time(), "tags": tags or {}})

    def get_uptime(self) -> float:
        return round(time.time() - self._start_time, 1)

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def get_success_rate(self) -> float:
        total = self._counters.get("success", 0) + self._counters.get("failure", 0)
        if total == 0:
            return 1.0
        return round(self._counters.get("success", 0) / total, 3)

    def get_all_counters(self) -> Dict[str, int]:
        return dict(self._counters)

    def get_all_gauges(self) -> Dict[str, float]:
        return dict(self._gauges)

    def get_recent_events(self, event_type: str = "",
                          count: int = 10) -> List[Dict[str, Any]]:
        events = self._metrics
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return events[-count:]

    def get_stats(self) -> Dict[str, Any]:
        return {"uptime": self.get_uptime(),
                "total_events": len(self._metrics),
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "success_rate": self.get_success_rate()}

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._metrics.clear()
        self._start_time = time.time()
