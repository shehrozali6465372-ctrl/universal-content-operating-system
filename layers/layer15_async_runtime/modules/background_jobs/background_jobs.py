"""Production-safe background job manager."""
from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from enum import Enum
from typing import Any, Callable


class JobState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BackgroundJob:
    __slots__ = ("job_id", "name", "handler", "args", "kwargs", "state",
                 "result", "error", "created_at", "started_at", "finished_at",
                 "retries", "max_retries", "interval_seconds", "metadata", "_task")

    def __init__(self, name: str, handler: Callable[..., Any], args: tuple[Any, ...] = (),
                 kwargs: dict[str, Any] | None = None, interval_seconds: float = 0.0,
                 max_retries: int = 0) -> None:
        self.job_id = str(uuid.uuid4())
        self.name = name
        self.handler = handler
        self.args = args
        self.kwargs = kwargs or {}
        self.state = JobState.QUEUED
        self.result: Any = None
        self.error: str | None = None
        self.created_at = time.time()
        self.started_at = 0.0
        self.finished_at = 0.0
        self.retries = 0
        self.max_retries = max_retries
        self.interval_seconds = interval_seconds
        self.metadata: dict[str, Any] = {}
        self._task: asyncio.Task[Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id, "name": self.name, "state": self.state.value,
            "retries": self.retries, "created_at": self.created_at,
            "error": self.error,
        }


class BackgroundJobs:
    def __init__(self) -> None:
        self._jobs: dict[str, BackgroundJob] = {}
        self._history: list[dict[str, Any]] = {}

    def add_job(self, name: str, handler: Callable[..., Any], *args: Any,
                interval_seconds: float = 0.0, max_retries: int = 0,
                **kwargs: Any) -> BackgroundJob:
        if not callable(handler):
            raise TypeError("handler must be callable")
        if interval_seconds < 0 or max_retries < 0:
            raise ValueError("invalid interval or retry count")
        job = BackgroundJob(name, handler, args, kwargs, interval_seconds, max_retries)
        self._jobs[job.job_id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None or job.state == JobState.RUNNING:
            return False
        del self._jobs[job_id]
        return True

    async def execute_job(self, job: BackgroundJob) -> dict[str, Any]:
        if job.state == JobState.CANCELLED:
            return job.to_dict()
        job.state = JobState.RUNNING
        job.started_at = time.time()
        try:
            while True:
                try:
                    result = job.handler(*job.args, **job.kwargs)
                    if inspect.isawaitable(result):
                        result = await result
                    job.result = result
                    job.state = JobState.COMPLETED
                    break
                except asyncio.CancelledError:
                    job.state = JobState.CANCELLED
                    raise
                except Exception as exc:
                    job.error = f"{type(exc).__name__}: {exc}"
                    if job.retries >= job.max_retries:
                        job.state = JobState.FAILED
                        break
                    job.retries += 1
                    await asyncio.sleep(min(2 ** (job.retries - 1), 30))
        finally:
            job.finished_at = time.time()
            self._history.append(job.to_dict())
        return job.to_dict()

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job is None:
            return False
        if job.state == JobState.QUEUED:
            job.state = JobState.CANCELLED
            return True
        if job.state == JobState.RUNNING and job._task is not None:
            return job._task.cancel()
        return False

    async def run_all(self) -> list[dict[str, Any]]:
        queued = [j for j in self._jobs.values() if j.state == JobState.QUEUED]
        tasks = []
        for job in queued:
            task = asyncio.create_task(self.execute_job(job))
            job._task = task
            tasks.append(task)
        return await asyncio.gather(*tasks)

    def get_job(self, job_id: str) -> BackgroundJob | None:
        return self._jobs.get(job_id)

    def list_jobs(self) -> list[dict[str, Any]]:
        return [j.to_dict() for j in self._jobs.values()]

    def get_history(self) -> list[dict[str, Any]]:
        return list(self._history)

    def stats(self) -> dict[str, Any]:
        states: dict[str, int] = {}
        for job in self._jobs.values():
            states[job.state.value] = states.get(job.state.value, 0) + 1
        return {"total": len(self._jobs), "states": states}
