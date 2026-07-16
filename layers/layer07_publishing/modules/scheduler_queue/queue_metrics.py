"""Queue Metrics — Track queue performance and health."""
from __future__ import annotations
import time
from typing import Any, Dict, List

from layers.layer07_publishing.modules.scheduler_queue.publish_job import PublishJob


class QueueMetrics:
    def __init__(self) -> None:
        self._snapshots: List[Dict[str, Any]] = []

    def snapshot(self, jobs: List[PublishJob]) -> Dict[str, Any]:
        now = time.time()
        total = len(jobs)
        completed = sum(1 for j in jobs if j.status == "completed")
        failed = sum(1 for j in jobs if j.status in ("failed", "dead"))
        running = sum(1 for j in jobs if j.status == "running")
        pending = sum(1 for j in jobs if j.status in ("pending", "scheduled"))

        durations = [
            j.completed_at - j.started_at
            for j in jobs
            if j.completed_at and j.started_at
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        success_rate = completed / max(1, completed + failed)
        total_attempts = sum(j.attempts for j in jobs)
        retry_rate = total_attempts / max(1, total)

        snap = {
            "timestamp": now,
            "total": total,
            "pending": pending,
            "running": running,
            "completed": completed,
            "failed": failed,
            "success_rate": round(success_rate, 3),
            "retry_rate": round(retry_rate, 3),
            "avg_duration_ms": round(avg_duration * 1000, 2),
        }
        self._snapshots.append(snap)
        return snap

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._snapshots)

    def get_latest(self) -> Dict[str, Any]:
        return self._snapshots[-1] if self._snapshots else {}
