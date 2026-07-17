"""Dependency Manager — Track and resolve module dependencies."""
from __future__ import annotations
from typing import Dict, List, Optional
from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import (
    PipelineStage, PIPELINE_DEPENDENCIES,
)


class DependencyGraph:
    """Manage dependency relationships between learning modules."""

    def __init__(self) -> None:
        self._custom_deps: Dict[PipelineStage, List[PipelineStage]] = {}
        self._resolved: List[PipelineStage] = []

    def get_dependencies(self, stage: PipelineStage) -> List[PipelineStage]:
        return list(PIPELINE_DEPENDENCIES.get(stage, []))

    def add_custom_dependency(self, stage: PipelineStage, depends_on: PipelineStage) -> None:
        if stage not in self._custom_deps:
            self._custom_deps[stage] = []
        self._custom_deps[stage].append(depends_on)

    def resolve_order(self, stages: Optional[List[PipelineStage]] = None) -> List[PipelineStage]:
        stages = stages or list(PipelineStage)
        resolved: List[PipelineStage] = []
        remaining = set(stages)
        while remaining:
            ready = [
                s for s in remaining
                if all(dep in resolved for dep in self.get_dependencies(s))
            ]
            if not ready:
                ready = list(remaining)
            resolved.extend(ready)
            remaining -= set(ready)
        self._resolved = resolved
        return resolved

    def get_ready_stages(self, completed: List[PipelineStage],
                          stages: Optional[List[PipelineStage]] = None) -> List[PipelineStage]:
        stages = stages or list(PipelineStage)
        remaining = [s for s in stages if s not in completed]
        return [
            s for s in remaining
            if all(dep in completed for dep in self.get_dependencies(s))
        ]

    def is_satisfied(self, completed: List[PipelineStage],
                      stage: PipelineStage) -> bool:
        deps = self.get_dependencies(stage)
        return all(d in completed for d in deps)

    def to_dict(self) -> Dict[str, List[str]]:
        return {
            s.value: [d.value for d in self.get_dependencies(s)]
            for s in PipelineStage
        }
