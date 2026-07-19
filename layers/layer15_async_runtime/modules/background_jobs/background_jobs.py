"""BackgroundJobs — manage background job execution."""
from __future__ import annotations
import asyncio
import time
import uuid
from typing import Any, Callable, Coroutine, Dict, List, Optional
from enum import Enum


class JobState(str, Enum):
    QUEUED = "queued"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; CANCELLED = "cancelled"


class BackgroundJob:
    __slots__ = ("job_id", "name", "handler", "args", "kwargs", "state",
                 "result", "error", "created_at", "started_at", "finished_at",
                 "retries", "max_retries", "interval_seconds", "metadata")

    def __init__(self, name: str, handler: Callable, args: tuple = (),
                 kwargs: Optional[Dict] = None, interval_seconds: float = 0.0,
                 max_retries: int = 0) -> None:
        self.job_id = str(uuid.uuid4())[:12]
        self.name = name
        self.handler = handler
        self.args = args
        self.kwargs = kwargs or {}
        self.state = JobState.QUEUED
        self.result: Any = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.retries = 0
        self.max_retries = max_retries
        self.interval_seconds = interval_seconds
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"job_id": self.job_id, "name": self.name, "state": self.state.value,
                "retries": self.retries, "created_at": self.created_at}


class BackgroundJobs:
    def __init__(self) -> None:
        self._jobs: Dict[str, BackgroundJob] = {}
        self._history: List[Dict[str, Any]] = []
        self._running = False

    def add_job(self, name: str, handler: Callable, *args: Any,
                interval_seconds: float = 0.0, max_retries: int = 0,
                **kwargs: Any) -> BackgroundJob:
        job = BackgroundJob(name, handler, args, kwargs, interval_seconds, max_retries)
        self._jobs[job.job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            del self._jobs[job_id]
            return True
        return False

    async def execute_job(self, job: BackgroundJob) -> Dict[str, Any]:
        job.state = JobState.RUNNING
        job.started_at = time.time()
        try:
            result = job.handler(*job.args, **job.kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            job.result = result
            job.state = JobState.COMPLETED
        except Exception as exc:
            job.error = str(exc)
            if job.retries < job.max_retries:
                job.retries += 1
                job.state = JobState.QUEUED
                return await self.execute_job(job)
            job.state = JobState.FAILED
        job.finished_at = time.time()
        entry = job.to_dict()
        self._history.append(entry)
        return entry

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.state in (JobState.QUEUED, JobState.RUNNING):
            job.state = JobState.CANCELLED
            return True
        return False

    async def run_all(self) -> List[Dict[str, Any]]:
        queued = [j for j in self._jobs.values() if j.state == JobState.QUEUED]
        return [await self.execute_job(j) for j in queued]

    def get_job(self, job_id: str) -> Optional[BackgroundJob]:
        return self._jobs.get(job_id)

    def list_jobs(self) -> List[Dict[str, Any]]:
        return [j.to_dict() for j in self._jobs.values()]

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def stats(self) -> Dict[str, Any]:
        states = {}
        for j in self._jobs.values():
            states[j.state.value] = states.get(j.state.value, 0) + 1
        return {"total": len(self._jobs), "states": states}
