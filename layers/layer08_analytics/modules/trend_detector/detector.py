"""Deterministic trend and anomaly detection."""
from __future__ import annotations
import math
import time
import uuid
from threading import RLock
from typing import Any, Dict, List, Optional


class TrendPoint:
    __slots__ = ("timestamp", "value", "label")
    def __init__(self, value: float = 0.0, label: str = "") -> None:
        if not math.isfinite(float(value)):
            raise ValueError("trend value must be finite")
        self.timestamp, self.value, self.label = time.time(), float(value), label
    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "value": self.value, "label": self.label}


class DetectedTrend:
    __slots__ = ("trend_id", "metric_name", "direction", "strength", "start_value",
                 "end_value", "data_points", "confidence", "anomalies")
    def __init__(self, metric_name: str = "", direction: str = "stable") -> None:
        self.trend_id = f"trend_{uuid.uuid4().hex}"
        self.metric_name, self.direction = metric_name, direction
        self.strength = self.confidence = 0.0
        self.start_value = self.end_value = 0.0
        self.data_points: List[TrendPoint] = []
        self.anomalies: List[Dict[str, Any]] = []
    def to_dict(self) -> Dict[str, Any]:
        return {"trend_id": self.trend_id, "metric_name": self.metric_name,
                "direction": self.direction, "strength": round(self.strength, 3),
                "confidence": round(self.confidence, 3), "anomaly_count": len(self.anomalies)}


class TrendDetector:
    def __init__(self) -> None:
        self._series: Dict[str, List[float]] = {}
        self._detected_trends: List[DetectedTrend] = []
        self._detection_count = 0
        self._lock = RLock()

    def add_datapoint(self, metric_name: str, value: float) -> None:
        if not metric_name.strip() or not math.isfinite(float(value)):
            raise ValueError("metric_name and finite value are required")
        with self._lock:
            self._series.setdefault(metric_name.strip(), []).append(float(value))

    def add_batch(self, metric_name: str, values: List[float]) -> None:
        for value in values:
            if not math.isfinite(float(value)):
                raise ValueError("all trend values must be finite")
        if not metric_name.strip():
            raise ValueError("metric_name is required")
        with self._lock:
            self._series.setdefault(metric_name.strip(), []).extend(float(v) for v in values)

    def detect(self, metric_name: str, sensitivity: float = 0.1) -> Optional[DetectedTrend]:
        if sensitivity <= 0:
            raise ValueError("sensitivity must be positive")
        with self._lock:
            values = list(self._series.get(metric_name, []))
        if len(values) < 3:
            return None
        trend = DetectedTrend(metric_name)
        trend.start_value, trend.end_value = values[0], values[-1]
        trend.data_points = [TrendPoint(v) for v in values]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = math.sqrt(variance)
        scale = max(1.0, abs(mean))
        change = trend.end_value - trend.start_value
        relative_change = change / max(1.0, abs(trend.start_value))
        if std_dev <= sensitivity * scale:
            trend.direction, trend.strength, trend.confidence = "stable", 0.0, 0.9
        elif relative_change >= sensitivity:
            trend.direction = "up"
            trend.strength = min(1.0, abs(relative_change))
            trend.confidence = 0.85
        elif relative_change <= -sensitivity:
            trend.direction = "down"
            trend.strength = min(1.0, abs(relative_change))
            trend.confidence = 0.85
        else:
            trend.direction, trend.strength, trend.confidence = "stable", 0.0, 0.8
        if std_dev > 0:
            for i, value in enumerate(values):
                z = abs(value - mean) / std_dev
                if z > 2.5:
                    trend.anomalies.append({"index": i, "value": value, "z_score": round(z, 2)})
        with self._lock:
            self._detected_trends.append(trend)
            self._detection_count += 1
        return trend

    def detect_all(self, sensitivity: float = 0.1) -> List[DetectedTrend]:
        names = self.get_all_metrics()
        results: List[DetectedTrend] = []
        for name in names:
            detected = self.detect(name, sensitivity)
            if detected is not None:
                results.append(detected)
        return results

    def get_series(self, metric_name: str) -> List[float]:
        with self._lock:
            return list(self._series.get(metric_name, []))
    def get_all_metrics(self) -> List[str]:
        with self._lock:
            return list(self._series.keys())
    def get_trends(self) -> List[DetectedTrend]:
        with self._lock:
            return list(self._detected_trends)
    @property
    def detection_count(self) -> int:
        with self._lock:
            return self._detection_count
