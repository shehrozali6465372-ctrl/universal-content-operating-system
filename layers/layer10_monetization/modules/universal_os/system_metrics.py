"""SystemMetrics — bounded operational counters, gauges, and event history."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class SystemMetrics:
    def __init__(self, max_events: int = 10000) -> None:
        if max_events <= 0:
            raise ValueError("max_events must be positive")
        self._max_events = max_events
        self._start_time = time.time()
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
                     tags: Optional[Dict[str, str]] = None) -> None:
        self._metrics.append({"type": event_type, "value": value,
                              "timestamp": time.time(), "tags": dict(tags or {})})
        if len(self._metrics) > self._max_events:
            del self._metrics[:-self._max_events]

    def get_uptime(self) -> float:
        return round(time.time() - self._start_time, 1)

    def get_counter(self, name: str) -> int:
        return self._counters.get(name, 0)

    def get_gauge(self, name: str) -> float:
        return self._gauges.get(name, 0.0)

    def get_success_rate(self) -> float:
        total = self._counters.get("success", 0) + self._counters.get("failure", 0)
        return round(self._counters.get("success", 0) / total, 3) if total else 1.0

    def get_all_counters(self) -> Dict[str, int]:
        return dict(self._counters)

    def get_all_gauges(self) -> Dict[str, float]:
        return dict(self._gauges)

    def get_recent_events(self, event_type: str = "", count: int = 10) -> List[Dict[str, Any]]:
        if count <= 0:
            return []
        events = self._metrics if not event_type else [
            event for event in self._metrics if event["type"] == event_type
        ]
        return list(events[-count:])

    def get_stats(self) -> Dict[str, Any]:
        return {"uptime": self.get_uptime(), "total_events": len(self._metrics),
                "counters": dict(self._counters), "gauges": dict(self._gauges),
                "success_rate": self.get_success_rate()}

    def reset(self) -> None:
        self._counters.clear()
        self._gauges.clear()
        self._metrics.clear()
        self._start_time = time.time()
