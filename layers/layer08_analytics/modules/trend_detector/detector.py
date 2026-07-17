"""Trend Detector — Detect trends, anomalies, and patterns in analytics data."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class TrendPoint:
    """A point in a detected trend."""

    __slots__ = ("timestamp", "value", "label")

    def __init__(self, value: float = 0.0, label: str = "") -> None:
        self.timestamp: float = time.time()
        self.value = value
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "value": self.value, "label": self.label}


class DetectedTrend:
    """A detected trend in the data."""

    __slots__ = ("trend_id", "metric_name", "direction", "strength",
                 "start_value", "end_value", "data_points", "confidence",
                 "anomalies")

    def __init__(self, metric_name: str = "", direction: str = "stable") -> None:
        self.trend_id: str = f"trend_{int(time.time() * 1000) % 100000}"
        self.metric_name = metric_name
        self.direction = direction
        self.strength: float = 0.0
        self.start_value: float = 0.0
        self.end_value: float = 0.0
        self.data_points: List[TrendPoint] = []
        self.confidence: float = 0.0
        self.anomalies: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_id": self.trend_id,
            "metric_name": self.metric_name,
            "direction": self.direction,
            "strength": round(self.strength, 3),
            "confidence": round(self.confidence, 3),
            "anomaly_count": len(self.anomalies),
        }


class TrendDetector:
    """Detect trends and anomalies in data series."""

    def __init__(self) -> None:
        self._series: Dict[str, List[float]] = {}
        self._detected_trends: List[DetectedTrend] = []
        self._detection_count = 0

    def add_datapoint(self, metric_name: str, value: float) -> None:
        self._series.setdefault(metric_name, []).append(value)

    def add_batch(self, metric_name: str, values: List[float]) -> None:
        self._series.setdefault(metric_name, []).extend(values)

    def detect(self, metric_name: str, sensitivity: float = 0.1) -> Optional[DetectedTrend]:
        values = self._series.get(metric_name, [])
        if len(values) < 3:
            return None
        trend = DetectedTrend(metric_name)
        trend.start_value = values[0]
        trend.end_value = values[-1]
        trend.data_points = [TrendPoint(v) for v in values]
        mean = sum(values) / len(values)
        std_dev = (sum((x - mean) ** 2 for x in values) / len(values)) ** 0.5

        if std_dev < sensitivity * mean:
            trend.direction = "stable"
            trend.strength = 0.0
            trend.confidence = 0.9
        elif trend.end_value > trend.start_value * (1 + sensitivity):
            trend.direction = "up"
            trend.strength = min(1.0, (trend.end_value - trend.start_value) / max(1, abs(trend.start_value)))
            trend.confidence = 0.85
        elif trend.end_value < trend.start_value * (1 - sensitivity):
            trend.direction = "down"
            trend.strength = min(1.0, (trend.start_value - trend.end_value) / max(1, abs(trend.start_value)))
            trend.confidence = 0.85
        else:
            trend.direction = "stable"
            trend.strength = 0.0
            trend.confidence = 0.8

        if std_dev > 0:
            for i, v in enumerate(values):
                z_score = abs(v - mean) / std_dev
                if z_score > 2.5:
                    trend.anomalies.append({
                        "index": i,
                        "value": v,
                        "z_score": round(z_score, 2),
                    })

        self._detected_trends.append(trend)
        self._detection_count += 1
        return trend

    def detect_all(self, sensitivity: float = 0.1) -> List[DetectedTrend]:
        return [self.detect(name, sensitivity) for name in self._series if self.detect(name, sensitivity)]

    def get_series(self, metric_name: str) -> List[float]:
        return list(self._series.get(metric_name, []))

    def get_all_metrics(self) -> List[str]:
        return list(self._series.keys())

    def get_trends(self) -> List[DetectedTrend]:
        return list(self._detected_trends)

    @property
    def detection_count(self) -> int:
        return self._detection_count
