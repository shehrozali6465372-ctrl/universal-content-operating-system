"""WorkflowManager — Define, register, and manage workflow definitions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowDefinition, WorkflowStep, WorkflowStatus, Priority,
)


class WorkflowManager:
    """Manage workflow definitions for the orchestrator."""

    def __init__(self) -> None:
        self._workflows: Dict[str, WorkflowDefinition] = {}

    def create_workflow(self, name: str, description: str = "",
                        priority: Priority = Priority.NORMAL,
                        tags: Optional[List[str]] = None) -> WorkflowDefinition:
        wf = WorkflowDefinition(name=name, description=description,
                                priority=priority, tags=tags)
        self._workflows[wf.workflow_id] = wf
        return wf

    def get_workflow(self, workflow_id: str) -> Optional[WorkflowDefinition]:
        return self._workflows.get(workflow_id)

    def update_workflow(self, workflow_id: str, **updates) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        for key, val in updates.items():
            if hasattr(wf, key):
                setattr(wf, key, val)
        wf.updated_at = time.time()
        return True

    def delete_workflow(self, workflow_id: str) -> bool:
        return self._workflows.pop(workflow_id, None) is not None

    def get_all_workflows(self) -> List[WorkflowDefinition]:
        return list(self._workflows.values())

    def activate_workflow(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        wf.status = WorkflowStatus.ACTIVE
        wf.updated_at = time.time()
        return True

    def pause_workflow(self, workflow_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        wf.status = WorkflowStatus.PAUSED
        wf.updated_at = time.time()
        return True

    def add_step(self, workflow_id: str, step: WorkflowStep) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        wf.add_step(step)
        return True

    def remove_step(self, workflow_id: str, step_id: str) -> bool:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return False
        wf.steps = [s for s in wf.steps if s.step_id != step_id]
        wf.updated_at = time.time()
        return True

    def get_workflows_by_tag(self, tag: str) -> List[WorkflowDefinition]:
        return [wf for wf in self._workflows.values() if tag in wf.tags]

    def get_stats(self) -> Dict[str, Any]:
        workflows = self._workflows.values()
        return {
            "total": len(workflows),
            "active": sum(1 for w in workflows if w.status == WorkflowStatus.ACTIVE),
            "draft": sum(1 for w in workflows if w.status == WorkflowStatus.DRAFT),
            "paused": sum(1 for w in workflows if w.status == WorkflowStatus.PAUSED),
            "total_steps": sum(len(w.steps) for w in workflows),
        }
