"""ConfidenceEngine — calculate and calibrate confidence scores."""
from __future__ import annotations

import math
from typing import Any, Dict, List

from .models import ModelResponse


class ConfidenceEngine:
    """Calculate and calibrate confidence scores for model responses."""

    def __init__(self, calibration_offset: float = 0.0) -> None:
        self.calibration_offset = calibration_offset
        self._history: List[Dict[str, Any]] = []

    def calculate(self, responses: List[ModelResponse]) -> Dict[str, Any]:
        if not responses:
            return {"overall_confidence": 0.0, "agreement": 0.0, "model_scores": {}}

        successful = [r for r in responses if r.is_success]
        if not successful:
            return {"overall_confidence": 0.0, "agreement": 0.0, "model_scores": {}}

        model_scores = {}
        confidences = []
        for r in successful:
            calibrated = self._calibrate(r.confidence)
            model_scores[r.model] = calibrated
            confidences.append(calibrated)

        overall = sum(confidences) / len(confidences) if confidences else 0.0
        agreement = self._agreement_score(confidences)

        result = {
            "overall_confidence": overall,
            "agreement": agreement,
            "model_scores": model_scores,
            "std_dev": self._std_dev(confidences),
            "response_count": len(successful),
        }
        self._history.append(result)
        return result

    def is_confident(self, confidence: float, threshold: float = 0.6) -> bool:
        return confidence >= threshold

    def _calibrate(self, raw: float) -> float:
        calibrated = raw + self.calibration_offset
        return max(0.0, min(1.0, calibrated))

    @staticmethod
    def _agreement_score(scores: List[float]) -> float:
        if len(scores) < 2:
            return 1.0
        mean = sum(scores) / len(scores)
        variance = sum((s - mean) ** 2 for s in scores) / len(scores)
        return max(0.0, 1.0 - math.sqrt(variance))

    @staticmethod
    def _std_dev(values: List[float]) -> float:
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return math.sqrt(variance)

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)
