"""Mistake Detector — Detect mistakes in content and publishing."""
from __future__ import annotations
from typing import Any, Dict, List
import itertools


MISTAKE_SEVERITY = ("critical", "high", "medium", "low")
MISTAKE_CATEGORIES = ("content", "publishing", "strategy", "brand", "seo", "engagement", "technical")


class DetectedMistake:
    """A detected mistake with context."""

    __slots__ = ("mistake_id", "category", "severity", "description",
                 "context", "metric_name", "metric_value",
                 "expected_value", "suggestion")

    _counter = 0

    def __init__(self, category: str = "content", severity: str = "medium") -> None:
        next(_MDTC)
        self.mistake_id: str = f"mdt_{next(_MDTC)}"
        self.category = category if category in MISTAKE_CATEGORIES else "content"
        self.severity = severity if severity in MISTAKE_SEVERITY else "medium"
        self.description: str = ""
        self.context: Dict[str, Any] = {}
        self.metric_name: str = ""
        self.metric_value: float = 0.0
        self.expected_value: float = 0.0
        self.suggestion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mistake_id": self.mistake_id,
            "category": self.category,
            "severity": self.severity,
            "description": self.description,
            "metric_name": self.metric_name,
        }


_MDTC = itertools.count(1)

class MistakeDetector:
    """Detect mistakes from performance data and quality checks."""

    def __init__(self) -> None:
        self._mistakes: List[DetectedMistake] = []
        self._detection_count: int = 0

    def detect_from_metrics(self, metrics: Dict[str, float],
                            thresholds: Dict[str, float]) -> List[DetectedMistake]:
        results = []
        for metric_name, value in metrics.items():
            threshold = thresholds.get(metric_name)
            if threshold is not None and value < threshold:
                m = DetectedMistake("content", "high")
                m.description = f"{metric_name} ({value:.2f}) below threshold ({threshold:.2f})"
                m.metric_name = metric_name
                m.metric_value = value
                m.expected_value = threshold
                m.suggestion = f"Improve {metric_name} to reach {threshold:.2f}"
                results.append(m)
                self._mistakes.append(m)
        self._detection_count += 1
        return results

    def detect_from_quality(self, quality_scores: Dict[str, float],
                            min_score: float = 0.5) -> List[DetectedMistake]:
        results = []
        for area, score in quality_scores.items():
            if score < min_score:
                severity = "critical" if score < 0.2 else "high" if score < 0.35 else "medium"
                m = DetectedMistake("content", severity)
                m.description = f"Low {area} quality: {score:.2f}"
                m.metric_name = area
                m.metric_value = score
                m.expected_value = min_score
                m.suggestion = f"Focus on improving {area}"
                results.append(m)
                self._mistakes.append(m)
        return results

    def detect_from_feedback(self, feedback_items: List[Dict[str, Any]]) -> List[DetectedMistake]:
        results = []
        for item in feedback_items:
            if item.get("negative", False):
                m = DetectedMistake(
                    item.get("category", "content"),
                    item.get("severity", "medium"),
                )
                m.description = item.get("description", "Negative feedback received")
                m.context = item
                results.append(m)
                self._mistakes.append(m)
        return results

    def get_mistakes(self, category: str = "", severity: str = "") -> List[DetectedMistake]:
        result = self._mistakes
        if category:
            result = [m for m in result if m.category == category]
        if severity:
            result = [m for m in result if m.severity == severity]
        return result

    def get_critical(self) -> List[DetectedMistake]:
        return self.get_mistakes(severity="critical")

    @property
    def mistake_count(self) -> int:
        return len(self._mistakes)

    @property
    def detection_count(self) -> int:
        return self._detection_count
