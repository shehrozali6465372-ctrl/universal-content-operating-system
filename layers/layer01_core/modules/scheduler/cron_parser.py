"""
Cron Parser Module
Layer 1: Core System — Module 7

Parses cron expressions into run times.
Supports: minute hour day month weekday
"""

from typing import Optional, List
from datetime import datetime, timedelta


class CronParser:
    """Parse cron expressions and calculate next run times."""

    def __init__(self, expression: str):
        """
        expression: "minute hour day month weekday"
        Example: "0 20 * * 1-5" = Weekdays at 8 PM
        """
        self._original = expression
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression (need 5 parts): {expression}")
        self._minute = self._parse_field(parts[0], 0, 59)
        self._hour = self._parse_field(parts[1], 0, 23)
        self._day = self._parse_field(parts[2], 1, 31)
        self._month = self._parse_field(parts[3], 1, 12)
        self._weekday = self._parse_field(parts[4], 0, 6)

    def _parse_field(self, field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field (supports numbers, ranges, steps, wildcards)."""
        values = set()
        for part in field.split(","):
            part = part.strip()
            if part == "*":
                return list(range(min_val, max_val + 1))
            if "/" in part:
                base, step = part.split("/")
                step = int(step)
                if base == "*":
                    base_range = range(min_val, max_val + 1)
                elif "-" in base:
                    s, e = map(int, base.split("-"))
                    base_range = range(s, e + 1)
                else:
                    base_range = range(int(base), max_val + 1)
                values.update(base_range[::step])
            elif "-" in part:
                s, e = map(int, part.split("-"))
                values.update(range(s, e + 1))
            else:
                values.add(int(part))
        # Filter valid range
        return [v for v in values if min_val <= v <= max_val]

    def is_match(self, dt: datetime) -> bool:
        """Check if a datetime matches the cron expression."""
        return (
            dt.minute in self._minute
            and dt.hour in self._hour
            and dt.day in self._day
            and dt.month in self._month
            and dt.weekday() in self._weekday
        )

    def get_next_run(self, from_dt: Optional[datetime] = None) -> datetime:
        """Calculate next run time from given datetime."""
        dt = (from_dt or datetime.now()).replace(second=0, microsecond=0)
        for _ in range(525600):  # Max 1 year
            if self.is_match(dt):
                return dt
            dt += timedelta(minutes=1)
        raise RuntimeError("Could not find next run time within 1 year")

    def get_next_runs(self, count: int = 5) -> List[datetime]:
        """Get next N run times."""
        runs = []
        dt = datetime.now()
        while len(runs) < count:
            dt = self.get_next_run(dt + timedelta(minutes=1))
            runs.append(dt)
        return runs

    def describe(self) -> str:
        """Human-readable description of cron expression."""
        parts = self._original.split()
        minute = "every minute" if parts[0] == "*" else f"minute {parts[0]}"
        hour = "every hour" if parts[1] == "*" else f"hour {parts[1]}"
        day = "every day" if parts[2] == "*" else f"day {parts[2]}"
        month = "every month" if parts[3] == "*" else f"month {parts[3]}"
        weekday = "any weekday" if parts[4] == "*" else f"weekday {parts[4]}"
        return f"{minute}, {hour}, {day}, {month}, {weekday}"
