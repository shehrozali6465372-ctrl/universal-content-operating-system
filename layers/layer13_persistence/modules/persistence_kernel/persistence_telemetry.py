"""persistence_telemetry.py — Telemetry collection."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class TelemetrySpan:
    """A telemetry span."""
    __slots__ = ("span_id", "operation", "start_time", "end_time", "attributes", "status")
    _counter = 0

    def __init__(self, operation: str) -> None:
        PersistenceTelemetry._counter += 1
        self.span_id: int = PersistenceTelemetry._counter
        self.operation = operation
        self.start_time: float = time.time()
        self.end_time: float = 0.0
        self.attributes: Dict[str, Any] = {}
        self.status: str = "ok"

    def finish(self, status: str = "ok") -> None:
        self.end_time = time.time()
        self.status = status

    def duration_ms(self) -> float:
        end = self.end_time if self.end_time else time.time()
        return (end - self.start_time) * 1000

    def to_dict(self) -> Dict[str, Any]:
        return {"operation": self.operation, "duration_ms": self.duration_ms(),
                "status": self.status}


class PersistenceTelemetry:
    """Collects telemetry data."""
    _counter = 0

    def __init__(self) -> None:
        self._spans: List[TelemetrySpan] = []
        self._counters: Dict[str, int] = {}

    def start_span(self, operation: str) -> TelemetrySpan:
        span = TelemetrySpan(operation)
        self._spans.append(span)
        return span

    def increment(self, metric: str, value: int = 1) -> None:
        self._counters[metric] = self._counters.get(metric, 0) + value

    def get_spans(self, limit: int = 100) -> List[TelemetrySpan]:
        return self._spans[-limit:]

    def get_counters(self) -> Dict[str, int]:
        return dict(self._counters)

    def stats(self) -> Dict[str, Any]:
        return {"spans": len(self._spans), "counters": len(self._counters)}
