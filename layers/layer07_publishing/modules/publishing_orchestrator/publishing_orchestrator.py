"""Publishing Orchestrator — Orchestrate the complete publishing pipeline."""
from __future__ import annotations
import itertools
from typing import Any, Dict, Optional

from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_stage import PipelineStage, PipelineDefinition
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_context import PipelineContext
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_executor import PipelineExecutor
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_monitor import PipelineMonitor, ExecutionRecord
from layers.layer07_publishing.modules.publishing_orchestrator.parallel_executor import ParallelExecutor
from layers.layer07_publishing.modules.publishing_orchestrator.event_handler import EventHandler, PipelineEvent
from layers.layer07_publishing.modules.publishing_orchestrator.module_registry import ModuleRegistry
from layers.layer07_publishing.modules.publishing_orchestrator.health_checker import HealthChecker
from layers.layer07_publishing.modules.publishing_orchestrator.metrics_collector import MetricsCollector

_ORCH_COUNTER = itertools.count(1)


class PublishingOrchestrator:
    """Final orchestration layer for the publishing pipeline.

    Coordinates all 9 Layer 7 modules into a complete pipeline:
    Plan → Validate → Schedule → Upload → Publish → Recover → Analytics → Memory → Policies
    """

    def __init__(self) -> None:
        self.pipeline_executor = PipelineExecutor()
        self.monitor = PipelineMonitor()
        self.parallel_executor = ParallelExecutor()
        self.event_handler = EventHandler()
        self.module_registry = ModuleRegistry()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self._orchestration_count = 0

    def create_default_pipeline(self) -> PipelineDefinition:
        """Create the default publishing pipeline."""
        pipeline = PipelineDefinition("default_publishing")

        pipeline.add_stage(PipelineStage("validate", "Validate content", 1, True,
            lambda ctx: {"valid": True}))
        pipeline.add_stage(PipelineStage("plan", "Create publish plan", 2, True,
            lambda ctx: {"planned": True}))
        pipeline.add_stage(PipelineStage("check_policies", "Check policies", 3, True,
            lambda ctx: {"passed": True}))
        pipeline.add_stage(PipelineStage("schedule", "Schedule publishing", 4, False,
            lambda ctx: {"scheduled": True}))
        pipeline.add_stage(PipelineStage("upload_media", "Upload media", 5, False,
            lambda ctx: {"uploaded": True}))
        pipeline.add_stage(PipelineStage("publish", "Publish content", 6, True,
            lambda ctx: {"post_id": f"post_{next(_ORCH_COUNTER)}"}))
        pipeline.add_stage(PipelineStage("handle_failure", "Handle failures", 7, False,
            lambda ctx: {"recovered": True}))
        pipeline.add_stage(PipelineStage("collect_analytics", "Collect analytics", 8, False,
            lambda ctx: {"analytics_collected": True}))
        pipeline.add_stage(PipelineStage("update_memory", "Update memory", 9, False,
            lambda ctx: {"memory_updated": True}))

        return pipeline

    def publish(
        self,
        platform: str,
        content: str,
        pipeline: Optional[PipelineDefinition] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute full publishing pipeline."""
        pipeline = pipeline or self.create_default_pipeline()
        context = PipelineContext(platform=platform, content=content)
        context.metadata.update(kwargs)

        # Fire start event
        self.event_handler.publish(PipelineEvent("pipeline_started", "orchestrator"))

        # Execute pipeline
        result = self.pipeline_executor.execute(pipeline, context)

        # Record metrics
        stages_completed = len(result.completed_stages)
        self.metrics_collector.record(
            result.success, result.total_duration_ms, stages_completed
        )

        # Record in monitor
        exec_record = ExecutionRecord(pipeline.name, result.success)
        exec_record.total_duration_ms = result.total_duration_ms
        exec_record.completed_stages = stages_completed
        exec_record.failed_stages = len(result.failed_stages)
        self.monitor.record_execution(exec_record)

        # Fire completion event
        event_type = "pipeline_completed" if result.success else "pipeline_failed"
        self.event_handler.publish(PipelineEvent(event_type, "orchestrator"))

        self._orchestration_count += 1

        return {
            "success": result.success,
            "platform": platform,
            "completed_stages": result.completed_stages,
            "failed_stages": result.failed_stages,
            "duration_ms": round(result.total_duration_ms, 2),
        }

    def get_health(self) -> Dict[str, Any]:
        return {
            "monitor": self.monitor.get_health(),
            "metrics": self.metrics_collector.get_metrics().to_dict(),
            "modules": self.module_registry.enabled_count,
            "total_executions": self._orchestration_count,
        }

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
