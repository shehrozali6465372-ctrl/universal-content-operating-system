"""backup_scheduler.py — Backup scheduling."""
from __future__ import annotations
import time
from typing import Any, Dict, List


class BackupSchedule:
    """A backup schedule entry."""
    __slots__ = ("schedule_id", "name", "backup_type", "interval_seconds",
                 "next_run", "enabled")
    _counter = 0

    def __init__(self, name: str, backup_type: str = "full",
                 interval_seconds: float = 86400.0) -> None:
        BackupSchedule._counter += 1
        self.schedule_id: int = BackupSchedule._counter
        self.name = name
        self.backup_type = backup_type
        self.interval_seconds = interval_seconds
        self.next_run: float = time.time() + interval_seconds
        self.enabled: bool = True


class BackupScheduler:
    """Schedules and manages backup jobs."""

    def __init__(self) -> None:
        self._schedules: Dict[int, BackupSchedule] = {}
        self._history: List[Dict[str, Any]] = []

    def add_schedule(self, schedule: BackupSchedule) -> BackupSchedule:
        self._schedules[schedule.schedule_id] = schedule
        return schedule

    def remove_schedule(self, schedule_id: int) -> bool:
        return self._schedules.pop(schedule_id, None) is not None

    def get_due_schedules(self) -> List[BackupSchedule]:
        now = time.time()
        return [s for s in self._schedules.values()
                if s.enabled and s.next_run <= now]

    def mark_completed(self, schedule_id: int) -> None:
        s = self._schedules.get(schedule_id)
        if s:
            s.next_run = time.time() + s.interval_seconds
            self._history.append({"schedule_id": schedule_id, "time": time.time()})

    def list_schedules(self) -> List[BackupSchedule]:
        return list(self._schedules.values())

    def stats(self) -> Dict[str, Any]:
        return {"schedules": len(self._schedules), "history": len(self._history)}
