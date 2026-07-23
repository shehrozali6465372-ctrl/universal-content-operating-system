"""RedisQueue — Task queue with priority, retry, and dead letter support.

Features:
- FIFO queue for task processing
- Priority support (high, normal, low)
- Task status tracking (pending, processing, completed, failed)
- Dead letter queue for permanently failed tasks
- Retry mechanism with max attempts
- Queue statistics
"""
from __future__ import annotations
import json
import time
import uuid
import threading
from typing import Any, Callable, Dict, List, Optional


class RedisQueue:
    """Task queue backed by Redis lists."""

    def __init__(self, client: Any, name: str = "default"):
        self._client = client
        self._name = name
        self._prefix = f"queue:{name}"
        self._lock = threading.Lock()

        # Stats
        self._enqueued = 0
        self._dequeued = 0
        self._completed = 0
        self._failed = 0
        self._retried = 0

    def _queue_key(self, priority: str = "normal") -> str:
        return f"{self._prefix}:{priority}"

    def _task_key(self, task_id: str) -> str:
        return f"{self._prefix}:task:{task_id}"

    def _dlq_key(self) -> str:
        return f"{self._prefix}:dead_letter"

    def enqueue(self, task_type: str, payload: Dict[str, Any], priority: str = "normal",
                max_retries: int = 3, delay: float = 0.0) -> str:
        """Enqueue a task.

        Args:
            task_type: Type of task (e.g., "generate_post", "publish")
            payload: Task data
            priority: "high", "normal", or "low"
            max_retries: Maximum retry attempts
            delay: Delay in seconds before task becomes available

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        now = time.time()

        task = {
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload,
            "priority": priority,
            "status": "pending",
            "max_retries": max_retries,
            "retries": 0,
            "created_at": now,
            "enqueued_at": now + delay,
            "processing_started": None,
            "completed_at": None,
            "error": None,
        }

        # Store task data
        self._client.set(self._task_key(task_id), json.dumps(task, default=str), ttl=86400)

        # Add to queue
        queue_key = self._queue_key(priority)
        self._client.rpush(queue_key, task_id)

        self._enqueued += 1
        return task_id

    def dequeue(self) -> Optional[Dict[str, Any]]:
        """Dequeue the next task (FIFO, high priority first).

        Returns:
            Task dict or None if queue is empty
        """
        now = time.time()

        # Try high priority first, then normal, then low
        for priority in ("high", "normal", "low"):
            queue_key = self._queue_key(priority)

            while True:
                task_id_raw = self._client.lpop(queue_key)
                if not task_id_raw:
                    break

                task_id = task_id_raw if isinstance(task_id_raw, str) else str(task_id_raw)
                task_data_raw = self._client.get(self._task_key(task_id))

                if not task_data_raw:
                    continue

                try:
                    task = json.loads(task_data_raw)
                except (json.JSONDecodeError, TypeError):
                    continue

                # Check if task is delayed
                if task.get("enqueued_at", 0) > now:
                    # Put it back
                    self._client.rpush(queue_key, task_id)
                    continue

                # Mark as processing
                task["status"] = "processing"
                task["processing_started"] = now
                self._client.set(self._task_key(task_id), json.dumps(task, default=str), ttl=86400)

                self._dequeued += 1
                return task

        return None

    def complete(self, task_id: str, result: Any = None) -> bool:
        """Mark a task as completed."""
        task_data_raw = self._client.get(self._task_key(task_id))
        if not task_data_raw:
            return False

        try:
            task = json.loads(task_data_raw)
        except (json.JSONDecodeError, TypeError):
            return False

        task["status"] = "completed"
        task["completed_at"] = time.time()
        task["result"] = result
        self._client.set(self._task_key(task_id), json.dumps(task, default=str), ttl=3600)

        self._completed += 1
        return True

    def fail(self, task_id: str, error: str, requeue: bool = True) -> bool:
        """Mark a task as failed. Requeue if retries remaining."""
        task_data_raw = self._client.get(self._task_key(task_id))
        if not task_data_raw:
            return False

        try:
            task = json.loads(task_data_raw)
        except (json.JSONDecodeError, TypeError):
            return False

        task["retries"] = task.get("retries", 0) + 1
        task["error"] = error

        if requeue and task["retries"] < task.get("max_retries", 3):
            # Requeue with delay
            task["status"] = "pending"
            task["enqueued_at"] = time.time() + (task["retries"] * 5)  # Exponential-ish backoff
            task["processing_started"] = None
            self._client.set(self._task_key(task_id), json.dumps(task, default=str), ttl=86400)

            # Re-add to queue
            queue_key = self._queue_key(task.get("priority", "normal"))
            self._client.rpush(queue_key, task_id)

            self._retried += 1
            return True
        else:
            # Move to dead letter queue
            task["status"] = "dead_letter"
            self._client.set(self._task_key(task_id), json.dumps(task, default=str), ttl=604800)  # 7 days
            self._client.rpush(self._dlq_key(), task_id)

            self._failed += 1
            return False

    def peek(self, count: int = 5) -> List[Dict[str, Any]]:
        """Peek at next tasks without dequeuing."""
        result = []
        for priority in ("high", "normal", "low"):
            queue_key = self._queue_key(priority)
            task_ids = self._client.lrange(queue_key, 0, count - 1 - len(result))
            for task_id_raw in task_ids:
                if len(result) >= count:
                    break
                task_id = task_id_raw if isinstance(task_id_raw, str) else str(task_id_raw)
                task_data_raw = self._client.get(self._task_key(task_id))
                if task_data_raw:
                    try:
                        result.append(json.loads(task_data_raw))
                    except (json.JSONDecodeError, TypeError):
                        pass
            if len(result) >= count:
                break
        return result

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        task_data_raw = self._client.get(self._task_key(task_id))
        if not task_data_raw:
            return None
        try:
            return json.loads(task_data_raw)
        except (json.JSONDecodeError, TypeError):
            return None

    def size(self) -> Dict[str, int]:
        """Get queue sizes by priority."""
        return {
            "high": self._client.llen(self._queue_key("high")),
            "normal": self._client.llen(self._queue_key("normal")),
            "low": self._client.llen(self._queue_key("low")),
            "dead_letter": self._client.llen(self._dlq_key()),
            "total": (self._client.llen(self._queue_key("high")) +
                      self._client.llen(self._queue_key("normal")) +
                      self._client.llen(self._queue_key("low"))),
        }

    def clear(self) -> bool:
        """Clear all queues."""
        for priority in ("high", "normal", "low"):
            self._client.delete(self._queue_key(priority))
        self._client.delete(self._dlq_key())
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        sizes = self.size()
        return {
            "name": self._name,
            "sizes": sizes,
            "total_enqueued": self._enqueued,
            "total_dequeued": self._dequeued,
            "total_completed": self._completed,
            "total_failed": self._failed,
            "total_retried": self._retried,
            "success_rate_pct": round(
                self._completed / (self._completed + self._failed) * 100, 1
            ) if (self._completed + self._failed) > 0 else 0.0,
        }
