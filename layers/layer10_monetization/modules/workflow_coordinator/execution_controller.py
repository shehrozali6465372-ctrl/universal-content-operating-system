"""Execution Controller — Control stage execution modes."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List
from layers.layer10_monetization.modules.workflow_coordinator.workflow_stage import WorkflowStage


class ExecutionController:
    """Control execution of workflow stages (sequential, parallel, conditional)."""

    def __init__(self) -> None:
        self._max_parallel: int = 5
        self._executions: List[Dict[str, Any]] = []

    def execute_sequential(self, stages: List[WorkflowStage],
                           executor: Callable) -> List[WorkflowStage]:
        results = []
        for stage in stages:
            stage.start()
            start = time.time()
            try:
                result = executor(stage.layer)
                stage.finish(result)
            except Exception as e:
                stage.fail(str(e))
            stage.duration_ms = (time.time() - start) * 1000
            results.append(stage)
            self._executions.append({
                "stage_id": stage.stage_id,
                "layer": stage.layer,
                "status": stage.status,
                "duration_ms": stage.duration_ms,
            })
        return results

    def execute_parallel(self, stages: List[WorkflowStage],
                         executor: Callable) -> List[WorkflowStage]:
        results = []
        for stage in stages:
            stage.start()
            start = time.time()
            try:
                result = executor(stage.layer)
                stage.finish(result)
            except Exception as e:
                stage.fail(str(e))
            stage.duration_ms = (time.time() - start) * 1000
            results.append(stage)
        return results

    def execute_conditional(self, stage: WorkflowStage, condition: Callable,
                            executor: Callable) -> WorkflowStage:
        if condition(stage.layer):
            stage.start()
            start = time.time()
            try:
                result = executor(stage.layer)
                stage.finish(result)
            except Exception as e:
                stage.fail(str(e))
            stage.duration_ms = (time.time() - start) * 1000
        else:
            stage.status = "skipped"
        return stage

    def execute_with_retry(self, stage: WorkflowStage, executor: Callable,
                           max_retries: int = 3) -> WorkflowStage:
        stage.max_retries = max_retries
        for attempt in range(max_retries + 1):
            stage.start()
            start = time.time()
            try:
                result = executor(stage.layer)
                stage.finish(result)
                return stage
            except Exception as e:
                stage.fail(str(e))
                stage.duration_ms = (time.time() - start) * 1000
                if attempt < max_retries:
                    stage.retry()
        return stage

    def get_execution_stats(self) -> Dict[str, Any]:
        total = len(self._executions)
        successful = sum(1 for e in self._executions if e["status"] == "completed")
        avg_duration = 0.0
        if self._executions:
            avg_duration = sum(e["duration_ms"] for e in self._executions) / total
        return {
            "total_executions": total,
            "successful": successful,
            "failed": total - successful,
            "avg_duration_ms": round(avg_duration, 1),
        }
