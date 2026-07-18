"""TrendAnalyzer — Detect performance trends and patterns."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_TA_COUNTER = itertools.count(1)


class TrendPattern:
    """A detected trend pattern."""

    __slots__ = ("pattern_id", "pattern_type", "description", "direction",
                 "strength", "platform", "metric", "detected_at")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.pattern_id: str = f"tp_{next(_TA_COUNTER)}"
        self.pattern_type = pattern_type
        self.description = description
        self.direction: str = "stable"  # up, down, stable, volatile
        self.strength: float = 0.0
        self.platform: str = ""
        self.metric: str = ""
        self.detected_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"pattern_id": self.pattern_id, "type": self.pattern_type,
                "direction": self.direction, "strength": round(self.strength, 3),
                "metric": self.metric}


class TrendAnalyzer:
    """Detect trends, anomalies, and patterns in analytics data."""

    def __init__(self) -> None:
        self._patterns: List[TrendPattern] = []
        self._baselines: Dict[str, float] = {}

    def analyze(self, metric_name: str, values: List[float],
                platform: str = "") -> TrendPattern:
        pattern = TrendPattern("performance_trend", f"Trend for {metric_name}")
        pattern.platform = platform
        pattern.metric = metric_name
        if len(values) < 2:
            pattern.direction = "stable"
            pattern.strength = 0.0
        else:
            recent = values[-1]
            previous = values[-2]
            baseline = self._baselines.get(metric_name, previous)
            if baseline > 0:
                change = (recent - baseline) / baseline
            else:
                change = 0.0
            if change > 0.1:
                pattern.direction = "up"
                pattern.strength = min(1.0, abs(change))
            elif change < -0.1:
                pattern.direction = "down"
                pattern.strength = min(1.0, abs(change))
            else:
                pattern.direction = "stable"
                pattern.strength = 0.0
            self._baselines[metric_name] = recent
        self._patterns.append(pattern)
        return pattern

    def detect_anomaly(self, metric_name: str, value: float,
                       threshold: float = 2.0) -> bool:
        baseline = self._baselines.get(metric_name, value)
        if baseline == 0:
            return False
        deviation = abs(value - baseline) / baseline
        return deviation > threshold

    def set_baseline(self, metric_name: str, value: float) -> None:
        self._baselines[metric_name] = value

    def get_patterns(self, platform: str = "",
                     direction: str = "") -> List[TrendPattern]:
        results = self._patterns
        if platform:
            results = [p for p in results if p.platform == platform]
        if direction:
            results = [p for p in results if p.direction == direction]
        return results

    def get_stats(self) -> Dict[str, Any]:
        directions: Dict[str, int] = {}
        for p in self._patterns:
            directions[p.direction] = directions.get(p.direction, 0) + 1
        return {"total_patterns": len(self._patterns),
                "by_direction": directions, "baselines": len(self._baselines)}
