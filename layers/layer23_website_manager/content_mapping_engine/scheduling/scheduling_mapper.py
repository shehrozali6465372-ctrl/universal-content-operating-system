"""SchedulingMapper — Decide publishing priority, timing, and schedule strategy."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import Priority


class SchedulingMapper:
    """Map content to publishing priority and optimal schedule time."""

    # Peak hours per niche (hour in 24h, UTC)
    NICHE_PEAK_HOURS: Dict[str, List[int]] = {
        "home_decor": [10, 14, 19],
        "fashion": [11, 15, 20],
        "beauty": [12, 16, 21],
        "food": [9, 13, 17],
        "tech": [10, 15, 20],
        "fitness": [7, 12, 18],
        "travel": [11, 16, 20],
        "finance": [9, 14, 19],
        "diy": [10, 15, 18],
    }

    def __init__(self) -> None:
        self._scheduling_log: List[dict] = []

    def schedule(self, niche: str, intent: str, confidence: float,
                  existing_queue: int = 0) -> Dict[str, Any]:
        """Determine priority, suggested publish time, and reason."""
        # Priority based on confidence and intent
        if confidence >= 0.8 and intent in ("commercial", "educational"):
            priority = Priority.HIGH
            reason = "High confidence content with commercial/educational value"
        elif confidence >= 0.6:
            priority = Priority.MEDIUM
            reason = "Medium confidence content"
        else:
            priority = Priority.LOW
            reason = "Low confidence content, needs review"

        # Suggest publish time based on niche peak hours
        peak_hours = self.NICHE_PEAK_HOURS.get(niche, [12])
        peak_hour = random.choice(peak_hours)

        now = time.time()
        current_hour = time.gmtime(now).tm_hour

        # Calculate seconds until next peak hour
        if current_hour < peak_hour:
            hours_until = peak_hour - current_hour
        else:
            hours_until = (24 - current_hour) + peak_hour

        suggested_time = now + (hours_until * 3600)

        result = {
            "priority": priority.value,
            "suggested_publish_time": suggested_time,
            "schedule_reason": reason,
            "peak_hour": peak_hour,
            "queue_position": existing_queue + 1,
        }

        # Adjust for queue
        if existing_queue > 5:
            result["priority"] = Priority.LOW.value
            result["schedule_reason"] += " (delayed due to queue)"

        self._scheduling_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        priorities: Dict[str, int] = {}
        for entry in self._scheduling_log:
            p = entry["priority"]
            priorities[p] = priorities.get(p, 0) + 1
        return {
            "total_scheduled": len(self._scheduling_log),
            "by_priority": priorities,
        }
