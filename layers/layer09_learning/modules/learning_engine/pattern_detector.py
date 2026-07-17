"""Pattern Detector — Detect success, failure, and repeated behaviour patterns."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer09_learning.modules.learning_engine.learning_signal import LearningSignal


class DetectedPattern:
    """A detected pattern in the data."""

    __slots__ = ("pattern_id", "pattern_type", "description", "confidence",
                 "frequency", "example_signals", "platform", "tags")

    PATTERN_TYPES = ("success", "failure", "repeated", "correlation", "seasonal")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.pattern_id: str = f"pat_{int(time.time() * 1000) % 100000}"
        self.pattern_type = pattern_type if pattern_type in self.PATTERN_TYPES else "repeated"
        self.description = description
        self.confidence: float = 0.0
        self.frequency: int = 0
        self.example_signals: List[Dict[str, Any]] = []
        self.platform: str = ""
        self.tags: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "frequency": self.frequency,
            "platform": self.platform,
        }


class PatternDetector:
    """Detect patterns in learning signals."""

    MIN_FREQUENCY = 3
    MIN_CONFIDENCE = 0.5

    def __init__(self) -> None:
        self._patterns: List[DetectedPattern] = []
        self._detection_count = 0

    def detect(self, signals: List[LearningSignal]) -> List[DetectedPattern]:
        self._patterns.clear()
        if not signals:
            return self._patterns
        self._detect_success_patterns(signals)
        self._detect_failure_patterns(signals)
        self._detect_repeated_patterns(signals)
        self._detect_metric_patterns(signals)
        self._detection_count += 1
        return list(self._patterns)

    def _detect_success_patterns(self, signals: List[LearningSignal]) -> None:
        positive = [s for s in signals if s.is_positive()]
        if len(positive) >= self.MIN_FREQUENCY:
            platforms = set(s.platform for s in positive if s.platform)
            for platform in platforms:
                platform_signals = [s for s in positive if s.platform == platform]
                if len(platform_signals) >= self.MIN_FREQUENCY:
                    p = DetectedPattern("success", f"Repeated success on {platform}")
                    p.confidence = min(1.0, len(platform_signals) / max(1, len(signals)))
                    p.frequency = len(platform_signals)
                    p.platform = platform
                    p.example_signals = [s.to_dict() for s in platform_signals[:3]]
                    self._patterns.append(p)

    def _detect_failure_patterns(self, signals: List[LearningSignal]) -> None:
        negative = [s for s in signals if not s.is_positive()]
        if len(negative) >= self.MIN_FREQUENCY:
            metric_counts: Dict[str, int] = {}
            for s in negative:
                metric_counts[s.metric_name] = metric_counts.get(s.metric_name, 0) + 1
            for metric, count in metric_counts.items():
                if count >= self.MIN_FREQUENCY:
                    p = DetectedPattern("failure", f"Repeated failure in {metric}")
                    p.confidence = min(1.0, count / max(1, len(negative)))
                    p.frequency = count
                    p.tags.append(metric)
                    self._patterns.append(p)

    def _detect_repeated_patterns(self, signals: List[LearningSignal]) -> None:
        metric_values: Dict[str, List[float]] = {}
        for s in signals:
            metric_values.setdefault(s.metric_name, []).append(s.value)
        for metric, values in metric_values.items():
            if len(values) >= self.MIN_FREQUENCY:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                if variance < (mean * 0.1) ** 2 if mean > 0 else True:
                    p = DetectedPattern("repeated", f"Consistent {metric} values around {round(mean, 2)}")
                    p.confidence = 0.8
                    p.frequency = len(values)
                    p.tags.append(metric)
                    self._patterns.append(p)

    def _detect_metric_patterns(self, signals: List[LearningSignal]) -> None:
        metric_counts: Dict[str, int] = {}
        for s in signals:
            metric_counts[s.metric_name] = metric_counts.get(s.metric_name, 0) + 1
        for metric, count in metric_counts.items():
            if count >= self.MIN_FREQUENCY:
                p = DetectedPattern("repeated", f"Metric '{metric}' observed {count} times")
                p.confidence = min(1.0, count / max(1, len(signals)))
                p.frequency = count
                p.tags.append(metric)
                self._patterns.append(p)

    def get_patterns(self, pattern_type: str = "") -> List[DetectedPattern]:
        if pattern_type:
            return [p for p in self._patterns if p.pattern_type == pattern_type]
        return list(self._patterns)

    @property
    def pattern_count(self) -> int:
        return len(self._patterns)

    @property
    def detection_count(self) -> int:
        return self._detection_count
