"""CronExpression — Parse and evaluate cron expressions.

Supports standard 5-field cron:
  minute hour day_of_month month day_of_week

Examples:
  "0 9 * * *"      → Every day at 9:00 AM
  "0 9,18 * * *"    → Every day at 9 AM and 6 PM
  "0 9 * * 1-5"     → Weekdays at 9 AM
  "*/30 * * * *"    → Every 30 minutes
  "0 0 1 * *"       → First day of every month
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import List, Optional


class CronExpression:
    """Parse and evaluate standard cron expressions."""

    PRESETS = {
        "hourly": "0 * * * *",
        "daily": "0 9 * * *",
        "daily_morning": "0 8 * * *",
        "daily_evening": "0 18 * * *",
        "weekdays": "0 9 * * 1-5",
        "weekends": "0 10 * * 0,6",
        "weekly": "0 9 * * 1",
        "biweekly": "0 9 * * 1/2",
        "monthly": "0 9 1 * *",
        "twice_daily": "0 9,18 * * *",
        "every_2_hours": "0 */2 * * *",
        "every_6_hours": "0 */6 * * *",
    }

    def __init__(self, expression: str = "0 9 * * *") -> None:
        self._raw = expression.strip()
        self._fields: List[str] = self._parse_expression(self._raw)
        self._validate()

    def _parse_expression(self, expr: str) -> List[str]:
        if expr in self.PRESETS:
            expr = self.PRESETS[expr]
        fields = expr.split()
        if len(fields) != 5:
            fields = ["0", "9", "*", "*", "*"]
        return fields

    def _validate(self) -> None:
        ranges = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 7)]
        for i, (field, (lo, hi)) in enumerate(zip(self._fields, ranges)):
            parts = field.split(",")
            for part in parts:
                if part == "*":
                    continue
                if "/" in part:
                    continue
                if "-" in part:
                    a, b = part.split("-", 1)
                    if not (lo <= int(a) <= hi and lo <= int(b) <= hi):
                        raise ValueError(f"Invalid cron field: {field}")
                else:
                    val = int(part)
                    if not (lo <= val <= hi):
                        raise ValueError(f"Invalid cron field: {field}")

    def matches(self, dt: Optional[datetime] = None) -> bool:
        """Check if a datetime matches this cron expression."""
        if dt is None:
            dt = datetime.now(timezone.utc)

        return (
            self._matches_field(self._fields[0], dt.minute, 0, 59) and
            self._matches_field(self._fields[1], dt.hour, 0, 23) and
            self._matches_field(self._fields[2], dt.day, 1, 31) and
            self._matches_field(self._fields[3], dt.month, 1, 12) and
            self._matches_field(self._fields[4], dt.isoweekday() % 7, 0, 7)
        )

    def _matches_field(self, field: str, value: int, lo: int, hi: int) -> bool:
        if field == "*":
            return True
        for part in field.split(","):
            if "/" in part:
                base, step = part.split("/", 1)
                step = int(step)
                start = lo if base == "*" else int(base)
                if (value - start) % step == 0 and value >= start:
                    return True
            elif "-" in part:
                a, b = part.split("-", 1)
                if int(a) <= value <= int(b):
                    return True
            else:
                if int(part) == value:
                    return True
        return False

    def next_run_time(self, after: Optional[datetime] = None,
                      limit: int = 2000) -> Optional[datetime]:
        """Find the next datetime that matches this cron expression."""
        if after is None:
            after = datetime.now(timezone.utc)

        # Start from next minute
        candidate = after.replace(second=0, microsecond=0)
        from datetime import timedelta
        candidate += timedelta(minutes=1)

        for _ in range(limit):
            if self.matches(candidate):
                return candidate
            candidate += timedelta(minutes=1)
        return None

    def get_preset(self, name: str) -> str:
        return self.PRESETS.get(name, "0 9 * * *")

    def list_presets(self) -> List[str]:
        return list(self.PRESETS.keys())

    @property
    def raw(self) -> str:
        return self._raw

    def __str__(self) -> str:
        return self._raw
