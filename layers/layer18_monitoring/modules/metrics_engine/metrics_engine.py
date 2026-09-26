"""Thread-safe bounded metrics collection."""
from __future__ import annotations

import threading
import time
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional


class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricPoint:
    __slots__ = ("name", "value", "metric_type", "labels", "timestamp", "metadata")

    def __init__(self, name: str, value: float, metric_type: MetricType = MetricType.COUNTER,
                 labels: Optional[Dict[str, str]] = None) -> None:
        self.name, self.value, self.metric_type = name, float(value), metric_type
        self.labels = dict(labels or {})
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "value": self.value, "type": self.metric_type.value,
                "labels": dict(self.labels), "timestamp": self.timestamp}


class MetricsEngine:
    def __init__(self, history_size: int = 10000) -> None:
        if history_size <= 0:
            raise ValueError("history_size must be positive")
        self._history_size = history_size
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
        self._history: List[MetricPoint] = []

    @staticmethod
    def _make_key(name: str, labels: Optional[Dict[str, str]] = None) -> str:
        if not name or not name.strip():
            raise ValueError("metric name is required")
        if not labels:
            return name
        return f'{name}' + "{" + ",".join(f"{k}={labels[k]}" for k in sorted(labels)) + "}"

    def increment(self, name: str, value: float = 1.0,
                  labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += float(value)
            self._record(MetricPoint(name, self._counters[key], MetricType.COUNTER, labels))

    def decrement(self, name: str, value: float = 1.0,
                  labels: Optional[Dict[str, str]] = None) -> None:
        self.increment(name, -value, labels)

    def gauge_set(self, name: str, value: float,
                  labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = float(value)
            self._record(MetricPoint(name, value, MetricType.GAUGE, labels))

    def histogram_observe(self, name: str, value: float,
                          labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms[key]
            values.append(float(value))
            if len(values) > self._history_size:
                del values[:-self._history_size]
            self._record(MetricPoint(name, value, MetricType.HISTOGRAM, labels))

    def _record(self, point: MetricPoint) -> None:
        self._history.append(point)
        if len(self._history) > self._history_size:
            del self._history[:-self._history_size]

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        with self._lock:
            return self._counters.get(self._make_key(name, labels), 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        with self._lock:
            return self._gauges.get(self._make_key(name, labels), 0.0)

    def get_histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        with self._lock:
            values = list(self._histograms.get(self._make_key(name, labels), []))
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        values.sort()
        n = len(values)
        def percentile(q: float) -> float:
            return values[min(n - 1, max(0, int((n - 1) * q)))]
        return {"count": n, "min": values[0], "max": values[-1],
                "avg": round(sum(values) / n, 3), "p50": percentile(.50),
                "p95": percentile(.95), "p99": percentile(.99)}

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {"counters": dict(self._counters), "gauges": dict(self._gauges),
                    "histograms": {k: len(v) for k, v in self._histograms.items()},
                    "total_points": len(self._history)}

    def reset(self) -> None:
        with self._lock:
            self._counters.clear(); self._gauges.clear()
            self._histograms.clear(); self._history.clear()
