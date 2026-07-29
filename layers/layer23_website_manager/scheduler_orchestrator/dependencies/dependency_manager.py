"""DependencyManager — Ensure workflow steps execute in correct order."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set

from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowStep, Dependency,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import DependencyError


class DependencyManager:
    """Manage inter-step dependencies within workflows."""

    def __init__(self) -> None:
        self._dependencies: Dict[str, Dependency] = {}

    def add_dependency(self, source_step: str, target_step: str,
                       condition: str = "completed", optional: bool = False,
                       timeout: float = 600.0) -> Dependency:
        dep = Dependency(source_step, target_step, condition, optional, timeout)
        self._dependencies[dep.dependency_id] = dep
        return dep

    def remove_dependency(self, dependency_id: str) -> bool:
        return self._dependencies.pop(dependency_id, None) is not None

    def get_dependencies_for(self, step_id: str) -> List[Dependency]:
        return [d for d in self._dependencies.values() if d.target_step == step_id]

    def get_dependents_of(self, step_id: str) -> List[Dependency]:
        return [d for d in self._dependencies.values() if d.source_step == step_id]

    def can_execute(self, step: WorkflowStep,
                    completed_steps: Set[str],
                    failed_steps: Set[str]) -> bool:
        deps = self.get_dependencies_for(step.step_id)
        for dep in deps:
            if dep.optional:
                continue
            if dep.source_step in failed_steps:
                return False
            if dep.source_step not in completed_steps:
                return False
        return True

    def get_ready_steps(self, steps: List[WorkflowStep],
                        completed: Set[str],
                        failed: Set[str]) -> List[WorkflowStep]:
        return [
            s for s in steps
            if s.step_id not in completed and s.step_id not in failed
            and self.can_execute(s, completed, failed)
        ]

    def validate_workflow(self, steps: List[WorkflowStep]) -> List[str]:
        errors: List[str] = []
        step_ids = {s.step_id for s in steps}
        for dep in self._dependencies.values():
            if dep.source_step not in step_ids:
                errors.append(f"Dependency source '{dep.source_step}' not found in workflow")
            if dep.target_step not in step_ids:
                errors.append(f"Dependency target '{dep.target_step}' not found in workflow")
        # Check for circular dependencies
        visited: Set[str] = set()
        recursion_stack: Set[str] = set()

        def has_cycle(step_id: str) -> bool:
            visited.add(step_id)
            recursion_stack.add(step_id)
            for dep in self._dependencies.values():
                if dep.source_step == step_id:
                    if dep.target_step not in visited:
                        if has_cycle(dep.target_step):
                            return True
                    elif dep.target_step in recursion_stack:
                        return True
            recursion_stack.discard(step_id)
            return False

        for s in steps:
            if s.step_id not in visited:
                if has_cycle(s.step_id):
                    errors.append(f"Circular dependency detected involving step '{s.step_id}'")
                    break
        return errors

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total": len(self._dependencies),
            "optional": sum(1 for d in self._dependencies.values() if d.optional),
        }
