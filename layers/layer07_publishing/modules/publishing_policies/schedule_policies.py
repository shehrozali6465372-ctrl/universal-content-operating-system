"""Schedule Policies — Platform-specific scheduling restrictions."""
from __future__ import annotations
from typing import Any, Dict, List


class SchedulePolicy:
    """Schedule policy for a platform."""

    __slots__ = ("platform", "supports_scheduling", "min_advance_minutes",
                 "max_advance_days", "timezone_aware", "business_hours_only",
                 "blocked_hours")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.supports_scheduling: bool = True
        self.min_advance_minutes: int = 10
        self.max_advance_days: int = 60
        self.timezone_aware: bool = True
        self.business_hours_only: bool = False
        self.blocked_hours: List[int] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "supports_scheduling": self.supports_scheduling,
            "min_advance_minutes": self.min_advance_minutes,
            "max_advance_days": self.max_advance_days,
            "timezone_aware": self.timezone_aware,
        }


DEFAULT_SCHEDULE_POLICIES: Dict[str, SchedulePolicy] = {
    "facebook": SchedulePolicy("facebook"),
    "instagram": SchedulePolicy("instagram"),
    "twitter": SchedulePolicy("twitter"),
    "linkedin": SchedulePolicy("linkedin"),
    "youtube": SchedulePolicy("youtube"),
    "tiktok": SchedulePolicy("tiktok"),
}


class SchedulePolicies:
    """Centralized schedule policies for all platforms."""

    def __init__(self) -> None:
        self._policies: Dict[str, SchedulePolicy] = dict(DEFAULT_SCHEDULE_POLICIES)

    def get_policy(self, platform: str) -> SchedulePolicy:
        return self._policies.get(platform.lower(), SchedulePolicy(platform))

    def can_schedule(self, platform: str, advance_minutes: int) -> bool:
        policy = self.get_policy(platform)
        if not policy.supports_scheduling:
            return False
        return advance_minutes >= policy.min_advance_minutes

    def is_valid_schedule_time(self, platform: str, hour: int) -> bool:
        policy = self.get_policy(platform)
        if policy.business_hours_only:
            return 9 <= hour < 17
        if policy.blocked_hours:
            return hour not in policy.blocked_hours
        return True

    def get_all_policies(self) -> Dict[str, SchedulePolicy]:
        return dict(self._policies)
