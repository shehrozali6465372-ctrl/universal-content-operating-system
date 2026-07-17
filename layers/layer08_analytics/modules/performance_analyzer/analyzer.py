"""Performance Analyzer — Analyze performance across dimensions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class PerformanceDimension:
    """A dimension to analyze performance across."""

    __slots__ = ("dimension_id", "name", "values", "timestamps", "metadata")

    def __init__(self, dimension_id: str = "", name: str = "") -> None:
        self.dimension_id = dimension_id
        self.name = name
        self.values: List[float] = []
        self.timestamps: List[float] = []
        self.metadata: Dict[str, Any] = {}

    def add_datapoint(self, value: float, timestamp: float = 0.0) -> None:
        self.values.append(value)
        self.timestamps.append(timestamp or time.time())

    @property
    def count(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        return sum(self.values) / max(1, len(self.values))

    @property
    def trend(self) -> str:
        if len(self.values) < 2:
            return "insufficient_data"
        recent = self.values[-5:] if len(self.values) >= 5 else self.values
        first_half = sum(recent[:len(recent)//2]) / max(1, len(recent)//2)
        second_half = sum(recent[len(recent)//2:]) / max(1, len(recent) - len(recent)//2)
        if second_half > first_half * 1.05:
            return "improving"
        elif second_half < first_half * 0.95:
            return "declining"
        return "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "name": self.name,
            "count": self.count,
            "mean": round(self.mean, 4),
            "trend": self.trend,
        }


class PerformanceResult:
    """Result of a performance analysis."""

    __slots__ = ("dimension_id", "score", "rating", "trend",
                 "insights", "benchmark_comparison")

    def __init__(self, dimension_id: str = "") -> None:
        self.dimension_id = dimension_id
        self.score: float = 0.0
        self.rating: str = ""
        self.trend: str = ""
        self.insights: List[str] = []
        self.benchmark_comparison: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension_id": self.dimension_id,
            "score": round(self.score, 2),
            "rating": self.rating,
            "trend": self.trend,
            "insights": self.insights,
        }


class PerformanceAnalyzer:
    """Analyze performance across multiple dimensions."""

    BENCHMARKS = {
        "engagement_rate": {"excellent": 5.0, "good": 2.0, "average": 0.5},
        "conversion_rate": {"excellent": 3.0, "good": 1.0, "average": 0.3},
        "growth_rate": {"excellent": 20.0, "good": 5.0, "average": 1.0},
    }

    def __init__(self) -> None:
        self._dimensions: Dict[str, PerformanceDimension] = {}
        self._results: List[PerformanceResult] = []
        self._analysis_count = 0

    def add_dimension(self, dimension: PerformanceDimension) -> None:
        self._dimensions[dimension.dimension_id] = dimension

    def analyze(self, dimension_id: str) -> Optional[PerformanceResult]:
        dim = self._dimensions.get(dimension_id)
        if not dim or dim.count == 0:
            return None
        result = PerformanceResult(dimension_id)
        result.score = dim.mean
        result.trend = dim.trend
        result.rating = self._get_rating(dim.name, dim.mean)
        result.insights = self._generate_insights(dim)
        result.benchmark_comparison = self._compare_benchmark(dim.name, dim.mean)
        self._results.append(result)
        self._analysis_count += 1
        return result

    def analyze_all(self) -> List[PerformanceResult]:
        results = []
        for dim_id in self._dimensions:
            r = self.analyze(dim_id)
            if r:
                results.append(r)
        return results

    def get_dimension(self, dimension_id: str) -> Optional[PerformanceDimension]:
        return self._dimensions.get(dimension_id)

    def get_all_dimensions(self) -> List[PerformanceDimension]:
        return list(self._dimensions.values())

    def _get_rating(self, name: str, value: float) -> str:
        benchmarks = self.BENCHMARKS.get(name)
        if not benchmarks:
            return "unrated"
        if value >= benchmarks["excellent"]:
            return "excellent"
        elif value >= benchmarks["good"]:
            return "good"
        elif value >= benchmarks["average"]:
            return "average"
        return "below_average"

    def _generate_insights(self, dim: PerformanceDimension) -> List[str]:
        insights = []
        if dim.trend == "improving":
            insights.append(f"{dim.name} is trending upward")
        elif dim.trend == "declining":
            insights.append(f"{dim.name} is declining — needs attention")
        if dim.mean > 0:
            insights.append(f"Average {dim.name}: {round(dim.mean, 2)}")
        return insights

    def _compare_benchmark(self, name: str, value: float) -> Dict[str, Any]:
        benchmarks = self.BENCHMARKS.get(name, {})
        comparison: Dict[str, Any] = {}
        for level, threshold in benchmarks.items():
            comparison[level] = {
                "threshold": threshold,
                "exceeds": value >= threshold,
                "gap": round(value - threshold, 2),
            }
        return comparison

    @property
    def analysis_count(self) -> int:
        return self._analysis_count
