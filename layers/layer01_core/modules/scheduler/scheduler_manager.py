"""
Scheduler Manager Module
Layer 1: Core System — Module 7

Task Orchestrator with:
- One-time, recurring, and cron jobs
- Priority queue
- Retry with backoff
- Task dependencies
- Decision-based conditions
- Health monitoring
"""

import time
import traceback
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timezone
from threading import Event

from layers.layer01_core.modules.scheduler.task_queue import (
    Task, TaskQueue, TaskPriority, TaskStatus,
)
from layers.layer01_core.modules.scheduler.retry_manager import RetryManager
from layers.layer01_core.modules.scheduler.cron_parser import CronParser


class SchedulerManager:
    """Task Orchestrator with decision-based scheduling."""

    def __init__(self):
        self._queue = TaskQueue()
        self._retry_manager = RetryManager()
        self._handlers: Dict[str, Callable] = {}
        self._history: List[Dict] = []
        self._cron_jobs: Dict[str, Dict] = {}
        self._running = False
        self._stop_event = Event()

    # ── Job Registration ────────────────────

    def register_handler(self, job_type: str, handler: Callable) -> None:
        self._handlers[job_type] = handler

    # ── Add Jobs ────────────────────────────

    def add_task(
        self,
        name: str,
        job_type: str,
        priority: str = "NORMAL",
        params: Optional[Dict] = None,
        dependencies: Optional[List[str]] = None,
        timeout_seconds: int = 300,
        max_retries: int = 3,
        conditions: Optional[Dict] = None,
    ) -> str:
        task = Task(
            name=name,
            job_type=job_type,
            priority=TaskPriority(priority),
            params=params or {},
            dependencies=dependencies or [],
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            conditions=conditions,
        )
        return self._queue.add(task)

    def add_cron_job(
        self,
        name: str,
        cron_expr: str,
        job_type: str,
        params: Optional[Dict] = None,
    ) -> str:
        """Add a recurring cron-based job."""
        parser = CronParser(cron_expr)
        task_id = self.add_task(name, job_type, params=params)
        self._cron_jobs[task_id] = {
            "name": name,
            "cron": parser,
            "job_type": job_type,
            "params": params or {},
            "last_run": None,
        }
        return task_id

    # ── Execution ───────────────────────────

    def run_task(self, task: Task) -> Dict[str, Any]:
        """Execute a single task. Returns result dict."""
        result = {
            "task_id": task.task_id,
            "task_name": task.name,
            "job_type": task.job_type,
            "status": "FAILED",
            "error": None,
            "duration_ms": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }

        # Check conditions
        if task.conditions and not self._check_conditions(task.conditions):
            result["status"] = "SKIPPED"
            result["error"] = "Conditions not met"
            self._queue.update_status(task.task_id, TaskStatus.WAITING)
            return result

        self._queue.update_status(task.task_id, TaskStatus.RUNNING)
        handler = self._handlers.get(task.job_type)

        if not handler:
            result["error"] = f"No handler registered for: {task.job_type}"
            self._queue.update_status(task.task_id, TaskStatus.FAILED)
            self._record_history(task, result)
            return result

        start_time = time.time()
        try:
            handler(task.params)
            result["status"] = "SUCCESS"
            self._queue.update_status(task.task_id, TaskStatus.SUCCESS)
            self._retry_manager.record_success(task.task_id)
        except Exception as e:
            result["error"] = str(e)
            result["traceback"] = traceback.format_exc()

            retry_info = self._retry_manager.record_failure(task.task_id)
            if self._retry_manager.should_retry(task.task_id, task.max_retries):
                result["status"] = "RETRY"
                result["retry"] = retry_info
                self._queue.update_status(task.task_id, TaskStatus.PENDING)
            else:
                result["status"] = "FAILED"
                self._queue.update_status(task.task_id, TaskStatus.FAILED)
        finally:
            result["duration_ms"] = round((time.time() - start_time) * 1000, 2)
            result["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._record_history(task, result)

        return result

    def _check_conditions(self, conditions: Dict) -> bool:
        """Evaluate decision-based conditions."""
        for key, value in conditions.items():
            if isinstance(value, dict):
                op = value.get("op", "gt")
                threshold = value.get("value", 0)
                actual = value.get("actual", 0)
                if op == "gt" and not (actual > threshold):
                    return False
                elif op == "lt" and not (actual < threshold):
                    return False
                elif op == "eq" and actual != threshold:
                    return False
                elif op == "gte" and not (actual >= threshold):
                    return False
        return True

    def run_next(self) -> Optional[Dict[str, Any]]:
        """Run the next ready task."""
        task = self._queue.next_task()
        if task is None:
            return None
        return self.run_task(task)

    def run_all(self) -> List[Dict[str, Any]]:
        """Run all pending tasks."""
        results = []
        while True:
            result = self.run_next()
            if result is None:
                break
            results.append(result)
            if result["status"] == "RETRY":
                time.sleep(1)
        return results

    def _record_history(self, task: Task, result: Dict) -> None:
        self._history.append({
            "task_id": task.task_id,
            "name": task.name,
            "status": result["status"],
            "duration_ms": result["duration_ms"],
            "timestamp": result["started_at"],
        })

    # ── Cron Processing ─────────────────────

    def process_cron_jobs(self) -> List[Dict]:
        """Check and run due cron jobs."""
        results = []
        now = datetime.now()
        for job_id, job in self._cron_jobs.items():
            last_run = job.get("last_run")
            if last_run:
                # Convert string back to datetime if needed
                if isinstance(last_run, str):
                    last_run = datetime.fromisoformat(last_run)

            next_run = job["cron"].get_next_run(now)

            # Check if we're within 1 minute of the next run
            time_diff = abs((now - next_run).total_seconds())
            if time_diff < 60 and (last_run is None or next_run > last_run):
                task = Task(
                    name=job["name"],
                    job_type=job["job_type"],
                    params=job["params"],
                )
                result = self.run_task(task)
                job["last_run"] = now
                results.append(result)

        return results

    # ── Query ───────────────────────────────

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._queue.get(task_id)

    def get_history(self, limit: int = 50) -> List[Dict]:
        return self._history[-limit:]

    def get_queue_stats(self) -> Dict[str, Any]:
        return {
            "total": self._queue.total_count,
            "pending": self._queue.pending_count,
            "running": len(self._queue.get_by_status(TaskStatus.RUNNING)),
            "success": len(self._queue.get_by_status(TaskStatus.SUCCESS)),
            "failed": len(self._queue.get_by_status(TaskStatus.FAILED)),
            "cron_jobs": len(self._cron_jobs),
        }

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        stats = self.get_queue_stats()
        report["checks"]["queue"] = {
            "status": "PASS",
            "message": f"{stats['total']} tasks, {stats['pending']} pending",
        }
        if stats["failed"] > 0:
            report["checks"]["failures"] = {
                "status": "WARN",
                "message": f"{stats['failed']} failed tasks",
            }
        else:
            report["checks"]["failures"] = {"status": "PASS", "message": "No failures"}

        report["checks"]["handlers"] = {
            "status": "PASS" if self._handlers else "WARN",
            "message": f"{len(self._handlers)} handlers registered",
        }
        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report
