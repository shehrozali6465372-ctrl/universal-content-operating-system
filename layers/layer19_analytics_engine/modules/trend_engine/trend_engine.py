"""TrendEngine — detect and analyze trends in time series data."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from enum import Enum


class TrendDirection(str, Enum):
    UP = "up"; DOWN = "down"; STABLE = "stable"; VOLATILE = "volatile"


class TrendPoint:
    __slots__ = ("timestamp", "value", "label")

    def __init__(self, value: float, label: str = "") -> None:
        self.timestamp = time.time()
        self.value = value
        self.label = label


class TrendEngine:
    def __init__(self) -> None:
        self._series: Dict[str, List[TrendPoint]] = {}

    def add_point(self, series_name: str, value: float, label: str = "") -> TrendPoint:
        point = TrendPoint(value, label)
        self._series.setdefault(series_name, []).append(point)
        return point

    def detect_trend(self, series_name: str, window: int = 5) -> Dict[str, Any]:
        points = self._series.get(series_name, [])
        if len(points) < window:
            return {"direction": TrendDirection.STABLE.value, "confidence": 0.0}
        recent = points[-window:]
        values = [p.value for p in recent]
        slope = (values[-1] - values[0]) / max(window - 1, 1)
        avg = sum(values) / len(values)
        volatility = max(values) - min(values)
        direction = TrendDirection.STABLE
        if abs(slope) > avg * 0.1:
            direction = TrendDirection.UP if slope > 0 else TrendDirection.DOWN
        if volatility > avg * 0.3:
            direction = TrendDirection.VOLATILE
        confidence = min(abs(slope) / max(avg, 0.01), 1.0)
        return {"direction": direction.value, "slope": round(slope, 4),
                "confidence": round(confidence, 4),
                "latest": values[-1], "window": window}

    def get_series(self, series_name: str) -> List[Dict[str, Any]]:
        return [{"value": p.value, "label": p.label, "timestamp": p.timestamp}
                for p in self._series.get(series_name, [])]

    def list_series(self) -> List[str]:
        return list(self._series.keys())

    def moving_average(self, series_name: str, window: int = 3) -> List[float]:
        points = self._series.get(series_name, [])
        values = [p.value for p in points]
        if len(values) < window:
            return values
        return [round(sum(values[i:i+window]) / window, 4) for i in range(len(values) - window + 1)]
