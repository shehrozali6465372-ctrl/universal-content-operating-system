"""JobQueueManager — Priority-based job queue with retry support."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    ScheduledJob, QueueItem, Priority, JobStatus,
)


class JobQueueManager:
    """Manage job queues with priority ordering."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._queues: Dict[Priority, List[QueueItem]] = {
            Priority.LOW: [],
            Priority.NORMAL: [],
            Priority.HIGH: [],
            Priority.CRITICAL: [],
        }
        self._retry_queue: List[QueueItem] = []
        self._failed_queue: List[QueueItem] = []
        self._completed: List[QueueItem] = []
        self._total_enqueued: int = 0

    def enqueue(self, job: ScheduledJob, priority: Optional[Priority] = None) -> str:
        p = priority or job.priority
        item = QueueItem(job=job, priority=p)
        with self._lock:
            self._queues[p].append(item)
            self._total_enqueued += 1
        return item.item_id

    def dequeue(self) -> Optional[ScheduledJob]:
        with self._lock:
            for priority in (Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW):
                q = self._queues[priority]
                if q:
                    item = q.pop(0)
                    item.status = "dequeued"
                    return item.job
        return None

    def enqueue_retry(self, job: ScheduledJob) -> str:
        item = QueueItem(job=job, priority=Priority.NORMAL)
        with self._lock:
            self._retry_queue.append(item)
        return item.item_id

    def dequeue_retry(self) -> Optional[ScheduledJob]:
        with self._lock:
            if self._retry_queue:
                item = self._retry_queue.pop(0)
                return item.job
        return None

    def mark_failed(self, job: ScheduledJob) -> None:
        with self._lock:
            self._failed_queue.append(QueueItem(job=job))

    def mark_completed(self, job: ScheduledJob) -> None:
        with self._lock:
            self._completed.append(QueueItem(job=job))

    def get_queue_sizes(self) -> Dict[str, int]:
        with self._lock:
            return {
                "low": len(self._queues[Priority.LOW]),
                "normal": len(self._queues[Priority.NORMAL]),
                "high": len(self._queues[Priority.HIGH]),
                "critical": len(self._queues[Priority.CRITICAL]),
                "retry": len(self._retry_queue),
                "failed": len(self._failed_queue),
                "completed": len(self._completed),
                "total_enqueued": self._total_enqueued,
            }

    def clear_completed(self) -> int:
        with self._lock:
            count = len(self._completed)
            self._completed.clear()
        return count

    def get_stats(self) -> Dict[str, Any]:
        sizes = self.get_queue_sizes()
        total_active = sizes["low"] + sizes["normal"] + sizes["high"] + sizes["critical"]
        return {
            **sizes,
            "total_active": total_active,
            "total_pending": total_active + sizes["retry"],
        }
