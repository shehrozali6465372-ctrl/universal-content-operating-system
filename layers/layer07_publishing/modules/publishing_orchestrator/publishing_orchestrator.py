"""Publishing Orchestrator — production entry point for Layer 7."""
from __future__ import annotations

import itertools
import time
from typing import Any, Dict, Optional

from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
from layers.layer07_publishing.modules.publisher_engine.publish_request import PublishRequest
from layers.layer07_publishing.modules.publisher_engine.publisher_manager import PublisherManager
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_stage import (
    PipelineDefinition,
    PipelineStage,
)
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_context import PipelineContext
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_executor import PipelineExecutor
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_monitor import (
    ExecutionRecord,
    PipelineMonitor,
)
from layers.layer07_publishing.modules.publishing_orchestrator.parallel_executor import ParallelExecutor
from layers.layer07_publishing.modules.publishing_orchestrator.event_handler import EventHandler, PipelineEvent
from layers.layer07_publishing.modules.publishing_orchestrator.module_registry import ModuleRegistry
from layers.layer07_publishing.modules.publishing_orchestrator.health_checker import HealthChecker
from layers.layer07_publishing.modules.publishing_orchestrator.metrics_collector import MetricsCollector

_ORCH_COUNTER = itertools.count(1)


class PublishingOrchestrator:
    """Coordinate the production publishing manager and observability."""

    def __init__(self, publisher_manager: Optional[PublisherManager] = None) -> None:
        self.publisher_manager = publisher_manager or PublisherManager()
        self.pipeline_executor = PipelineExecutor()
        self.monitor = PipelineMonitor()
        self.parallel_executor = ParallelExecutor()
        self.event_handler = EventHandler()
        self.module_registry = ModuleRegistry()
        self.health_checker = HealthChecker()
        self.metrics_collector = MetricsCollector()
        self._orchestration_count = 0

    def create_default_pipeline(self) -> PipelineDefinition:
        """Build the legacy dry-run pipeline definition for isolated stage tests."""
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

    def publish(self, platform: str, content: str, **kwargs: Any) -> Dict[str, Any]:
        """Publish through the real Layer 7 PublisherManager.

        No synthetic post ID or fake provider result is generated here.
        """
        started = time.monotonic()
        request = PublishRequest(
            platform=platform,
            content=content,
            content_type=str(kwargs.pop("content_type", "post")),
        )
        metadata = kwargs.pop("metadata", {})
        if isinstance(metadata, dict):
            request.metadata.update(metadata)
        request.metadata.update(kwargs)

        media_paths = request.metadata.pop("media_paths", None)
        if media_paths:
            request.media_assets = [MediaAsset(str(path)) for path in media_paths]

        self.event_handler.publish(PipelineEvent("pipeline_started", "orchestrator"))
        result = self.publisher_manager.publish(request)

        completed = ["validate"]
        failed = []
        if result.success:
            completed.append("publish")
        else:
            failed.append("publish")

        duration_ms = (time.monotonic() - started) * 1000
        self.metrics_collector.record(result.success, duration_ms, len(completed))
        record = ExecutionRecord("production_publishing", result.success)
        record.total_duration_ms = duration_ms
        record.completed_stages = len(completed)
        record.failed_stages = len(failed)
        self.monitor.record_execution(record)

        event_type = "pipeline_completed" if result.success else "pipeline_failed"
        self.event_handler.publish(PipelineEvent(event_type, "orchestrator"))
        self._orchestration_count += 1

        return {
            "success": result.success,
            "platform": platform,
            "post_id": result.post_id,
            "url": result.url,
            "error": result.error_message,
            "error_category": getattr(result, "error_category", ""),
            "completed_stages": completed,
            "failed_stages": failed,
            "duration_ms": round(duration_ms, 2),
        }

    def get_health(self) -> Dict[str, Any]:
        return {
            "monitor": self.monitor.get_health(),
            "metrics": self.metrics_collector.get_metrics().to_dict(),
            "modules": self.module_registry.enabled_count,
            "publisher_manager": True,
            "total_executions": self._orchestration_count,
        }

    @property
    def orchestration_count(self) -> int:
        return self._orchestration_count
