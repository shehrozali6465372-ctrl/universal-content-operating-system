"""AutomationPipeline — Execute the full automation pipeline."""
from __future__ import annotations
import time
import threading
from typing import Any, Callable, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import (
    PipelineTask, AutomationResult,
)
from layers.layer23_website_manager.automation_engine.exceptions import PipelineError


class AutomationPipeline:
    """Execute pipeline tasks in order."""

    def __init__(self) -> None:
        self._tasks: Dict[str, PipelineTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._lock = threading.RLock()

    def add_task(self, name: str, module: str, action: str, order: int = 0,
                 depends_on: Optional[List[str]] = None) -> PipelineTask:
        task = PipelineTask(name, module, action, order, depends_on)
        with self._lock:
            self._tasks[task.task_id] = task
        return task

    def remove_task(self, task_id: str) -> bool:
        with self._lock:
            return self._tasks.pop(task_id, None) is not None

    def get_task(self, task_id: str) -> Optional[PipelineTask]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[PipelineTask]:
        return list(self._tasks.values())

    def register_handler(self, action: str, handler: Callable) -> None:
        with self._lock:
            self._handlers[action] = handler

    def execute(self, workflow_id: str = "",
                context: Optional[Dict[str, Any]] = None) -> AutomationResult:
        result = AutomationResult(workflow_id=workflow_id, trigger="pipeline")
        ctx = dict(context or {})

        sorted_tasks = sorted(self._tasks.values(), key=lambda t: t.order)
        completed: set = set()

        try:
            for task in sorted_tasks:
                deps_met = all(d in completed for d in task.depends_on)
                if not deps_met:
                    continue
                task.started_at = time.time()
                task.status = "running"

                handler = self._handlers.get(task.action)
                if handler:
                    try:
                        res = handler(task, ctx)
                        task.result = res if isinstance(res, dict) else {"result": res}
                        task.status = "completed"
                    except Exception as exc:
                        task.status = "failed"
                        task.error = str(exc)
                        result.tasks_failed += 1
                else:
                    task.status = "completed"
                    task.result = {"status": "simulated"}

                task.completed_at = time.time()
                completed.add(task.task_id)
                if task.status == "completed":
                    result.tasks_completed += 1

            result.complete(
                "completed" if result.tasks_failed == 0 else "completed_with_errors"
            )
        except Exception as exc:
            result.complete("failed")
            result.error = str(exc)

        return result

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            tasks = self._tasks.values()
            return {
                "total_tasks": len(tasks),
                "handlers": len(self._handlers),
            }
