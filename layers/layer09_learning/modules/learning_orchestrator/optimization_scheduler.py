"""Optimization Scheduler — Schedule learning optimization runs."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional
from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import PipelineStage

_OS_COUNTER = itertools.count(1)


class OptimizationRun:
    """A scheduled optimization run."""

    __slots__ = ("run_id", "status", "stages_completed", "stages_failed",
                 "started_at", "completed_at", "duration_ms", "results")

    def __init__(self) -> None:
        self.run_id: str = f"or_{next(_OS_COUNTER)}"
        self.status: str = "pending"
        self.stages_completed: List[str] = []
        self.stages_failed: List[str] = []
        self.started_at: float = 0.0
        self.completed_at: float = 0.0
        self.duration_ms: float = 0.0
        self.results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "status": self.status,
            "stages_completed": self.stages_completed,
            "stages_failed": self.stages_failed,
            "duration_ms": round(self.duration_ms, 1),
        }


class OptimizationScheduler:
    """Schedule and track optimization runs."""

    def __init__(self) -> None:
        self._runs: List[OptimizationRun] = []
        self._max_concurrent: int = 1

    def start_run(self, stages: Optional[List[PipelineStage]] = None) -> OptimizationRun:
        run = OptimizationRun()
        run.status = "running"
        run.started_at = time.time()
        self._runs.append(run)
        return run

    def complete_run(self, run_id: str, success: bool = True) -> Optional[OptimizationRun]:
        for run in self._runs:
            if run.run_id == run_id:
                run.status = "completed" if success else "failed"
                run.completed_at = time.time()
                run.duration_ms = (run.completed_at - run.started_at) * 1000
                return run
        return None

    def get_active_runs(self) -> List[OptimizationRun]:
        return [r for r in self._runs if r.status == "running"]

    def get_completed_runs(self, limit: int = 10) -> List[OptimizationRun]:
        completed = [r for r in self._runs if r.status in ("completed", "failed")]
        return completed[-limit:]

    def get_total_runs(self) -> int:
        return len(self._runs)

    def get_success_rate(self) -> float:
        if not self._runs:
            return 0.0
        completed = [r for r in self._runs if r.status in ("completed", "failed")]
        if not completed:
            return 0.0
        successful = sum(1 for r in completed if r.status == "completed")
        return round(successful / len(completed), 3)
