"""WorkflowOptimizer — Optimize execution order, parallelism, runtime."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.automation_engine.models.automation_models import PipelineTask


class WorkflowOptimizer:
    """Analyze and optimize workflow execution."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._optimization_log: List[Dict[str, Any]] = []

    def optimize_order(self, tasks: List[PipelineTask]) -> List[PipelineTask]:
        """Sort tasks by dependency order."""
        ordered = []
        visited: set = set()
        task_map = {t.task_id: t for t in tasks}

        def _visit(task_id: str) -> None:
            if task_id in visited:
                return
            visited.add(task_id)
            task = task_map.get(task_id)
            if task:
                for dep in task.depends_on:
                    _visit(dep)
                ordered.append(task)

        for task in tasks:
            _visit(task.task_id)

        self._log("order_optimized", {"original": len(tasks), "optimized": len(ordered)})
        return ordered

    def estimate_duration(self, tasks: List[PipelineTask],
                          avg_times: Optional[Dict[str, float]] = None) -> float:
        avg = avg_times or {}
        total = 0.0
        for task in tasks:
            total += avg.get(task.action, 10.0)  # default 10s
        return total

    def suggest_parallelism(self, tasks: List[PipelineTask]) -> int:
        """Suggest number of parallel workers based on independent tasks."""
        independent = sum(1 for t in tasks if not t.depends_on)
        return max(1, min(independent, 10))

    def _log(self, action: str, data: Dict[str, Any]) -> None:
        with self._lock:
            self._optimization_log.append({
                "action": action,
                "data": data,
                "timestamp": time.time(),
            })

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_optimizations": len(self._optimization_log),
            }
