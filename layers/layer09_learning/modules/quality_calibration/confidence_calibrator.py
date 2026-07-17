"""Confidence Calibrator — Calibrate confidence scores against outcomes."""
from __future__ import annotations
from typing import Any, Dict, List


class CalibrationBin:
    """A confidence bin for calibration analysis."""

    __slots__ = ("bin_label", "predicted_confidence", "actual_accuracy",
                 "sample_count", "calibration_error")

    def __init__(self, bin_label: str = "") -> None:
        self.bin_label = bin_label
        self.predicted_confidence: float = 0.0
        self.actual_accuracy: float = 0.0
        self.sample_count: int = 0
        self.calibration_error: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bin_label": self.bin_label,
            "predicted_confidence": round(self.predicted_confidence, 3),
            "actual_accuracy": round(self.actual_accuracy, 3),
            "sample_count": self.sample_count,
            "calibration_error": round(self.calibration_error, 4),
        }


class ConfidenceCalibrator:
    """Calibrate confidence scores to match actual accuracy."""

    BIN_EDGES = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]

    def __init__(self) -> None:
        self._bins: Dict[str, CalibrationBin] = {}
        self._calibration_count: int = 0

    def calibrate(self, predictions: List[Dict[str, float]]) -> List[CalibrationBin]:
        self._bins.clear()
        bins_data: Dict[str, List[Dict[str, float]]] = {}
        for pred in predictions:
            conf = pred.get("confidence", 0.5)
            bin_label = self._get_bin_label(conf)
            bins_data.setdefault(bin_label, []).append(pred)

        for label, items in bins_data.items():
            b = CalibrationBin(label)
            b.sample_count = len(items)
            b.predicted_confidence = sum(i.get("confidence", 0.5) for i in items) / len(items)
            correct = sum(1 for i in items if i.get("correct", False))
            b.actual_accuracy = correct / len(items) if items else 0.0
            b.calibration_error = abs(b.predicted_confidence - b.actual_accuracy)
            self._bins[label] = b

        self._calibration_count += 1
        return list(self._bins.values())

    def _get_bin_label(self, confidence: float) -> str:
        for i in range(len(self.BIN_EDGES) - 1):
            if self.BIN_EDGES[i] <= confidence < self.BIN_EDGES[i + 1]:
                return f"{self.BIN_EDGES[i]:.1f}-{self.BIN_EDGES[i+1]:.1f}"
        return "0.8-1.0"

    def get_overall_ece(self) -> float:
        if not self._bins:
            return 0.0
        total = sum(b.sample_count for b in self._bins.values())
        if total == 0:
            return 0.0
        return round(
            sum(b.calibration_error * b.sample_count for b in self._bins.values()) / total, 4,
        )

    def get_bins(self) -> List[CalibrationBin]:
        return list(self._bins.values())

    @property
    def calibration_count(self) -> int:
        return self._calibration_count
