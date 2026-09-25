"""Thread-safe performance analysis with configurable benchmark policy."""
from __future__ import annotations
import math
import time
from threading import RLock
from typing import Any, Dict, List, Optional


class PerformanceDimension:
    __slots__ = ("dimension_id", "name", "values", "timestamps", "metadata")
    def __init__(self, dimension_id: str = "", name: str = "") -> None:
        if not dimension_id.strip(): raise ValueError("dimension_id is required")
        self.dimension_id, self.name = dimension_id, name
        self.values: List[float] = []; self.timestamps: List[float] = []; self.metadata: Dict[str, Any] = []
    def add_datapoint(self, value: float, timestamp: float = 0.0) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            raise ValueError("performance value must be finite")
        self.values.append(float(value)); self.timestamps.append(timestamp or time.time())
    @property
    def count(self) -> int: return len(self.values)
    @property
    def mean(self) -> float: return sum(self.values) / len(self.values) if self.values else 0.0
    @property
    def trend(self) -> str:
        if len(self.values) < 2: return "insufficient_data"
        recent = self.values[-5:]
        split = max(1, len(recent)//2)
        first = sum(recent[:split])/split; second = sum(recent[split:])/max(1, len(recent)-split)
        if second > first * 1.05: return "improving"
        if second < first * 0.95: return "declining"
        return "stable"
    def to_dict(self) -> Dict[str, Any]:
        return {"dimension_id": self.dimension_id, "name": self.name, "count": self.count,
                "mean": round(self.mean, 4), "trend": self.trend}


class PerformanceResult:
    __slots__ = ("dimension_id", "score", "rating", "trend", "insights", "benchmark_comparison")
    def __init__(self, dimension_id: str = "") -> None:
        self.dimension_id = dimension_id; self.score = 0.0; self.rating = ""; self.trend = ""
        self.insights: List[str] = []; self.benchmark_comparison: Dict[str, Any] = {}
    def to_dict(self) -> Dict[str, Any]:
        return {"dimension_id": self.dimension_id, "score": round(self.score, 2),
                "rating": self.rating, "trend": self.trend, "insights": list(self.insights)}


class PerformanceAnalyzer:
    DEFAULT_BENCHMARKS = {
        "engagement_rate": {"excellent": 5.0, "good": 2.0, "average": 0.5},
        "conversion_rate": {"excellent": 3.0, "good": 1.0, "average": 0.3},
        "growth_rate": {"excellent": 20.0, "good": 5.0, "average": 1.0},
    }
    def __init__(self, benchmarks: Optional[Dict[str, Dict[str, float]]] = None) -> None:
        self.BENCHMARKS = benchmarks if benchmarks is not None else self.DEFAULT_BENCHMARKS
        self._dimensions: Dict[str, PerformanceDimension] = {}; self._results: List[PerformanceResult] = []
        self._analysis_count = 0; self._lock = RLock()
    def add_dimension(self, dimension: PerformanceDimension) -> None:
        with self._lock:
            if dimension.dimension_id in self._dimensions: raise ValueError("duplicate dimension_id")
            self._dimensions[dimension.dimension_id] = dimension
    def analyze(self, dimension_id: str) -> Optional[PerformanceResult]:
        with self._lock: dim = self._dimensions.get(dimension_id)
        if not dim or dim.count == 0: return None
        result = PerformanceResult(dimension_id); result.score = dim.mean; result.trend = dim.trend
        result.rating = self._get_rating(dim.name, dim.mean); result.insights = self._generate_insights(dim)
        result.benchmark_comparison = self._compare_benchmark(dim.name, dim.mean)
        with self._lock: self._results.append(result); self._analysis_count += 1
        return result
    def analyze_all(self) -> List[PerformanceResult]:
        return [result for dimension in self.get_all_dimensions() if (result := self.analyze(dimension.dimension_id))]
    def get_dimension(self, dimension_id: str) -> Optional[PerformanceDimension]:
        with self._lock: return self._dimensions.get(dimension_id)
    def get_all_dimensions(self) -> List[PerformanceDimension]:
        with self._lock: return list(self._dimensions.values())
    def _get_rating(self, name: str, value: float) -> str:
        benchmarks = self.BENCHMARKS.get(name)
        if not benchmarks: return "unrated"
        if value >= benchmarks["excellent"]: return "excellent"
        if value >= benchmarks["good"]: return "good"
        if value >= benchmarks["average"]: return "average"
        return "below_average"
    def _generate_insights(self, dim: PerformanceDimension) -> List[str]:
        if dim.trend == "improving": insights = [f"{dim.name} is trending upward"]
        elif dim.trend == "declining": insights = [f"{dim.name} is declining — needs attention"]
        else: insights = []
        if dim.mean > 0: insights.append(f"Average {dim.name}: {round(dim.mean, 2)}")
        return insights
    def _compare_benchmark(self, name: str, value: float) -> Dict[str, Any]:
        return {level: {"threshold": threshold, "exceeds": value >= threshold, "gap": round(value-threshold, 2)}
                for level, threshold in self.BENCHMARKS.get(name, {}).items()}
    @property
    def analysis_count(self) -> int:
        with self._lock: return self._analysis_count
