"""
Pipeline Manager
Layer 2: Research Engine — Module 10

Manages the research pipeline lifecycle:
- Pipeline creation and configuration
- Module execution sequence
- Result aggregation
"""

from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from layers.layer02_research.modules.research_orchestrator.execution_context import ExecutionContext
from layers.layer02_research.modules.research_orchestrator.workflow_engine import WorkflowEngine
from layers.layer02_research.modules.research_orchestrator.parallel_executor import ParallelExecutor
from layers.layer02_research.modules.research_orchestrator.exceptions import PipelineError


class PipelineResult:
    """Result of a complete pipeline execution."""

    __slots__ = (
        "execution_id", "topic", "success", "status",
        "module_results", "overall_confidence",
        "total_duration_sec", "completed_modules",
        "failed_modules", "error_summary",
    )

    def __init__(self, execution_id: str, topic: str):
        self.execution_id = execution_id
        self.topic = topic
        self.success = False
        self.status = "pending"
        self.module_results: Dict[str, Any] = {}
        self.overall_confidence = 0.0
        self.total_duration_sec = 0.0
        self.completed_modules: List[str] = []
        self.failed_modules: List[str] = []
        self.error_summary: List[str] = []

    def to_dict(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "topic": self.topic,
            "success": self.success,
            "status": self.status,
            "overall_confidence": round(self.overall_confidence, 3),
            "total_duration_sec": round(self.total_duration_sec, 3),
            "completed_modules": self.completed_modules,
            "failed_modules": self.failed_modules,
            "error_summary": self.error_summary,
        }


class PipelineManager:
    """Manages research pipeline creation and execution."""

    def __init__(self, workflow_engine: Optional[WorkflowEngine] = None):
        self.workflow_engine = workflow_engine or WorkflowEngine()
        self.executor = ParallelExecutor()
        self._pipelines: Dict[str, Dict] = {}

    def create_pipeline(
        self,
        topic: str,
        workflow_name: str = "default_research",
        niche: str = "general",
    ) -> ExecutionContext:
        """Create a new pipeline execution context."""
        wf = self.workflow_engine.get_workflow(workflow_name)
        if not wf:
            raise PipelineError(f"Workflow '{workflow_name}' not found")

        errors = wf.validate()
        if errors:
            raise PipelineError(f"Workflow validation failed: {'; '.join(errors)}")

        ctx = ExecutionContext(
            execution_id=f"exec_{int(datetime.now(timezone.utc).timestamp())}_{hash(topic) % 100000}",
            topic=topic,
            niche=niche,
        )

        self._pipelines[ctx.execution_id] = {
            "context": ctx,
            "workflow": wf,
        }

        return ctx

    def execute_pipeline(
        self,
        context: ExecutionContext,
        module_funcs: Optional[Dict[str, Callable]] = None,
        custom_context: Optional[Dict] = None,
    ) -> PipelineResult:
        """Execute a pipeline from start to finish."""
        pipeline_data = self._pipelines.get(context.execution_id)
        if not pipeline_data:
            raise PipelineError(f"Pipeline not found for execution '{context.execution_id}'")

        workflow = pipeline_data["workflow"]
        funcs = module_funcs or self.workflow_engine.get_module_funcs()
        ctx = custom_context or {"topic": context.topic, "niche": context.niche}

        result = PipelineResult(context.execution_id, context.topic)
        context.start()

        start = datetime.now(timezone.utc)

        try:
            module_order = workflow.get_module_order()
            dependencies = workflow.get_dependencies()

            exec_results = self.executor.execute_all(
                module_order, funcs, dependencies, ctx
            )

            for module, er in exec_results.items():
                result.module_results[module] = er.to_dict()
                if er.success:
                    context.complete_module(module, er.result, er.confidence)
                    result.completed_modules.append(module)
                else:
                    context.fail_module(module)
                    result.failed_modules.append(module)
                    result.error_summary.append(f"{module}: {er.error}")

            end = datetime.now(timezone.utc)
            result.total_duration_sec = (end - start).total_seconds()
            context.total_duration_sec = result.total_duration_sec

            if result.failed_modules:
                result.status = "partial"
                result.success = len(result.completed_modules) > 0
            else:
                result.status = "completed"
                result.success = True

            # Calculate overall confidence
            confidences = [
                er.confidence for er in exec_results.values()
                if er.success and er.confidence > 0
            ]
            result.overall_confidence = (
                round(sum(confidences) / len(confidences), 3)
                if confidences else 0.0
            )
            context.overall_confidence = result.overall_confidence

            context.complete(result.overall_confidence)

        except Exception as exc:
            result.status = "failed"
            result.success = False
            result.error_summary.append(str(exc))
            context.fail()

        return result

    def get_pipeline(self, execution_id: str) -> Optional[Dict]:
        return self._pipelines.get(execution_id)

    def list_pipelines(self) -> List[str]:
        return list(self._pipelines.keys())

    def reset(self):
        self._pipelines.clear()
        self.executor.reset()
