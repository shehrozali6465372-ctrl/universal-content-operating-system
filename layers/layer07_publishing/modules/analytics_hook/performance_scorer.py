"""Performance Scorer — Score and grade analytics performance."""
from __future__ import annotations
from typing import Any, Dict

from layers.layer07_publishing.modules.analytics_hook.analytics_event import AnalyticsEvent

GRADE_THRESHOLDS = [
    (95, "A+"), (90, "A"), (85, "A-"), (80, "B+"),
    (75, "B"), (70, "B-"), (65, "C+"), (60, "C"),
    (50, "D"), (0, "F"),
]


class PerformanceResult:
    """Performance scoring result."""

    __slots__ = ("score", "grade", "success_level", "breakdown", "benchmarks")

    def __init__(self) -> None:
        self.score: float = 0.0
        self.grade: str = "F"
        self.success_level: str = "poor"
        self.breakdown: Dict[str, float] = {}
        self.benchmarks: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 2),
            "grade": self.grade,
            "success_level": self.success_level,
            "breakdown": {k: round(v, 2) for k, v in self.breakdown.items()},
            "benchmarks": self.benchmarks,
        }


class PerformanceScorer:
    """Score analytics performance and assign grades."""

    WEIGHTS = {
        "engagement": 0.35,
        "reach": 0.25,
        "conversion": 0.20,
        "growth": 0.20,
    }

    BENCHMARKS = {
        "engagement_rate": {"excellent": 5.0, "good": 2.0, "average": 0.5},
        "ctr": {"excellent": 5.0, "good": 2.0, "average": 0.5},
    }

    def __init__(self) -> None:
        self._scoring_count = 0

    def score(
        self,
        engagement_rate: float = 0.0,
        reach: float = 0.0,
        ctr: float = 0.0,
        growth_rate: float = 0.0,
    ) -> PerformanceResult:
        result = PerformanceResult()
        result.breakdown = {
            "engagement": min(100, engagement_rate * 20),
            "reach": min(100, reach / 100),
            "conversion": min(100, ctr * 20),
            "growth": min(100, max(0, growth_rate)),
        }
        result.score = sum(
            result.breakdown[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )
        result.grade = self._get_grade(result.score)
        result.success_level = self._get_level(result.score)
        result.benchmarks = self._compare_benchmarks(engagement_rate, ctr)
        self._scoring_count += 1
        return result

    def score_event(self, event: AnalyticsEvent) -> PerformanceResult:
        return self.score(
            engagement_rate=event.get("engagement_rate", 0),
            reach=event.get("reach", 0) or event.get("impressions", 0),
            ctr=event.get("ctr", 0),
            growth_rate=event.get("growth_rate", 0),
        )

    def _get_grade(self, score: float) -> str:
        for threshold, grade in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    def _get_level(self, score: float) -> str:
        if score >= 90: return "excellent"
        if score >= 75: return "good"
        if score >= 50: return "average"
        if score >= 25: return "below_average"
        return "poor"

    def _compare_benchmarks(self, engagement_rate: float, ctr: float) -> Dict[str, str]:
        benchmarks: Dict[str, str] = {}
        er_bench = self.BENCHMARKS["engagement_rate"]
        if engagement_rate >= er_bench["excellent"]:
            benchmarks["engagement"] = "excellent"
        elif engagement_rate >= er_bench["good"]:
            benchmarks["engagement"] = "good"
        elif engagement_rate >= er_bench["average"]:
            benchmarks["engagement"] = "average"
        else:
            benchmarks["engagement"] = "below_average"
        ctr_bench = self.BENCHMARKS["ctr"]
        if ctr >= ctr_bench["excellent"]:
            benchmarks["ctr"] = "excellent"
        elif ctr >= ctr_bench["good"]:
            benchmarks["ctr"] = "good"
        elif ctr >= ctr_bench["average"]:
            benchmarks["ctr"] = "average"
        else:
            benchmarks["ctr"] = "below_average"
        return benchmarks

    @property
    def scoring_count(self) -> int:
        return self._scoring_count
