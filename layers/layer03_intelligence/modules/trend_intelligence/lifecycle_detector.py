"""Lifecycle Detector — detects where a trend is in its lifecycle."""

from typing import List


class LifecycleStage:
    EMERGING = "emerging"
    GROWING = "growing"
    PEAK = "peak"
    DECLINING = "declining"
    DEAD = "dead"


class LifecycleResult:
    __slots__ = ("stage", "confidence", "progress_pct")

    def __init__(self, stage: str = "emerging", confidence: float = 0.5, progress_pct: float = 0.0):
        self.stage = stage
        self.confidence = confidence
        self.progress_pct = progress_pct

    def to_dict(self) -> dict:
        return {"stage": self.stage, "confidence": self.confidence, "progress_pct": self.progress_pct}


class LifecycleDetector:
    def detect(self, scores: List[float]) -> LifecycleResult:
        if len(scores) < 3:
            return LifecycleResult(LifecycleStage.EMERGING, 0.3, 0.0)

        peak = max(scores)
        current = scores[-1]
        ratio = current / max(peak, 0.1)
        avg_first = sum(scores[:len(scores)//2]) / max(len(scores)//2, 1)
        avg_second = sum(scores[len(scores)//2:]) / max(len(scores) - len(scores)//2, 1)

        if ratio > 0.9 and avg_second > avg_first:
            return LifecycleResult(LifecycleStage.GROWING, 0.8, 40.0)
        elif ratio > 0.95:
            return LifecycleResult(LifecycleStage.PEAK, 0.85, 70.0)
        elif ratio < 0.3 and avg_second < avg_first:
            return LifecycleResult(LifecycleStage.DECLINING, 0.8, 90.0)
        elif ratio < 0.1:
            return LifecycleResult(LifecycleStage.DEAD, 0.9, 100.0)
        elif avg_second > avg_first * 1.2:
            return LifecycleResult(LifecycleStage.GROWING, 0.7, 30.0)
        else:
            return LifecycleResult(LifecycleStage.EMERGING, 0.6, 10.0)
