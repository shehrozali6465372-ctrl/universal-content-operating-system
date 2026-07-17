"""Voice Metrics — Track brand voice learning performance metrics."""
from __future__ import annotations
from typing import Any, Dict, List


class VoiceMetrics:
    """Track metrics across brand voice learning cycles."""

    def __init__(self) -> None:
        self._total_analyses: int = 0
        self._total_consistency_checks: int = 0
        self._total_violations: int = 0
        self._consistency_scores: List[float] = []
        self._tone_adjustments: int = 0
        self._vocabulary_adjustments: int = 0

    def record_analysis(self) -> None:
        self._total_analyses += 1

    def record_consistency_check(self, score: float, violations: int = 0) -> None:
        self._total_consistency_checks += 1
        self._consistency_scores.append(score)
        self._total_violations += violations

    def record_tone_adjustment(self) -> None:
        self._tone_adjustments += 1

    def record_vocabulary_adjustment(self) -> None:
        self._vocabulary_adjustments += 1

    def get_avg_consistency(self) -> float:
        if not self._consistency_scores:
            return 0.0
        return round(sum(self._consistency_scores) / len(self._consistency_scores), 3)

    def get_violation_rate(self) -> float:
        if self._total_consistency_checks == 0:
            return 0.0
        return round(self._total_violations / self._total_consistency_checks, 3)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_analyses": self._total_analyses,
            "total_consistency_checks": self._total_consistency_checks,
            "avg_consistency": self.get_avg_consistency(),
            "total_violations": self._total_violations,
            "violation_rate": self.get_violation_rate(),
            "tone_adjustments": self._tone_adjustments,
            "vocabulary_adjustments": self._vocabulary_adjustments,
        }

    def reset(self) -> None:
        self._total_analyses = 0
        self._total_consistency_checks = 0
        self._total_violations = 0
        self._consistency_scores.clear()
        self._tone_adjustments = 0
        self._vocabulary_adjustments = 0
