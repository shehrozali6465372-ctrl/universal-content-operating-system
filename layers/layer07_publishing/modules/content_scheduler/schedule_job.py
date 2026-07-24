"""ScheduleJob — A single scheduled publishing job."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional
from enum import Enum


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class _JobIDCounter:
    """Thread-safe monotonically increasing job ID counter."""
    def __init__(self):
        self._counter = 0
        self._lock = threading.Lock()

    def next(self):
        with self._lock:
            self._counter += 1
            return self._counter

_job_counter = _JobIDCounter()


class ScheduleJob:
    """A scheduled content publishing job."""

    __slots__ = ("job_id", "topic", "platforms", "content_template",
                 "cron_expression", "timezone", "next_run", "last_run",
                 "status", "run_count", "fail_count", "metadata", "created_at")

    def __init__(self, topic: str = "", platforms: Optional[List[str]] = None) -> None:
        self.job_id: str = f"job_{_job_counter.next()}"
        self.topic: str = topic
        self.platforms: List[str] = platforms or ["facebook"]
        self.content_template: str = ""
        self.cron_expression: str = ""
        self.timezone: str = "UTC"
        self.next_run: float = 0.0
        self.last_run: float = 0.0
        self.status: JobStatus = JobStatus.PENDING
        self.run_count: int = 0
        self.fail_count: int = 0
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()

    @property
    def is_due(self) -> bool:
        """Is this job due for execution?"""
        if self.status in (JobStatus.CANCELLED, JobStatus.PAUSED):
            return False
        return time.time() >= self.next_run and self.next_run > 0

    @property
    def success_rate(self) -> float:
        if self.run_count == 0:
            return 0.0
        return round((self.run_count - self.fail_count) / self.run_count * 100, 1)

    def mark_running(self) -> None:
        self.status = JobStatus.RUNNING

    def mark_completed(self) -> None:
        self.status = JobStatus.COMPLETED
        self.run_count += 1
        self.last_run = time.time()

    def mark_failed(self) -> None:
        self.status = JobStatus.FAILED
        self.fail_count += 1
        self.last_run = time.time()

    def cancel(self) -> None:
        self.status = JobStatus.CANCELLED

    def pause(self) -> None:
        self.status = JobStatus.PAUSED

    def resume(self) -> None:
        self.status = JobStatus.PENDING

    def to_dict(self) -> Dict[str, Any]:
        from datetime import datetime, timezone as tz
        return {
            "job_id": self.job_id,
            "topic": self.topic,
            "platforms": self.platforms,
            "cron": self.cron_expression,
            "timezone": self.timezone,
            "status": self.status.value,
            "next_run": datetime.fromtimestamp(self.next_run, tz=tz.utc).isoformat() if self.next_run else "never",
            "last_run": datetime.fromtimestamp(self.last_run, tz=tz.utc).isoformat() if self.last_run else "never",
            "run_count": self.run_count,
            "fail_count": self.fail_count,
            "success_rate": self.success_rate,
            "created_at": datetime.fromtimestamp(self.created_at, tz=tz.utc).isoformat(),
        }
