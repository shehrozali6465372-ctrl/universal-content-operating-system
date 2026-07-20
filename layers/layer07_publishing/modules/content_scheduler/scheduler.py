"""ContentScheduler — Cron-like scheduling for content publishing.

Manages scheduled jobs, evaluates cron expressions, and triggers
content generation + publishing at specified times.

Features:
- Add/remove/pause/resume jobs
- Cron expression support with presets
- Next-run calculation
- Job history and statistics
- Integration with pipeline
"""
from __future__ import annotations
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.content_scheduler.schedule_job import ScheduleJob, JobStatus
from layers.layer07_publishing.modules.content_scheduler.cron_parser import CronExpression


class SchedulerEvent:
    """Event emitted by the scheduler."""

    __slots__ = ("event_type", "job_id", "timestamp", "data")

    def __init__(self, event_type: str, job_id: str = "",
                 data: Optional[Dict] = None) -> None:
        self.event_type = event_type
        self.job_id = job_id
        self.timestamp: float = time.time()
        self.data: Dict[str, Any] = data or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event_type,
            "job_id": self.job_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


class ContentScheduler:
    """Cron-like scheduler for content publishing.

    Usage:
        scheduler = ContentScheduler()
        scheduler.add_job(
            topic="AI Trends",
            platforms=["facebook", "twitter"],
            cron="daily",
        )
        due = scheduler.get_due_jobs()
        for job in due:
            scheduler.execute_job(job)
    """

    def __init__(self) -> None:
        self._jobs: Dict[str, ScheduleJob] = {}
        self._events: List[SchedulerEvent] = []
        self._execution_log: List[Dict[str, Any]] = []
        self._execute_callback: Optional[Callable] = None

    def set_execute_callback(self, callback: Callable) -> None:
        """Set callback for job execution."""
        self._execute_callback = callback

    def add_job(
        self,
        topic: str,
        platforms: Optional[List[str]] = None,
        cron: str = "daily",
        timezone: str = "UTC",
        content_template: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ScheduleJob:
        """Add a new scheduled job."""
        job = ScheduleJob(topic=topic, platforms=platforms)
        job.cron_expression = cron
        job.timezone = timezone
        job.content_template = content_template
        job.metadata = metadata or {}

        # Calculate next run
        try:
            expr = CronExpression(cron)
            next_run = expr.next_run_time()
            if next_run:
                job.next_run = next_run.timestamp()
        except Exception:
            pass

        self._jobs[job.job_id] = job
        self._emit("job_added", job.job_id, {"topic": topic, "cron": cron})
        return job

    def remove_job(self, job_id: str) -> bool:
        if job_id in self._jobs:
            self._emit("job_removed", job_id)
            del self._jobs[job_id]
            return True
        return False

    def pause_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.pause()
            self._emit("job_paused", job_id)
            return True
        return False

    def resume_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.resume()
            # Recalculate next run
            try:
                expr = CronExpression(job.cron_expression)
                next_run = expr.next_run_time()
                if next_run:
                    job.next_run = next_run.timestamp()
            except Exception:
                pass
            self._emit("job_resumed", job_id)
            return True
        return False

    def cancel_job(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job:
            job.cancel()
            self._emit("job_cancelled", job_id)
            return True
        return False

    def get_due_jobs(self) -> List[ScheduleJob]:
        """Get all jobs that are due for execution."""
        return [j for j in self._jobs.values() if j.is_due]

    def get_job(self, job_id: str) -> Optional[ScheduleJob]:
        return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[ScheduleJob]:
        return list(self._jobs.values())

    def get_jobs_by_status(self, status: JobStatus) -> List[ScheduleJob]:
        return [j for j in self._jobs.values() if j.status == status]

    def get_jobs_by_platform(self, platform: str) -> List[ScheduleJob]:
        return [j for j in self._jobs.values() if platform in j.platforms]

    def execute_job(self, job: ScheduleJob) -> Dict[str, Any]:
        """Execute a scheduled job."""
        job.mark_running()
        self._emit("job_started", job.job_id)

        start = time.time()
        result = {"job_id": job.job_id, "status": "unknown"}

        try:
            if self._execute_callback:
                callback_result = self._execute_callback(job)
                result = callback_result if isinstance(callback_result, dict) else {"status": "completed"}
            else:
                result = self._default_execute(job)

            job.mark_completed()
            # Recalculate next run
            try:
                expr = CronExpression(job.cron_expression)
                next_run = expr.next_run_time()
                if next_run:
                    job.next_run = next_run.timestamp()
            except Exception:
                pass

            result["status"] = "completed"
            self._emit("job_completed", job.job_id, result)

        except Exception as exc:
            job.mark_failed()
            result["status"] = "failed"
            result["error"] = str(exc)
            self._emit("job_failed", job.job_id, {"error": str(exc)})

        duration_ms = (time.time() - start) * 1000
        self._execution_log.append({
            "job_id": job.job_id,
            "topic": job.topic,
            "platforms": job.platforms,
            "status": result.get("status", "unknown"),
            "duration_ms": round(duration_ms, 1),
            "timestamp": time.time(),
        })
        return result

    def _default_execute(self, job: ScheduleJob) -> Dict[str, Any]:
        """Default execution — generate and publish content."""
        try:
            from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
                PipelineWiring, ContentRequest,
            )
            pipe = PipelineWiring()
            platform = job.platforms[0] if job.platforms else "facebook"
            req = ContentRequest(
                topic=job.topic, platform=platform,
                tone="professional", style="educational",
            )
            response = pipe.execute(req)
            return {
                "status": "completed",
                "content_length": len(response.text),
                "quality_score": response.quality_score,
                "platform": platform,
            }
        except Exception as exc:
            return {"status": "error", "error": str(exc)}

    def get_stats(self) -> Dict[str, Any]:
        jobs = list(self._jobs.values())
        return {
            "total_jobs": len(jobs),
            "pending": len([j for j in jobs if j.status == JobStatus.PENDING]),
            "running": len([j for j in jobs if j.status == JobStatus.RUNNING]),
            "completed": len([j for j in jobs if j.status == JobStatus.COMPLETED]),
            "failed": len([j for j in jobs if j.status == JobStatus.FAILED]),
            "cancelled": len([j for j in jobs if j.status == JobStatus.CANCELLED]),
            "paused": len([j for j in jobs if j.status == JobStatus.PAUSED]),
            "total_executions": len(self._execution_log),
            "due_now": len(self.get_due_jobs()),
        }

    def get_execution_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._execution_log[-limit:]

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [e.to_dict() for e in self._events[-limit:]]

    def _emit(self, event_type: str, job_id: str = "",
              data: Optional[Dict] = None) -> None:
        self._events.append(SchedulerEvent(event_type, job_id, data))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "jobs": {jid: j.to_dict() for jid, j in self._jobs.items()},
            "stats": self.get_stats(),
        }
