"""Tests for Layer 9 Module 10 — Learning Orchestrator Engine."""
from layers.layer09_learning.modules.learning_orchestrator.exceptions import (
    LearningOrchestratorError, PipelineError, ModuleExecutionError, AggregationError,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_pipeline import (
    PipelineStage, PipelineDefinition, PIPELINE_DEPENDENCIES,
)
from layers.layer09_learning.modules.learning_orchestrator.event_router import (
    EventRouter, LearningEvent,
)
from layers.layer09_learning.modules.learning_orchestrator.workflow_engine import (
    WorkflowEngine,
)
from layers.layer09_learning.modules.learning_orchestrator.dependency_manager import (
    DependencyGraph,
)
from layers.layer09_learning.modules.learning_orchestrator.optimization_scheduler import (
    OptimizationScheduler,
)
from layers.layer09_learning.modules.learning_orchestrator.health_monitor import (
    HealthMonitor,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_report import LearningReport
from layers.layer09_learning.modules.learning_orchestrator.orchestrator_metrics import OrchestratorMetrics
from layers.layer09_learning.modules.learning_orchestrator.learning_events import (
    LearningEventBus, LearningSystemEvent, EVENT_LEARNING_STARTED, EVENT_LEARNING_COMPLETED,
)
from layers.layer09_learning.modules.learning_orchestrator.learning_orchestrator import LearningOrchestrator


# ─── Exceptions Tests ─────────────────────────────────────────────
class TestExceptions:
    def test_base_exception(self):
        with raise_ctx(LearningOrchestratorError("test")):
            raise LearningOrchestratorError("test")

    def test_pipeline_error(self):
        with raise_ctx(PipelineError("test")):
            raise PipelineError("test")

    def test_module_execution_error(self):
        with raise_ctx(ModuleExecutionError("test")):
            raise ModuleExecutionError("test")

    def test_aggregation_error(self):
        with raise_ctx(AggregationError("test")):
            raise AggregationError("test")

    def test_inheritance(self):
        assert issubclass(PipelineError, LearningOrchestratorError)
        assert issubclass(ModuleExecutionError, LearningOrchestratorError)
        assert issubclass(AggregationError, LearningOrchestratorError)


# ─── PipelineStage Tests ──────────────────────────────────────────
class TestPipelineStage:
    def test_all_stages_defined(self):
        stages = list(PipelineStage)
        assert len(stages) == 9

    def test_stage_values(self):
        assert PipelineStage.COLLECT_FEEDBACK.value == "collect_feedback"
        assert PipelineStage.OPTIMIZE_PROMPTS.value == "optimize_prompts"
        assert PipelineStage.PREDICT_ENGAGEMENT.value == "predict_engagement"

    def test_dependencies_defined(self):
        assert len(PIPELINE_DEPENDENCIES) == 9
        assert PipelineStage.COLLECT_FEEDBACK in PIPELINE_DEPENDENCIES


# ─── PipelineDefinition Tests ─────────────────────────────────────
class TestPipelineDefinition:
    def setup_method(self):
        self.pipeline = PipelineDefinition()

    def test_get_execution_order(self):
        batches = self.pipeline.get_execution_order()
        assert len(batches) > 0
        all_stages = [s for batch in batches for s in batch]
        assert len(all_stages) == 9

    def test_execution_order_first_batch(self):
        batches = self.pipeline.get_execution_order()
        first_batch = batches[0]
        assert PipelineStage.COLLECT_FEEDBACK in first_batch

    def test_dependencies_correct(self):
        deps = self.pipeline.get_dependencies(PipelineStage.OPTIMIZE_PROMPTS)
        assert PipelineStage.COLLECT_FEEDBACK in deps

    def test_validate(self):
        assert self.pipeline.validate() is True

    def test_stage_count(self):
        assert self.pipeline.get_stage_count() == 9

    def test_custom_stages(self):
        custom = PipelineDefinition([PipelineStage.COLLECT_FEEDBACK, PipelineStage.OPTIMIZE_PROMPTS])
        assert custom.get_stage_count() == 2
        batches = custom.get_execution_order()
        all_stages = [s for batch in batches for s in batch]
        assert len(all_stages) == 2


# ─── EventRouter Tests ────────────────────────────────────────────
class TestEventRouter:
    def setup_method(self):
        self.router = EventRouter()

    def test_register_handler(self):
        self.router.register("test_event", lambda e: None)
        assert self.router.handler_count == 1

    def test_route_event(self):
        received = []
        self.router.register("test_event", lambda e: received.append(e))
        event = LearningEvent(event_type="test_event")
        count = self.router.route(event)
        assert count == 1
        assert len(received) == 1

    def test_route_no_handler(self):
        event = LearningEvent(event_type="unknown")
        count = self.router.route(event)
        assert count == 0

    def test_event_log(self):
        event = LearningEvent(event_type="test_event")
        self.router.route(event)
        log = self.router.get_event_log()
        assert len(log) == 1

    def test_event_count(self):
        self.router.route(LearningEvent(event_type="a"))
        self.router.route(LearningEvent(event_type="b"))
        assert self.router.event_count == 2


# ─── WorkflowEngine Tests ─────────────────────────────────────────
class TestWorkflowEngine:
    def setup_method(self):
        self.engine = WorkflowEngine()

    def test_create_workflow(self):
        stages = [PipelineStage.COLLECT_FEEDBACK, PipelineStage.OPTIMIZE_PROMPTS]
        steps = self.engine.create_workflow("w1", stages)
        assert len(steps) == 2
        assert steps[0].status == "pending"

    def test_execute_step(self):
        self.engine.create_workflow("w1", [PipelineStage.COLLECT_FEEDBACK])
        step = self.engine.execute_step("w1", 0, lambda s: {"done": True})
        assert step.status == "completed"
        assert step.result == {"done": True}
        assert step.duration_ms >= 0

    def test_execute_step_failure(self):
        self.engine.create_workflow("w1", [PipelineStage.COLLECT_FEEDBACK])
        step = self.engine.execute_step("w1", 0, lambda s: 1 / 0)
        assert step.status == "failed"
        assert step.error is not None

    def test_execute_step_workflow_not_found(self):
        try:
            self.engine.execute_step("nonexistent", 0, lambda s: None)
            assert False, "Should have raised"
        except ValueError:
            pass

    def test_execute_step_out_of_range(self):
        self.engine.create_workflow("w1", [PipelineStage.COLLECT_FEEDBACK])
        try:
            self.engine.execute_step("w1", 5, lambda s: None)
            assert False, "Should have raised"
        except IndexError:
            pass

    def test_get_workflow_status(self):
        self.engine.create_workflow("w1", [PipelineStage.COLLECT_FEEDBACK, PipelineStage.OPTIMIZE_PROMPTS])
        self.engine.execute_step("w1", 0, lambda s: None)
        status = self.engine.get_workflow_status("w1")
        assert status["completed"] == 1
        assert status["pending"] == 1
        assert status["is_complete"] is False

    def test_get_step_results(self):
        self.engine.create_workflow("w1", [PipelineStage.COLLECT_FEEDBACK])
        self.engine.execute_step("w1", 0, lambda s: None)
        results = self.engine.get_step_results("w1")
        assert len(results) == 1
        assert results[0]["status"] == "completed"


# ─── DependencyGraph Tests ────────────────────────────────────────
class TestDependencyGraph:
    def setup_method(self):
        self.graph = DependencyGraph()

    def test_get_dependencies(self):
        deps = self.graph.get_dependencies(PipelineStage.OPTIMIZE_PROMPTS)
        assert PipelineStage.COLLECT_FEEDBACK in deps

    def test_resolve_order(self):
        order = self.graph.resolve_order()
        assert len(order) == 9
        # COLLECT_FEEDBACK should come first
        assert order[0] == PipelineStage.COLLECT_FEEDBACK

    def test_get_ready_stages(self):
        ready = self.graph.get_ready_stages([])
        assert PipelineStage.COLLECT_FEEDBACK in ready

    def test_get_ready_after_collect(self):
        ready = self.graph.get_ready_stages([PipelineStage.COLLECT_FEEDBACK])
        assert PipelineStage.OPTIMIZE_PROMPTS in ready
        assert PipelineStage.COLLECT_FEEDBACK not in ready

    def test_is_satisfied(self):
        assert self.graph.is_satisfied([], PipelineStage.COLLECT_FEEDBACK) is True
        assert self.graph.is_satisfied([], PipelineStage.OPTIMIZE_PROMPTS) is False
        assert self.graph.is_satisfied(
            [PipelineStage.COLLECT_FEEDBACK], PipelineStage.OPTIMIZE_PROMPTS
        ) is True

    def test_to_dict(self):
        d = self.graph.to_dict()
        assert "collect_feedback" in d
        assert isinstance(d["collect_feedback"], list)


# ─── OptimizationScheduler Tests ──────────────────────────────────
class TestOptimizationScheduler:
    def setup_method(self):
        self.scheduler = OptimizationScheduler()

    def test_start_run(self):
        run = self.scheduler.start_run()
        assert run.run_id.startswith("or_")
        assert run.status == "running"

    def test_complete_run_success(self):
        run = self.scheduler.start_run()
        completed = self.scheduler.complete_run(run.run_id, success=True)
        assert completed is not None
        assert completed.status == "completed"
        assert completed.duration_ms >= 0

    def test_complete_run_failure(self):
        run = self.scheduler.start_run()
        completed = self.scheduler.complete_run(run.run_id, success=False)
        assert completed.status == "failed"

    def test_complete_run_not_found(self):
        result = self.scheduler.complete_run("nonexistent")
        assert result is None

    def test_get_active_runs(self):
        self.scheduler.start_run()
        self.scheduler.start_run()
        assert len(self.scheduler.get_active_runs()) == 2

    def test_get_completed_runs(self):
        run = self.scheduler.start_run()
        self.scheduler.complete_run(run.run_id)
        completed = self.scheduler.get_completed_runs()
        assert len(completed) == 1

    def test_get_success_rate(self):
        r1 = self.scheduler.start_run()
        r2 = self.scheduler.start_run()
        self.scheduler.complete_run(r1.run_id, success=True)
        self.scheduler.complete_run(r2.run_id, success=False)
        assert self.scheduler.get_success_rate() == 0.5

    def test_get_total_runs(self):
        self.scheduler.start_run()
        self.scheduler.start_run()
        assert self.scheduler.get_total_runs() == 2

    def test_to_dict(self):
        run = self.scheduler.start_run()
        d = run.to_dict()
        assert "run_id" in d
        assert "status" in d


# ─── HealthMonitor Tests ──────────────────────────────────────────
class TestHealthMonitor:
    def setup_method(self):
        self.monitor = HealthMonitor()

    def test_register_module(self):
        health = self.monitor.register_module("test_module")
        assert health.module_name == "test_module"

    def test_record_success(self):
        self.monitor.record_success("mod1", duration_ms=100)
        h = self.monitor.get_module_health("mod1")
        assert h.is_healthy is True
        assert h.success_count == 1
        assert h.avg_duration_ms == 100

    def test_record_failure(self):
        self.monitor.register_module("mod1")
        self.monitor.record_failure("mod1", error="test error")
        h = self.monitor.get_module_health("mod1")
        assert h.status == "degraded"
        assert h.failure_count == 1
        assert h.last_error == "test error"

    def test_get_all_health(self):
        self.monitor.record_success("mod1")
        self.monitor.record_success("mod2")
        health = self.monitor.get_all_health()
        assert len(health) == 2

    def test_get_healthy_count(self):
        self.monitor.record_success("mod1")
        self.monitor.record_failure("mod2", "error")
        assert self.monitor.get_healthy_count() == 1

    def test_get_degraded_count(self):
        self.monitor.record_success("mod1")
        self.monitor.record_failure("mod2", "error")
        assert self.monitor.get_degraded_count() == 1

    def test_get_overall_status_healthy(self):
        self.monitor.record_success("mod1")
        assert self.monitor.get_overall_status() == "healthy"

    def test_get_overall_status_degraded(self):
        self.monitor.record_success("mod1")
        self.monitor.record_success("mod2")
        self.monitor.record_success("mod3")
        self.monitor.record_failure("mod4", "error")
        assert self.monitor.get_overall_status() == "degraded"

    def test_get_overall_status_critical(self):
        self.monitor.record_success("mod1")
        for i in range(5):
            self.monitor.record_failure(f"mod{i+2}", "error")
        assert self.monitor.get_overall_status() == "critical"

    def test_to_dict(self):
        self.monitor.record_success("mod1", duration_ms=50)
        h = self.monitor.get_module_health("mod1")
        d = h.to_dict()
        assert "module_name" in d
        assert "status" in d
        assert d["status"] == "healthy"


# ─── LearningReport Tests ─────────────────────────────────────────
class TestLearningReport:
    def setup_method(self):
        self.report = LearningReport()

    def test_create(self):
        assert self.report.report_id.startswith("lr_")
        assert self.report.lessons == []
        assert self.report.improvements == []

    def test_add_lesson(self):
        self.report.add_lesson("test", "learned something", "high")
        assert len(self.report.lessons) == 1
        assert self.report.lessons[0]["source"] == "test"

    def test_add_improvement(self):
        self.report.add_improvement("test", "improved something", priority=2)
        assert len(self.report.improvements) == 1

    def test_add_mistake(self):
        self.report.add_mistake("test", "made a mistake", severity="high")
        assert len(self.report.mistakes) == 1

    def test_add_optimization(self):
        self.report.add_optimization("test", "optimized something", gain=0.1)
        assert len(self.report.optimizations) == 1

    def test_compute_learning_score(self):
        self.report.add_lesson("test", "lesson 1")
        self.report.add_lesson("test", "lesson 2")
        self.report.add_improvement("test", "improvement 1")
        score = self.report.compute_learning_score()
        assert score > 0

    def test_compute_learning_score_with_mistakes(self):
        self.report.add_lesson("test", "lesson 1")
        self.report.add_mistake("test", "mistake 1")
        self.report.add_mistake("test", "mistake 2")
        score = self.report.compute_learning_score()
        assert score >= 0

    def test_compute_confidence(self):
        self.report.modules_executed = ["m1", "m2", "m3"]
        self.report.modules_failed = ["m4"]
        self.report.add_lesson("test", "lesson 1")
        conf = self.report.compute_confidence()
        assert 0 <= conf <= 1.0

    def test_get_summary(self):
        self.report.add_lesson("test", "lesson")
        summary = self.report.get_summary()
        assert "lessons_count" in summary
        assert "learning_score" in summary
        assert "modules_executed" in summary

    def test_to_dict(self):
        d = self.report.to_dict()
        assert "report_id" in d


# ─── OrchestratorMetrics Tests ────────────────────────────────────
class TestOrchestratorMetrics:
    def setup_method(self):
        self.metrics = OrchestratorMetrics()

    def test_record_run(self):
        self.metrics.record_run(success=True, duration_ms=100, lessons=3, improvements=2)
        assert self.metrics._total_runs == 1
        assert self.metrics._successful_runs == 1

    def test_record_run_failure(self):
        self.metrics.record_run(success=False, duration_ms=50)
        assert self.metrics._failed_runs == 1

    def test_success_rate(self):
        self.metrics.record_run(success=True)
        self.metrics.record_run(success=True)
        self.metrics.record_run(success=False)
        rate = self.metrics.get_success_rate()
        assert abs(rate - 0.667) < 0.01

    def test_avg_duration(self):
        self.metrics.record_run(duration_ms=100)
        self.metrics.record_run(duration_ms=200)
        assert self.metrics.get_avg_duration() == 150.0

    def test_avg_learning_score(self):
        self.metrics.record_run(learning_score=80)
        self.metrics.record_run(learning_score=90)
        assert self.metrics.get_avg_learning_score() == 85.0

    def test_summary(self):
        self.metrics.record_run(success=True, duration_ms=100, lessons=3)
        summary = self.metrics.get_summary()
        assert "total_runs" in summary
        assert "success_rate" in summary

    def test_reset(self):
        self.metrics.record_run(success=True)
        self.metrics.reset()
        assert self.metrics._total_runs == 0


# ─── LearningEventBus Tests ──────────────────────────────────────
class TestLearningEventBus:
    def setup_method(self):
        self.bus = LearningEventBus()

    def test_emit(self):
        event = LearningSystemEvent(event_type="test", source="test")
        self.bus.emit(event)
        assert self.bus.get_event_count() == 1

    def test_subscribe_and_emit(self):
        received = []
        self.bus.subscribe("test", lambda e: received.append(e))
        self.bus.emit(LearningSystemEvent(event_type="test"))
        assert len(received) == 1

    def test_get_events_filtered(self):
        self.bus.emit(LearningSystemEvent(event_type="a"))
        self.bus.emit(LearningSystemEvent(event_type="b"))
        self.bus.emit(LearningSystemEvent(event_type="a"))
        assert self.bus.get_event_count("a") == 2
        assert self.bus.get_event_count("b") == 1

    def test_clear(self):
        self.bus.emit(LearningSystemEvent(event_type="test"))
        self.bus.clear()
        assert self.bus.get_event_count() == 0

    def test_event_constants(self):
        assert EVENT_LEARNING_STARTED == "learning_started"
        assert EVENT_LEARNING_COMPLETED == "learning_completed"


# ─── LearningOrchestrator Tests ───────────────────────────────────
class TestLearningOrchestrator:
    def setup_method(self):
        self.orchestrator = LearningOrchestrator()

    def test_orchestrate_basic(self):
        report = self.orchestrator.orchestrate("Test content", platform="facebook")
        assert report.report_id.startswith("lr_")
        assert len(report.modules_executed) > 0
        assert report.duration_ms >= 0

    def test_orchestrate_with_context(self):
        context = {"brand": "test", "goal": "engagement"}
        report = self.orchestrator.orchestrate("Test", context=context)
        assert len(report.modules_executed) > 0

    def test_orchestrate_all_modules_executed(self):
        report = self.orchestrator.orchestrate("Test content")
        expected = [s.value for s in PipelineStage]
        for module in expected:
            assert module in report.modules_executed

    def test_orchestrate_learning_score(self):
        report = self.orchestrator.orchestrate("Test content")
        assert report.learning_score > 0

    def test_orchestrate_confidence(self):
        report = self.orchestrator.orchestrate("Test content")
        assert report.confidence_score > 0

    def test_orchestrate_empty_content(self):
        report = self.orchestrator.orchestrate("")
        assert len(report.modules_executed) > 0

    def test_health(self):
        self.orchestrator.orchestrate("Test")
        health = self.orchestrator.get_health()
        assert health["pipeline_stages"] == 9
        assert "health_status" in health
        assert "metrics" in health

    def test_recent_reports(self):
        for i in range(3):
            self.orchestrator.orchestrate(f"Content {i}")
        reports = self.orchestrator.get_recent_reports(2)
        assert len(reports) == 2

    def test_orchestration_count(self):
        assert self.orchestrator.orchestration_count == 0
        self.orchestrator.orchestrate("Test 1")
        self.orchestrator.orchestrate("Test 2")
        assert self.orchestrator.orchestration_count == 2

    def test_event_bus_has_events(self):
        self.orchestrator.orchestrate("Test content")
        events = self.orchestrator.event_bus_instance.get_events()
        assert len(events) > 0

    def test_metrics_recorded(self):
        self.orchestrator.orchestrate("Test content")
        metrics = self.orchestrator.metrics.get_summary()
        assert metrics["total_runs"] == 1
        assert metrics["successful_runs"] == 1

    def test_scheduler_runs(self):
        self.orchestrator.orchestrate("Test content")
        assert self.orchestrator.scheduler.get_total_runs() == 1

    def test_health_monitor_updates(self):
        self.orchestrator.orchestrate("Test content")
        health_status = self.orchestrator.health_monitor.get_overall_status()
        assert health_status in ("healthy", "degraded", "critical", "unknown")

    def test_multiple_orchestrations(self):
        for i in range(5):
            self.orchestrator.orchestrate(f"Content {i}", platform="facebook")
        assert self.orchestrator.orchestration_count == 5
        assert self.orchestrator.metrics.get_summary()["total_runs"] == 5

    def test_patterns_detected(self):
        report = self.orchestrator.orchestrate("Test content with patterns")
        assert isinstance(report.patterns_detected, list)

    def test_report_summary(self):
        report = self.orchestrator.orchestrate("Test")
        summary = report.get_summary()
        assert "lessons_count" in summary
        assert "improvements_count" in summary
        assert "learning_score" in summary

    def test_different_platforms(self):
        for platform in ("facebook", "instagram", "linkedin", "x"):
            report = self.orchestrator.orchestrate(f"Content for {platform}", platform=platform)
            assert len(report.modules_executed) > 0


# ─── Integration Tests ────────────────────────────────────────────
class TestLearningOrchestratorIntegration:
    def setup_method(self):
        self.orchestrator = LearningOrchestrator()

    def test_full_pipeline(self):
        content = "AI is transforming the future of work."
        report = self.orchestrator.orchestrate(content, platform="linkedin")

        assert len(report.modules_executed) == 9
        assert len(report.modules_failed) == 0
        assert report.learning_score > 0
        assert report.confidence_score > 0
        assert report.duration_ms > 0

    def test_cross_platform_pipeline(self):
        platforms = ["facebook", "instagram", "x", "linkedin", "tiktok"]
        reports = []
        for platform in platforms:
            report = self.orchestrator.orchestrate(f"Content for {platform}", platform=platform)
            reports.append(report)

        assert len(reports) == 5
        assert all(len(r.modules_executed) > 0 for r in reports)

    def test_pipeline_with_different_content_types(self):
        content_types = [
            "Short post",
            "Long article about AI transformation in enterprise",
            "Question: What do you think about the future of AI?",
            "#AI #Future #Technology #Innovation",
        ]
        for ct in content_types:
            report = self.orchestrator.orchestrate(ct, platform="facebook")
            assert len(report.modules_executed) > 0

    def test_health_monitoring_across_runs(self):
        for i in range(3):
            self.orchestrator.orchestrate(f"Content {i}")

        health = self.orchestrator.get_health()
        assert health["health_status"] in ("healthy", "degraded")
        assert health["metrics"]["total_runs"] == 3

    def test_event_bus_tracks_all_events(self):
        self.orchestrator.orchestrate("Test content")
        events = self.orchestrator.event_bus_instance.get_events()
        event_types = [e.event_type for e in events]
        assert "learning_started" in event_types
        assert "learning_completed" in event_types

    def test_metrics_accuracy(self):
        for i in range(5):
            self.orchestrator.orchestrate(f"Content {i}")
        metrics = self.orchestrator.metrics.get_summary()
        assert metrics["total_runs"] == 5
        assert metrics["successful_runs"] == 5
        assert metrics["success_rate"] == 1.0


# ─── Helper ───────────────────────────────────────────────────────
class raise_ctx:
    def __init__(self, exc):
        self.exc = exc
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        assert exc_type is type(self.exc)
        assert str(exc_val) == str(self.exc)
        return True
