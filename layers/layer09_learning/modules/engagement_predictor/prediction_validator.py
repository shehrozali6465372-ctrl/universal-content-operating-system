"""Prediction Validator — Validate prediction quality and detect drift."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.engagement_predictor.engagement_model import EngagementPrediction
from layers.layer09_learning.modules.engagement_predictor.prediction_memory import PredictionMemory


class ValidationResult:
    """Result of validating a prediction."""

    __slots__ = ("is_valid", "quality_score", "issues", "warnings",
                 "drift_detected", "confidence_level")

    def __init__(self) -> None:
        self.is_valid: bool = True
        self.quality_score: float = 1.0
        self.issues: List[str] = []
        self.warnings: List[str] = []
        self.drift_detected: bool = False
        self.confidence_level: str = "medium"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "quality_score": round(self.quality_score, 3),
            "issues": self.issues,
            "warnings": self.warnings,
            "drift_detected": self.drift_detected,
            "confidence_level": self.confidence_level,
        }


class PredictionValidator:
    """Validate prediction quality, detect anomalies, and check for drift."""

    def __init__(self, memory: Optional[PredictionMemory] = None) -> None:
        self._memory = memory
        self._min_confidence: float = 0.3
        self._max_engagement_rate: float = 1.0
        self._drift_threshold: float = 0.3

    def validate(self, prediction: EngagementPrediction,
                 platform: str = "") -> ValidationResult:
        result = ValidationResult()

        # Check confidence
        if prediction.confidence < self._min_confidence:
            result.warnings.append(f"Low confidence: {prediction.confidence:.3f}")

        # Check engagement rate bounds
        if prediction.engagement_rate > self._max_engagement_rate:
            result.issues.append(f"Engagement rate exceeds maximum: {prediction.engagement_rate:.4f}")
            result.is_valid = False
            result.quality_score *= 0.5

        # Check for negative values
        for field in ("likes", "comments", "shares", "saves", "reach", "impressions"):
            val = getattr(prediction, field)
            if val < 0:
                result.issues.append(f"Negative {field}: {val}")
                result.is_valid = False
                result.quality_score *= 0.8

        # Check for suspiciously high metrics relative to reach
        if prediction.reach > 0:
            total_engagement = prediction.likes + prediction.comments + prediction.shares
            if total_engagement / prediction.reach > 0.5:
                result.warnings.append("Unusually high engagement-to-reach ratio")

        # Confidence level
        if prediction.confidence >= 0.8:
            result.confidence_level = "high"
        elif prediction.confidence >= 0.5:
            result.confidence_level = "medium"
        else:
            result.confidence_level = "low"

        # Drift detection
        if self._memory:
            drift = self._detect_drift(prediction, platform)
            if drift > self._drift_threshold:
                result.drift_detected = True
                result.warnings.append(f"Model drift detected: {drift:.3f}")
                result.quality_score *= 0.9

        return result

    def _detect_drift(self, prediction: EngagementPrediction, platform: str) -> float:
        if not self._memory:
            return 0.0
        comparisons = self._memory.get_comparisons(platform, limit=20)
        if len(comparisons) < 5:
            return 0.0

        errors = []
        for r in comparisons:
            if r.actual is None:
                continue
            for key in ("likes", "comments", "shares"):
                if key in r.predicted and key in r.actual and r.actual[key] > 0:
                    error = abs(r.predicted[key] - r.actual[key]) / r.actual[key]
                    errors.append(error)

        if not errors:
            return 0.0
        return sum(errors) / len(errors)

    def set_min_confidence(self, value: float) -> None:
        self._min_confidence = max(0.0, min(1.0, value))

    def set_drift_threshold(self, value: float) -> None:
        self._drift_threshold = max(0.0, min(1.0, value))
