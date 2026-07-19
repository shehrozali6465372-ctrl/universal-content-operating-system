"""WorkflowEngine — execute multi-step cross-layer workflows."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class StepStatus(str, Enum):
    PENDING = "pending"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    CREATED = "created"; RUNNING = "running"; COMPLETED = "completed"
    FAILED = "failed"; PAUSED = "paused"; CANCELLED = "cancelled"


class WorkflowStep:
    __slots__ = ("step_id", "name", "handler", "status", "result",
                 "error", "duration_ms", "retries", "max_retries", "metadata")

    def __init__(self, step_id: str, name: str, handler: Callable,
                 max_retries: int = 0) -> None:
        self.step_id = step_id
        self.name = name
        self.handler = handler
        self.status = StepStatus.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0
        self.retries = 0
        self.max_retries = max_retries
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"step_id": self.step_id, "name": self.name,
                "status": self.status.value, "duration_ms": round(self.duration_ms, 2),
                "retries": self.retries, "error": self.error}


class Workflow:
    __slots__ = ("workflow_id", "name", "steps", "status", "context",
                 "created_at", "started_at", "finished_at", "metadata")

    def __init__(self, workflow_id: str, name: str) -> None:
        self.workflow_id = workflow_id
        self.name = name
        self.steps: List[WorkflowStep] = []
        self.status = WorkflowStatus.CREATED
        self.context: Dict[str, Any] = {}
        self.created_at = time.time()
        self.started_at: float = 0.0
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def add_step(self, step: WorkflowStep) -> None:
        self.steps.append(step)

    def to_dict(self) -> Dict[str, Any]:
        return {"workflow_id": self.workflow_id, "name": self.name,
                "status": self.status.value, "step_count": len(self.steps),
                "steps": [s.to_dict() for s in self.steps]}


class WorkflowEngine:
    def __init__(self) -> None:
        self._workflows: Dict[str, Workflow] = {}
        self._completed: List[str] = []

    def create_workflow(self, workflow_id: str, name: str) -> Workflow:
        wf = Workflow(workflow_id, name)
        self._workflows[workflow_id] = wf
        return wf

    def add_step(self, workflow_id: str, step_id: str, name: str,
                 handler: Callable, max_retries: int = 0) -> Optional[WorkflowStep]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        step = WorkflowStep(step_id, name, handler, max_retries)
        wf.add_step(step)
        return step

    def execute(self, workflow_id: str) -> Dict[str, Any]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return {"error": "workflow_not_found"}
        wf.status = WorkflowStatus.RUNNING
        wf.started_at = time.time()
        failed = False
        for step in wf.steps:
            if step.status == StepStatus.SKIPPED:
                continue
            step.status = StepStatus.RUNNING
            start = time.time()
            try:
                step.result = step.handler(wf.context)
                step.status = StepStatus.COMPLETED
            except Exception as exc:
                step.error = str(exc)
                if step.retries < step.max_retries:
                    step.retries += 1
                    step.status = StepStatus.PENDING
                    try:
                        step.result = step.handler(wf.context)
                        step.status = StepStatus.COMPLETED
                    except Exception as exc2:
                        step.error = str(exc2)
                        step.status = StepStatus.FAILED
                        failed = True
                else:
                    step.status = StepStatus.FAILED
                    failed = True
            step.duration_ms = (time.time() - start) * 1000
            if failed:
                wf.status = WorkflowStatus.FAILED
                wf.finished_at = time.time()
                return wf.to_dict()
        wf.status = WorkflowStatus.COMPLETED
        wf.finished_at = time.time()
        self._completed.append(workflow_id)
        return wf.to_dict()

    def pause(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if wf and wf.status == WorkflowStatus.RUNNING:
            wf.status = WorkflowStatus.PAUSED
            return True
        return False

    def cancel(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if wf and wf.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED, WorkflowStatus.CREATED):
            wf.status = WorkflowStatus.CANCELLED
            return True
        return False

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        return [w.to_dict() for w in self._workflows.values()]

    def count(self) -> int:
        return len(self._workflows)
