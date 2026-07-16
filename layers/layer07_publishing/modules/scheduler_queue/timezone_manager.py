"""Timezone Manager — Handle timezone conversions for scheduling."""
from __future__ import annotations
import datetime
from typing import Dict


# Common timezone offsets (UTC)
TIMEZONE_OFFSETS: Dict[str, int] = {
    "UTC": 0, "US/Eastern": -5, "US/Central": -6, "US/Pacific": -8,
    "Europe/London": 0, "Europe/Berlin": 1, "Europe/Paris": 1,
    "Asia/Dubai": 4, "Asia/Karachi": 5, "Asia/Kolkata": 5,
    "Asia/Shanghai": 8, "Asia/Tokyo": 9,
    "Australia/Sydney": 10, "Pacific/Auckland": 12,
}


class TimezoneManager:
    def __init__(self, default_tz: str = "UTC") -> None:
        self._default_tz = default_tz

    def to_utc(self, timestamp: float, from_tz: str) -> float:
        offset = TIMEZONE_OFFSETS.get(from_tz, 0)
        return timestamp - (offset * 3600)

    def to_local(self, timestamp: float, to_tz: str) -> float:
        offset = TIMEZONE_OFFSETS.get(to_tz, 0)
        return timestamp + (offset * 3600)

    def convert(self, timestamp: float, from_tz: str, to_tz: str) -> float:
        utc = self.to_utc(timestamp, from_tz)
        return self.to_local(utc, to_tz)

    def get_local_hour(self, timestamp: float, tz: str = "") -> int:
        tz = tz or self._default_tz
        local_ts = self.to_local(timestamp, tz)
        return datetime.datetime.utcfromtimestamp(local_ts).hour

    def is_business_hours(self, timestamp: float, tz: str = "", start: int = 9, end: int = 17) -> bool:
        hour = self.get_local_hour(timestamp, tz)
        return start <= hour < end

    @staticmethod
    def list_timezones():
        return list(TIMEZONE_OFFSETS.keys())
