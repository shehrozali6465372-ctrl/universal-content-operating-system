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
        """Parse one cron field with strict range and step validation."""
        values = set()
        for part in field.split(","):
            part = part.strip()
            if not part:
                raise ValueError("Invalid empty cron field")

            if part == "*":
                values.update(range(min_val, max_val + 1))
                continue

            if "/" in part:
                if part.count("/") != 1:
                    raise ValueError(f"Invalid cron step: {part}")
                base, step_text = part.split("/", 1)
                try:
                    step = int(step_text)
                except ValueError as exc:
                    raise ValueError(f"Invalid cron step: {part}") from exc
                if step <= 0:
                    raise ValueError(f"Cron step must be positive: {part}")
                if base == "*":
                    start = min_val
                    stop = max_val
                elif "-" in base:
                    pieces = base.split("-", 1)
                    try:
                        start, stop = int(pieces[0]), int(pieces[1])
                    except ValueError as exc:
                        raise ValueError(f"Invalid cron range: {part}") from exc
                else:
                    try:
                        start = int(base)
                    except ValueError as exc:
                        raise ValueError(f"Invalid cron value: {part}") from exc
                    stop = max_val
                if start < min_val or stop > max_val or start > stop:
                    raise ValueError(f"Cron range out of bounds: {part}")
                values.update(range(start, stop + 1, step))
                continue

            if "-" in part:
                pieces = part.split("-", 1)
                try:
                    start, stop = int(pieces[0]), int(pieces[1])
                except ValueError as exc:
                    raise ValueError(f"Invalid cron range: {part}") from exc
                if start < min_val or stop > max_val or start > stop:
                    raise ValueError(f"Cron range out of bounds: {part}")
                values.update(range(start, stop + 1))
                continue

            try:
                value = int(part)
            except ValueError as exc:
                raise ValueError(f"Invalid cron value: {part}") from exc
            if value < min_val or value > max_val:
                raise ValueError(f"Cron value out of bounds: {part}")
            values.add(value)

        if not values:
            raise ValueError(f"Cron field produced no valid values: {field}")
        return sorted(values)

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
