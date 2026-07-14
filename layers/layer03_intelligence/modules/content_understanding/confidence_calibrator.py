"""
Confidence Calibrator — Sprint 3 (v3.0)

Calibrates and normalizes confidence scores across different analysis signals.

Public API:
    calibrate(signals) -> CalibratedConfidence
    normalize_score(score, min_val, max_val) -> float
    aggregate_confidence(confidences, weights) -> float
    reliability_grade(confidence) -> str

Version: 3.0.0
"""

from __future__ import annotations
from typing import Dict, List, Optional


class CalibratedConfidence:
    """Result of confidence calibration."""

    __slots__ = ("overall", "component_scores", "reliability", "explanation")

    def __init__(self) -> None:
        self.overall: float = 0.0
        self.component_scores: Dict[str, float] = {}
        self.reliability: str = "low"
        self.explanation: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "overall": round(self.overall, 4),
            "component_scores": {k: round(v, 4) for k, v in self.component_scores.items()},
            "reliability": self.reliability,
            "explanation": list(self.explanation),
        }


class ConfidenceCalibrator:
    """Calibrates and normalizes confidence scores.

    Usage::

        calibrator = ConfidenceCalibrator()
        result = calibrator.calibrate({
            "topic": 0.8,
            "intent": 0.7,
            "entity": 0.9,
            "sentiment": 0.6,
        })
        print(result.overall, result.reliability)
    """

    # Optimal weights per component
    DEFAULT_WEIGHTS: Dict[str, float] = {
        "topic": 0.25,
        "intent": 0.20,
        "entity": 0.15,
        "sentiment": 0.10,
        "context": 0.15,
        "complexity": 0.05,
        "embedding": 0.10,
    }

    # Reliability thresholds
    GRADES = {
        "excellent": 0.85,
        "good": 0.70,
        "moderate": 0.50,
        "low": 0.30,
        "unreliable": 0.0,
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None) -> None:
        self._weights = weights or dict(self.DEFAULT_WEIGHTS)

    def calibrate(self, signals: Dict[str, float], weights: Optional[Dict[str, float]] = None) -> CalibratedConfidence:
        """Calibrate raw confidence signals into a reliable overall score.

        Args:
            signals: Dict of component name -> raw confidence (0.0–1.0).
            weights: Optional override for component weights.

        Returns:
            CalibratedConfidence with overall score and component breakdown.
        """
        result = CalibratedConfidence()
        w = weights or self._weights

        if not signals:
            return result

        # Normalize each signal
        normalized: Dict[str, float] = {}
        for name, score in signals.items():
            normalized[name] = self.normalize_score(score)

        result.component_scores = dict(normalized)

        # Weighted aggregation
        total_weight = 0.0
        weighted_sum = 0.0
        for name, score in normalized.items():
            weight = w.get(name, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            result.overall = round(weighted_sum / total_weight, 4)

        # Reliability grade
        result.reliability = self.reliability_grade(result.overall)

        # Explanation
        result.explanation = self._build_explanation(normalized, w, result.overall)

        return result

    def normalize_score(self, score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
        """Normalize a score to 0.0–1.0 range."""
        if max_val == min_val:
            return 0.5
        normalized = (score - min_val) / (max_val - min_val)
        return round(max(0.0, min(1.0, normalized)), 4)

    def aggregate_confidence(self, confidences: List[float], weights: Optional[List[float]] = None) -> float:
        """Aggregate multiple confidence values into one score."""
        if not confidences:
            return 0.0

        if weights and len(weights) == len(confidences):
            total_w = sum(weights)
            if total_w > 0:
                return round(sum(c * w for c, w in zip(confidences, weights)) / total_w, 4)

        return round(sum(confidences) / len(confidences), 4)

    def reliability_grade(self, confidence: float) -> str:
        """Map confidence to a reliability grade."""
        for grade, threshold in sorted(self.GRADES.items(), key=lambda x: -x[1]):
            if confidence >= threshold:
                return grade
        return "unreliable"

    def set_weights(self, weights: Dict[str, float]) -> None:
        self._weights = weights

    def _build_explanation(self, signals: Dict[str, float], weights: Dict[str, float], overall: float) -> List[str]:
        explanations: List[str] = []

        # Top contributing signals
        contributions = []
        for name, score in signals.items():
            w = weights.get(name, 0.1)
            contributions.append((name, score * w))
        contributions.sort(key=lambda x: -x[1])

        if contributions:
            top = contributions[0]
            explanations.append(
                f"Highest contributor: {top[0]} (weighted score: {top[1]:.3f})"
            )

        # Weakest signal
        if len(contributions) > 1:
            weakest = contributions[-1]
            explanations.append(
                f"Weakest signal: {weakest[0]} (weighted score: {weakest[1]:.3f})"
            )

        # Overall assessment
        grade = self.reliability_grade(overall)
        explanations.append(f"Overall reliability: {grade} ({overall:.1%})")

        return explanations
