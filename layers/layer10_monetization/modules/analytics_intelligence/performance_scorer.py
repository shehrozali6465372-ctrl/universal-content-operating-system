"""PerformanceScorer — Score and grade content performance."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer10_monetization.modules.analytics_intelligence.analytics_profile import AnalyticsProfile

_PS_COUNTER = itertools.count(1)

GRADE_THRESHOLDS = [
    (0.9, "A+"), (0.85, "A"), (0.8, "A-"), (0.75, "B+"),
    (0.7, "B"), (0.65, "B-"), (0.6, "C+"), (0.55, "C"),
    (0.5, "C-"), (0.4, "D"), (0.0, "F"),
]


class PerformanceScore:
    """A scored performance result."""

    __slots__ = ("score_id", "profile_id", "platform", "raw_score",
                 "normalized_score", "grade", "factors", "scored_at")

    def __init__(self, profile_id: str = "", platform: str = "") -> None:
        self.score_id: str = f"ps_{next(_PS_COUNTER)}"
        self.profile_id = profile_id
        self.platform = platform
        self.raw_score: float = 0.0
        self.normalized_score: float = 0.0
        self.grade: str = "F"
        self.factors: Dict[str, float] = {}
        self.scored_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {"score_id": self.score_id, "platform": self.platform,
                "raw_score": round(self.raw_score, 4),
                "normalized_score": round(self.normalized_score, 4),
                "grade": self.grade, "factors": {k: round(v, 3) for k, v in self.factors.items()}}


class PerformanceScorer:
    """Score and grade analytics performance with configurable weights."""

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or {
            "engagement_rate": 0.30, "ctr": 0.20, "reach": 0.15,
            "likes": 0.10, "comments": 0.10, "shares": 0.10,
            "saves": 0.05,
        }
        self._scores: List[PerformanceScore] = []
        self._benchmarks: Dict[str, Dict[str, float]] = {}

    def score(self, profile: AnalyticsProfile) -> PerformanceScore:
        result = PerformanceScore(profile.profile_id, profile.platform)
        factor_scores: Dict[str, float] = {}
        raw = 0.0
        total_weight = sum(self._weights.values())
        for metric, weight in self._weights.items():
            value = getattr(profile, metric, 0)
            if isinstance(value, int):
                normalized = min(1.0, value / max(1, 1000))
            else:
                normalized = min(1.0, max(0.0, value))
            factor_scores[metric] = normalized
            raw += normalized * (weight / total_weight)
        result.factors = factor_scores
        result.raw_score = raw
        result.normalized_score = min(1.0, max(0.0, raw))
        result.grade = self._to_grade(result.normalized_score)
        self._scores.append(result)
        return result

    def score_batch(self, profiles: List[AnalyticsProfile]) -> List[PerformanceScore]:
        return [self.score(p) for p in profiles]

    def set_benchmark(self, platform: str, benchmarks: Dict[str, float]) -> None:
        self._benchmarks[platform] = benchmarks

    def compare_to_benchmark(self, profile: AnalyticsProfile) -> Dict[str, Any]:
        benchmark = self._benchmarks.get(profile.platform, {})
        if not benchmark:
            return {"comparison": "no_benchmark"}
        score = self.score(profile)
        differences: Dict[str, float] = {}
        for metric, bench_val in benchmark.items():
            actual = getattr(profile, metric, 0)
            if isinstance(actual, int):
                actual = min(1.0, actual / 1000)
            differences[metric] = round(actual - bench_val, 4)
        above = sum(1 for v in differences.values() if v > 0)
        below = sum(1 for v in differences.values() if v < 0)
        return {"score": score.to_dict(), "differences": differences,
                "above_benchmark": above, "below_benchmark": below}

    def get_avg_score(self, platform: str = "") -> float:
        scores = self._scores
        if platform:
            scores = [s for s in scores if s.platform == platform]
        if not scores:
            return 0.0
        return round(sum(s.normalized_score for s in scores) / len(scores), 4)

    def get_grade_distribution(self) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for s in self._scores:
            dist[s.grade] = dist.get(s.grade, 0) + 1
        return dist

    @staticmethod
    def _to_grade(score: float) -> str:
        for threshold, grade in GRADE_THRESHOLDS:
            if score >= threshold:
                return grade
        return "F"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_scored": len(self._scores),
                "avg_score": self.get_avg_score(),
                "grade_distribution": self.get_grade_distribution()}
