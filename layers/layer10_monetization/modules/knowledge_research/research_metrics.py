"""ResearchMetrics — Track research performance."""
from __future__ import annotations
from typing import Any, Dict, List


class ResearchMetrics:
    """Track research speed, accuracy, coverage, and cost."""

    def __init__(self) -> None:
        self._total_research: int = 0
        self._successful: int = 0
        self._failed: int = 0
        self._durations: List[float] = []
        self._api_calls: int = 0
        self._cache_hits: int = 0
        self._accuracy_scores: List[float] = []

    def record_research(self, success: bool = True, duration_ms: float = 0.0,
                        accuracy: float = 0.0, api_calls: int = 0,
                        cache_hit: bool = False) -> None:
        self._total_research += 1
        if success:
            self._successful += 1
        else:
            self._failed += 1
        if duration_ms > 0:
            self._durations.append(duration_ms)
        self._api_calls += api_calls
        if cache_hit:
            self._cache_hits += 1
        if accuracy > 0:
            self._accuracy_scores.append(accuracy)

    def get_success_rate(self) -> float:
        if self._total_research == 0:
            return 0.0
        return round(self._successful / self._total_research, 3)

    def get_avg_duration(self) -> float:
        if not self._durations:
            return 0.0
        return round(sum(self._durations) / len(self._durations), 1)

    def get_accuracy(self) -> float:
        if not self._accuracy_scores:
            return 0.0
        return round(sum(self._accuracy_scores) / len(self._accuracy_scores), 3)

    def get_cache_hit_rate(self) -> float:
        if self._total_research == 0:
            return 0.0
        return round(self._cache_hits / self._total_research, 3)

    def get_summary(self) -> Dict[str, Any]:
        return {"total_research": self._total_research, "successful": self._successful,
                "failed": self._failed, "success_rate": self.get_success_rate(),
                "avg_duration_ms": self.get_avg_duration(), "accuracy": self.get_accuracy(),
                "api_calls": self._api_calls, "cache_hit_rate": self.get_cache_hit_rate()}

    def reset(self) -> None:
        self._total_research = 0
        self._successful = 0
        self._failed = 0
        self._durations.clear()
        self._api_calls = 0
        self._cache_hits = 0
        self._accuracy_scores.clear()
