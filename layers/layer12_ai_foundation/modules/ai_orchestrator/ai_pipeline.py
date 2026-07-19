"""AIPipeline — manage AI processing pipelines."""
from __future__ import annotations
import time
from typing import Any, Callable, Dict, List, Optional
from .models import Pipeline, PipelineStatus, Task, TaskStatus

class AIPipeline:
    def __init__(self) -> None:
        self._pipelines: Dict[str, Pipeline] = {}
    def create(self, name: str, steps: List[str] | None = None) -> Pipeline:
        pipeline = Pipeline(name=name)
        if steps:
            for s in steps:
                pipeline.tasks.append(Task(name=s))
        self._pipelines[pipeline.pipeline_id] = pipeline
        return pipeline
    def get(self, pipeline_id: str) -> Optional[Pipeline]:
        return self._pipelines.get(pipeline_id)
    def execute(self, pipeline_id: str, executor: Callable | None = None) -> Dict[str, Any]:
        pipeline = self._pipelines.get(pipeline_id)
        if not pipeline: return {"error": "Pipeline not found"}
        pipeline.status = PipelineStatus.RUNNING
        results = []
        for task in pipeline.tasks:
            task.status = TaskStatus.RUNNING
            try:
                if executor:
                    task.output_data = executor(task)
                else:
                    task.output_data = {"result": f"executed_{task.name}"}
                task.status = TaskStatus.COMPLETED
                task.completed_at = time.time()
                results.append({"task": task.name, "status": "completed"})
            except Exception as exc:
                task.status = TaskStatus.FAILED
                task.error = str(exc)
                results.append({"task": task.name, "status": "failed", "error": str(exc)})
                pipeline.status = PipelineStatus.FAILED
                break
        if pipeline.status == PipelineStatus.RUNNING:
            pipeline.status = PipelineStatus.COMPLETED
        return {"pipeline": pipeline.to_dict(), "results": results}
    def list_pipelines(self) -> List[Dict[str, Any]]:
        return [p.to_dict() for p in self._pipelines.values()]
    def delete(self, pipeline_id: str) -> bool:
        return self._pipelines.pop(pipeline_id, None) is not None
    def count(self) -> int:
        return len(self._pipelines)
