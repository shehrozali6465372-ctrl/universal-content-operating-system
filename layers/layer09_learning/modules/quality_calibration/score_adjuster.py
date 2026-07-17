"""Score Adjuster — Adjust quality scores based on calibration data."""
from __future__ import annotations
from typing import Any, Dict, List


class AdjustmentResult:
    """Result of adjusting a score."""

    __slots__ = ("metric", "original_score", "adjusted_score", "adjustment",
                 "bias_applied", "confidence")

    def __init__(self, metric: str = "") -> None:
        self.metric = metric
        self.original_score: float = 0.0
        self.adjusted_score: float = 0.0
        self.adjustment: float = 0.0
        self.bias_applied: float = 0.0
        self.confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "metric": self.metric,
            "original_score": round(self.original_score, 4),
            "adjusted_score": round(self.adjusted_score, 4),
            "adjustment": round(self.adjustment, 4),
            "bias_applied": round(self.bias_applied, 4),
            "confidence": round(self.confidence, 3),
        }


class ScoreAdjuster:
    """Adjust quality scores using calibration bias data."""

    def __init__(self) -> None:
        self._biases: Dict[str, float] = {}
        self._confidence: Dict[str, float] = {}
        self._adjustments: List[AdjustmentResult] = []

    def set_bias(self, metric: str, bias: float, confidence: float = 0.5) -> None:
        self._biases[metric] = bias
        self._confidence[metric] = confidence

    def adjust(self, metric: str, score: float) -> AdjustmentResult:
        result = AdjustmentResult(metric)
        result.original_score = score
        bias = self._biases.get(metric, 0.0)
        conf = self._confidence.get(metric, 0.0)
        result.bias_applied = bias
        result.confidence = conf
        adjusted = score + bias * conf
        result.adjusted_score = round(max(0.0, min(1.0, adjusted)), 4)
        result.adjustment = round(result.adjusted_score - score, 4)
        self._adjustments.append(result)
        return result

    def adjust_batch(self, scores: Dict[str, float]) -> List[AdjustmentResult]:
        return [self.adjust(metric, score) for metric, score in scores.items()]

    def get_adjustments(self) -> List[AdjustmentResult]:
        return list(self._adjustments)

    def get_bias(self, metric: str) -> float:
        return self._biases.get(metric, 0.0)

    def get_biases(self) -> Dict[str, float]:
        return dict(self._biases)
