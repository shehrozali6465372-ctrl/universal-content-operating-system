"""Learning Report — Aggregate all learning results into a unified report."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_LR_COUNTER = itertools.count(1)


class LearningReport:
    """Unified report from all learning modules."""

    __slots__ = ("report_id", "lessons", "improvements", "mistakes",
                 "optimizations", "patterns_detected", "calibration_adjustments",
                 "predictions", "confidence_score", "learning_score",
                 "modules_executed", "modules_failed", "duration_ms",
                 "timestamp")

    def __init__(self) -> None:
        self.report_id: str = f"lr_{next(_LR_COUNTER)}"
        self.lessons: List[Dict[str, Any]] = []
        self.improvements: List[Dict[str, Any]] = []
        self.mistakes: List[Dict[str, Any]] = []
        self.optimizations: List[Dict[str, Any]] = []
        self.patterns_detected: List[str] = []
        self.calibration_adjustments: List[str] = []
        self.predictions: Dict[str, Any] = {}
        self.confidence_score: float = 0.0
        self.learning_score: float = 0.0
        self.modules_executed: List[str] = []
        self.modules_failed: List[str] = []
        self.duration_ms: float = 0.0
        self.timestamp: float = time.time()

    def add_lesson(self, source: str, description: str, impact: str = "medium") -> None:
        self.lessons.append({"source": source, "description": description, "impact": impact})

    def add_improvement(self, source: str, description: str, priority: int = 1) -> None:
        self.improvements.append({"source": source, "description": description, "priority": priority})

    def add_mistake(self, source: str, description: str, severity: str = "low") -> None:
        self.mistakes.append({"source": source, "description": description, "severity": severity})

    def add_optimization(self, source: str, description: str, gain: float = 0.0) -> None:
        self.optimizations.append({"source": source, "description": description, "gain": gain})

    def compute_learning_score(self) -> float:
        total = len(self.lessons) + len(self.improvements) + len(self.optimizations)
        mistakes_penalty = len(self.mistakes) * 0.5
        raw = max(0.0, total - mistakes_penalty)
        self.learning_score = round(min(100.0, raw * 5), 1)
        return self.learning_score

    def compute_confidence(self) -> float:
        modules_ratio = len(self.modules_executed) / max(1, len(self.modules_executed) + len(self.modules_failed))
        content_ratio = min(1.0, len(self.lessons) / 5) * 0.3
        self.confidence_score = round(modules_ratio * 0.7 + content_ratio, 3)
        return self.confidence_score

    def get_summary(self) -> Dict[str, Any]:
        return {
            "report_id": self.report_id,
            "lessons_count": len(self.lessons),
            "improvements_count": len(self.improvements),
            "mistakes_count": len(self.mistakes),
            "optimizations_count": len(self.optimizations),
            "patterns_detected": len(self.patterns_detected),
            "confidence_score": round(self.confidence_score, 3),
            "learning_score": round(self.learning_score, 1),
            "modules_executed": len(self.modules_executed),
            "modules_failed": len(self.modules_failed),
            "duration_ms": round(self.duration_ms, 1),
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_summary()
