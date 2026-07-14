"""Lifecycle Detector - Detects where a trend is in its lifecycle."""
from __future__ import annotations
from typing import Dict, List


class LifecycleStage:
    EMERGING = "emerging"
    GROWING = "growing"
    PEAK = "peak"
    DECLINING = "declining"
    DEAD = "dead"


class LifecycleResult:
    """Result of lifecycle detection."""
    __slots__ = ("stage", "confidence", "progress_pct", "time_in_stage", "next_expected")

    def __init__(self, stage: str = "emerging", confidence: float = 0.5,
                 progress_pct: float = 0.0) -> None:
        self.stage = stage
        self.confidence = confidence
        self.progress_pct = progress_pct
        self.time_in_stage = 0
        self.next_expected = ""

    def to_dict(self) -> Dict:
        return {
            "stage": self.stage, "confidence": round(self.confidence, 3),
            "progress_pct": round(self.progress_pct, 3),
            "time_in_stage": self.time_in_stage, "next_expected": self.next_expected,
        }


class LifecycleDetector:
    """Detects the lifecycle stage of a trend based on data points."""

    def detect(self, data_points: List[float]) -> LifecycleResult:
        if len(data_points) < 3:
            return LifecycleResult(LifecycleStage.EMERGING, 0.3, 0.0)

        n = len(data_points)
        first_third = data_points[:n // 3]
        last_third = data_points[2 * n // 3:]

        avg_first = sum(first_third) / len(first_third) if first_third else 0
        avg_last = sum(last_third) / len(last_third) if last_third else 0
        max_val = max(data_points)
        current = data_points[-1]
        peak_idx = data_points.index(max_val)

        growth = avg_last - avg_first
        relative_growth = growth / max(max_val, 0.01)

        if current < max_val * 0.3 and peak_idx < n * 0.6:
            stage = LifecycleStage.DEAD
            confidence = 0.7
            progress = 1.0
            next_exp = "N/A"
        elif relative_growth < -0.2:
            stage = LifecycleStage.DECLINING
            confidence = 0.7
            progress = 0.75
            next_exp = "dead"
        elif current >= max_val * 0.9 and n > 5 and peak_idx < n - 2:
            stage = LifecycleStage.PEAK
            confidence = 0.6
            progress = 0.6
            next_exp = "declining"
        elif relative_growth > 0.15:
            stage = LifecycleStage.GROWING
            confidence = 0.7
            progress = 0.3 + min(0.3, relative_growth)
            next_exp = "peak"
        else:
            stage = LifecycleStage.EMERGING
            confidence = 0.5
            progress = 0.1 + min(0.2, relative_growth + 0.2)
            next_exp = "growing"

        return LifecycleResult(stage, confidence, round(progress, 3))
