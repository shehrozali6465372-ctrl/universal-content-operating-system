"""Scheduler — Schedule content publishing at optimal times."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer07_publishing.modules.publishing_planner.publish_plan import PublishPlan
from layers.layer07_publishing.modules.publishing_planner.platform_selector import PEAK_HOURS


DEFAULT_TIMEZONE = "UTC"


class Scheduler:
    """Schedule publishing for optimal engagement."""

    def __init__(self, default_timezone: str = "UTC") -> None:
        self._default_tz = default_timezone
        self._schedule_count = 0

    def schedule_immediate(self, plan: PublishPlan) -> PublishPlan:
        """Set all targets to publish immediately."""
        now = time.time()
        for target in plan.targets:
            target.scheduled_time = now
            target.timezone = self._default_tz
        self._schedule_count += 1
        return plan

    def schedule_optimal(self, plan: PublishPlan, prefer_peak: bool = True) -> PublishPlan:
        """Schedule at optimal engagement times."""
        for target in plan.targets:
            if prefer_peak:
                target.scheduled_time = self._next_peak_time(target.platform)
            else:
                target.scheduled_time = time.time() + 3600  # 1 hour from now
            target.timezone = self._default_tz
        self._schedule_count += 1
        return plan

    def schedule_delayed(self, plan: PublishPlan, delay_seconds: float) -> PublishPlan:
        """Schedule with a specific delay."""
        future_time = time.time() + delay_seconds
        for target in plan.targets:
            target.scheduled_time = future_time
            target.timezone = self._default_tz
        self._schedule_count += 1
        return plan

    def stagger(self, plan: PublishPlan, interval_minutes: int = 30) -> PublishPlan:
        """Stagger publishing across platforms."""
        base_time = time.time()
        for i, target in enumerate(plan.targets):
            target.scheduled_time = base_time + (i * interval_minutes * 60)
            target.timezone = self._default_tz
        self._schedule_count += 1
        return plan

    def get_scheduled(self, plan: PublishPlan) -> List[Dict[str, Any]]:
        """Get all scheduled targets with their times."""
        result = []
        for target in plan.targets:
            result.append({
                "platform": target.platform,
                "scheduled_time": target.scheduled_time,
                "timezone": target.timezone,
            })
        return result

    def _next_peak_time(self, platform: str) -> float:
        """Find the next peak engagement time."""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        peak_hours = PEAK_HOURS.get(platform, [9, 12, 18])

        for hour in peak_hours:
            target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
            if target > now:
                return target.timestamp()
        # If all peak hours passed today, use tomorrow's first peak
        tomorrow = now + datetime.timedelta(days=1)
        target = tomorrow.replace(hour=peak_hours[0], minute=0, second=0, microsecond=0)
        return target.timestamp()

    @property
    def schedule_count(self) -> int:
        return self._schedule_count
