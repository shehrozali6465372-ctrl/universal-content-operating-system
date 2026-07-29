"""CronManager — Schedule recurring automation jobs."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import CronSchedule


# Simple cron presets
_CRON_PRESETS = {
    "every_hour": 3600,
    "every_2_hours": 7200,
    "every_4_hours": 14400,
    "every_6_hours": 21600,
    "every_12_hours": 43200,
    "daily": 86400,
    "weekly": 604800,
    "monthly": 2592000,
}


class CronManager:
    """Manage cron-based scheduling."""

    def __init__(self) -> None:
        self._schedules: Dict[str, CronSchedule] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._loop_running: bool = False
        self._loop_thread: Optional[threading.Thread] = None

    def add_schedule(self, name: str, cron_expr: str,
                     workflow_id: str = "") -> CronSchedule:
        sched = CronSchedule(name=name, cron_expr=cron_expr, workflow_id=workflow_id)
        interval = _CRON_PRESETS.get(cron_expr, 86400)
        sched.next_run = time.time() + interval
        with self._lock:
            self._schedules[sched.schedule_id] = sched
        return sched

    def remove_schedule(self, schedule_id: str) -> bool:
        with self._lock:
            return self._schedules.pop(schedule_id, None) is not None

    def get_schedule(self, schedule_id: str) -> Optional[CronSchedule]:
        return self._schedules.get(schedule_id)

    def get_all_schedules(self) -> List[CronSchedule]:
        return list(self._schedules.values())

    def enable_schedule(self, schedule_id: str) -> bool:
        s = self._schedules.get(schedule_id)
        if not s:
            return False
        s.enabled = True
        return True

    def disable_schedule(self, schedule_id: str) -> bool:
        s = self._schedules.get(schedule_id)
        if not s:
            return False
        s.enabled = False
        return True

    def register_handler(self, schedule_id: str, handler: Callable) -> None:
        with self._lock:
            self._handlers[schedule_id] = handler

    def get_due_schedules(self) -> List[CronSchedule]:
        now = time.time()
        with self._lock:
            return [
                s for s in self._schedules.values()
                if s.enabled and now >= s.next_run
            ]

    def tick(self) -> List[str]:
        fired = []
        for sched in self.get_due_schedules():
            sched.last_run = time.time()
            sched.run_count += 1
            interval = _CRON_PRESETS.get(sched.cron_expr, 86400)
            sched.next_run = time.time() + interval
            handler = self._handlers.get(sched.schedule_id)
            if handler:
                try:
                    handler(sched)
                except Exception:
                    pass
            fired.append(sched.schedule_id)
        return fired

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_schedules": len(self._schedules),
                "enabled": sum(1 for s in self._schedules.values() if s.enabled),
                "due_now": len(self.get_due_schedules()),
                "handlers": len(self._handlers),
            }
