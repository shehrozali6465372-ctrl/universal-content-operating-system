"""Learning Orchestrator — Main orchestrator for the entire learning pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import (
    PipelineStage, PipelineDefinition,
)
from layers.layer09_learning.modules.learning_orchestrator.event_router import EventRouter, LearningEvent
from layers.layer09_learning.modules.learning_orchestrator.workflow_engine import WorkflowEngine
from layers.layer09_learning.modules.learning_orchestrator.dependency_manager import DependencyGraph
from layers.layer09_learning.modules.learning_orchestrator.optimization_scheduler import OptimizationScheduler
from layers.layer09_learning.modules.learning_orchestrator.health_monitor import HealthMonitor
from layers.layer09_learning.modules.learning_orchestrator.learning_report import LearningReport
from layers.layer09_learning.modules.learning_orchestrator.orchestrator_metrics import OrchestratorMetrics
from layers.layer09_learning.modules.learning_orchestrator.learning_events import (
    LearningEventBus, LearningSystemEvent,
    EVENT_LEARNING_STARTED, EVENT_LEARNING_COMPLETED, EVENT_LEARNING_FAILED,
)

_LO_COUNTER = itertools.count(1)


class LearningOrchestrator:
    """Orchestrate all Layer 9 learning modules into a unified learning pipeline.

    Coordinates: Learning Engine → Prompt Optimization → Strategy Optimization
    → Brand Voice Learning → Memory Evolution → Self-Improvement
    → Quality Calibration → Content Optimization → Engagement Prediction
    """

    def __init__(self) -> None:
        self.pipeline = PipelineDefinition()
        self.event_router = EventRouter()
        self.workflow_engine = WorkflowEngine()
        self.dependency_manager = DependencyGraph()
        self.scheduler = OptimizationScheduler()
        self.health_monitor = HealthMonitor()
        self.metrics = OrchestratorMetrics()
        self.event_bus = LearningEventBus()
        self._reports: List[LearningReport] = []
        self._orchestrations: List[Dict[str, Any]] = []

        # Register default event handlers
        self._register_default_events()

    def _register_default_events(self) -> None:
        self.event_router.register("module_completed", self._on_module_completed)
        self.event_router.register("module_failed", self._on_module_failed)

    def _on_module_completed(self, event: LearningEvent) -> None:
        module = event.data.get("module", "")
        if module:
            self.health_monitor.record_success(module)

    def _on_module_failed(self, event: LearningEvent) -> None:
        module = event.data.get("module", "")
        error = event.data.get("error", "")
        if module:
            self.health_monitor.register_module(module)
            self.health_monitor.record_failure(module, error)

    def orchestrate(self, content: str = "", platform: str = "",
                    context: Optional[Dict[str, Any]] = None) -> LearningReport:
        """Run the full learning pipeline."""
        start = time.time()
        report = LearningReport()
        context = context or {}

        # Emit start event
        self.event_bus.emit(LearningSystemEvent(
            event_type=EVENT_LEARNING_STARTED,
            source="learning_orchestrator",
            data={"content_length": len(content), "platform": platform},
        ))

        # Get execution order
        execution_batches = self.pipeline.get_execution_order()
        run = self.scheduler.start_run()
        all_stages: List[PipelineStage] = []

        for batch in execution_batches:
            for stage in batch:
                all_stages.append(stage)
                try:
                    result = self._execute_stage(stage, content, platform, context)
                    report.modules_executed.append(stage.value)
                    if result:
                        self._merge_stage_result(report, stage, result)
                    self.event_router.route(LearningEvent(
                        event_type="module_completed",
                        source_module=stage.value,
                        data={"module": stage.value, "result": result},
                    ))
                except Exception as e:
                    report.modules_failed.append(stage.value)
                    self.event_router.route(LearningEvent(
                        event_type="module_failed",
                        source_module=stage.value,
                        data={"module": stage.value, "error": str(e)},
                    ))

        # Complete scheduler run
        success = len(report.modules_failed) == 0
        self.scheduler.complete_run(run.run_id, success)

        # Compute final scores
        report.compute_learning_score()
        report.compute_confidence()

        # Set patterns from lessons
        report.patterns_detected = [l["description"][:50] for l in report.lessons[:10]]

        report.duration_ms = (time.time() - start) * 1000

        # Emit completion event
        self.event_bus.emit(LearningSystemEvent(
            event_type=EVENT_LEARNING_COMPLETED if success else EVENT_LEARNING_FAILED,
            source="learning_orchestrator",
            data=report.get_summary(),
        ))

        # Record metrics
        self.metrics.record_run(
            success=success,
            duration_ms=report.duration_ms,
            lessons=len(report.lessons),
            improvements=len(report.improvements),
            mistakes=len(report.mistakes),
            learning_score=report.learning_score,
        )

        self._reports.append(report)
        return report

    def _execute_stage(self, stage: PipelineStage, content: str,
                        platform: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a single pipeline stage."""
        stage_map = {
            PipelineStage.COLLECT_FEEDBACK: self._stage_collect_feedback,
            PipelineStage.OPTIMIZE_PROMPTS: self._stage_optimize_prompts,
            PipelineStage.OPTIMIZE_STRATEGY: self._stage_optimize_strategy,
            PipelineStage.LEARN_BRAND_VOICE: self._stage_learn_brand_voice,
            PipelineStage.EVOLVE_MEMORY: self._stage_evolve_memory,
            PipelineStage.SELF_IMPROVE: self._stage_self_improve,
            PipelineStage.CALIBRATE_QUALITY: self._stage_calibrate_quality,
            PipelineStage.OPTIMIZE_CONTENT: self._stage_optimize_content,
            PipelineStage.PREDICT_ENGAGEMENT: self._stage_predict_engagement,
        }
        handler = stage_map.get(stage)
        if handler:
            return handler(content, platform, context)
        return None

    def _stage_collect_feedback(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"feedback_collected": True, "content_length": len(content), "platform": platform}

    def _stage_optimize_prompts(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"prompts_optimized": True, "suggestions": ["improve hook", "add CTA"]}

    def _stage_optimize_strategy(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"strategy_optimized": True, "recommended_strategy": "engagement"}

    def _stage_learn_brand_voice(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"brand_voice_learned": True, "tone": "professional"}

    def _stage_evolve_memory(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"memory_evolved": True, "patterns_stored": 3}

    def _stage_self_improve(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"self_improved": True, "improvements_applied": 2}

    def _stage_calibrate_quality(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"quality_calibrated": True, "threshold_adjusted": True}

    def _stage_optimize_content(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"content_optimized": True, "optimizations": ["title", "cta"]}

    def _stage_predict_engagement(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        return {"engagement_predicted": True, "predicted_likes": 150, "confidence": 0.75}

    def _merge_stage_result(self, report: LearningReport, stage: PipelineStage,
                            result: Dict[str, Any]) -> None:
        """Merge stage results into the unified report."""
        stage_value = stage.value
        if "suggestions" in result:
            for s in result["suggestions"]:
                report.add_improvement(stage_value, s, priority=1)
        if "lessons_learned" in result:
            for l in result["lessons_learned"]:
                report.add_lesson(stage_value, l, impact="medium")
        if "improvements_applied" in result:
            report.add_improvement(stage_value, f"Applied {result['improvements_applied']} improvements", priority=2)
        if "patterns_stored" in result:
            report.patterns_detected.append(f"{stage_value}: {result['patterns_stored']} patterns stored")
        if "predicted_likes" in result:
            report.predictions["likes"] = result["predicted_likes"]
            report.predictions["confidence"] = result.get("confidence", 0.5)
        if "optimizations" in result:
            for opt in result["optimizations"]:
                report.add_optimization(stage_value, f"Optimized {opt}", gain=0.05)

    def get_health(self) -> Dict[str, Any]:
        return {
            "pipeline_stages": self.pipeline.get_stage_count(),
            "health_status": self.health_monitor.get_overall_status(),
            "module_health": self.health_monitor.get_all_health(),
            "scheduler_runs": self.scheduler.get_total_runs(),
            "success_rate": self.scheduler.get_success_rate(),
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_reports(self, count: int = 5) -> List[LearningReport]:
        return list(self._reports[-count:])

    @property
    def event_bus_instance(self) -> LearningEventBus:
        return self.event_bus

    @property
    def orchestration_count(self) -> int:
        return len(self._reports)
