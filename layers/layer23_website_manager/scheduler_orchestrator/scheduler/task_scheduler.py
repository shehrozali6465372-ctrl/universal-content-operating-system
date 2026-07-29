"""TaskScheduler — Schedule jobs for future execution."""
from __future__ import annotations
import time
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Callable

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    ScheduledJob, Priority, JobStatus,
)


class TaskScheduler:
    """Schedule and manage timed job execution."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduledJob] = {}

    def schedule_job(self, workflow_id: str, name: str = "",
                     priority: Priority = Priority.NORMAL,
                     scheduled_time: Optional[float] = None,
                     delay_seconds: float = 0,
                     max_retries: int = 3) -> ScheduledJob:
        if delay_seconds > 0:
            scheduled_time = time.time() + delay_seconds
        job = ScheduledJob(
            workflow_id=workflow_id, name=name, priority=priority,
            scheduled_time=scheduled_time, max_retries=max_retries,
        )
        self._jobs[job.job_id] = job
        return job

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = JobStatus.CANCELLED
        return True

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.status == JobStatus.PENDING:
            job.status = JobStatus.PAUSED
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        if job.status == JobStatus.PAUSED:
            job.status = JobStatus.PENDING
            return True
        return False

    def get_due_jobs(self) -> List[ScheduledJob]:
        now = time.time()
        return [
            j for j in self._jobs.values()
            if j.status == JobStatus.PENDING and now >= j.scheduled_time
        ]

    def get_job(self, job_id: str) -> Optional[ScheduledJob]:
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[ScheduledJob]:
        return list(self._jobs.values())

    def get_jobs_by_status(self, status: JobStatus) -> List[ScheduledJob]:
        return [j for j in self._jobs.values() if j.status == status]

    def get_jobs_by_workflow(self, workflow_id: str) -> List[ScheduledJob]:
        return [j for j in self._jobs.values() if j.workflow_id == workflow_id]

    def mark_running(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = JobStatus.RUNNING
        job.started_time = time.time()
        return True

    def mark_completed(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = JobStatus.COMPLETED
        job.completed_time = time.time()
        return True

    def mark_failed(self, job_id: str, error: str = "") -> bool:
        job = self._jobs.get(job_id)
        if not job:
            return False
        job.status = JobStatus.FAILED
        job.completed_time = time.time()
        job.error = error
        return True

    def get_stats(self) -> Dict[str, Any]:
        jobs = self._jobs.values()
        return {
            "total": len(jobs),
            "pending": sum(1 for j in jobs if j.status == JobStatus.PENDING),
            "running": sum(1 for j in jobs if j.status == JobStatus.RUNNING),
            "completed": sum(1 for j in jobs if j.status == JobStatus.COMPLETED),
            "failed": sum(1 for j in jobs if j.status == JobStatus.FAILED),
            "cancelled": sum(1 for j in jobs if j.status == JobStatus.CANCELLED),
            "paused": sum(1 for j in jobs if j.status == JobStatus.PAUSED),
            "due_now": len(self.get_due_jobs()),
        }
