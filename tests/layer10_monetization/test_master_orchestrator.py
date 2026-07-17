"""Tests for Layer 10 Module 1 — Master Orchestrator Engine."""
from layers.layer10_monetization.modules.master_orchestrator.exceptions import (
    OrchestratorError, WorkflowError, RoutingError, DependencyError,
    ExecutionError, SchedulerError, HealthError,
)
from layers.layer10_monetization.modules.master_orchestrator.orchestration_context import OrchestrationContext
from layers.layer10_monetization.modules.master_orchestrator.layer_router import LayerRouter
from layers.layer10_monetization.modules.master_orchestrator.dependency_manager import LayerDependencies
from layers.layer10_monetization.modules.master_orchestrator.execution_scheduler import ExecutionScheduler
from layers.layer10_monetization.modules.master_orchestrator.system_health_monitor import SystemHealthMonitor
from layers.layer10_monetization.modules.master_orchestrator.event_bus import SystemEventBus, SystemEvent
from layers.layer10_monetization.modules.master_orchestrator.orchestrator_metrics import OrchestratorMetrics
from layers.layer10_monetization.modules.master_orchestrator.orchestrator_report import OrchestratorReport
from layers.layer10_monetization.modules.master_orchestrator.workflow_engine import WorkflowEngine
from layers.layer10_monetization.modules.master_orchestrator.master_orchestrator import MasterOrchestrator


# ─── Exceptions Tests ─────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        with raise_ctx(OrchestratorError("test")):
            raise OrchestratorError("test")

    def test_workflow(self):
        with raise_ctx(WorkflowError("test")):
            raise WorkflowError("test")

    def test_routing(self):
        with raise_ctx(RoutingError("test")):
            raise RoutingError("test")

    def test_dependency(self):
        with raise_ctx(DependencyError("test")):
            raise DependencyError("test")

    def test_execution(self):
        with raise_ctx(ExecutionError("test")):
            raise ExecutionError("test")

    def test_scheduler(self):
        with raise_ctx(SchedulerError("test")):
            raise SchedulerError("test")

    def test_health(self):
        with raise_ctx(HealthError("test")):
            raise HealthError("test")

    def test_inheritance(self):
        assert issubclass(WorkflowError, OrchestratorError)
        assert issubclass(RoutingError, OrchestratorError)
        assert issubclass(DependencyError, OrchestratorError)
        assert issubclass(ExecutionError, OrchestratorError)
        assert issubclass(SchedulerError, OrchestratorError)
        assert issubclass(HealthError, OrchestratorError)


# ─── OrchestrationContext Tests ───────────────────────────────────
class TestOrchestrationContext:
    def test_create(self):
        ctx = OrchestrationContext(user_id="u1", session_id="s1")
        assert ctx.request_id.startswith("req_")
        assert ctx.user_id == "u1"
        assert ctx.session_id == "s1"
        assert ctx.workflow_state == "created"

    def test_create_defaults(self):
        ctx = OrchestrationContext()
        assert ctx.request_id.startswith("req_")
        assert ctx.session_id.startswith("sess_")

    def test_update_state(self):
        ctx = OrchestrationContext()
        ctx.update_state("running")
        assert ctx.workflow_state == "running"
        assert "running" in ctx.timestamps

    def test_set_layer(self):
        ctx = OrchestrationContext()
        ctx.set_layer("layer04_writing")
        assert ctx.current_layer == "layer04_writing"

    def test_complete_layer(self):
        ctx = OrchestrationContext()
        ctx.complete_layer("layer04_writing", output={"draft": "text"})
        assert ctx.layer_outputs["layer04_writing"]["draft"] == "text"

    def test_add_error(self):
        ctx = OrchestrationContext()
        ctx.add_error("layer04_writing", "generation failed")
        assert len(ctx.errors) == 1
        assert ctx.errors[0]["error"] == "generation failed"

    def test_clone(self):
        ctx = OrchestrationContext(user_id="u1")
        ctx.update_state("running")
        clone = ctx.clone()
        assert clone.request_id == ctx.request_id
        assert clone.workflow_state == ctx.workflow_state
        clone.update_state("paused")
        assert ctx.workflow_state == "running"

    def test_clear(self):
        ctx = OrchestrationContext()
        ctx.update_state("running")
        ctx.complete_layer("layer01_core", "output")
        ctx.clear()
        assert ctx.workflow_state == "created"
        assert len(ctx.layer_outputs) == 0

    def test_to_dict(self):
        ctx = OrchestrationContext(user_id="u1")
        d = ctx.to_dict()
        assert "request_id" in d
        assert "workflow_state" in d
        assert "layers_completed" in d


# ─── LayerRouter Tests ────────────────────────────────────────────
class TestLayerRouter:
    def setup_method(self):
        self.router = LayerRouter()

    def test_default_routes(self):
        assert self.router.route_count > 0

    def test_route_write(self):
        route = self.router.route("write")
        assert route is not None
        assert route.layer_id == "layer04_writing"

    def test_route_publish(self):
        route = self.router.route("publish")
        assert route is not None
        assert route.layer_id == "layer07_publishing"

    def test_route_unknown(self):
        route = self.router.route("unknown_task")
        assert route is None

    def test_register_custom(self):
        self.router.register("custom_task", "layer_custom", priority=10)
        route = self.router.route("custom_task")
        assert route is not None
        assert route.layer_id == "layer_custom"
        assert route.priority == 10

    def test_unregister(self):
        result = self.router.unregister("write")
        assert result is True
        assert self.router.route("write") is None

    def test_unregister_nonexistent(self):
        result = self.router.unregister("nonexistent")
        assert result is False

    def test_get_layer_for_task(self):
        assert self.router.get_layer_for_task("write") == "layer04_writing"
        assert self.router.get_layer_for_task("unknown") == ""

    def test_get_tasks_for_layer(self):
        tasks = self.router.get_tasks_for_layer("layer04_writing")
        assert "write" in tasks

    def test_get_all_routes(self):
        routes = self.router.get_all_routes()
        assert "write" in routes
        assert routes["write"] == "layer04_writing"


# ─── LayerDependencies Tests ──────────────────────────────────────
class TestLayerDependencies:
    def setup_method(self):
        self.deps = LayerDependencies()

    def test_default_dependencies(self):
        deps = self.deps.get_dependencies("layer04_writing")
        assert "layer03_intelligence" in deps

    def test_add_dependency(self):
        self.deps.add_dependency("layer_custom", "layer01_core")
        deps = self.deps.get_dependencies("layer_custom")
        assert "layer01_core" in deps

    def test_resolve_order(self):
        order = self.deps.resolve_order()
        assert len(order) > 0
        assert order[0] == "layer01_core"

    def test_validate(self):
        assert self.deps.validate() is True

    def test_get_ready_layers(self):
        ready = self.deps.get_ready_layers([])
        assert "layer01_core" in ready

    def test_get_ready_after_core(self):
        ready = self.deps.get_ready_layers(["layer01_core"])
        assert "layer02_research" in ready

    def test_is_satisfied(self):
        assert self.deps.is_satisfied([], "layer01_core") is True
        assert self.deps.is_satisfied([], "layer04_writing") is False
        assert self.deps.is_satisfied(
            ["layer01_core", "layer03_intelligence"],
            "layer04_writing"
        ) is True


# ─── ExecutionScheduler Tests ─────────────────────────────────────
class TestExecutionScheduler:
    def setup_method(self):
        self.scheduler = ExecutionScheduler()

    def test_schedule(self):
        task = self.scheduler.schedule("layer04_writing", priority=5)
        assert task.task_id.startswith("task_")
        assert task.layer == "layer04_writing"
        assert task.priority == 5

    def test_next_task(self):
        self.scheduler.schedule("layer04_writing")
        task = self.scheduler.next_task()
        assert task is not None
        assert task.status == "queued"

    def test_start_task(self):
        task = self.scheduler.schedule("layer04_writing")
        started = self.scheduler.start_task(task.task_id)
        assert started is not None
        assert started.status == "running"

    def test_complete_task(self):
        task = self.scheduler.schedule("layer04_writing")
        self.scheduler.start_task(task.task_id)
        completed = self.scheduler.complete_task(task.task_id, result={"draft": "text"})
        assert completed is not None
        assert completed.status == "completed"
        assert completed.result == {"draft": "text"}

    def test_complete_task_failure(self):
        task = self.scheduler.schedule("layer04_writing")
        self.scheduler.start_task(task.task_id)
        completed = self.scheduler.complete_task(task.task_id, error="API error")
        assert completed.status == "failed"

    def test_cancel_task(self):
        task = self.scheduler.schedule("layer04_writing")
        result = self.scheduler.cancel_task(task.task_id)
        assert result is True

    def test_priority_ordering(self):
        self.scheduler.schedule("low", priority=1)
        self.scheduler.schedule("high", priority=10)
        next_task = self.scheduler.next_task()
        assert next_task.priority == 10

    def test_get_stats(self):
        self.scheduler.schedule("layer01")
        self.scheduler.schedule("layer02")
        stats = self.scheduler.get_stats()
        assert stats["queued"] == 2

    def test_to_dict(self):
        task = self.scheduler.schedule("layer04_writing")
        d = task.to_dict()
        assert "task_id" in d
        assert "layer" in d
        assert "status" in d


# ─── SystemHealthMonitor Tests ────────────────────────────────────
class TestSystemHealthMonitor:
    def setup_method(self):
        self.monitor = SystemHealthMonitor()

    def test_register_component(self):
        self.monitor.register_component("layer01_core")
        assert "layer01_core" in self.monitor.get_all_status()

    def test_check(self):
        check = self.monitor.check("layer01_core", status="healthy", latency_ms=10)
        assert check.status == "healthy"
        assert check.latency_ms == 10

    def test_check_creates_component(self):
        self.monitor.check("new_component", status="healthy")
        assert "new_component" in self.monitor.get_all_status()

    def test_get_status(self):
        self.monitor.check("layer01_core", status="healthy")
        check = self.monitor.get_status("layer01_core")
        assert check is not None
        assert check.status == "healthy"

    def test_get_overall_healthy(self):
        self.monitor.check("layer01", status="healthy")
        self.monitor.check("layer02", status="healthy")
        assert self.monitor.get_overall_status() == "healthy"

    def test_get_overall_degraded(self):
        self.monitor.check("layer01", status="healthy")
        self.monitor.check("layer02", status="degraded")
        assert self.monitor.get_overall_status() == "degraded"

    def test_get_overall_critical(self):
        self.monitor.check("layer01", status="critical")
        assert self.monitor.get_overall_status() == "critical"

    def test_get_alerts(self):
        self.monitor.check("layer01", status="healthy")
        self.monitor.check("layer02", status="degraded")
        alerts = self.monitor.get_alerts()
        assert len(alerts) == 1

    def test_get_diagnostics(self):
        self.monitor.check("layer01", status="healthy")
        diag = self.monitor.get_diagnostics()
        assert "overall" in diag
        assert "components" in diag

    def test_to_dict(self):
        check = self.monitor.check("layer01", status="healthy", latency_ms=5)
        d = check.to_dict()
        assert "component" in d
        assert "status" in d


# ─── SystemEventBus Tests ─────────────────────────────────────────
class TestSystemEventBus:
    def setup_method(self):
        self.bus = SystemEventBus()

    def test_publish(self):
        event = SystemEvent(event_type="test", source="test")
        count = self.bus.publish(event)
        assert count == 0
        assert self.bus.get_event_count() == 1

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe("test", lambda e: received.append(e))
        event = SystemEvent(event_type="test", source="test")
        count = self.bus.publish(event)
        assert count == 1
        assert len(received) == 1

    def test_unsubscribe(self):
        handler = lambda e: None
        self.bus.subscribe("test", handler)
        result = self.bus.unsubscribe("test", handler)
        assert result is True
        assert self.bus.subscriber_count == 0

    def test_unsubscribe_nonexistent(self):
        result = self.bus.unsubscribe("nonexistent", lambda e: None)
        assert result is False

    def test_get_events_filtered(self):
        self.bus.publish(SystemEvent(event_type="a"))
        self.bus.publish(SystemEvent(event_type="b"))
        self.bus.publish(SystemEvent(event_type="a"))
        assert self.bus.get_event_count("a") == 2

    def test_event_to_dict(self):
        event = SystemEvent(event_type="test", source="test")
        d = event.to_dict()
        assert "event_id" in d
        assert "event_type" in d


# ─── OrchestratorMetrics Tests ────────────────────────────────────
class TestOrchestratorMetrics:
    def setup_method(self):
        self.metrics = OrchestratorMetrics()

    def test_record_run(self):
        self.metrics.record_run(success=True, duration_ms=100, layers_executed=5)
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

    def test_avg_retries(self):
        self.metrics.record_run(retries=1)
        self.metrics.record_run(retries=3)
        assert self.metrics.get_avg_retries() == 2.0

    def test_throughput(self):
        self.metrics.record_run(duration_ms=1000)
        t = self.metrics.get_throughput()
        assert t > 0

    def test_record_layer_failure(self):
        self.metrics.record_layer_failure("layer04_writing")
        self.metrics.record_layer_failure("layer04_writing")
        summary = self.metrics.get_summary()
        assert summary["total_layers_executed"] >= 0

    def test_summary(self):
        self.metrics.record_run(success=True, duration_ms=100)
        summary = self.metrics.get_summary()
        assert "total_runs" in summary
        assert "success_rate" in summary

    def test_reset(self):
        self.metrics.record_run(success=True)
        self.metrics.reset()
        assert self.metrics._total_runs == 0


# ─── OrchestratorReport Tests ─────────────────────────────────────
class TestOrchestratorReport:
    def setup_method(self):
        self.report = OrchestratorReport(request_id="req_1")

    def test_create(self):
        assert self.report.report_id.startswith("orep_")
        assert self.report.request_id == "req_1"
        assert self.report.success is True

    def test_add_layer_output(self):
        self.report.add_layer_output("layer04_writing", {"draft": "text"})
        assert "layer04_writing" in self.report.layer_outputs

    def test_add_failure(self):
        self.report.add_failure("layer04_writing", "API error")
        assert self.report.success is False
        assert "layer04_writing" in self.report.layers_failed
        assert len(self.report.warnings) == 1

    def test_add_warning(self):
        self.report.add_warning("slow response")
        assert len(self.report.warnings) == 1

    def test_add_recommendation(self):
        self.report.add_recommendation("optimize hooks")
        assert len(self.report.recommendations) == 1

    def test_set_metrics(self):
        self.report.set_metrics({"success_rate": 0.95})
        assert self.report.metrics["success_rate"] == 0.95

    def test_get_summary(self):
        summary = self.report.get_summary()
        assert "report_id" in summary
        assert "success" in summary

    def test_export_dict(self):
        self.report.add_layer_output("layer01_core", "ok")
        d = self.report.export_dict()
        assert "layers_executed" in d
        assert "warnings" in d
        assert "metrics" in d


# ─── WorkflowEngine Tests ─────────────────────────────────────────
class TestWorkflowEngine:
    def setup_method(self):
        self.engine = WorkflowEngine()

    def test_create_workflow(self):
        wf = self.engine.create_workflow(["layer01_core", "layer04_writing", "layer07_publishing"])
        assert len(wf.steps) == 3
        assert wf.steps[0].layer == "layer01_core"

    def test_execute_step(self):
        wf = self.engine.create_workflow(["layer04_writing"])
        step = self.engine.execute_step(wf.workflow_id, 0, lambda l: {"draft": "text"})
        assert step.status == "completed"
        assert step.result == {"draft": "text"}

    def test_execute_step_failure(self):
        wf = self.engine.create_workflow(["layer04_writing"])
        step = self.engine.execute_step(wf.workflow_id, 0, lambda l: 1/0)
        assert step.status == "failed"
        assert step.error is not None

    def test_execute_step_workflow_not_found(self):
        try:
            self.engine.execute_step("nonexistent", 0, lambda l: None)
            assert False
        except ValueError:
            pass

    def test_skip_step(self):
        wf = self.engine.create_workflow(["layer01", "layer02"])
        result = self.engine.skip_step(wf.workflow_id, 1)
        assert result is True
        assert wf.steps[1].status == "skipped"

    def test_rollback(self):
        wf = self.engine.create_workflow(["layer01", "layer02", "layer03"])
        self.engine.execute_step(wf.workflow_id, 0, lambda l: "ok")
        count = self.engine.rollback(wf.workflow_id)
        assert count >= 1

    def test_workflow_is_complete(self):
        wf = self.engine.create_workflow(["layer01"])
        self.engine.execute_step(wf.workflow_id, 0, lambda l: "ok")
        assert wf.is_complete is True

    def test_workflow_has_failures(self):
        wf = self.engine.create_workflow(["layer01"])
        self.engine.execute_step(wf.workflow_id, 0, lambda l: 1/0)
        assert wf.has_failures is True

    def test_get_workflow(self):
        wf = self.engine.create_workflow(["layer01"])
        retrieved = self.engine.get_workflow(wf.workflow_id)
        assert retrieved is not None

    def test_get_status(self):
        wf = self.engine.create_workflow(["layer01"])
        status = self.engine.get_status(wf.workflow_id)
        assert "workflow_id" in status

    def test_workflow_to_dict(self):
        wf = self.engine.create_workflow(["layer01", "layer02"])
        d = wf.to_dict()
        assert "total_steps" in d
        assert "workflow_id" in d


# ─── MasterOrchestrator Tests ─────────────────────────────────────
class TestMasterOrchestrator:
    def setup_method(self):
        self.orchestrator = MasterOrchestrator()

    def test_start(self):
        ctx = self.orchestrator.start(user_id="u1", session_id="s1")
        assert ctx.request_id.startswith("req_")
        assert ctx.workflow_state == "started"
        assert self.orchestrator.is_running is True

    def test_execute(self):
        self.orchestrator.start()
        report = self.orchestrator.execute(["write", "publish"])
        assert report.report_id.startswith("orep_")
        assert report.duration_ms >= 0

    def test_execute_with_handler(self):
        self.orchestrator.start()
        self.orchestrator.register_layer_handler("layer04_writing",
            lambda ctx: {"draft": "AI content"})
        report = self.orchestrator.execute(["write"])
        assert "layer04_writing" in report.layers_executed

    def test_execute_all_layers(self):
        self.orchestrator.start()
        self.orchestrator.register_layer_handler("layer01_core", lambda ctx: "ok")
        report = self.orchestrator.execute(["write"])
        assert len(report.layers_executed) > 0

    def test_pause(self):
        self.orchestrator.start()
        result = self.orchestrator.pause()
        assert result is True
        assert self.orchestrator.is_running is False

    def test_pause_when_not_running(self):
        result = self.orchestrator.pause()
        assert result is False

    def test_resume(self):
        self.orchestrator.start()
        self.orchestrator.pause()
        result = self.orchestrator.resume()
        assert result is True
        assert self.orchestrator.is_running is True

    def test_cancel(self):
        self.orchestrator.start()
        result = self.orchestrator.cancel()
        assert result is True
        assert self.orchestrator.is_running is False

    def test_status(self):
        self.orchestrator.start()
        status = self.orchestrator.status()
        assert "running" in status
        assert "health" in status
        assert "metrics" in status

    def test_shutdown(self):
        self.orchestrator.start()
        result = self.orchestrator.shutdown()
        assert result["status"] == "shutdown"

    def test_get_health(self):
        health = self.orchestrator.get_health()
        assert "overall" in health

    def test_event_bus_tracking(self):
        self.orchestrator.start()
        self.orchestrator.execute(["write"])
        events = self.orchestrator.event_bus.get_events()
        assert len(events) > 0

    def test_metrics_recorded(self):
        self.orchestrator.start()
        self.orchestrator.execute(["write"])
        summary = self.orchestrator.metrics.get_summary()
        assert summary["total_runs"] == 1

    def test_execution_count(self):
        assert self.orchestrator.execution_count == 0
        self.orchestrator.start()
        self.orchestrator.execute(["write"])
        assert self.orchestrator.execution_count == 1

    def test_multiple_executions(self):
        for _ in range(3):
            self.orchestrator.start()
            self.orchestrator.execute(["write"])
        assert self.orchestrator.execution_count == 3

    def test_different_tasks(self):
        self.orchestrator.start()
        report = self.orchestrator.execute(["write", "publish", "learn"])
        assert report.duration_ms >= 0

    def test_handler_failure(self):
        self.orchestrator.start()
        self.orchestrator.register_layer_handler("layer04_writing",
            lambda ctx: 1/0)
        report = self.orchestrator.execute(["write"])
        assert report.success is False
        assert len(report.layers_failed) > 0

    def test_router_integration(self):
        self.orchestrator.start()
        self.orchestrator.register_layer_handler("layer04_writing",
            lambda ctx: {"draft": "content"})
        self.orchestrator.register_layer_handler("layer07_publishing",
            lambda ctx: {"post_id": "123"})
        report = self.orchestrator.execute(["write", "publish"])
        assert len(report.layers_executed) > 0

    def test_recent_reports(self):
        for _ in range(3):
            self.orchestrator.start()
            self.orchestrator.execute(["write"])
        reports = self.orchestrator.get_recent_reports(2)
        assert len(reports) == 2


# ─── Integration Tests ────────────────────────────────────────────
class TestMasterOrchestratorIntegration:
    def setup_method(self):
        self.orchestrator = MasterOrchestrator()

    def test_full_pipeline(self):
        self.orchestrator.register_layer_handler("layer01_core", lambda ctx: {"core": "ready"})
        self.orchestrator.register_layer_handler("layer02_research",
            lambda ctx: {"facts": ["AI is evolving"]})
        self.orchestrator.register_layer_handler("layer03_intelligence",
            lambda ctx: {"insight": "strong trend"})
        self.orchestrator.register_layer_handler("layer04_writing",
            lambda ctx: {"draft": "AI is transforming industries"})
        self.orchestrator.register_layer_handler("layer06_quality",
            lambda ctx: {"score": 95})
        self.orchestrator.register_layer_handler("layer07_publishing",
            lambda ctx: {"post_id": "fb_123", "url": "https://fb.com/123"})
        self.orchestrator.register_layer_handler("layer08_analytics",
            lambda ctx: {"impressions": 500})
        self.orchestrator.register_layer_handler("layer09_learning",
            lambda ctx: {"lesson": "engagement up 15%"})

        self.orchestrator.start(user_id="user_1", metadata={"goal": "engagement"})
        report = self.orchestrator.execute(["write", "publish", "learn"])

        assert report.success is True
        assert len(report.layers_executed) > 0
        assert report.duration_ms > 0

    def test_cross_task_pipeline(self):
        self.orchestrator.register_layer_handler("layer01_core", lambda ctx: "ok")
        self.orchestrator.register_layer_handler("layer03_intelligence", lambda ctx: "insights")
        self.orchestrator.register_layer_handler("layer04_writing", lambda ctx: "draft")
        self.orchestrator.register_layer_handler("layer05_image", lambda ctx: "image")
        self.orchestrator.register_layer_handler("layer06_quality", lambda ctx: "pass")
        self.orchestrator.register_layer_handler("layer07_publishing", lambda ctx: "published")

        self.orchestrator.start()
        report = self.orchestrator.execute(["write", "generate_image", "quality_check", "publish"])

        assert len(report.layers_executed) > 0

    def test_health_across_runs(self):
        self.orchestrator.register_layer_handler("layer01_core", lambda ctx: "ok")
        for _ in range(3):
            self.orchestrator.start()
            self.orchestrator.execute(["write"])
        health = self.orchestrator.get_health()
        assert health["overall"] in ("healthy", "degraded")

    def test_event_bus_full_lifecycle(self):
        self.orchestrator.start()
        self.orchestrator.execute(["write"])
        events = self.orchestrator.event_bus.get_events()
        types = [e.event_type for e in events]
        assert "workflow_started" in types
        assert "workflow_completed" in types

    def test_metrics_accuracy(self):
        for _ in range(5):
            self.orchestrator.start()
            self.orchestrator.execute(["write"])
        metrics = self.orchestrator.metrics.get_summary()
        assert metrics["total_runs"] == 5
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
