"""Tone Learning — Learn tone preferences from performance feedback."""
from __future__ import annotations
from typing import Any, Dict, List


class ToneLearningResult:
    """Result of tone learning analysis."""

    __slots__ = ("tone", "suggested_weight", "current_weight",
                 "performance_correlation", "confidence", "reason")

    def __init__(self, tone: str = "") -> None:
        self.tone = tone
        self.suggested_weight: float = 0.5
        self.current_weight: float = 0.5
        self.performance_correlation: float = 0.0
        self.confidence: float = 0.0
        self.reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tone": self.tone,
            "suggested_weight": round(self.suggested_weight, 3),
            "current_weight": round(self.current_weight, 3),
            "performance_correlation": round(self.performance_correlation, 3),
            "confidence": round(self.confidence, 3),
        }


class ToneLearner:
    """Learn which tones perform best for a brand."""

    def __init__(self) -> None:
        self._results: List[ToneLearningResult] = []
        self._learning_count: int = 0

    def learn(
        self,
        current_tones: Dict[str, float],
        tone_performance: Dict[str, List[float]],
    ) -> List[ToneLearningResult]:
        self._results.clear()
        for tone, performances in tone_performance.items():
            if not performances:
                continue
            result = ToneLearningResult(tone)
            result.current_weight = current_tones.get(tone, 0.5)
            avg_perf = sum(performances) / len(performances)
            result.performance_correlation = round(avg_perf, 3)
            result.suggested_weight = round(min(1.0, max(0.0, avg_perf)), 3)
            result.confidence = round(min(1.0, len(performances) / 10.0), 3)
            if avg_perf > result.current_weight:
                result.reason = f"Performance ({avg_perf:.2f}) exceeds current weight ({result.current_weight:.2f})"
            elif avg_perf < result.current_weight:
                result.reason = f"Performance ({avg_perf:.2f}) below current weight ({result.current_weight:.2f})"
            else:
                result.reason = "Performance matches current weight"
            self._results.append(result)
        self._learning_count += 1
        return list(self._results)

    def get_best_tones(self, count: int = 3) -> List[ToneLearningResult]:
        sorted_results = sorted(self._results, key=lambda r: r.performance_correlation, reverse=True)
        return sorted_results[:count]

    def get_worst_tones(self, count: int = 3) -> List[ToneLearningResult]:
        sorted_results = sorted(self._results, key=lambda r: r.performance_correlation)
        return sorted_results[:count]

    def get_tone(self, tone: str) -> ToneLearningResult | None:
        for r in self._results:
            if r.tone == tone:
                return r
        return None

    def get_results(self) -> List[ToneLearningResult]:
        return list(self._results)

    @property
    def learning_count(self) -> int:
        return self._learning_count
