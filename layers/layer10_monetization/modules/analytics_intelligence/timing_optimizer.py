"""TimingOptimizer — Find the best times to publish."""
from __future__ import annotations
import itertools
from typing import Any, Dict, List

_TO_COUNTER = itertools.count(1)


class TimingSlot:
    """A time slot with engagement data."""

    __slots__ = ("slot_id", "hour", "day_of_week", "platform",
                 "avg_engagement", "sample_count", "confidence")

    def __init__(self, hour: int = 0, day_of_week: int = 0) -> None:
        self.slot_id: str = f"ts_{next(_TO_COUNTER)}"
        self.hour = hour
        self.day_of_week = day_of_week
        self.platform: str = ""
        self.avg_engagement: float = 0.0
        self.sample_count: int = 0
        self.confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"slot_id": self.slot_id, "hour": self.hour,
                "day_of_week": self.day_of_week, "avg_engagement": round(self.avg_engagement, 4),
                "sample_count": self.sample_count}


class TimingOptimizer:
    """Find optimal publishing times based on historical engagement."""

    def __init__(self) -> None:
        self._slots: List[TimingSlot] = []
        self._slot_index: Dict[str, TimingSlot] = {}

    def record_engagement(self, hour: int, day_of_week: int,
                          platform: str, engagement: float) -> TimingSlot:
        key = f"{platform}:{hour}:{day_of_week}"
        if key in self._slot_index:
            slot = self._slot_index[key]
            total = slot.avg_engagement * slot.sample_count + engagement
            slot.sample_count += 1
            slot.avg_engagement = total / slot.sample_count
            slot.confidence = min(1.0, slot.sample_count / 30.0)
        else:
            slot = TimingSlot(hour, day_of_week)
            slot.platform = platform
            slot.avg_engagement = engagement
            slot.sample_count = 1
            slot.confidence = 1.0 / 30.0
            self._slots.append(slot)
            self._slot_index[key] = slot
        return slot

    def get_best_times(self, platform: str = "", count: int = 5,
                       day_of_week: int = -1) -> List[TimingSlot]:
        slots = self._slots
        if platform:
            slots = [s for s in slots if s.platform == platform]
        if day_of_week >= 0:
            slots = [s for s in slots if s.day_of_week == day_of_week]
        return sorted(slots, key=lambda s: s.avg_engagement, reverse=True)[:count]

    def get_slot(self, hour: int, day_of_week: int,
                 platform: str = "") -> TimingSlot:
        key = f"{platform}:{hour}:{day_of_week}"
        return self._slot_index.get(key)

    def get_slots_for_day(self, day_of_week: int,
                          platform: str = "") -> List[TimingSlot]:
        slots = self._slots
        if platform:
            slots = [s for s in slots if s.platform == platform]
        return sorted([s for s in slots if s.day_of_week == day_of_week],
                       key=lambda s: s.avg_engagement, reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        platforms: Dict[str, int] = {}
        for s in self._slots:
            platforms[s.platform] = platforms.get(s.platform, 0) + 1
        return {"total_slots": len(self._slots), "by_platform": platforms}
