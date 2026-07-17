"""Schedule Memory — Learn best posting hours, weekdays, seasonal patterns."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.publishing_memory.publish_history import PublishRecord


class ScheduleInsight:
    """Insight about optimal scheduling."""

    __slots__ = ("best_hours", "best_weekdays", "seasonal_notes",
                 "total_data_points", "confidence")

    def __init__(self) -> None:
        self.best_hours: List[int] = []
        self.best_weekdays: List[int] = []
        self.seasonal_notes: List[str] = []
        self.total_data_points: int = 0
        self.confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return {
            "best_hours": self.best_hours,
            "best_weekdays": [day_names[d] for d in self.best_weekdays if 0 <= d < 7],
            "seasonal_notes": self.seasonal_notes,
            "total_data_points": self.total_data_points,
            "confidence": round(self.confidence, 3),
        }


class ScheduleMemory:
    """Learn optimal posting schedules from history."""

    def __init__(self) -> None:
        self._hour_counts: Dict[int, int] = {}
        self._weekday_counts: Dict[int, int] = {}
        self._hour_success: Dict[int, int] = {}
        self._weekday_success: Dict[int, int] = {}
        self._total_count: int = 0

    def observe(self, record: PublishRecord, success: bool = True) -> None:
        hour = record.get_hour()
        weekday = record.get_weekday()
        self._hour_counts[hour] = self._hour_counts.get(hour, 0) + 1
        self._weekday_counts[weekday] = self._weekday_counts.get(weekday, 0) + 1
        if success:
            self._hour_success[hour] = self._hour_success.get(hour, 0) + 1
            self._weekday_success[weekday] = self._weekday_success.get(weekday, 0) + 1
        self._total_count += 1

    def get_insight(self) -> ScheduleInsight:
        insight = ScheduleInsight()
        insight.total_data_points = self._total_count
        insight.confidence = min(1.0, self._total_count / 100)

        if self._hour_counts:
            hours_by_success = sorted(
                self._hour_counts.keys(),
                key=lambda h: self._hour_success.get(h, 0) / max(1, self._hour_counts.get(h, 1)),
                reverse=True,
            )
            insight.best_hours = hours_by_success[:3]

        if self._weekday_counts:
            weekdays_by_success = sorted(
                self._weekday_counts.keys(),
                key=lambda w: self._weekday_success.get(w, 0) / max(1, self._weekday_counts.get(w, 1)),
                reverse=True,
            )
            insight.best_weekdays = weekdays_by_success[:2]

        return insight

    def get_hour_distribution(self) -> Dict[int, float]:
        total = max(1, sum(self._hour_counts.values()))
        return {h: round(c / total, 3) for h, c in sorted(self._hour_counts.items())}

    def get_weekday_distribution(self) -> Dict[int, float]:
        total = max(1, sum(self._weekday_counts.values()))
        return {w: round(c / total, 3) for w, c in sorted(self._weekday_counts.items())}

    @property
    def total_count(self) -> int:
        return self._total_count
