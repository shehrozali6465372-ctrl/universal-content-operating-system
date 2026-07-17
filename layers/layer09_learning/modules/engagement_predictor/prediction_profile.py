"""Prediction Profile — Configuration for engagement predictions."""
from __future__ import annotations
from typing import Any, Dict
import itertools

_PRED_COUNTER = itertools.count(1)

PREDICTION_HORIZONS = ("immediate", "24h", "7d", "30d")
CONFIDENCE_LEVELS = ("low", "medium", "high", "very_high")


class PredictionProfile:
    """Configure an engagement prediction run."""

    __slots__ = ("profile_id", "horizon", "confidence_level", "platform",
                 "content_type", "audience_size", "historical_window_days",
                 "include_virality", "include_timing", "include_audience",
                 "metadata")

    def __init__(self, horizon: str = "24h",
                 confidence_level: str = "medium",
                 platform: str = "",
                 content_type: str = "") -> None:
        self.profile_id: str = f"pp_{next(_PRED_COUNTER)}"
        self.horizon = horizon if horizon in PREDICTION_HORIZONS else "24h"
        self.confidence_level = confidence_level if confidence_level in CONFIDENCE_LEVELS else "medium"
        self.platform = platform
        self.content_type = content_type
        self.audience_size: int = 0
        self.historical_window_days: int = 30
        self.include_virality: bool = True
        self.include_timing: bool = True
        self.include_audience: bool = True
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "horizon": self.horizon,
            "confidence_level": self.confidence_level,
            "platform": self.platform,
            "content_type": self.content_type,
            "audience_size": self.audience_size,
            "include_virality": self.include_virality,
            "include_timing": self.include_timing,
            "include_audience": self.include_audience,
        }
