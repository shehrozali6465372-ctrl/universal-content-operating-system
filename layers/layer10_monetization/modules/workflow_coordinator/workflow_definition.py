"""Workflow Definition — Model for a complete workflow."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_WD_COUNTER = itertools.count(1)


class WorkflowDefinition:
    """Define a workflow with stages, dependencies, and configuration."""

    __slots__ = ("workflow_id", "name", "stages", "dependencies", "priority",
                 "timeout_seconds", "max_retries", "metadata", "created_at")

    def __init__(self, name: str = "", stages: Optional[List[str]] = None) -> None:
        self.workflow_id: str = f"wfdef_{next(_WD_COUNTER)}"
        self.name = name or f"workflow_{self.workflow_id}"
        self.stages: List[str] = list(stages) if stages else []
        self.dependencies: Dict[str, List[str]] = {}
        self.priority: int = 0
        self.timeout_seconds: float = 300.0
        self.max_retries: int = 3
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()

    def add_stage(self, stage: str, depends_on: Optional[List[str]] = None) -> None:
        if stage not in self.stages:
            self.stages.append(stage)
        if depends_on:
            self.dependencies[stage] = depends_on

    def remove_stage(self, stage: str) -> bool:
        if stage in self.stages:
            self.stages.remove(stage)
            self.dependencies.pop(stage, None)
            for k in list(self.dependencies.keys()):
                self.dependencies[k] = [d for d in self.dependencies[k] if d != stage]
            return True
        return False

    def validate(self) -> bool:
        if not self.stages:
            return False
        all_stages = set(self.stages)
        for deps in self.dependencies.values():
            for d in deps:
                if d not in all_stages:
                    return False
        return True

    def get_execution_order(self) -> List[List[str]]:
        resolved: List[str] = []
        remaining = set(self.stages)
        batches: List[List[str]] = []
        while remaining:
            ready = [
                s for s in remaining
                if all(d in resolved for d in self.dependencies.get(s, []))
            ]
            if not ready:
                ready = list(remaining)
            batches.append(ready)
            resolved.extend(ready)
            remaining -= set(ready)
        return batches

    def clone(self) -> "WorkflowDefinition":
        wd = WorkflowDefinition(self.name, self.stages)
        wd.dependencies = dict(self.dependencies)
        wd.priority = self.priority
        wd.timeout_seconds = self.timeout_seconds
        wd.max_retries = self.max_retries
        wd.metadata = dict(self.metadata)
        return wd

    def to_dict(self) -> Dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "stages": self.stages,
            "stage_count": len(self.stages),
            "priority": self.priority,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
        }
