"""Production-safe Layer 9 learning orchestrator.

The orchestrator coordinates the real Layer 9 modules. It deliberately has no
synthetic/default learning results: production runs require observed inputs and
actual outcomes for stages that claim to learn from performance.
"""
from __future__ import annotations

import itertools
import logging
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.learning_engine.learning_manager import (
    LearningManager,
)
from layers.layer09_learning.modules.learning_engine.learning_signal import LearningSignal
from layers.layer09_learning.modules.prompt_optimization.prompt_manager import PromptManager
from layers.layer09_learning.modules.prompt_optimization.prompt_profile import PromptProfile
from layers.layer09_learning.modules.strategy_optimization.strategy_manager import StrategyManager
from layers.layer09_learning.modules.strategy_optimization.strategy_profile import StrategyProfile
from layers.layer09_learning.modules.brand_voice_learning.brand_manager import BrandManager
from layers.layer09_learning.modules.brand_voice_learning.brand_profile import BrandProfile
from layers.layer09_learning.modules.memory_evolution.memory_manager import MemoryManager
from layers.layer09_learning.modules.self_improvement.self_improvement_manager import (
    SelfImprovementManager,
)
from layers.layer09_learning.modules.quality_calibration.calibration_manager import (
    CalibrationManager,
)
from layers.layer09_learning.modules.content_optimization.optimization_manager import (
    OptimizationManager,
)
from layers.layer09_learning.modules.content_optimization.optimization_profile import (
    OptimizationProfile,
)
from layers.layer09_learning.modules.engagement_predictor.engagement_manager import (
    EngagementManager,
)
from layers.layer09_learning.modules.engagement_predictor.prediction_profile import (
    PredictionProfile,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import (
    PipelineDefinition,
    PipelineStage,
)
from layers.layer09_learning.modules.learning_orchestrator.event_router import (
    EventRouter,
    LearningEvent,
)
from layers.layer09_learning.modules.learning_orchestrator.workflow_engine import WorkflowEngine
from layers.layer09_learning.modules.learning_orchestrator.dependency_manager import DependencyGraph
from layers.layer09_learning.modules.learning_orchestrator.optimization_scheduler import (
    OptimizationScheduler,
)
from layers.layer09_learning.modules.learning_orchestrator.health_monitor import HealthMonitor
from layers.layer09_learning.modules.learning_orchestrator.learning_report import LearningReport
from layers.layer09_learning.modules.learning_orchestrator.orchestrator_metrics import (
    OrchestratorMetrics,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_events import (
    LearningEventBus,
    LearningSystemEvent,
    EVENT_LEARNING_STARTED,
    EVENT_LEARNING_COMPLETED,
    EVENT_LEARNING_FAILED,
)
from layers.layer09_learning.modules.learning_orchestrator.exceptions import (
    AggregationError,
    ModuleExecutionError,
    PipelineError,
    ProductionLearningDataRequired,
)

_LO_COUNTER = itertools.count(1)
_LOGGER = logging.getLogger(__name__)


class LearningOrchestrator:
    """Coordinate the real Layer 9 learning modules.

    A stage may only report success when its real module executed successfully.
    Missing observed data is treated as a production contract failure rather
    than being replaced by fabricated defaults.
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

        self.learning_manager = LearningManager()
        self.prompt_manager = PromptManager()
        self.strategy_manager = StrategyManager()
        self.brand_manager = BrandManager()
        self.memory_manager = MemoryManager()
        self.self_improvement_manager = SelfImprovementManager()
        self.calibration_manager = CalibrationManager()
        self.content_manager = OptimizationManager()
        self.engagement_manager = EngagementManager()

        self._register_default_events()

    def _register_default_events(self) -> None:
        self.event_router.register("module_completed", self._on_module_completed)
        self.event_router.register("module_failed", self._on_module_failed)

    def _on_module_completed(self, event: LearningEvent) -> None:
        module = event.data.get("module")
        if module:
            self.health_monitor.record_success(module)

    def _on_module_failed(self, event: LearningEvent) -> None:
        module = event.data.get("module")
        if module:
            self.health_monitor.record_failure(module, str(event.data.get("error", "")))

    def orchestrate(
        self,
        content: str = "",
        platform: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> LearningReport:
        """Run the production learning pipeline using only supplied evidence."""
        ctx = dict(context or {})
        self._validate_production_context(ctx)

        start = time.monotonic()
        report = LearningReport()
        run = self.scheduler.start_run()

        self.event_bus.emit(
            LearningSystemEvent(
                event_type=EVENT_LEARNING_STARTED,
                source="learning_orchestrator",
                data={"content_length": len(content), "platform": platform},
            )
        )

        completed: set[PipelineStage] = set()
        failed: set[PipelineStage] = set()

        try:
            for batch in self.pipeline.get_execution_order():
                for stage in batch:
                    dependencies = self.pipeline.get_dependencies(stage)
                    if any(dep in failed for dep in dependencies):
                        self._record_failure(
                            report,
                            stage,
                            "dependency_failed",
                        )
                        failed.add(stage)
                        continue

                    try:
                        result = self._execute_stage(stage, content, platform, ctx)
                        report.modules_executed.append(stage.value)
                        self._merge_stage_result(report, stage, result)
                        completed.add(stage)
                        self.event_router.route(
                            LearningEvent(
                                event_type="module_completed",
                                source_module=stage.value,
                                data={"module": stage.value, "result": result},
                            )
                        )
                    except ProductionLearningDataRequired as exc:
                        self._record_failure(report, stage, str(exc))
                        failed.add(stage)
                    except Exception as exc:
                        _LOGGER.exception("Layer 9 stage failed: %s", stage.value)
                        self._record_failure(report, stage, f"{type(exc).__name__}: {exc}")
                        failed.add(stage)

            stage_order = [
                stage.value
                for batch in self.pipeline.get_execution_order()
                for stage in batch
            ]
            report.modules_executed.sort(key=stage_order.index)
            success = not failed
            report.compute_learning_score()
            report.compute_confidence()
            report.duration_ms = (time.monotonic() - start) * 1000

            self.scheduler.complete_run(run.run_id, success)
            self.metrics.record_run(
                success=success,
                duration_ms=report.duration_ms,
                lessons=len(report.lessons),
                improvements=len(report.improvements),
                mistakes=len(report.mistakes),
                learning_score=report.learning_score,
            )

            event_type = EVENT_LEARNING_COMPLETED if success else EVENT_LEARNING_FAILED
            self.event_bus.emit(
                LearningSystemEvent(
                    event_type=event_type,
                    source="learning_orchestrator",
                    data=report.get_summary(),
                )
            )
            self._reports.append(report)
            return report
        except Exception:
            self.scheduler.complete_run(run.run_id, False)
            raise

    @staticmethod
    def _validate_production_context(context: Dict[str, Any]) -> None:
        signals = context.get("learning_signals")
        if not isinstance(signals, list) or not signals:
            raise ProductionLearningDataRequired(
                "learning_signals must contain observed feedback records"
            )

    def _execute_stage(
        self,
        stage: PipelineStage,
        content: str,
        platform: str,
        ctx: Dict[str, Any],
    ) -> Dict[str, Any]:
        handlers = {
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
        handler = handlers.get(stage)
        if handler is None:
            raise PipelineError(f"No handler registered for {stage.value}")
        return handler(content, platform, ctx)

    @staticmethod
    def _signals(raw: List[Dict[str, Any]]) -> List[LearningSignal]:
        signals: List[LearningSignal] = []
        for item in raw:
            if not isinstance(item, dict):
                raise ProductionLearningDataRequired("each learning signal must be an object")
            signal = LearningSignal(
                source=str(item.get("source", "analytics")),
                signal_type=str(item.get("signal_type", "engagement")),
                metric_name=str(item.get("metric_name", "")),
                value=float(item["value"]),
            )
            if "previous_value" in item:
                signal.previous_value = float(item["previous_value"])
            signal.confidence = float(item.get("confidence", 0.8))
            signal.platform = str(item.get("platform", ""))
            signal.content_id = str(item.get("content_id", ""))
            signal.context = dict(item.get("context", {}))
            signal.metadata = dict(item.get("metadata", {}))
            signals.append(signal)
        return signals

    def _stage_collect_feedback(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        signals = self._signals(ctx["learning_signals"])
        previous = self._signals(ctx.get("previous_learning_signals", []))
        result = self.learning_manager.run_learning_cycle(signals, previous or None)
        return {
            "lessons_learned": [x.get("description", "") for x in result.lessons],
            "mistakes": result.mistakes,
            "improvements": result.improvements,
            "learning_score": result.learning_score,
            "confidence": result.confidence,
            "signals": len(signals),
        }

    def _stage_optimize_prompts(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        profile = ctx.get("prompt_profile")
        if not isinstance(profile, PromptProfile):
            profile = PromptProfile(
                template=str(ctx.get("prompt_template", content)),
                category=str(ctx.get("prompt_category", "content_generation")),
            )
        profile.platform = platform
        profile.content_type = str(ctx.get("content_type", ""))
        result = self.prompt_manager.run_optimization_cycle(profile)
        return {
            "suggestions": [
                f"Prompt optimization changes: {result.improvements_suggested}",
            ],
            "validation_score": result.validation_score,
            "approved": result.is_approved,
            "profile_id": profile.profile_id,
        }

    def _stage_optimize_strategy(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        strategy = ctx.get("strategy_profile")
        if not isinstance(strategy, StrategyProfile):
            strategy = StrategyProfile(
                name=str(ctx.get("strategy_name", f"{platform} strategy")),
                strategy_type=str(ctx.get("strategy_type", "engagement")),
            )
        if platform and platform not in strategy.target_platforms:
            strategy.target_platforms.append(platform)
        self.strategy_manager.register_strategy(strategy)
        result = self.strategy_manager.run_optimization_cycle(strategy)
        return {
            "suggestions": [
                rec.get("description", "strategy recommendation")
                for rec in result.recommendations
                if isinstance(rec, dict)
            ],
            "validation_score": result.validation_score,
            "approved": result.is_approved,
            "strategy_id": strategy.strategy_id,
        }

    def _stage_learn_brand_voice(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        brand = ctx.get("brand_profile")
        if not isinstance(brand, BrandProfile):
            brand = BrandProfile(
                name=str(ctx.get("brand_name", "UCOS brand")),
                industry=str(ctx.get("brand_industry", "general")),
            )
        if platform and platform not in brand.supported_platforms:
            brand.supported_platforms.append(platform)
        samples = ctx.get("brand_content_samples")
        if not isinstance(samples, list) or not samples:
            samples = [content] if content else []
        if not samples:
            raise ProductionLearningDataRequired(
                "brand_content_samples or non-empty content is required for voice learning"
            )
        result = self.brand_manager.run_learning_cycle(brand, [str(x) for x in samples])
        return {
            "lessons_learned": result.recommendations,
            "consistency_score": result.consistency_score,
            "violations": result.violations_found,
            "brand_id": brand.profile_id,
        }

    def _stage_evolve_memory(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        entries = ctx.get("memory_entries")
        if not isinstance(entries, list):
            raise ProductionLearningDataRequired("memory_entries must be supplied for memory evolution")
        result = self.memory_manager.run_evolution_cycle(entries)
        return {
            "patterns_stored": result.merge_count + result.classification_count,
            "memory_cycle_id": result.cycle_id,
            "entries_processed": result.entries_processed,
            "entries_after": result.entries_after,
        }

    def _stage_self_improve(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        result = self.self_improvement_manager.run_improvement_cycle(
            metrics=ctx.get("metrics"),
            quality_scores=ctx.get("quality_scores"),
            feedback=ctx.get("feedback"),
            issues=ctx.get("issues"),
            current_score=float(ctx.get("current_score", 0.0)),
            action_outcomes=ctx.get("action_outcomes"),
            account_id=ctx.get("account_id"),
            platform=platform or ctx.get("account_platform"),
            niche=ctx.get("niche"),
            analytics_signal=ctx.get("analytics_signal"),
        )
        return {
            "improvements_applied": result.actions_completed,
            "mistakes_found": result.mistakes_found,
            "actions_created": result.actions_created,
            "observed_outcomes": result.actions_completed,
        }

    def _stage_calibrate_quality(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        predicted = ctx.get("predicted_scores")
        actual = ctx.get("actual_scores")
        if not isinstance(predicted, dict) or not isinstance(actual, dict) or not actual:
            raise ProductionLearningDataRequired(
                "predicted_scores and non-empty actual_scores are required for calibration"
            )
        result = self.calibration_manager.run_calibration_cycle(predicted, actual)
        return {
            "calibration_adjustments": result.bias_updates,
            "validation_score": result.validation_score,
            "is_valid": result.is_valid,
            "mae": result.mae,
            "ece": result.ece,
        }

    def _stage_optimize_content(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        if not content:
            raise ProductionLearningDataRequired("content is required for content optimization")
        profile = ctx.get("optimization_profile")
        if not isinstance(profile, OptimizationProfile):
            profile = OptimizationProfile(
                goal=str(ctx.get("optimization_goal", "engagement")),
                level=str(ctx.get("optimization_level", "moderate")),
            )
        profile.platform = platform
        profile.content_type = str(ctx.get("content_type", ""))
        result = self.content_manager.optimize(
            content,
            profile=profile,
            brand_terms=list(ctx.get("brand_terms", [])),
            forbidden_terms=list(ctx.get("forbidden_terms", [])),
        )
        return {
            "optimizations": ["content"],
            "optimized_content": result.optimized,
            "improvement_pct": result.improvement_pct,
            "validation_passed": result.validation_passed,
        }

    def _stage_predict_engagement(self, content: str, platform: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
        if not content:
            raise ProductionLearningDataRequired("content is required for engagement prediction")
        profile = ctx.get("prediction_profile")
        if not isinstance(profile, PredictionProfile):
            profile = PredictionProfile(
                platform=platform,
                content_type=str(ctx.get("content_type", "")),
            )
        report = self.engagement_manager.predict(
            content,
            profile=profile,
            audience_size=int(ctx.get("audience_size", 0)),
            platform=platform,
        )
        prediction = report.prediction.to_dict()
        return {
            "predictions": prediction,
            "confidence": prediction.get("confidence", 0.0),
            "prediction_id": report.report_id,
        }

    def _record_failure(self, report: LearningReport, stage: PipelineStage, error: str) -> None:
        report.modules_failed.append(stage.value)
        report.add_mistake(stage.value, error, severity="high")
        self.event_router.route(
            LearningEvent(
                event_type="module_failed",
                source_module=stage.value,
                data={"module": stage.value, "error": error},
            )
        )

    def _merge_stage_result(
        self,
        report: LearningReport,
        stage: PipelineStage,
        result: Dict[str, Any],
    ) -> None:
        if not isinstance(result, dict):
            raise AggregationError(f"{stage.value} returned a non-object result")

        source = stage.value
        for lesson in result.get("lessons_learned", []):
            if lesson:
                report.add_lesson(source, str(lesson), impact="medium")
        for improvement in result.get("improvements", []):
            if isinstance(improvement, dict):
                description = improvement.get("description", "observed improvement")
            else:
                description = str(improvement)
            report.add_improvement(source, description, priority=1)
        for mistake in result.get("mistakes", []):
            if isinstance(mistake, dict):
                description = mistake.get("description", "observed mistake")
            else:
                description = str(mistake)
            report.add_mistake(source, description, severity="medium")

        if "improvements_applied" in result:
            count = int(result["improvements_applied"])
            if count:
                report.add_improvement(source, f"Observed {count} completed improvement actions", priority=2)

        if "patterns_stored" in result:
            report.patterns_detected.append(
                f"{source}: {int(result['patterns_stored'])} memories optimized"
            )

        if "calibration_adjustments" in result:
            report.calibration_adjustments.append(
                f"{source}: {int(result['calibration_adjustments'])} bias updates"
            )

        if "predictions" in result and isinstance(result["predictions"], dict):
            report.predictions.update(result["predictions"])

        if "optimized_content" in result:
            report.predictions["optimized_content"] = result["optimized_content"]

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
        if count < 0:
            raise ValueError("count must be non-negative")
        return list(self._reports[-count:]) if count else []

    @property
    def event_bus_instance(self) -> LearningEventBus:
        return self.event_bus

    @property
    def orchestration_count(self) -> int:
        return len(self._reports)
