"""Tests for Layer 11 — Enterprise Async Runtime Framework."""
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_config import RuntimeConfig
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_state import RuntimeState
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_metrics import RuntimeMetrics
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_events import RuntimeEvents
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_health import RuntimeHealth
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_memory import RuntimeMemory
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_profiler import RuntimeProfiler
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_registry import RuntimeRegistry
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_report import RuntimeReportGenerator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_validator import RuntimeValidator
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_monitor import RuntimeMonitor
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_manager import RuntimeManager
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_builder import RuntimeBuilder
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_factory import RuntimeFactory
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime_context import RuntimeContext
from layers.layer11_async_runtime.modules.event_loop_management.loop_manager import LoopManager
from layers.layer11_async_runtime.modules.event_loop_management.event_loop import AsyncEventLoop
from layers.layer11_async_runtime.modules.event_loop_management.loop_registry import LoopRegistry
from layers.layer11_async_runtime.modules.async_task_manager.task import Task
from layers.layer11_async_runtime.modules.async_task_manager.task_graph import TaskGraph
from layers.layer11_async_runtime.modules.async_task_manager.task_scheduler import TaskScheduler
from layers.layer11_async_runtime.modules.async_task_manager.task_executor import TaskExecutor
from layers.layer11_async_runtime.modules.async_task_manager.models import AsyncTask, TaskState
from layers.layer11_async_runtime.modules.async_task_manager.task_retry import RetryPolicy
from layers.layer11_async_runtime.modules.async_task_manager.task_dependency import TaskDependency
from layers.layer11_async_runtime.modules.async_task_manager.task_metrics import TaskMetrics
from layers.layer11_async_runtime.modules.async_task_manager.task_history import TaskHistory
from layers.layer11_async_runtime.modules.async_task_manager.task_cancel import TaskCancel
from layers.layer11_async_runtime.modules.async_task_manager.task_pause import TaskPause


# ─── RuntimeConfig Tests ──────────────────────────────────────
class TestRuntimeConfig:
    def test_defaults(self):
        c = RuntimeConfig()
        assert c.max_workers == 10
        assert c.task_timeout == 300.0
        assert c.enable_profiling is False
    def test_to_dict(self):
        d = RuntimeConfig().to_dict()
        assert "max_workers" in d
        assert "task_timeout" in d
    def test_from_dict(self):
        c = RuntimeConfig.from_dict({"max_workers": 20, "task_timeout": 60})
        assert c.max_workers == 20
        assert c.task_timeout == 60


# ─── RuntimeState Tests ──────────────────────────────────────
class TestRuntimeState:
    def test_initial_state(self):
        s = RuntimeState()
        assert s.current == RuntimeState.CREATED
    def test_transition(self):
        s = RuntimeState()
        assert s.transition(RuntimeState.STARTING) is True
        assert s.current == RuntimeState.STARTING
    def test_invalid_transition(self):
        s = RuntimeState()
        assert s.transition(RuntimeState.RUNNING) is False
    def test_full_lifecycle(self):
        s = RuntimeState()
        s.transition(RuntimeState.STARTING)
        s.transition(RuntimeState.RUNNING)
        s.transition(RuntimeState.STOPPING)
        s.transition(RuntimeState.STOPPED)
        assert s.current == RuntimeState.STOPPED
    def test_history(self):
        s = RuntimeState()
        s.transition(RuntimeState.STARTING)
        s.transition(RuntimeState.RUNNING)
        assert len(s.get_history()) == 2
    def test_to_dict(self):
        d = RuntimeState().to_dict()
        assert "state" in d


# ─── RuntimeMetrics Tests ──────────────────────────────────────
class TestRuntimeMetrics:
    def test_increment(self):
        m = RuntimeMetrics()
        m.increment("tasks")
        m.increment("tasks")
        assert m.get_counter("tasks") == 2
    def test_set_gauge(self):
        m = RuntimeMetrics()
        m.set_gauge("memory", 1024.0)
        assert m.get_gauge("memory") == 1024.0
    def test_uptime(self):
        m = RuntimeMetrics()
        assert m.get_uptime() >= 0
    def test_throughput(self):
        m = RuntimeMetrics()
        m.increment("tasks_completed", 10)
        assert m.get_throughput() >= 0
    def test_error_rate(self):
        m = RuntimeMetrics()
        m.increment("tasks_completed", 8)
        m.increment("tasks_failed", 2)
        assert m.get_error_rate() == 0.2
    def test_to_dict(self):
        d = RuntimeMetrics().to_dict()
        assert "uptime" in d
    def test_reset(self):
        m = RuntimeMetrics()
        m.increment("test")
        m.reset()
        assert m.get_counter("test") == 0


# ─── RuntimeEvents Tests ──────────────────────────────────────
class TestRuntimeEvents:
    def test_publish(self):
        e = RuntimeEvents()
        ev = e.publish("started", "test")
        assert ev.event_type == "started"
    def test_subscribe(self):
        e = RuntimeEvents()
        handled = []
        e.subscribe("test", lambda ev: handled.append(ev.event_type))
        e.publish("test")
        assert len(handled) == 1
    def test_unsubscribe(self):
        e = RuntimeEvents()
        h = lambda ev: None
        e.subscribe("test", h)
        assert e.unsubscribe("test", h) is True
    def test_get_events(self):
        e = RuntimeEvents()
        e.publish("a"); e.publish("b")
        assert len(e.get_events()) == 2
    def test_clear(self):
        e = RuntimeEvents()
        e.publish("a")
        assert e.clear() == 1


# ─── RuntimeHealth Tests ──────────────────────────────────────
class TestRuntimeHealth:
    def test_run_checks(self):
        h = RuntimeHealth()
        h.register_check("test", lambda: True)
        results = h.run_checks()
        assert len(results) == 1
        assert results[0].healthy is True
    def test_is_healthy(self):
        h = RuntimeHealth()
        h.register_check("ok", lambda: True)
        h.run_checks()
        assert h.is_healthy() is True
    def test_unhealthy(self):
        h = RuntimeHealth()
        h.register_check("fail", lambda: False)
        h.run_checks()
        assert h.is_healthy() is False
        assert len(h.get_unhealthy()) == 1


# ─── RuntimeMemory Tests ──────────────────────────────────────
class TestRuntimeMemory:
    def test_save(self):
        m = RuntimeMemory()
        cp = m.save_checkpoint("running", {"key": "val"})
        assert cp.checkpoint_id.startswith("cp_")
    def test_get_latest(self):
        m = RuntimeMemory()
        m.save_checkpoint("a"); m.save_checkpoint("b")
        assert m.get_latest().state == "b"
    def test_max_entries(self):
        m = RuntimeMemory(max_checkpoints=3)
        for i in range(5): m.save_checkpoint(f"s{i}")
        assert len(m.get_all()) == 3


# ─── RuntimeProfiler Tests ──────────────────────────────────────
class TestRuntimeProfiler:
    def test_profile(self):
        p = RuntimeProfiler()
        p.start("op1")
        import time; time.sleep(0.01)
        dur = p.stop("op1")
        assert dur > 0
    def test_get_stats(self):
        p = RuntimeProfiler()
        p.start("op"); p.stop("op")
        stats = p.get_stats("op")
        assert stats["count"] == 1


# ─── RuntimeRegistry Tests ──────────────────────────────────────
class TestRuntimeRegistry:
    def test_register(self):
        r = RuntimeRegistry()
        c = r.register("comp1", "service")
        assert c.name == "comp1"
    def test_unregister(self):
        r = RuntimeRegistry()
        r.register("comp1")
        assert r.unregister("comp1") is True
    def test_get_by_type(self):
        r = RuntimeRegistry()
        r.register("a", "type1"); r.register("b", "type2")
        assert len(r.get_by_type("type1")) == 1


# ─── RuntimeValidator Tests ──────────────────────────────────────
class TestRuntimeValidator:
    def test_valid(self):
        v = RuntimeValidator()
        r = v.validate_config({"max_workers": 4, "task_timeout": 60, "max_tasks": 100})
        assert r.is_valid is True
    def test_invalid(self):
        v = RuntimeValidator()
        r = v.validate_config({"max_workers": 0})
        assert r.is_valid is False


# ─── RuntimeReportGenerator Tests ──────────────────────────────
class TestRuntimeReportGenerator:
    def test_generate(self):
        rg = RuntimeReportGenerator()
        report = rg.generate("status", {"uptime": 100})
        assert report.data["uptime"] == 100
    def test_get_recent(self):
        rg = RuntimeReportGenerator()
        rg.generate("a"); rg.generate("b")
        assert len(rg.get_recent(1)) == 1


# ─── RuntimeMonitor Tests ──────────────────────────────────────
class TestRuntimeMonitor:
    def test_record(self):
        m = RuntimeMonitor()
        m.record_snapshot({"cpu": 50})
        assert len(m.get_history()) == 1
    def test_alert(self):
        m = RuntimeMonitor()
        m.alert("warning", "High CPU")
        assert len(m.get_alerts("warning")) == 1
    def test_clear_alerts(self):
        m = RuntimeMonitor()
        m.alert("error", "fail")
        assert m.clear_alerts() == 1


# ─── RuntimeManager Tests ──────────────────────────────────────
class TestRuntimeManager:
    def test_start_stop(self):
        rm = RuntimeManager()
        assert rm.start() is True
        assert rm.stop() is True
    def test_pause_resume(self):
        rm = RuntimeManager()
        rm.start()
        assert rm.pause() is True
        assert rm.resume() is True
    def test_restart(self):
        rm = RuntimeManager()
        rm.start()
        assert rm.restart() is True
    def test_status(self):
        rm = RuntimeManager()
        s = rm.status()
        assert "state" in s
        assert "metrics" in s
    def test_health_check(self):
        rm = RuntimeManager()
        h = rm.health_check()
        assert "healthy" in h
    def test_generate_report(self):
        rm = RuntimeManager()
        r = rm.generate_report()
        assert "report_id" in r


# ─── RuntimeBuilder Tests ──────────────────────────────────────
class TestRuntimeBuilder:
    def test_build(self):
        rm = RuntimeBuilder().max_workers(5).task_timeout(60).build()
        assert rm.config.max_workers == 5
    def test_chaining(self):
        rm = RuntimeBuilder().max_workers(3).enable_profiling().log_level("DEBUG").build()
        assert rm.config.enable_profiling is True
        assert rm.config.log_level == "DEBUG"


# ─── RuntimeFactory Tests ──────────────────────────────────────
class TestRuntimeFactory:
    def test_create_dev(self):
        rm = RuntimeFactory.create("development")
        assert rm.config.max_workers == 2
    def test_create_prod(self):
        rm = RuntimeFactory.create("production")
        assert rm.config.max_workers == 10
    def test_create_custom(self):
        rm = RuntimeFactory.create_custom({"max_workers": 99})
        assert rm.config.max_workers == 99
    def test_get_presets(self):
        presets = RuntimeFactory.get_presets()
        assert "development" in presets
        assert "production" in presets


# ─── RuntimeContext Tests ──────────────────────────────────────
class TestRuntimeContext:
    def test_context(self):
        ctx = RuntimeContext("test_op")
        assert ctx.operation == "test_op"
        assert ctx.elapsed() >= 0
    def test_not_expired(self):
        ctx = RuntimeContext()
        ctx.timeout = 60
        assert ctx.is_expired() is False
    def test_to_dict(self):
        d = RuntimeContext("op").to_dict()
        assert "context_id" in d


# ─── LoopManager Tests ──────────────────────────────────────
class TestLoopManager:
    def test_create(self):
        lm = LoopManager()
        loop = lm.create_loop("test")
        assert loop.loop_id == "test"
    def test_get(self):
        lm = LoopManager()
        lm.create_loop("a")
        assert lm.get_loop("a") is not None
    def test_remove(self):
        lm = LoopManager()
        lm.create_loop("a")
        assert lm.remove_loop("a") is True
    def test_stats(self):
        lm = LoopManager()
        lm.create_loop("a"); lm.create_loop("b")
        assert lm.get_stats()["total_loops"] == 2


# ─── LoopRegistry Tests ──────────────────────────────────────
class TestLoopRegistry:
    def test_register(self):
        r = LoopRegistry()
        e = r.register("loop1")
        assert e.loop_id == "loop1"
    def test_unregister(self):
        r = LoopRegistry()
        r.register("loop1")
        assert r.unregister("loop1") is True


# ─── Task Tests ──────────────────────────────────────
class TestTask:
    def test_lifecycle(self):
        t = Task("test")
        assert t.state == TaskState.PENDING
        t.start()
        assert t.state == TaskState.RUNNING
        t.complete("result")
        assert t.state == TaskState.COMPLETED
    def test_fail(self):
        t = Task("test")
        t.start()
        t.fail("error")
        assert t.state == TaskState.FAILED
    def test_cancel(self):
        t = Task("test")
        t.cancel()
        assert t.state == TaskState.CANCELLED
    def test_to_dict(self):
        d = Task("test").to_dict()
        assert "task_id" in d


# ─── TaskGraph Tests ──────────────────────────────────────
class TestTaskGraph:
    def test_add_edge(self):
        g = TaskGraph()
        g.add_edge("a", "b")
        assert "b" in g.get_dependents("a")
    def test_dependencies(self):
        g = TaskGraph()
        g.add_edge("a", "b")
        assert "a" in g.get_dependencies("b")
    def test_no_cycle(self):
        g = TaskGraph()
        g.add_edge("a", "b"); g.add_edge("b", "c")
        assert g.has_cycle() is False
    def test_ready_tasks(self):
        g = TaskGraph()
        g.add_edge("a", "b"); g.add_edge("a", "c")
        ready = g.get_ready_tasks(set())
        assert "a" in ready
    def test_stats(self):
        g = TaskGraph()
        g.add_edge("a", "b")
        s = g.get_stats()
        assert s["edges"] == 1


# ─── TaskScheduler Tests ──────────────────────────────────────
class TestTaskScheduler:
    def test_schedule(self):
        ts = TaskScheduler()
        task = AsyncTask("test")
        ts.schedule(task)
        assert ts.size() == 1
    def test_next(self):
        ts = TaskScheduler()
        task = AsyncTask("test")
        ts.schedule(task)
        next_task = ts.next()
        assert next_task is not None


# ─── TaskExecutor Tests ──────────────────────────────────────
class TestTaskExecutor:
    def test_execute_success(self):
        te = TaskExecutor()
        task = Task("test")
        result = te.execute(task, lambda: "done")
        assert result["success"] is True
    def test_execute_fail(self):
        te = TaskExecutor()
        task = Task("test")
        result = te.execute(task, lambda: 1/0)
        assert result["success"] is False
    def test_stats(self):
        te = TaskExecutor()
        te.execute(Task("a"), lambda: None)
        assert te.get_stats()["completed"] == 1


# ─── RetryPolicy Tests ──────────────────────────────────────
class TestRetryPolicy:
    def test_can_retry(self):
        rp = RetryPolicy(max_retries=3)
        assert rp.can_retry(0) is True
        assert rp.can_retry(3) is False
    def test_delay(self):
        rp = RetryPolicy(delay=1.0, backoff=2.0)
        assert rp.get_delay(0) == 1.0
        assert rp.get_delay(1) == 2.0
        assert rp.get_delay(2) == 4.0


# ─── TaskDependency Tests ──────────────────────────────────────
class TestTaskDependency:
    def test_add_get(self):
        td = TaskDependency()
        td.add("b", "a")
        assert "a" in td.get("b")
    def test_is_satisfied(self):
        td = TaskDependency()
        td.add("b", "a")
        assert td.is_satisfied("b", {"a"}) is True
        assert td.is_satisfied("b", set()) is False


# ─── TaskMetrics Tests ──────────────────────────────────────
class TestTaskMetrics:
    def test_record(self):
        tm = TaskMetrics()
        tm.record("completed", 5)
        assert tm.get("completed") == 5
    def test_success_rate(self):
        tm = TaskMetrics()
        tm.record("completed", 8)
        tm.record("failed", 2)
        assert tm.get_success_rate() == 0.8


# ─── TaskHistory Tests ──────────────────────────────────────
class TestTaskHistory:
    def test_record(self):
        th = TaskHistory()
        th.record("t1", "completed")
        assert len(th.get_recent()) == 1
    def test_max_entries(self):
        th = TaskHistory(max_entries=3)
        for i in range(5): th.record(f"t{i}", "done")
        assert len(th.get_recent(10)) == 3


# ─── TaskCancel Tests ──────────────────────────────────────
class TestTaskCancel:
    def test_cancel(self):
        tc = TaskCancel()
        tc.cancel("t1")
        assert tc.is_cancelled("t1") is True
    def test_clear(self):
        tc = TaskCancel()
        tc.cancel("t1")
        tc.clear()
        assert tc.is_cancelled("t1") is False


# ─── TaskPause Tests ──────────────────────────────────────
class TestTaskPause:
    def test_pause_resume(self):
        tp = TaskPause()
        tp.pause("t1")
        assert tp.is_paused("t1") is True
        tp.resume("t1")
        assert tp.is_paused("t1") is False
