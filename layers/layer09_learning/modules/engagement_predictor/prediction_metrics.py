"""Prediction Metrics — Track MAE, RMSE, accuracy, and calibration."""
from __future__ import annotations
import math
from typing import Any, Dict, List


class PredictionMetrics:
    """Track prediction accuracy and performance metrics."""

    def __init__(self) -> None:
        self._total_predictions: int = 0
        self._total_comparisons: int = 0
        self._errors: List[float] = []
        self._squared_errors: List[float] = []
        self._direction_correct: int = 0
        self._direction_total: int = 0
        self._confidence_scores: List[float] = []
        self._confidence_correct: int = 0

    def record_prediction(self, confidence: float = 0.5) -> None:
        self._total_predictions += 1
        self._confidence_scores.append(confidence)

    def record_comparison(self, predicted: float, actual: float,
                          predicted_direction: int = 0, actual_direction: int = 0,
                          confidence: float = 0.5) -> None:
        self._total_comparisons += 1
        error = abs(predicted - actual)
        self._errors.append(error)
        self._squared_errors.append(error ** 2)

        if predicted_direction != 0 and actual_direction != 0:
            self._direction_total += 1
            if (predicted_direction > 0 and actual_direction > 0) or                (predicted_direction < 0 and actual_direction < 0):
                self._direction_correct += 1

        if confidence > 0.5 and abs(predicted - actual) / max(1.0, actual) < 0.2:
            self._confidence_correct += 1

    def get_mae(self) -> float:
        if not self._errors:
            return 0.0
        return round(sum(self._errors) / len(self._errors), 4)

    def get_rmse(self) -> float:
        if not self._squared_errors:
            return 0.0
        return round(math.sqrt(sum(self._squared_errors) / len(self._squared_errors)), 4)

    def get_accuracy(self) -> float:
        if not self._errors:
            return 0.0
        within_20pct = sum(1 for e, i in zip(self._errors, range(len(self._errors)))
                          if self._errors[i] < max(1.0, abs(self._errors[i] + 1.0)) * 0.2)
        return round(within_20pct / len(self._errors), 4) if self._errors else 0.0

    def get_direction_accuracy(self) -> float:
        if self._direction_total == 0:
            return 0.0
        return round(self._direction_correct / self._direction_total, 4)

    def get_calibration_score(self) -> float:
        if not self._confidence_scores:
            return 0.0
        avg_conf = sum(self._confidence_scores) / len(self._confidence_scores)
        if self._total_comparisons == 0:
            return round(avg_conf, 4)
        return round(self._confidence_correct / self._total_comparisons, 4)

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_predictions": self._total_predictions,
            "total_comparisons": self._total_comparisons,
            "mae": self.get_mae(),
            "rmse": self.get_rmse(),
            "direction_accuracy": self.get_direction_accuracy(),
            "calibration_score": self.get_calibration_score(),
        }

    def reset(self) -> None:
        self._total_predictions = 0
        self._total_comparisons = 0
        self._errors.clear()
        self._squared_errors.clear()
        self._direction_correct = 0
        self._direction_total = 0
        self._confidence_scores.clear()
        self._confidence_correct = 0
