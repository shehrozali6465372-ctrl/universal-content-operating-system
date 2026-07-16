"""Queue Orchestrator — Coordinate the full publishing queue pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob, JOB_PRIORITIES
from layers.layer07_publishing.modules.scheduler_queue.job_queue import JobQueue
from layers.layer07_publishing.modules.scheduler_queue.retry_manager import RetryManager
from layers.layer07_publishing.modules.scheduler_queue.dead_letter_queue import DeadLetterQueue
from layers.layer07_publishing.modules.scheduler_queue.batch_publisher import BatchPublisher
from layers.layer07_publishing.modules.scheduler_queue.queue_metrics import QueueMetrics
from layers.layer07_publishing.modules.scheduler_queue.worker_manager import WorkerManager

_COUNTER = itertools.count(1)


class QueueOrchestrator:
    """Orchestrate the full publishing queue pipeline."""

    def __init__(
        self,
        queue: Optional[JobQueue] = None,
        retry_manager: Optional[RetryManager] = None,
        dead_letter: Optional[DeadLetterQueue] = None,
        batch_publisher: Optional[BatchPublisher] = None,
        metrics: Optional[QueueMetrics] = None,
        worker_manager: Optional[WorkerManager] = None,
    ) -> None:
        self.queue = queue or JobQueue()
        self.retry = retry_manager or RetryManager()
        self.dead_letter = dead_letter or DeadLetterQueue()
        self.batch_publisher = batch_publisher or BatchPublisher()
        self.metrics = metrics or QueueMetrics()
        self.workers = worker_manager or WorkerManager()
        self._events: List[Dict[str, Any]] = []
        self._orchestration_count = 0

    def submit_job(
        self,
        content_id: str,
        platform: str,
        content: str,
        content_type: str = "post",
        priority: str = "normal",
        scheduled_time: Optional[float] = None,
        media_paths: Optional[List[str]] = None,
    ) -> PublishJob:
        """Submit a new job to the queue."""
        job = PublishJob(
            job_id=f"job_{next(_COUNTER)}",
            content_id=content_id,
            platform=platform,
            content=content,
        )
        job.content_type = content_type
        job.priority = JOB_PRIORITIES.get(priority, 5)
        job.media_paths = media_paths or []

        if scheduled_time:
            job.scheduled_time = scheduled_time
            job.status = "scheduled"
        else:
            job.scheduled_time = time.time()
            job.status = "scheduled"

        self.queue.enqueue(job)
        self._events.append({"event": "job_submitted", "job_id": job.job_id, "platform": platform})
        return job

    def process_next(self, executor: Callable[[PublishJob], bool]) -> Optional[Dict[str, Any]]:
        """Process the next available job."""
        job = self.queue.dequeue()
        if not job:
            return None

        job.started_at = time.time()
        worker = self.workers.get_idle_worker()

        try:
            success = executor(job)
        except Exception as e:
            success = False
            job.last_error = str(e)[:200]

        if success:
            job.status = "completed"
            job.completed_at = time.time()
            if worker:
                self.workers.complete_job(worker.worker_id)
            self._events.append({"event": "job_completed", "job_id": job.job_id})
        else:
            self.retry.record_failure(job, job.last_error)
            if self.retry.should_retry(job):
                job.status = "pending"
                job.scheduled_time = time.time() + self.retry.get_next_delay(job)
                self.queue.enqueue(job)
                self._events.append({"event": "job_retrying", "job_id": job.job_id, "attempt": job.attempts})
            else:
                self.dead_letter.add(job, job.last_error)
                self._events.append({"event": "job_dead", "job_id": job.job_id})

        return {"job_id": job.job_id, "status": job.status}

    def process_batch(
        self,
        executor: Callable[[PublishJob], bool],
        max_jobs: int = 10,
    ) -> Dict[str, Any]:
        """Process multiple jobs in a batch."""
        jobs = self.queue.dequeue_many(max_jobs)
        if not jobs:
            return {"processed": 0}

        result = self.batch_publisher.execute_batch(jobs, executor)

        # Handle failed jobs
        for entry in result.results:
            if entry["status"] == "failed":
                job = self.queue.get_job(entry["job_id"])
                if job:
                    self.retry.record_failure(job, job.last_error)
                    if not self.retry.should_retry(job):
                        self.dead_letter.add(job, job.last_error)

        return result.to_dict()

    def get_status(self) -> Dict[str, Any]:
        """Get overall queue status."""
        all_jobs = list(self.queue._jobs.values())
        return {
            "queue_size": self.queue.size,
            "pending": self.queue.count_by_status("pending"),
            "scheduled": self.queue.count_by_status("scheduled"),
            "running": self.queue.count_by_status("running"),
            "completed": self.queue.count_by_status("completed"),
            "failed": self.queue.count_by_status("failed"),
            "dead_letter_size": self.dead_letter.size,
            "workers": self.workers.get_workers(),
            "idle_workers": self.workers.idle_count(),
        }

    def take_metrics_snapshot(self) -> Dict[str, Any]:
        return self.metrics.snapshot(list(self.queue._jobs.values()))

    def cancel_job(self, job_id: str) -> bool:
        return self.queue.cancel(job_id)

    def recover_from_dead_letter(self, index: int) -> Optional[PublishJob]:
        job = self.dead_letter.recover(index)
        if job:
            self.queue.enqueue(job)
        return job

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
