"""GenerationMetrics — Track content generation performance."""
from __future__ import annotations
from typing import Any, Dict, List


class GenerationMetrics:
    """Track content generation metrics."""

    def __init__(self) -> None:
        self._total_generated: int = 0
        self._by_platform: Dict[str, int] = {}
        self._by_type: Dict[str, int] = {}
        self._generation_times: List[float] = []
        self._quality_scores: List[float] = []

    def record_generation(self, platform: str = "", content_type: str = "",
                           generation_time_ms: float = 0.0,
                           quality_score: float = 0.0) -> None:
        self._total_generated += 1
        if platform:
            self._by_platform[platform] = self._by_platform.get(platform, 0) + 1
        if content_type:
            self._by_type[content_type] = self._by_type.get(content_type, 0) + 1
        if generation_time_ms > 0:
            self._generation_times.append(generation_time_ms)
        if quality_score > 0:
            self._quality_scores.append(quality_score)

    def get_avg_generation_time(self) -> float:
        if not self._generation_times:
            return 0.0
        return round(sum(self._generation_times) / len(self._generation_times), 1)

    def get_avg_quality(self) -> float:
        if not self._quality_scores:
            return 0.0
        return round(sum(self._quality_scores) / len(self._quality_scores), 3)

    def get_throughput(self) -> float:
        if not self._generation_times:
            return 0.0
        total_seconds = sum(self._generation_times) / 1000
        return round(self._total_generated / max(0.001, total_seconds), 2)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_generated": self._total_generated,
            "by_platform": dict(self._by_platform),
            "by_type": dict(self._by_type),
            "avg_generation_time_ms": self.get_avg_generation_time(),
            "avg_quality": self.get_avg_quality(),
            "throughput_per_sec": self.get_throughput(),
        }

    def reset(self) -> None:
        self._total_generated = 0
        self._by_platform.clear()
        self._by_type.clear()
        self._generation_times.clear()
        self._quality_scores.clear()
