"""Pipeline Executor — Execute pipeline stages in order."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_stage import PipelineDefinition
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_context import PipelineContext


class PipelineResult:
    """Result of pipeline execution."""

    __slots__ = ("success", "completed_stages", "failed_stages",
                 "context", "total_duration_ms", "stage_results")

    def __init__(self) -> None:
        self.success: bool = False
        self.completed_stages: List[str] = []
        self.failed_stages: List[str] = []
        self.context: Optional[PipelineContext] = None
        self.total_duration_ms: float = 0.0
        self.stage_results: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "completed_stages": self.completed_stages,
            "failed_stages": self.failed_stages,
            "total_duration_ms": round(self.total_duration_ms, 2),
        }


class PipelineExecutor:
    """Execute pipeline stages in order with error handling."""

    def __init__(self) -> None:
        self._execution_count = 0

    def execute(
        self,
        pipeline: PipelineDefinition,
        context: PipelineContext,
    ) -> PipelineResult:
        start = time.time()
        result = PipelineResult()
        result.context = context

        for stage in pipeline.get_stages():
            success = stage.execute(context.__dict__)
            if success:
                result.completed_stages.append(stage.name)
                result.stage_results[stage.name] = stage.result
                context.set_result(stage.name, stage.result)
            else:
                result.failed_stages.append(stage.name)
                context.add_error(f"Stage {stage.name} failed: {stage.error}")
                if stage.required:
                    break

        result.success = len(result.failed_stages) == 0
        result.total_duration_ms = (time.time() - start) * 1000
        self._execution_count += 1
        return result

    @property
    def execution_count(self) -> int:
        return self._execution_count
