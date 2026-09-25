"""Pipeline Stage — deterministic execution with reset-safe state."""
from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Optional


class PipelineStage:
    """A single stage in a publishing pipeline."""

    __slots__ = ("name", "description", "order", "required", "handler",
                 "completed", "error", "duration_ms", "result")

    def __init__(
        self, name: str = "", description: str = "", order: int = 0,
        required: bool = True, handler: Optional[Callable] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.order = order
        self.required = required
        self.handler = handler
        self.completed = False
        self.error = ""
        self.duration_ms = 0.0
        self.result: Any = None

    def execute(self, context: Dict[str, Any]) -> bool:
        start = time.monotonic()
        self.completed = False
        self.error = ""
        self.result = None
        if self.handler is None:
            self.error = "Pipeline stage has no handler"
            self.duration_ms = (time.monotonic() - start) * 1000
            return False
        try:
            result = self.handler(context)
            if result is False:
                self.error = "Pipeline stage handler returned False"
                self.duration_ms = (time.monotonic() - start) * 1000
                return False
            self.result = result
            self.completed = True
        except Exception as exc:
            self.error = str(exc)[:500]
        self.duration_ms = (time.monotonic() - start) * 1000
        return self.completed

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "description": self.description,
                "order": self.order, "required": self.required,
                "completed": self.completed, "error": self.error,
                "duration_ms": round(self.duration_ms, 2)}


class PipelineDefinition:
    """Definition of the publishing pipeline."""

    def __init__(self, name: str = "publishing_pipeline") -> None:
        self.name = name
        self._stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> None:
        if not stage.name.strip():
            raise ValueError("Pipeline stage name is required")
        if any(existing.name == stage.name for existing in self._stages):
            raise ValueError(f"Duplicate pipeline stage: {stage.name}")
        self._stages.append(stage)
        self._stages.sort(key=lambda item: item.order)

    def get_stages(self) -> List[PipelineStage]:
        return list(self._stages)

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        return next((stage for stage in self._stages if stage.name == name), None)

    def get_required_stages(self) -> List[PipelineStage]:
        return [stage for stage in self._stages if stage.required]

    @property
    def stage_count(self) -> int:
        return len(self._stages)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "stages": [stage.to_dict() for stage in self._stages],
                "stage_count": self.stage_count}
