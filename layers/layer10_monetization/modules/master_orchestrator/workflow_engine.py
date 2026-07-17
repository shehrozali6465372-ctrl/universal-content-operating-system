"""Workflow Engine — Execute multi-layer workflows."""
from __future__ import annotations
import itertools
import time
from typing import Any, Callable, Dict, List, Optional

_WE_COUNTER = itertools.count(1)


class WorkflowStep:
    """A single step in a workflow."""

    __slots__ = ("step_id", "layer", "status", "result", "error", "duration_ms", "order")

    def __init__(self, layer: str = "", order: int = 0) -> None:
        self.step_id: str = f"ws_{next(_WE_COUNTER)}"
        self.layer = layer
        self.order = order
        self.status: str = "pending"
        self.result: Any = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0


class Workflow:
    """A workflow consisting of ordered steps."""

    __slots__ = ("workflow_id", "steps", "status", "current_step")

    def __init__(self, workflow_id: str = "") -> None:
        self.workflow_id = workflow_id or f"wf_{next(_WE_COUNTER)}"
        self.steps: List[WorkflowStep] = []
        self.status: str = "created"
        self.current_step: int = 0

    def add_step(self, layer: str) -> WorkflowStep:
        step = WorkflowStep(layer, len(self.steps))
        self.steps.append(step)
        return step

    def get_step(self, index: int) -> Optional[WorkflowStep]:
        if 0 <= index < len(self.steps):
            return self.steps[index]
        return None

    @property
    def is_complete(self) -> bool:
        return all(s.status in ("completed", "skipped", "cancelled") for s in self.steps)

    @property
    def has_failures(self) -> bool:
        return any(s.status == "failed" for s in self.steps)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "total_steps": len(self.steps),
            "status": self.status,
            "completed": sum(1 for s in self.steps if s.status == "completed"),
            "failed": sum(1 for s in self.steps if s.status == "failed"),
        }


class WorkflowEngine:
    """Execute workflows with step tracking and error handling."""

    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}

    def create_workflow(self, layers: List[str]) -> Workflow:
        wf = Workflow()
        for layer in layers:
            wf.add_step(layer)
        self._workflows[wf.workflow_id] = wf
        return wf

    def execute_step(self, workflow_id: str, step_index: int,
                     executor: Callable) -> WorkflowStep:
        wf = self._workflows.get(workflow_id)
        if not wf:
            raise ValueError(f"Workflow {workflow_id} not found")
        step = wf.get_step(step_index)
        if not step:
            raise IndexError(f"Step {step_index} out of range")

        step.status = "running"
        start = time.time()
        try:
            step.result = executor(step.layer)
            step.status = "completed"
        except Exception as e:
            step.status = "failed"
            step.error = str(e)
        step.duration_ms = (time.time() - start) * 1000
        return step

    def skip_step(self, workflow_id: str, step_index: int) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        step = wf.get_step(step_index)
        if step and step.status == "pending":
            step.status = "skipped"
            return True
        return False

    def rollback(self, workflow_id: str, up_to: int = -1) -> int:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return 0
        count = 0
        for i, step in enumerate(wf.steps):
            if i > up_to and up_to >= 0:
                break
            if step.status in ("completed", "running"):
                step.status = "rolled_back"
                count += 1
        return count

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def get_status(self, workflow_id: str) -> Dict[str, Any]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"error": "not found"}
        return wf.to_dict()
