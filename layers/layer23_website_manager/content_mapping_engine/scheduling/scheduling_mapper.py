"""SchedulingMapper — Decide when to publish content: priority, time, strategy."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import MappingPriority
from layers.layer23_website_manager.content_mapping_engine.exceptions import SchedulingMappingError


# Peak posting times per niche (hour in UTC)
PEAK_TIMES: Dict[str, List[int]] = {
    "home_decor": [10, 14, 19],  # 10am, 2pm, 7pm UTC
    "fashion": [11, 15, 20],
    "beauty": [10, 13, 18],
    "food": [9, 12, 17],
    "tech": [10, 14, 18],
    "fitness": [7, 12, 18],
    "travel": [10, 15, 20],
    "finance": [8, 12, 17],
    "diy": [10, 14, 19],
    "garden": [9, 13, 17],
}


class SchedulingMapper:
    """Determine optimal publishing time and priority for content."""

    def __init__(self) -> None:
        self._schedule_log: List[dict] = []
        self._total_scheduled = 0

    def map_schedule(self, niche: str = "", intent: str = "",
                      content_type: str = "article",
                      confidence: float = 0.7) -> Dict[str, Any]:
        """Determine priority and optimal publishing schedule."""
        priority = self._determine_priority(intent, content_type, confidence)
        schedule_time = self._get_optimal_time(niche)
        schedule_reason = self._generate_reason(priority, schedule_time, niche)

        result = {
            "priority": priority.value,
            "schedule_time": schedule_time,
            "schedule_reason": schedule_reason,
            "peak_hours": PEAK_TIMES.get(niche, [12]),
        }

        self._schedule_log.append(result)
        self._total_scheduled += 1
        return result

    def _determine_priority(self, intent: str, content_type: str,
                             confidence: float) -> MappingPriority:
        """Determine publishing priority based on multiple factors."""
        score = 0

        if intent in ["commercial", "trending"]:
            score += 2
        if content_type in ["news", "deal"]:
            score += 2
        if confidence > 0.9:
            score += 1
        if intent == "inspirational":
            score -= 1

        if score >= 3:
            return MappingPriority.HIGH
        elif score >= 1:
            return MappingPriority.MEDIUM
        return MappingPriority.LOW

    def _get_optimal_time(self, niche: str) -> float:
        """Get optimal publishing timestamp based on niche."""
        peaks = PEAK_TIMES.get(niche, [12])
        # Pick nearest peak hour
        current_hour = time.gmtime().tm_hour
        future_hours = [h for h in peaks if h > current_hour]

        if future_hours:
            target_hour = future_hours[0]
        else:
            # Next day first peak
            target_hour = peaks[0] + 24

        # Calculate seconds until target hour
        now = time.time()
        gmt = time.gmtime(now)
        seconds_to_target = (target_hour - gmt.tm_hour) * 3600 - gmt.tm_min * 60 - gmt.tm_sec
        if seconds_to_target < 0:
            seconds_to_target += 86400  # Next day

        return now + seconds_to_target

    def _generate_reason(self, priority: MappingPriority,
                          schedule_time: float, niche: str) -> str:
        """Generate human-readable reason for scheduling decision."""
        if priority == MappingPriority.HIGH:
            return f"High commercial intent content for {niche} - publish at next peak time"
        elif priority == MappingPriority.MEDIUM:
            return f"Standard content for {niche} - schedule during peak hours"
        return f"Low priority evergreen content for {niche} - publish when queue allows"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_scheduled": self._total_scheduled}
