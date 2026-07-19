"""PipelineEngine — sequential/parallel data pipelines across layers."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from enum import Enum


class StageStatus(str, Enum):
    IDLE = "idle"; RUNNING = "running"; DONE = "done"; FAILED = "failed"


class PipelineMode(str, Enum):
    SEQUENTIAL = "sequential"; PARALLEL = "parallel"


class PipelineStage:
    __slots__ = ("stage_id", "name", "handler", "status", "result",
                 "error", "duration_ms", "order")

    def __init__(self, stage_id: str, name: str, handler: Callable, order: int = 0) -> None:
        self.stage_id = stage_id
        self.name = name
        self.handler = handler
        self.status = StageStatus.IDLE
        self.result: Any = None
        self.error: Optional[str] = None
        self.duration_ms: float = 0.0
        self.order = order

    def to_dict(self) -> Dict[str, Any]:
        return {"stage_id": self.stage_id, "name": self.name,
                "status": self.status.value, "duration_ms": round(self.duration_ms, 2)}


class Pipeline:
    __slots__ = ("pipeline_id", "name", "stages", "mode", "status",
                 "created_at", "finished_at", "metadata")

    def __init__(self, pipeline_id: str, name: str,
                 mode: PipelineMode = PipelineMode.SEQUENTIAL) -> None:
        self.pipeline_id = pipeline_id
        self.name = name
        self.stages: List[PipelineStage] = []
        self.mode = mode
        self.status = StageStatus.IDLE
        self.created_at = time.time()
        self.finished_at: float = 0.0
        self.metadata: Dict[str, Any] = {}

    def add_stage(self, stage: PipelineStage) -> None:
        self.stages.append(stage)
        self.stages.sort(key=lambda s: s.order)

    def to_dict(self) -> Dict[str, Any]:
        return {"pipeline_id": self.pipeline_id, "name": self.name,
                "mode": self.mode.value, "status": self.status.value,
                "stage_count": len(self.stages),
                "stages": [s.to_dict() for s in self.stages]}


class PipelineEngine:
    def __init__(self) -> None:
        self._pipelines: Dict[str, Pipeline] = {}

    def create_pipeline(self, pipeline_id: str, name: str,
                        mode: PipelineMode = PipelineMode.SEQUENTIAL) -> Pipeline:
        p = Pipeline(pipeline_id, name, mode)
        self._pipelines[pipeline_id] = p
        return p

    def add_stage(self, pipeline_id: str, stage_id: str, name: str,
                  handler: Callable, order: int = 0) -> Optional[PipelineStage]:
        p = self._pipelines.get(pipeline_id)
        if not p:
            return None
        stage = PipelineStage(stage_id, name, handler, order)
        p.add_stage(stage)
        return stage

    def execute(self, pipeline_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        p = self._pipelines.get(pipeline_id)
        if not p:
            return {"error": "pipeline_not_found"}
        data = initial_data or {}
        p.status = StageStatus.RUNNING
        for stage in p.stages:
            stage.status = StageStatus.RUNNING
            start = time.time()
            try:
                stage.result = stage.handler(data)
                if isinstance(stage.result, dict):
                    data.update(stage.result)
                stage.status = StageStatus.DONE
            except Exception as exc:
                stage.error = str(exc)
                stage.status = StageStatus.FAILED
                p.status = StageStatus.FAILED
                p.finished_at = time.time()
                return p.to_dict()
            stage.duration_ms = (time.time() - start) * 1000
        p.status = StageStatus.DONE
        p.finished_at = time.time()
        return p.to_dict()

    def get_pipeline(self, pipeline_id: str) -> Optional[Pipeline]:
        return self._pipelines.get(pipeline_id)

    def list_pipelines(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pipelines.values()]

    def count(self) -> int:
        return len(self._pipelines)
