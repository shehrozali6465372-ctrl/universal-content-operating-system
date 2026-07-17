"""Calibration Profile — Calibration configuration and state."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List

_CP_COUNTER = itertools.count(1)

CALIBRATION_STATUSES = ("pending", "calibrating", "calibrated", "stale", "archived")
METRIC_TYPES = ("engagement", "reach", "conversion", "quality", "safety", "seo", "brand")


class CalibrationProfile:
    """Configuration and state for a single metric calibration."""

    __slots__ = ("profile_id", "metric_name", "metric_type", "status",
                 "predicted_weight", "actual_weight", "bias", "calibration_count",
                 "last_calibrated", "created_at", "updated_at", "tags")

    def __init__(self, metric_name: str = "", metric_type: str = "quality") -> None:
        self.profile_id: str = f"cp_{next(_CP_COUNTER)}"
        self.metric_name = metric_name
        self.metric_type = metric_type if metric_type in METRIC_TYPES else "quality"
        self.status: str = "pending"
        self.predicted_weight: float = 1.0
        self.actual_weight: float = 1.0
        self.bias: float = 0.0
        self.calibration_count: int = 0
        self.last_calibrated: float = 0.0
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self.tags: List[str] = []

    @property
    def calibration_accuracy(self) -> float:
        if self.calibration_count == 0:
            return 0.0
        return round(min(1.0, self.calibration_count / max(1, self.calibration_count + 5)), 3)

    @property
    def is_stale(self) -> bool:
        if self.last_calibrated == 0:
            return True
        return (time.time() - self.last_calibrated) > 86400 * 7

    def update(self, predicted: float, actual: float) -> None:
        self.predicted_weight = predicted
        self.actual_weight = actual
        self.bias = round(actual - predicted, 4)
        self.calibration_count += 1
        self.last_calibrated = time.time()
        self.updated_at = time.time()
        self.status = "calibrated"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "metric_name": self.metric_name,
            "metric_type": self.metric_type,
            "status": self.status,
            "predicted_weight": round(self.predicted_weight, 4),
            "actual_weight": round(self.actual_weight, 4),
            "bias": round(self.bias, 4),
            "calibration_count": self.calibration_count,
            "calibration_accuracy": self.calibration_accuracy,
        }
