"""Timing Optimizer — Predict best publishing time using historical patterns."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.engagement_predictor.prediction_memory import PredictionMemory

_TO_COUNTER = itertools.count(1)


class TimeSlot:
    """A time slot with predicted engagement quality."""

    __slots__ = ("slot_id", "hour", "day_of_week", "score", "confidence",
                 "historical_samples")

    def __init__(self, hour: int = 0, day_of_week: int = 0) -> None:
        self.slot_id: str = f"ts_{next(_TO_COUNTER)}"
        self.hour = hour
        self.day_of_week = day_of_week
        self.score: float = 0.0
        self.confidence: float = 0.0
        self.historical_samples: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "hour": self.hour,
            "day_of_week": self.day_of_week,
            "score": round(self.score, 3),
            "confidence": round(self.confidence, 3),
            "historical_samples": self.historical_samples,
        }


class TimingOptimizer:
    """Predict optimal publishing times based on platform patterns and history."""

    # Default peak hours by platform (UTC)
    DEFAULT_PEAKS: Dict[str, List[int]] = {
        "facebook": [9, 10, 12, 13, 19, 20],
        "instagram": [7, 8, 12, 17, 19, 21],
        "x": [8, 9, 12, 17, 18, 20],
        "linkedin": [7, 8, 10, 12, 17],
        "youtube": [12, 15, 18, 19, 20, 21],
        "tiktok": [7, 10, 12, 19, 21, 22],
        "pinterest": [20, 21, 22, 23, 14, 15],
        "reddit": [6, 7, 8, 12, 18, 19],
        "medium": [7, 8, 9, 10, 14, 17],
    }

    def __init__(self, memory: Optional[PredictionMemory] = None) -> None:
        self._memory = memory
        self._custom_peaks: Dict[str, List[int]] = {}

    def predict_best_times(self, platform: str = "", count: int = 3,
                           day_of_week: int = -1) -> List[TimeSlot]:
        """Return the best time slots for publishing."""
        peaks = self._get_peaks(platform)
        slots: List[TimeSlot] = []

        for hour in sorted(peaks):
            if day_of_week >= 0 and day_of_week in (0, 6):
                score = 0.85
            else:
                score = 0.9
            slot = TimeSlot(hour, day_of_week if day_of_week >= 0 else 0)
            slot.score = score
            slot.confidence = 0.6
            slot.historical_samples = 0
            slots.append(slot)

        slots.sort(key=lambda s: s.score, reverse=True)
        return slots[:count]

    def predict_for_content(self, platform: str = "", content_type: str = "",
                            count: int = 3) -> List[TimeSlot]:
        """Platform + content type aware timing."""
        base_slots = self.predict_best_times(platform, count=count)
        if content_type.lower() in ("reel", "short_video", "story"):
            for s in base_slots:
                if s.hour in (19, 20, 21, 22):
                    s.score = min(1.0, s.score + 0.1)
        elif content_type.lower() in ("article", "blog_post", "long_form"):
            for s in base_slots:
                if s.hour in (7, 8, 9, 10):
                    s.score = min(1.0, s.score + 0.1)
        base_slots.sort(key=lambda s: s.score, reverse=True)
        return base_slots[:count]

    def set_custom_peaks(self, platform: str, hours: List[int]) -> None:
        self._custom_peaks[platform.lower()] = hours

    def _get_peaks(self, platform: str) -> List[int]:
        p = platform.lower()
        if p in self._custom_peaks:
            return self._custom_peaks[p]
        return self.DEFAULT_PEAKS.get(p, [9, 12, 18, 20])

    def score_hour(self, hour: int, platform: str = "") -> float:
        peaks = self._get_peaks(platform)
        if hour in peaks:
            return 0.9
        if abs(min(peaks, key=lambda p: abs(p - hour)) - hour) <= 1:
            return 0.7
        return 0.4
