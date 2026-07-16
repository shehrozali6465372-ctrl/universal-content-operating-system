"""Trend Tracker — Track hourly/daily growth, peak detection, virality."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class TrendDataPoint:
    """A single data point in a trend."""

    __slots__ = ("timestamp", "value", "label")

    def __init__(self, value: float, label: str = "") -> None:
        self.timestamp: float = time.time()
        self.value = value
        self.label = label

    def to_dict(self) -> Dict[str, Any]:
        return {"timestamp": self.timestamp, "value": self.value, "label": self.label}


class TrendResult:
    """Result of a trend analysis."""

    __slots__ = ("trend_direction", "growth_rate", "is_viral",
                 "peak_value", "peak_index", "data_points_count")

    def __init__(self) -> None:
        self.trend_direction: str = "stable"  # up, down, stable
        self.growth_rate: float = 0.0
        self.is_viral: bool = False
        self.peak_value: float = 0.0
        self.peak_index: int = 0
        self.data_points_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trend_direction": self.trend_direction,
            "growth_rate": round(self.growth_rate, 3),
            "is_viral": self.is_viral,
            "peak_value": self.peak_value,
            "peak_index": self.peak_index,
            "data_points_count": self.data_points_count,
        }


class TrendTracker:
    """Track growth trends, detect peaks, and identify viral content."""

    VIRALITY_THRESHOLD = 10.0  # 10x growth = viral

    def __init__(self) -> None:
        self._history: Dict[str, List[TrendDataPoint]] = {}
        self._tracking_count = 0

    def record(self, post_id: str, value: float, label: str = "") -> TrendDataPoint:
        dp = TrendDataPoint(value, label)
        if post_id not in self._history:
            self._history[post_id] = []
        self._history[post_id].append(dp)
        return dp

    def get_history(self, post_id: str) -> List[TrendDataPoint]:
        return list(self._history.get(post_id, []))

    def analyze(self, post_id: str) -> TrendResult:
        result = TrendResult()
        points = self._history.get(post_id, [])
        if len(points) < 2:
            result.data_points_count = len(points)
            if points:
                result.peak_value = points[0].value
            return result

        values = [p.value for p in points]
        result.data_points_count = len(values)
        result.peak_value = max(values)
        result.peak_index = values.index(result.peak_value)

        first_half = sum(values[:len(values) // 2]) / max(1, len(values) // 2)
        second_half = sum(values[len(values) // 2:]) / max(1, len(values) - len(values) // 2)

        if second_half > first_half * 1.1:
            result.trend_direction = "up"
        elif second_half < first_half * 0.9:
            result.trend_direction = "down"
        else:
            result.trend_direction = "stable"

        result.growth_rate = round((second_half - first_half) / max(1, first_half) * 100, 2)
        result.is_viral = result.growth_rate >= self.VIRALITY_THRESHOLD * 100

        self._tracking_count += 1
        return result

    def get_all_post_ids(self) -> List[str]:
        return list(self._history.keys())

    @property
    def tracking_count(self) -> int:
        return self._tracking_count
