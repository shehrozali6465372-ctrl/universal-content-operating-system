"""PinScheduler — Schedule, queue, and manage pin publishing times."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import PinterestPin, PinStatus
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import SchedulingError


class PinScheduler:
    """Manage pin scheduling — schedule, queue, publish now, retry failed."""

    def __init__(self) -> None:
        self._scheduled_jobs: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._total_scheduled = 0

    def schedule(self, pin: PinterestPin, publish_time: float) -> bool:
        """Schedule a pin for future publishing."""
        if publish_time <= time.time():
            raise SchedulingError("Publish time must be in the future")

        with self._lock:
            pin.status = PinStatus.SCHEDULED
            pin.publish_time = publish_time
            self._scheduled_jobs[pin.pin_id] = {
                "pin_id": pin.pin_id,
                "publish_time": publish_time,
                "created": time.time(),
            }
            self._total_scheduled += 1
        return True

    def cancel_schedule(self, pin: PinterestPin) -> bool:
        """Cancel scheduled publishing."""
        with self._lock:
            pin.status = PinStatus.DRAFT
            pin.publish_time = 0.0
            return self._scheduled_jobs.pop(pin.pin_id, None) is not None

    def get_due_pins(self, pins: List[PinterestPin]) -> List[PinterestPin]:
        """Get pins that are due for publishing."""
        now = time.time()
        return [p for p in pins if p.status == PinStatus.SCHEDULED
                and 0 < p.publish_time <= now]

    def get_queue_stats(self) -> Dict[str, Any]:
        now = time.time()
        upcoming = [j for j in self._scheduled_jobs.values() if j["publish_time"] > now]
        overdue = [j for j in self._scheduled_jobs.values() if j["publish_time"] <= now]

        return {
            "total_scheduled": len(self._scheduled_jobs),
            "upcoming": len(upcoming),
            "overdue": len(overdue),
            "total_ever_scheduled": self._total_scheduled,
        }

    def get_stats(self) -> Dict[str, Any]:
        return self.get_queue_stats()
