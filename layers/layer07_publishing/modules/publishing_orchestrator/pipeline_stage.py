"""Pipeline Stage — Define and manage pipeline stages."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional


class PipelineStage:
    """A single stage in the publishing pipeline."""

    __slots__ = ("name", "description", "order", "required",
                 "handler", "completed", "error", "duration_ms", "result")

    def __init__(
        self,
        name: str = "",
        description: str = "",
        order: int = 0,
        required: bool = True,
        handler: Optional[Callable] = None,
    ) -> None:
        self.name = name
        self.description = description
        self.order = order
        self.required = required
        self.handler = handler
        self.completed: bool = False
        self.error: str = ""
        self.duration_ms: float = 0.0
        self.result: Any = None

    def execute(self, context: Dict[str, Any]) -> bool:
        start = time.time()
        if not self.handler:
            self.completed = True
            return True
        try:
            self.result = self.handler(context)
            self.completed = True
        except Exception as e:
            self.error = str(e)[:500]
            self.completed = False
        self.duration_ms = (time.time() - start) * 1000
        return self.completed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "order": self.order,
            "required": self.required,
            "completed": self.completed,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


class PipelineDefinition:
    """Definition of the publishing pipeline."""

    def __init__(self, name: str = "publishing_pipeline") -> None:
        self.name = name
        self._stages: List[PipelineStage] = []

    def add_stage(self, stage: PipelineStage) -> None:
        self._stages.append(stage)
        self._stages.sort(key=lambda s: s.order)

    def get_stages(self) -> List[PipelineStage]:
        return list(self._stages)

    def get_stage(self, name: str) -> Optional[PipelineStage]:
        for s in self._stages:
            if s.name == name:
                return s
        return None

    def get_required_stages(self) -> List[PipelineStage]:
        return [s for s in self._stages if s.required]

    @property
    def stage_count(self) -> int:
        return len(self._stages)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "stages": [s.to_dict() for s in self._stages],
            "stage_count": self.stage_count,
        }
