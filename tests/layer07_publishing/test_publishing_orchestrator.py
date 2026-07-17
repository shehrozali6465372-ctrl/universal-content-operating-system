"""Tests for Layer 7 Module 10 — Publishing Orchestrator."""
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_stage import PipelineStage, PipelineDefinition
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_context import PipelineContext
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_executor import PipelineExecutor, PipelineResult
from layers.layer07_publishing.modules.publishing_orchestrator.pipeline_monitor import PipelineMonitor, ExecutionRecord
from layers.layer07_publishing.modules.publishing_orchestrator.parallel_executor import ParallelExecutor, ParallelTask, ParallelResult
from layers.layer07_publishing.modules.publishing_orchestrator.event_handler import EventHandler, PipelineEvent
from layers.layer07_publishing.modules.publishing_orchestrator.module_registry import ModuleRegistry, ModuleInfo
from layers.layer07_publishing.modules.publishing_orchestrator.health_checker import HealthChecker, HealthCheck
from layers.layer07_publishing.modules.publishing_orchestrator.metrics_collector import MetricsCollector, PipelineMetrics
from layers.layer07_publishing.modules.publishing_orchestrator.publishing_orchestrator import PublishingOrchestrator
from layers.layer07_publishing.modules.publishing_orchestrator.exceptions import (
    OrchestratorError, PipelineError, IntegrationError,
)


# ─── PipelineStage Tests ─────────────────────────────────────────────
class TestPipelineStage:
    def test_create(self):
        s = PipelineStage("validate", "Validate content", 1, True)
        assert s.name == "validate"
        assert s.order == 1
        assert s.required is True

    def test_execute_success(self):
        def handler(ctx):
            return {"ok": True}
        s = PipelineStage("test", "test stage", 1, True, handler)
        result = s.execute({"key": "value"})
        assert result is True
        assert s.completed is True
        assert s.result == {"ok": True}

    def test_execute_exception(self):
        def handler(ctx):
            raise ValueError("test error")
        s = PipelineStage("fail", "fail stage", 1, True, handler)
        result = s.execute({})
        assert result is False
        assert "test error" in s.error

    def test_execute_no_handler(self):
        s = PipelineStage("noop", "no handler", 1)
        result = s.execute({})
        assert result is True

    def test_to_dict(self):
        s = PipelineStage("test", "desc", 1, True)
        d = s.to_dict()
        assert d["name"] == "test"
        assert d["required"] is True


class TestPipelineDefinition:
    def setup_method(self):
        self.pd = PipelineDefinition("test_pipeline")

    def test_add_stage(self):
        self.pd.add_stage(PipelineStage("s1", "stage 1", 1))
        assert self.pd.stage_count == 1

    def test_add_multiple_stages(self):
        self.pd.add_stage(PipelineStage("s2", "stage 2", 2))
        self.pd.add_stage(PipelineStage("s1", "stage 1", 1))
        assert self.pd.get_stages()[0].name == "s1"

    def test_get_stage(self):
        self.pd.add_stage(PipelineStage("s1", "stage 1", 1))
        assert self.pd.get_stage("s1") is not None
        assert self.pd.get_stage("missing") is None

    def test_get_required_stages(self):
        self.pd.add_stage(PipelineStage("s1", "stage 1", 1, True))
        self.pd.add_stage(PipelineStage("s2", "stage 2", 2, False))
        assert len(self.pd.get_required_stages()) == 1

    def test_to_dict(self):
        self.pd.add_stage(PipelineStage("s1", "stage 1", 1))
        d = self.pd.to_dict()
        assert d["stage_count"] == 1


# ─── PipelineContext Tests ────────────────────────────────────────────
class TestPipelineContext:
    def test_create(self):
        ctx = PipelineContext("facebook", "Hello world")
        assert ctx.platform == "facebook"
        assert ctx.content == "Hello world"
        assert ctx.request_id.startswith("ctx_")

    def test_set_get_result(self):
        ctx = PipelineContext()
        ctx.set_result("validate", {"valid": True})
        assert ctx.get_result("validate") == {"valid": True}
        assert ctx.get_result("missing") is None

    def test_add_error(self):
        ctx = PipelineContext()
        ctx.add_error("something went wrong")
        assert len(ctx.errors) == 1

    def test_to_dict(self):
        ctx = PipelineContext("fb", "Hi")
        d = ctx.to_dict()
        assert d["platform"] == "fb"
        assert d["content_length"] == 2


# ─── PipelineExecutor Tests ───────────────────────────────────────────
class TestPipelineResult:
    def test_create(self):
        r = PipelineResult()
        assert r.success is False

    def test_to_dict(self):
        r = PipelineResult()
        r.success = True
        d = r.to_dict()
        assert d["success"] is True


class TestPipelineExecutor:
    def setup_method(self):
        self.executor = PipelineExecutor()

    def test_execute_success(self):
        pipeline = PipelineDefinition("test")
        pipeline.add_stage(PipelineStage("s1", "stage 1", 1, True, lambda ctx: {"ok": True}))
        pipeline.add_stage(PipelineStage("s2", "stage 2", 2, True, lambda ctx: {"ok": True}))
        ctx = PipelineContext("fb", "Hi")
        result = self.executor.execute(pipeline, ctx)
        assert result.success is True
        assert len(result.completed_stages) == 2

    def test_execute_failure_optional(self):
        pipeline = PipelineDefinition("test")
        pipeline.add_stage(PipelineStage("s1", "stage 1", 1, False, lambda ctx: (_ for _ in ()).throw(ValueError("fail"))))
        pipeline.add_stage(PipelineStage("s2", "stage 2", 2, True, lambda ctx: {"ok": True}))
        ctx = PipelineContext("fb", "Hi")
        result = self.executor.execute(pipeline, ctx)
        assert len(result.failed_stages) == 1

    def test_execute_failure_required_stops(self):
        pipeline = PipelineDefinition("test")
        pipeline.add_stage(PipelineStage("s1", "stage 1", 1, True, lambda ctx: (_ for _ in ()).throw(ValueError("fail"))))
        pipeline.add_stage(PipelineStage("s2", "stage 2", 2, True, lambda ctx: {"ok": True}))
        ctx = PipelineContext("fb", "Hi")
        result = self.executor.execute(pipeline, ctx)
        assert result.success is False
        assert len(result.completed_stages) == 0

    def test_execution_count(self):
        pipeline = PipelineDefinition("test")
        pipeline.add_stage(PipelineStage("s1", "s1", 1, True, lambda ctx: {}))
        self.executor.execute(pipeline, PipelineContext())
        assert self.executor.execution_count == 1


# ─── PipelineMonitor Tests ───────────────────────────────────────────
class TestExecutionRecord:
    def test_create(self):
        r = ExecutionRecord("test", True)
        assert r.success is True

    def test_to_dict(self):
        r = ExecutionRecord("test", True)
        d = r.to_dict()
        assert d["pipeline_name"] == "test"


class TestPipelineMonitor:
    def setup_method(self):
        self.monitor = PipelineMonitor()

    def test_record_execution(self):
        r = ExecutionRecord("test", True)
        r.total_duration_ms = 100
        self.monitor.record_execution(r)
        assert self.monitor.execution_count == 1

    def test_get_health(self):
        for _ in range(5):
            r = ExecutionRecord("test", True)
            r.total_duration_ms = 100
            self.monitor.record_execution(r)
        health = self.monitor.get_health()
        assert health["success_rate"] == 1.0
        assert health["status"] == "healthy"

    def test_get_health_degraded(self):
        for _ in range(5):
            r = ExecutionRecord("test", False)
            r.total_duration_ms = 100
            self.monitor.record_execution(r)
        assert self.monitor.get_health()["status"] == "degraded"

    def test_get_recent(self):
        for _ in range(10):
            self.monitor.record_execution(ExecutionRecord("test", True))
        assert len(self.monitor.get_recent(3)) == 3

    def test_get_records_success_only(self):
        self.monitor.record_execution(ExecutionRecord("test", True))
        self.monitor.record_execution(ExecutionRecord("test", False))
        assert len(self.monitor.get_records(success_only=True)) == 1


# ─── ParallelExecutor Tests ──────────────────────────────────────────
class TestParallelTask:
    def test_create(self):
        t = ParallelTask("task1")
        assert t.name == "task1"

    def test_to_dict(self):
        t = ParallelTask("task1")
        d = t.to_dict()
        assert d["name"] == "task1"


class TestParallelResult:
    def test_create(self):
        r = ParallelResult()
        assert r.success is True

    def test_to_dict(self):
        r = ParallelResult()
        d = r.to_dict()
        assert "task_count" in d


class TestParallelExecutor:
    def setup_method(self):
        self.pe = ParallelExecutor()

    def test_execute_success(self):
        tasks = [
            ParallelTask("t1", lambda ctx: "result1"),
            ParallelTask("t2", lambda ctx: "result2"),
        ]
        result = self.pe.execute(tasks, {})
        assert result.success is True
        assert len(result.tasks) == 2

    def test_execute_with_exception(self):
        def boom(ctx):
            raise RuntimeError("fail")
        tasks = [ParallelTask("fail", boom)]
        result = self.pe.execute(tasks, {})
        assert result.success is False
        assert result.tasks[0].error == "fail"

    def test_execute_no_handler(self):
        tasks = [ParallelTask("noop")]
        result = self.pe.execute(tasks, {})
        assert result.success is True

    def test_parallel_count(self):
        self.pe.execute([], {})
        assert self.pe.parallel_count == 1


# ─── EventHandler Tests ───────────────────────────────────────────────
class TestPipelineEvent:
    def test_create(self):
        e = PipelineEvent("started", "orchestrator")
        assert e.event_type == "started"

    def test_to_dict(self):
        e = PipelineEvent("test", "src")
        d = e.to_dict()
        assert d["event_type"] == "test"


class TestEventHandler:
    def setup_method(self):
        self.eh = EventHandler()

    def test_publish(self):
        e = PipelineEvent("started", "orch")
        self.eh.publish(e)
        assert self.eh.event_count == 1

    def test_subscribe_and_publish(self):
        received = []
        self.eh.subscribe("started", lambda e: received.append(e))
        self.eh.publish(PipelineEvent("started", "orch"))
        assert len(received) == 1

    def test_get_events_by_type(self):
        self.eh.publish(PipelineEvent("started", "orch"))
        self.eh.publish(PipelineEvent("completed", "orch"))
        assert len(self.eh.get_events("started")) == 1

    def test_get_events_all(self):
        self.eh.publish(PipelineEvent("started", "orch"))
        self.eh.publish(PipelineEvent("completed", "orch"))
        assert len(self.eh.get_events()) == 2


# ─── ModuleRegistry Tests ─────────────────────────────────────────────
class TestModuleInfo:
    def test_create(self):
        m = ModuleInfo("test", "1.0.0")
        assert m.name == "test"
        assert m.enabled is True

    def test_to_dict(self):
        m = ModuleInfo("test", "1.0.0")
        d = m.to_dict()
        assert d["name"] == "test"


class TestModuleRegistry:
    def setup_method(self):
        self.mr = ModuleRegistry()

    def test_defaults_loaded(self):
        assert self.mr.module_count >= 10

    def test_register(self):
        self.mr.register("custom_module", "1.0.0", "Custom module")
        assert self.mr.get_module("custom_module") is not None

    def test_get_module(self):
        m = self.mr.get_module("publishing_planner")
        assert m is not None

    def test_disable_enable(self):
        self.mr.disable_module("publishing_planner")
        assert self.mr.get_module("publishing_planner").enabled is False
        self.mr.enable_module("publishing_planner")
        assert self.mr.get_module("publishing_planner").enabled is True

    def test_get_enabled_modules(self):
        enabled = self.mr.get_enabled_modules()
        assert len(enabled) >= 10

    def test_enabled_count(self):
        assert self.mr.enabled_count >= 10


# ─── HealthChecker Tests ─────────────────────────────────────────────
class TestHealthCheck:
    def test_create(self):
        hc = HealthCheck("database", True)
        assert hc.healthy is True

    def test_to_dict(self):
        hc = HealthCheck("db", True)
        d = hc.to_dict()
        assert d["component"] == "db"


class TestHealthChecker:
    def setup_method(self):
        self.hc = HealthChecker()

    def test_check(self):
        check = self.hc.check("database")
        assert check.healthy is True

    def test_get_checks(self):
        self.hc.check("db")
        self.hc.check("api")
        assert len(self.hc.get_checks()) == 2
        assert len(self.hc.get_checks("db")) == 1

    def test_is_healthy(self):
        self.hc.check("db")
        assert self.hc.is_healthy() is True

    def test_get_overall_status(self):
        self.hc.check("db")
        status = self.hc.get_overall_status()
        assert status["healthy"] == 1
        assert status["status"] == "healthy"


# ─── MetricsCollector Tests ───────────────────────────────────────────
class TestPipelineMetrics:
    def test_create(self):
        m = PipelineMetrics()
        assert m.total_executions == 0

    def test_to_dict(self):
        m = PipelineMetrics()
        d = m.to_dict()
        assert "total_executions" in d


class TestMetricsCollector:
    def setup_method(self):
        self.mc = MetricsCollector()

    def test_record(self):
        self.mc.record(True, 100, 5)
        metrics = self.mc.get_metrics()
        assert metrics.total_executions == 1
        assert metrics.success_count == 1

    def test_record_failure(self):
        self.mc.record(False, 200, 3)
        metrics = self.mc.get_metrics()
        assert metrics.failure_count == 1
        assert metrics.error_rate == 1.0

    def test_get_metrics_multiple(self):
        self.mc.record(True, 100, 5)
        self.mc.record(True, 200, 4)
        self.mc.record(False, 150, 3)
        m = self.mc.get_metrics()
        assert m.total_executions == 3
        assert m.success_count == 2
        assert m.avg_duration_ms == 150.0

    def test_get_history(self):
        self.mc.record(True, 100, 5)
        history = self.mc.get_history()
        assert len(history) == 1


# ─── PublishingOrchestrator Tests ─────────────────────────────────────
class TestPublishingOrchestrator:
    def setup_method(self):
        self.orch = PublishingOrchestrator()

    def test_create_default_pipeline(self):
        pipeline = self.orch.create_default_pipeline()
        assert pipeline.stage_count >= 8

    def test_publish_success(self):
        result = self.orch.publish("facebook", "Hello world")
        assert result["success"] is True
        assert result["platform"] == "facebook"
        assert len(result["completed_stages"]) >= 5

    def test_publish_multiple_platforms(self):
        r1 = self.orch.publish("facebook", "FB post")
        r2 = self.orch.publish("linkedin", "LI post")
        assert r1["success"] is True
        assert r2["success"] is True

    def test_orchestration_count(self):
        self.orch.publish("fb", "Hi")
        self.orch.publish("li", "Hi")
        assert self.orch.orchestration_count == 2

    def test_health(self):
        self.orch.publish("fb", "Hi")
        health = self.orch.get_health()
        assert health["total_executions"] >= 1
        assert "monitor" in health
        assert "metrics" in health

    def test_events_tracked(self):
        self.orch.publish("fb", "Hi")
        events = self.orch.event_handler.get_events()
        assert len(events) >= 2

    def test_monitor_tracked(self):
        self.orch.publish("fb", "Hi")
        assert self.orch.monitor.execution_count >= 1

    def test_metrics_recorded(self):
        self.orch.publish("fb", "Hi")
        m = self.orch.metrics_collector.get_metrics()
        assert m.total_executions >= 1


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(OrchestratorError, Exception)
        assert issubclass(PipelineError, OrchestratorError)
        assert issubclass(IntegrationError, OrchestratorError)

    def test_message(self):
        err = PipelineError("pipeline failed")
        assert str(err) == "pipeline failed"
