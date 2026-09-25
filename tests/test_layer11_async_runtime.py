"""Tests for Layer 11 — Enterprise Async Runtime Framework."""
import asyncio
import threading

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
from layers.layer11_async_runtime.modules.async_runtime_engine.runtime import AsyncRuntime


class TestRuntimeConfig:
    def test_defaults(self):
        c = RuntimeConfig()
        assert c.max_workers == 10
        assert c.task_timeout == 300.0
        assert c.enable_profiling is False

    def test_to_dict(self):
        assert "max_workers" in RuntimeConfig().to_dict()

    def test_from_dict(self):
        c = RuntimeConfig.from_dict({"max_workers": 20, "task_timeout": 60})
        assert c.max_workers == 20
        assert c.task_timeout == 60


class TestRuntimeState:
    def test_initial_state(self):
        assert RuntimeState().current == RuntimeState.CREATED

    def test_transition(self):
        s = RuntimeState()
        assert s.transition(RuntimeState.STARTING) is True
        assert s.current == RuntimeState.STARTING

    def test_invalid_transition(self):
        assert RuntimeState().transition(RuntimeState.RUNNING) is False

    def test_full_lifecycle(self):
        s = RuntimeState()
        for state in (RuntimeState.STARTING, RuntimeState.RUNNING,
                      RuntimeState.STOPPING, RuntimeState.STOPPED):
            assert s.transition(state) is True
        assert s.current == RuntimeState.STOPPED

    def test_history_is_bounded_and_validated(self):
        s = RuntimeState(max_history=2)
        s.transition(RuntimeState.STARTING)
        s.transition(RuntimeState.RUNNING)
        s.transition(RuntimeState.STOPPING)
        assert len(s.get_history()) == 2
        assert s.get_history(0) == []
        try:
            s.get_history(-1)
        except ValueError:
            pass
        else:
            raise AssertionError("negative history count must be rejected")

    def test_concurrent_transitions_are_serialized(self):
        s = RuntimeState()
        assert s.transition(RuntimeState.STARTING)
        results = []

        def move() -> None:
            results.append(s.transition(RuntimeState.RUNNING))

        threads = [threading.Thread(target=move) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert sum(results) == 1
        assert s.current == RuntimeState.RUNNING

    def test_to_dict(self):
        assert "state" in RuntimeState().to_dict()


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
        assert RuntimeMetrics().get_uptime() >= 0

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
        assert "uptime" in RuntimeMetrics().to_dict()

    def test_reset(self):
        m = RuntimeMetrics()
        m.increment("test")
        m.reset()
        assert m.get_counter("test") == 0


class TestRuntimeEvents:
    def test_publish(self):
        e = RuntimeEvents()
        assert e.publish("started", "test").event_type == "started"

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
        e.publish("a")
        e.publish("b")
        assert len(e.get_events()) == 2

    def test_clear(self):
        e = RuntimeEvents()
        e.publish("a")
        assert e.clear() == 1


class TestRuntimeHealth:
    def test_run_checks(self):
        h = RuntimeHealth()
        h.register_check("test", lambda: True)
        results = h.run_checks()
        assert len(results) == 1
        assert results[0].healthy is True

    def test_non_bool_check_is_failure(self):
        h = RuntimeHealth()
        h.register_check("bad", lambda: "yes")
        assert h.run_checks()[0].healthy is False
        assert h.is_healthy() is False

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


class TestRuntimeMemory:
    def test_save(self):
        cp = RuntimeMemory().save_checkpoint("running", {"key": "val"})
        assert cp.checkpoint_id.startswith("cp_")

    def test_get_latest(self):
        m = RuntimeMemory()
        m.save_checkpoint("a")
        m.save_checkpoint("b")
        assert m.get_latest().state == "b"

    def test_max_entries(self):
        m = RuntimeMemory(max_checkpoints=3)
        for i in range(5):
            m.save_checkpoint(f"s{i}")
        assert len(m.get_all()) == 3


class TestRuntimeProfiler:
    def test_profile(self):
        p = RuntimeProfiler()
        p.start("op1")
        import time
        time.sleep(0.01)
        assert p.stop("op1") > 0

    def test_get_stats(self):
        p = RuntimeProfiler()
        p.start("op")
        p.stop("op")
        assert p.get_stats("op")["count"] == 1


class TestRuntimeRegistry:
    def test_register(self):
        r = RuntimeRegistry()
        assert r.register("comp1", "service").name == "comp1"

    def test_unregister(self):
        r = RuntimeRegistry()
        r.register("comp1")
        assert r.unregister("comp1") is True

    def test_get_by_type(self):
        r = RuntimeRegistry()
        r.register("a", "type1")
        r.register("b", "type2")
        assert len(r.get_by_type("type1")) == 1


class TestRuntimeValidator:
    def test_valid(self):
        r = RuntimeValidator().validate_config(
            {"max_workers": 4, "task_timeout": 60, "max_tasks": 100}
        )
        assert r.is_valid is True

    def test_invalid(self):
        assert RuntimeValidator().validate_config({"max_workers": 0}).is_valid is False


class TestRuntimeReportGenerator:
    def test_generate(self):
        report = RuntimeReportGenerator().generate("status", {"uptime": 100})
        assert report.data["uptime"] == 100

    def test_get_recent(self):
        rg = RuntimeReportGenerator()
        rg.generate("a")
        rg.generate("b")
        assert len(rg.get_recent(1)) == 1


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
        s = RuntimeManager().status()
        assert "state" in s
        assert "metrics" in s

    def test_health_check(self):
        assert "healthy" in RuntimeManager().health_check()

    def test_generate_report(self):
        assert "report_id" in RuntimeManager().generate_report()


class TestRuntimeBuilder:
    def test_build(self):
        rm = RuntimeBuilder().max_workers(5).task_timeout(60).build()
        assert rm.config.max_workers == 5

    def test_chaining(self):
        rm = RuntimeBuilder().max_workers(3).enable_profiling().log_level("DEBUG").build()
        assert rm.config.enable_profiling is True
        assert rm.config.log_level == "DEBUG"


class TestRuntimeFactory:
    def test_create_dev(self):
        assert RuntimeFactory.create("development").config.max_workers == 2

    def test_create_prod(self):
        assert RuntimeFactory.create("production").config.max_workers == 10

    def test_create_custom(self):
        assert RuntimeFactory.create_custom({"max_workers": 99}).config.max_workers == 99

    def test_get_presets(self):
        assert "development" in RuntimeFactory.get_presets()


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
        assert "context_id" in RuntimeContext("op").to_dict()


class TestLoopManager:
    def test_create(self):
        loop = LoopManager().create_loop("test")
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
        lm.create_loop("a")
        lm.create_loop("b")
        assert lm.get_stats()["total_loops"] == 2


class TestLoopRegistry:
    def test_register(self):
        assert LoopRegistry().register("loop1").loop_id == "loop1"

    def test_unregister(self):
        r = LoopRegistry()
        r.register("loop1")
        assert r.unregister("loop1") is True


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
        assert "task_id" in Task("test").to_dict()


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
        g.add_edge("a", "b")
        g.add_edge("b", "c")
        assert g.has_cycle() is False

    def test_ready_tasks(self):
        g = TaskGraph()
        g.add_edge("a", "b")
        g.add_edge("a", "c")
        assert "a" in g.get_ready_tasks(set())

    def test_stats(self):
        g = TaskGraph()
        g.add_edge("a", "b")
        assert g.get_stats()["edges"] == 1


class TestTaskScheduler:
    def test_schedule(self):
        ts = TaskScheduler()
        ts.schedule(AsyncTask("test"))
        assert ts.size() == 1

    def test_next(self):
        ts = TaskScheduler()
        ts.schedule(AsyncTask("test"))
        assert ts.next() is not None


class TestTaskExecutor:
    def test_execute_success(self):
        result = TaskExecutor().execute(Task("test"), lambda: "done")
        assert result["success"] is True

    def test_execute_fail(self):
        result = TaskExecutor().execute(Task("test"), lambda: 1 / 0)
        assert result["success"] is False

    def test_execute_async(self):
        async def work():
            await asyncio.sleep(0)
            return "done"

        async def case():
            result = await TaskExecutor().execute_async(Task("async"), work)
            assert result["success"] is True

        asyncio.run(case())

    def test_execute_async_timeout(self):
        async def work():
            await asyncio.sleep(1)

        async def case():
            result = await TaskExecutor().execute_async(Task("timeout"), work, timeout=0.01)
            assert result["success"] is False

        asyncio.run(case())

    def test_stats(self):
        te = TaskExecutor()
        te.execute(Task("a"), lambda: None)
        assert te.get_stats()["completed"] == 1


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


class TestTaskHistory:
    def test_record(self):
        th = TaskHistory()
        th.record("t1", "completed")
        assert len(th.get_recent()) == 1

    def test_max_entries(self):
        th = TaskHistory(max_entries=3)
        for i in range(5):
            th.record(f"t{i}", "done")
        assert len(th.get_recent(10)) == 3


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


class TestTaskPause:
    def test_pause_resume(self):
        tp = TaskPause()
        tp.pause("t1")
        assert tp.is_paused("t1") is True
        tp.resume("t1")
        assert tp.is_paused("t1") is False


class TestAsyncRuntime:
    def test_lifecycle_and_restart(self):
        runtime = AsyncRuntime(max_workers=2)
        assert runtime.is_running is False
        runtime.start()
        assert runtime.is_running is True
        runtime.stop()
        assert runtime.is_running is False
        runtime.start()
        assert runtime.run_coroutine(asyncio_sleep_result()) == "ok"
        runtime.stop()

    def test_parallel_execution(self):
        runtime = AsyncRuntime(max_workers=2)
        runtime.start()
        assert runtime.run_parallel(
            asyncio_sleep_result("a"), asyncio_sleep_result("b")
        ) == ["a", "b"]
        assert runtime.metrics["completed"] == 2
        runtime.stop()

    def test_failure_and_cancellation_metrics(self):
        runtime = AsyncRuntime()
        runtime.start()
        try:
            runtime.run_coroutine(asyncio_failure())
        except ValueError:
            pass
        assert runtime.metrics["failed"] == 1
        runtime.stop()

    def test_pause_rejects_new_coroutines(self):\n        runtime = AsyncRuntime()\n        runtime.start()\n        runtime.pause()\n        try:\n            runtime.run_coroutine(asyncio_sleep_result())\n        except RuntimeError as exc:\n            assert "paused" in str(exc)\n        else:\n            raise AssertionError("paused runtime must reject new coroutines")\n        runtime.resume()\n        assert runtime.run_coroutine(asyncio_sleep_result()) == "ok"\n        runtime.stop()\n\n    def test_thread_pool(self):
        runtime = AsyncRuntime(max_workers=2)
        runtime.start()
        assert runtime.submit_to_thread(lambda x: x + 1, 4) == 5
        runtime.stop()

    def test_requires_running_runtime(self):
        runtime = AsyncRuntime()
        try:
            runtime.run_coroutine(asyncio_sleep_result())
        except RuntimeError as exc:
            assert "not running" in str(exc)
        else:
            raise AssertionError("runtime must reject execution before start")

    def test_task_ids_are_unique(self):
        ids = {AsyncRuntimeTaskId() for _ in range(100)}
        assert len(ids) == 100


def AsyncRuntimeTaskId():
    from layers.layer11_async_runtime.modules.async_runtime_engine.runtime import AsyncTask
    return AsyncTask().task_id


async def asyncio_sleep_result(value="ok"):
    await asyncio.sleep(0)
    return value


async def asyncio_failure():
    await asyncio.sleep(0)
    raise ValueError("boom")
