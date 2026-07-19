"""MetricsEngine — collect, store, and query system metrics."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from enum import Enum
from collections import defaultdict


class MetricType(str, Enum):
    COUNTER = "counter"; GAUGE = "gauge"; HISTOGRAM = "histogram"; SUMMARY = "summary"


class MetricPoint:
    __slots__ = ("name", "value", "metric_type", "labels", "timestamp", "metadata")

    def __init__(self, name: str, value: float, metric_type: MetricType = MetricType.COUNTER,
                 labels: Optional[Dict[str, str]] = None) -> None:
        self.name = name
        self.value = value
        self.metric_type = metric_type
        self.labels = labels or {}
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}


class MetricsEngine:
    def __init__(self) -> None:
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        self._history: List[MetricPoint] = []

    def increment(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._history.append(MetricPoint(name, self._counters[key], MetricType.COUNTER, labels))

    def decrement(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        self.increment(name, -value, labels)

    def gauge_set(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._history.append(MetricPoint(name, value, MetricType.GAUGE, labels))

    def histogram_observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            self._history.append(MetricPoint(name, value, MetricType.HISTOGRAM, labels))

    def get_counter(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        key = self._make_key(name, labels)
        return self._counters.get(key, 0.0)

    def get_gauge(self, name: str, labels: Optional[Dict[str, str]] = None) -> float:
        key = self._make_key(name, labels)
        return self._gauges.get(key, 0.0)

    def get_histogram(self, name: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, float]:
        key = self._make_key(name, labels)
        values = self._histograms.get(key, [])
        if not values:
            return {"count": 0, "min": 0, "max": 0, "avg": 0, "p50": 0, "p95": 0, "p99": 0}
        sorted_v = sorted(values)
        return {
            "count": len(values), "min": sorted_v[0], "max": sorted_v[-1],
            "avg": round(sum(values) / len(values), 3),
            "p50": sorted_v[len(sorted_v) // 2],
            "p95": sorted_v[int(len(sorted_v) * 0.95)] if len(sorted_v) >= 20 else sorted_v[-1],
            "p99": sorted_v[int(len(sorted_v) * 0.99)] if len(sorted_v) >= 100 else sorted_v[-1],
        }

    def _make_key(self, name: str, labels: Optional[Dict[str, str]] = None) -> str:
        if labels:
            label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
            return f"{name}{{{label_str}}}"
        return name

    def summary(self) -> Dict[str, Any]:
        return {"counters": dict(self._counters), "gauges": dict(self._gauges),
                "histograms": {k: len(v) for k, v in self._histograms.items()},
                "total_points": len(self._history)}

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()
            self._histograms.clear()
            self._history.clear()
