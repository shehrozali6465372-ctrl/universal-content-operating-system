"""Workflow Engine — Execute learning workflows with state tracking."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import PipelineStage


class WorkflowStep:
    """A single step in a workflow."""

    __slots__ = ("step_id", "stage", "status", "result", "error", "duration_ms")

    def __init__(self, step_id: str = "", stage: PipelineStage = PipelineStage.COLLECT_FEEDBACK) -> None:
        self.step_id = step_id
        self.stage = stage
        self.status: str = "pending"
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0


class WorkflowEngine:
    """Execute workflows with state tracking and error handling."""

    def __init__(self) -> None:
        self._workflows: Dict[str, List[WorkflowStep]] = {}
        self._active_workflow: Optional[str] = None

    def create_workflow(self, workflow_id: str, stages: List[PipelineStage]) -> List[WorkflowStep]:
        steps = []
        for i, stage in enumerate(stages):
            step = WorkflowStep(f"{workflow_id}_s{i}", stage)
            steps.append(step)
        self._workflows[workflow_id] = steps
        return steps

    def execute_step(self, workflow_id: str, step_index: int,
                     executor: Callable) -> WorkflowStep:
        if workflow_id not in self._workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        steps = self._workflows[workflow_id]
        if step_index >= len(steps):
            raise IndexError(f"Step {step_index} out of range")

        step = steps[step_index]
        step.status = "running"
        start = time.time()
        try:
            step.result = executor(step.stage)
            step.status = "completed"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
        step.duration_ms = (time.time() - start) * 1000
        return step

    def get_workflow(self, workflow_id: str) -> List[WorkflowStep]:
        return list(self._workflows.get(workflow_id, []))

    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        steps = self._workflows.get(workflow_id, [])
        completed = sum(1 for s in steps if s.status == "completed")
        failed = sum(1 for s in steps if s.status == "failed")
        return {
            "workflow_id": workflow_id,
            "total_steps": len(steps),
            "completed": completed,
            "failed": failed,
            "pending": len(steps) - completed - failed,
            "is_complete": completed + failed == len(steps),
        }

    def get_step_results(self, workflow_id: str) -> List[Dict[str, Any]]:
        steps = self._workflows.get(workflow_id, [])
        return [
            {
                "step_id": s.step_id,
                "stage": s.stage.value,
                "status": s.status,
                "duration_ms": round(s.duration_ms, 1),
                "error": s.error,
            }
            for s in steps
        ]
