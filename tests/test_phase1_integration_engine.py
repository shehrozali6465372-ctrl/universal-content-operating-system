"""Tests for Phase 1 — Cross-Layer Integration Engine (17 modules)."""
from __future__ import annotations
import time
import threading
import pytest

# ─── Module 1: Integration Kernel ───────────────────────────────────
from layers.layer14_enterprise_integration.modules.integration_kernel.integration_kernel import IntegrationKernel, KernelState


class TestIntegrationKernel:
    def setup_method(self):
        self.kernel = IntegrationKernel()

    def test_initial_state(self):
        assert self.kernel.state == KernelState.INITIALIZED
        assert self.kernel.uptime == 0.0

    def test_register_subsystem(self):
        self.kernel.register_subsystem("test", {"data": 1})
        assert self.kernel.get_subsystem("test") == {"data": 1}
        assert "test" in self.kernel.list_subsystems()

    def test_start_stop(self):
        result = self.kernel.start()
        assert result["status"] == "started"
        assert self.kernel.state == KernelState.RUNNING
        assert self.kernel.uptime >= 0
        result = self.kernel.stop()
        assert result["status"] == "stopped"
        assert self.kernel.state == KernelState.STOPPED

    def test_double_start(self):
        self.kernel.start()
        result = self.kernel.start()
        assert result["status"] == "already_running"

    def test_stop_not_running(self):
        result = self.kernel.stop()
        assert result["status"] == "not_running"

    def test_hooks(self):
        called = []
        self.kernel.add_hook("after_start", lambda: called.append("started"))
        self.kernel.start()
        assert "started" in called

    def test_status(self):
        status = self.kernel.status()
        assert "state" in status
        assert "subsystems" in status
        assert "hooks" in status

    def test_errors(self):
        def bad_hook():
            raise Exception("hook error")
        self.kernel.add_hook("after_start", bad_hook)
        self.kernel.start()
        assert len(self.kernel.get_errors()) == 1
        self.kernel.clear_errors()
        assert len(self.kernel.get_errors()) == 0


# ─── Module 2: Layer Registry ──────────────────────────────────────
from layers.layer14_enterprise_integration.modules.layer_registry.layer_registry import LayerRegistry, LayerStatus


class TestLayerRegistry:
    def setup_method(self):
        self.registry = LayerRegistry()

    def test_register_layer(self):
        info = self.registry.register("layer01", "Core", "1.0.0")
        assert info.layer_id == "layer01"
        assert info.name == "Core"
        assert self.registry.count() == 1

    def test_unregister(self):
        self.registry.register("layer01", "Core")
        assert self.registry.unregister("layer01")
        assert self.registry.count() == 0

    def test_get_layer(self):
        self.registry.register("layer01", "Core")
        layer = self.registry.get("layer01")
        assert layer is not None
        assert layer.name == "Core"

    def test_register_service(self):
        self.registry.register("layer01", "Core")
        assert self.registry.register_service("layer01", "engine", {"type": "core"})
        assert self.registry.get_service("engine") == {"type": "core"}

    def test_get_layer_for_service(self):
        self.registry.register("layer01", "Core")
        self.registry.register_service("layer01", "engine", {})
        assert self.registry.get_layer_for_service("engine") == "layer01"

    def test_set_status(self):
        self.registry.register("layer01", "Core")
        assert self.registry.set_status("layer01", LayerStatus.RUNNING)
        layer = self.registry.get("layer01")
        assert layer.status == LayerStatus.RUNNING

    def test_dependencies(self):
        self.registry.register("layer02", "Research", dependencies=["layer01"])
        deps = self.registry.get_dependencies("layer02")
        assert "layer01" in deps

    def test_dependents(self):
        self.registry.register("layer01", "Core")
        self.registry.register("layer02", "Research", dependencies=["layer01"])
        dependents = self.registry.get_dependents("layer01")
        assert "layer02" in dependents

    def test_summary(self):
        self.registry.register("layer01", "Core")
        summary = self.registry.summary()
        assert summary["total"] == 1
        assert "registered" in summary["statuses"]


# ─── Module 3: Dependency Graph ────────────────────────────────────
from layers.layer14_enterprise_integration.modules.dependency_graph.dependency_graph import DependencyGraph


class TestDependencyGraph:
    def setup_method(self):
        self.graph = DependencyGraph()

    def test_add_node(self):
        node = self.graph.add_node("A")
        assert node.node_id == "A"
        assert self.graph.count() == 1

    def test_add_dependency(self):
        self.graph.add_dependency("B", "A")
        assert "A" in self.graph.get_dependencies("B")
        assert "B" in self.graph.get_nodes() if hasattr(self.graph, 'get_nodes') else True

    def test_topological_sort(self):
        self.graph.add_dependency("B", "A")
        self.graph.add_dependency("C", "B")
        order = self.graph.topological_sort()
        assert order.index("A") < order.index("B") < order.index("C")

    def test_has_cycle(self):
        self.graph.add_dependency("B", "A")
        self.graph.add_dependency("C", "B")
        assert not self.graph.has_cycle()
        self.graph.add_dependency("A", "C")
        assert self.graph.has_cycle()

    def test_get_roots(self):
        self.graph.add_dependency("B", "A")
        roots = self.graph.get_roots()
        assert "A" in roots

    def test_get_leaves(self):
        self.graph.add_dependency("B", "A")
        leaves = self.graph.get_leaves()
        assert "B" in leaves

    def test_remove_node(self):
        self.graph.add_dependency("B", "A")
        assert self.graph.remove_node("B")
        assert self.graph.count() == 1

    def test_get_all_dependencies(self):
        self.graph.add_dependency("C", "B")
        self.graph.add_dependency("B", "A")
        all_deps = self.graph.get_all_dependencies("C")
        assert "A" in all_deps and "B" in all_deps

    def test_validate(self):
        self.graph.add_dependency("B", "A")
        result = self.graph.validate()
        assert result["valid"]


# ─── Module 4: Workflow Engine ─────────────────────────────────────
from layers.layer14_enterprise_integration.modules.workflow_engine.workflow_engine import WorkflowEngine, StepStatus, WorkflowStatus


class TestWorkflowEngine:
    def setup_method(self):
        self.engine = WorkflowEngine()

    def test_create_workflow(self):
        wf = self.engine.create_workflow("wf1", "Test Workflow")
        assert wf.name == "Test Workflow"
        assert wf.status == WorkflowStatus.CREATED

    def test_add_step(self):
        self.engine.create_workflow("wf1", "Test")
        step = self.engine.add_step("wf1", "s1", "Step 1", lambda ctx: "done")
        assert step is not None
        assert step.name == "Step 1"

    def test_execute_workflow(self):
        self.engine.create_workflow("wf1", "Test")
        self.engine.add_step("wf1", "s1", "Step 1", lambda ctx: {"result": "ok"})
        self.engine.add_step("wf1", "s2", "Step 2", lambda ctx: {"result": "done"})
        result = self.engine.execute("wf1")
        assert result["status"] == "completed"
        assert len(result["steps"]) == 2

    def test_execute_with_failure(self):
        self.engine.create_workflow("wf1", "Test")
        self.engine.add_step("wf1", "s1", "Good", lambda ctx: "ok")
        self.engine.add_step("wf1", "s2", "Bad", lambda ctx: (_ for _ in ()).throw(Exception("fail")))
        result = self.engine.execute("wf1")
        assert result["status"] == "failed"

    def test_execute_with_retry(self):
        call_count = [0]
        def flaky(ctx):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("not yet")
            return "ok"
        self.engine.create_workflow("wf1", "Test")
        self.engine.add_step("wf1", "s1", "Flaky", flaky, max_retries=1)
        result = self.engine.execute("wf1")
        assert result["status"] == "completed"

    def test_pause_cancel(self):
        self.engine.create_workflow("wf1", "Test")
        self.engine.add_step("wf1", "s1", "Step", lambda ctx: "ok")
        self.engine.execute("wf1")
        wf = self.engine.get_workflow("wf1")
        wf.status = WorkflowStatus.RUNNING
        assert self.engine.pause("wf1")
        assert self.engine.cancel("wf1")

    def test_not_found(self):
        result = self.engine.execute("nonexistent")
        assert result.get("error") == "workflow_not_found"


# ─── Module 5: Pipeline Engine ─────────────────────────────────────
from layers.layer14_enterprise_integration.modules.pipeline_engine.pipeline_engine import PipelineEngine, PipelineMode, StageStatus


class TestPipelineEngine:
    def setup_method(self):
        self.engine = PipelineEngine()

    def test_create_pipeline(self):
        p = self.engine.create_pipeline("p1", "Test Pipeline")
        assert p.name == "Test Pipeline"

    def test_add_stage(self):
        self.engine.create_pipeline("p1", "Test")
        stage = self.engine.add_stage("p1", "s1", "Stage 1", lambda d: {"step1": True})
        assert stage is not None

    def test_execute_pipeline(self):
        self.engine.create_pipeline("p1", "Test")
        self.engine.add_stage("p1", "s1", "Stage 1", lambda d: {"a": 1}, order=1)
        self.engine.add_stage("p1", "s2", "Stage 2", lambda d: {"b": 2}, order=2)
        result = self.engine.execute("p1", {"initial": True})
        assert result["status"] == "done"

    def test_pipeline_failure(self):
        self.engine.create_pipeline("p1", "Test")
        self.engine.add_stage("p1", "s1", "OK", lambda d: "ok")
        self.engine.add_stage("p1", "s2", "Fail", lambda d: (_ for _ in ()).throw(Exception("boom")))
        result = self.engine.execute("p1")
        assert result["status"] == "failed"

    def test_not_found(self):
        result = self.engine.execute("nonexistent")
        assert result.get("error") == "pipeline_not_found"


# ─── Module 6: Execution Context ───────────────────────────────────
from layers.layer14_enterprise_integration.modules.execution_context.execution_context import ExecutionContext


class TestExecutionContext:
    def setup_method(self):
        self.ctx = ExecutionContext()

    def test_set_get(self):
        self.ctx.set("key1", "value1")
        assert self.ctx.get("key1") == "value1"

    def test_has_delete(self):
        self.ctx.set("key1", "value1")
        assert self.ctx.has("key1")
        assert self.ctx.delete("key1")
        assert not self.ctx.has("key1")

    def test_update(self):
        self.ctx.update({"a": 1, "b": 2})
        assert self.ctx.get("a") == 1
        assert self.ctx.get("b") == 2

    def test_snapshot_restore(self):
        self.ctx.set("key1", "value1")
        snap = self.ctx.snapshot()
        self.ctx.clear()
        self.ctx.restore(snap)
        assert self.ctx.get("key1") == "value1"

    def test_fork(self):
        self.ctx.set("key1", "value1")
        child = self.ctx.fork()
        assert child.get("key1") == "value1"
        assert child.parent_id == self.ctx.context_id

    def test_tags(self):
        self.ctx.add_tag("important")
        assert self.ctx.has_tag("important")
        assert self.ctx.remove_tag("important")
        assert not self.ctx.has_tag("important")

    def test_history(self):
        self.ctx.set("a", 1)
        self.ctx.set("b", 2)
        assert len(self.ctx.get_history()) == 2

    def test_keys_values(self):
        self.ctx.update({"x": 10, "y": 20})
        assert "x" in self.ctx.keys()
        assert 10 in self.ctx.values()


# ─── Module 7: Service Locator ─────────────────────────────────────
from layers.layer14_enterprise_integration.modules.service_locator.service_locator import ServiceLocator


class TestServiceLocator:
    def setup_method(self):
        self.locator = ServiceLocator()

    def test_register_resolve(self):
        self.locator.register("engine", {"type": "core"}, layer="layer01")
        assert self.locator.resolve("engine") == {"type": "core"}

    def test_unregister(self):
        self.locator.register("engine", {})
        assert self.locator.unregister("engine")
        assert not self.locator.has("engine")

    def test_find_by_layer(self):
        self.locator.register("a", {}, layer="layer01")
        self.locator.register("b", {}, layer="layer02")
        assert self.locator.find_by_layer("layer01") == ["a"]

    def test_find_by_tag(self):
        self.locator.register("a", {}, tags=["fast"])
        self.locator.register("b", {}, tags=["slow"])
        assert self.locator.find_by_tag("fast") == ["a"]

    def test_count(self):
        self.locator.register("a", {})
        self.locator.register("b", {})
        assert self.locator.count() == 2


# ─── Module 8: Command Bus ─────────────────────────────────────────
from layers.layer14_enterprise_integration.modules.command_bus.command_bus import CommandBus, Command


class TestCommandBus:
    def setup_method(self):
        self.bus = CommandBus()

    def test_register_dispatch(self):
        self.bus.register("ping", lambda payload: "pong")
        result = self.bus.dispatch("ping")
        assert result.success
        assert result.result == "pong"

    def test_dispatch_no_handler(self):
        result = self.bus.dispatch("unknown")
        assert not result.success
        assert result.error == "no_handler_registered"

    def test_dispatch_with_payload(self):
        self.bus.register("add", lambda p: p.get("a", 0) + p.get("b", 0))
        result = self.bus.dispatch("add", {"a": 3, "b": 4})
        assert result.result == 7

    def test_dispatch_error(self):
        self.bus.register("fail", lambda p: (_ for _ in ()).throw(Exception("boom")))
        result = self.bus.dispatch("fail")
        assert not result.success

    def test_history(self):
        self.bus.register("ping", lambda p: "pong")
        self.bus.dispatch("ping")
        assert len(self.bus.get_history()) == 1

    def test_unregister(self):
        self.bus.register("ping", lambda p: "pong")
        assert self.bus.unregister("ping")
        assert "ping" not in self.bus.list_commands()


# ─── Module 9: Query Bus ───────────────────────────────────────────
from layers.layer14_enterprise_integration.modules.query_bus.query_bus import QueryBus


class TestQueryBus:
    def setup_method(self):
        self.bus = QueryBus()

    def test_register_execute(self):
        self.bus.register("get_count", lambda params: 42)
        result = self.bus.execute("get_count")
        assert result.success
        assert result.data == 42

    def test_execute_no_handler(self):
        result = self.bus.execute("unknown")
        assert not result.success

    def test_with_params(self):
        self.bus.register("multiply", lambda p: p.get("a", 0) * p.get("b", 0))
        result = self.bus.execute("multiply", {"a": 5, "b": 3})
        assert result.data == 15

    def test_history(self):
        self.bus.register("q", lambda p: 1)
        self.bus.execute("q")
        assert len(self.bus.get_history()) == 1


# ─── Module 10: Response Router ────────────────────────────────────
from layers.layer14_enterprise_integration.modules.response_router.response_router import ResponseRouter, ResponseEnvelope


class TestResponseRouter:
    def setup_method(self):
        self.router = ResponseRouter()

    def test_add_route(self):
        self.router.add_route("layer01", lambda data: {"processed": True})
        result = self.router.route("layer01", {"input": "test"})
        assert result.status == "ok"

    def test_no_route(self):
        result = self.router.route("nonexistent")
        assert result.status == "no_route"

    def test_route_error(self):
        self.router.add_route("bad", lambda data: (_ for _ in ()).throw(Exception("fail")))
        result = self.router.route("bad")
        assert result.status == "error"

    def test_route_all(self):
        self.router.add_route("a", lambda d: "ok_a")
        self.router.add_route("b", lambda d: "ok_b")
        results = self.router.route_all({"a": {}, "b": {}})
        assert len(results) == 2

    def test_aggregate(self):
        r1 = ResponseEnvelope("a", status="ok")
        r2 = ResponseEnvelope("b", status="error")
        agg = self.router.aggregate([r1, r2])
        assert agg["success"] == 1
        assert agg["failed"] == 1

    def test_list_routes(self):
        self.router.add_route("a", lambda d: None)
        self.router.add_route("b", lambda d: None)
        assert set(self.router.list_routes()) == {"a", "b"}


# ─── Module 11: Context Sync ───────────────────────────────────────
from layers.layer14_enterprise_integration.modules.context_sync.context_sync import ContextSync


class TestContextSync:
    def setup_method(self):
        self.sync = ContextSync()

    def test_create_get_set(self):
        self.sync.create_context("ctx1", {"init": True})
        self.sync.set("ctx1", "key1", "value1")
        assert self.sync.get("ctx1", "key1") == "value1"

    def test_merge(self):
        self.sync.create_context("ctx1")
        self.sync.merge("ctx1", {"a": 1, "b": 2})
        assert self.sync.get("ctx1", "a") == 1

    def test_snapshot_restore(self):
        self.sync.create_context("ctx1", {"data": 1})
        snap = self.sync.snapshot("ctx1")
        self.sync.restore("ctx1", {"data": 2})
        self.sync.restore("ctx1", snap)
        assert self.sync.get("ctx1", "data") == 1

    def test_delete_context(self):
        self.sync.create_context("ctx1")
        assert self.sync.delete_context("ctx1")
        assert "ctx1" not in self.sync.list_contexts()

    def test_barrier(self):
        self.sync.create_barrier("barrier1", 2)
        results = []
        def worker():
            self.sync.wait_barrier("barrier1", timeout=5.0)
            results.append("done")
        t1 = threading.Thread(target=worker)
        t2 = threading.Thread(target=worker)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        assert len(results) == 2


# ─── Module 12: Memory Bridge ──────────────────────────────────────
from layers.layer14_enterprise_integration.modules.memory_bridge.memory_bridge import MemoryBridge


class TestMemoryBridge:
    def setup_method(self):
        self.bridge = MemoryBridge()

    def test_put_get(self):
        self.bridge.put("key1", "value1")
        assert self.bridge.get("key1") == "value1"

    def test_namespace(self):
        self.bridge.put("key1", "val1", namespace="ns1")
        self.bridge.put("key1", "val2", namespace="ns2")
        assert self.bridge.get("key1", "ns1") == "val1"
        assert self.bridge.get("key1", "ns2") == "val2"

    def test_ttl_expiry(self):
        self.bridge.put("key1", "value1", ttl=0.01)
        time.sleep(0.02)
        assert self.bridge.get("key1") is None

    def test_delete(self):
        self.bridge.put("key1", "value1")
        assert self.bridge.delete("key1")
        assert self.bridge.get("key1") is None

    def test_list_keys(self):
        self.bridge.put("a", 1, namespace="ns")
        self.bridge.put("b", 2, namespace="ns")
        keys = self.bridge.list_keys("ns")
        assert set(keys) == {"a", "b"}

    def test_cleanup_expired(self):
        self.bridge.put("a", 1, ttl=0.01)
        self.bridge.put("b", 2)
        time.sleep(0.02)
        cleaned = self.bridge.cleanup_expired()
        assert cleaned == 1
        assert self.bridge.get("b") == 2

    def test_clear_namespace(self):
        self.bridge.put("a", 1, namespace="ns1")
        self.bridge.put("b", 2, namespace="ns2")
        count = self.bridge.clear_namespace("ns1")
        assert count == 1
        assert self.bridge.get("b", "ns2") == 2


# ─── Module 13: Event Bridge ───────────────────────────────────────
from layers.layer14_enterprise_integration.modules.event_bridge.event_bridge import EventBridge, Event


class TestEventBridge:
    def setup_method(self):
        self.bridge = EventBridge()

    def test_subscribe_publish(self):
        received = []
        self.bridge.subscribe("test.event", lambda e: received.append(e))
        self.bridge.emit("test.event", source="layer01")
        assert len(received) == 1

    def test_wildcard(self):
        received = []
        self.bridge.subscribe("*", lambda e: received.append(e))
        self.bridge.emit("any.event")
        self.bridge.emit("other.event")
        assert len(received) == 2

    def test_source_filter(self):
        received = []
        self.bridge.subscribe("test.event", lambda e: received.append(e), source_filter="layer01")
        self.bridge.emit("test.event", source="layer01")
        self.bridge.emit("test.event", source="layer02")
        assert len(received) == 1

    def test_unsubscribe(self):
        sub_id = self.bridge.subscribe("test.event", lambda e: None)
        assert self.bridge.unsubscribe(sub_id)

    def test_history(self):
        self.bridge.emit("test.event")
        history = self.bridge.get_history()
        assert len(history) == 1

    def test_publish_with_errors(self):
        self.bridge.subscribe("bad.event", lambda e: (_ for _ in ()).throw(Exception("fail")))
        result = self.bridge.emit("bad.event")
        assert result["delivered"] == 0
        assert len(result["errors"]) == 1


# ─── Module 14: Transaction Manager ────────────────────────────────
from layers.layer14_enterprise_integration.modules.transaction_manager.transaction_manager import TransactionManager, TxStatus


class TestTransactionManager:
    def setup_method(self):
        self.tm = TransactionManager()

    def test_begin_commit(self):
        tx = self.tm.begin()
        assert tx.status == TxStatus.ACTIVE
        self.tm.add_operation(tx.tx_id, "op1", lambda: "done")
        result = self.tm.commit(tx.tx_id)
        assert result["status"] == "committed"

    def test_rollback(self):
        tx = self.tm.begin()
        self.tm.add_operation(tx.tx_id, "op1", lambda: "done")
        result = self.tm.rollback(tx.tx_id)
        assert result["status"] == "rolled_back"

    def test_commit_with_failure(self):
        tx = self.tm.begin()
        self.tm.add_operation(tx.tx_id, "op1", lambda: "ok")
        self.tm.add_operation(tx.tx_id, "op2", lambda: (_ for _ in ()).throw(Exception("fail")))
        result = self.tm.commit(tx.tx_id)
        assert result.get("rolled_back") or "error" in result

    def test_compensation(self):
        compensated = [False]
        tx = self.tm.begin()
        self.tm.add_operation(tx.tx_id, "op1", lambda: "ok",
                              compensate=lambda: compensated.__setitem__(0, True))
        self.tm.add_operation(tx.tx_id, "op2", lambda: (_ for _ in ()).throw(Exception("fail")))
        self.tm.commit(tx.tx_id)
        assert compensated[0]

    def test_not_found(self):
        result = self.tm.commit("nonexistent")
        assert result.get("error") == "transaction_not_found"


# ─── Module 15: Lifecycle Manager ──────────────────────────────────
from layers.layer14_enterprise_integration.modules.lifecycle_manager.lifecycle_manager import LifecycleManager, ComponentState


class TestLifecycleManager:
    def setup_method(self):
        self.lm = LifecycleManager()

    def test_register_start_stop(self):
        self.lm.register("comp1", start_fn=lambda: None, stop_fn=lambda: None)
        result = self.lm.start_component("comp1")
        assert result["status"] == "started"
        comp = self.lm.get_component("comp1")
        assert comp.state == ComponentState.RUNNING
        result = self.lm.stop_component("comp1")
        assert result["status"] == "stopped"

    def test_start_error(self):
        def bad_start():
            raise Exception("boom")
        self.lm.register("bad", start_fn=bad_start)
        result = self.lm.start_component("bad")
        assert "error" in result

    def test_start_all_stop_all(self):
        self.lm.register("a", start_fn=lambda: None, stop_fn=lambda: None)
        self.lm.register("b", start_fn=lambda: None, stop_fn=lambda: None)
        result = self.lm.start_all()
        assert result["started"] == 2
        result = self.lm.stop_all()
        assert result["stopped"] == 2

    def test_health_check(self):
        self.lm.register("h", health_fn=lambda: {"healthy": True})
        self.lm.start_component("h")
        result = self.lm.health_check("h")
        assert result["health"]["healthy"]

    def test_unregister(self):
        self.lm.register("x")
        assert self.lm.unregister("x")
        assert self.lm.get_component("x") is None

    def test_status(self):
        self.lm.register("a")
        status = self.lm.status()
        assert status["total"] == 1


# ─── Module 16: Shared State ───────────────────────────────────────
from layers.layer14_enterprise_integration.modules.shared_state.shared_state import SharedState


class TestSharedState:
    def setup_method(self):
        self.state = SharedState()

    def test_get_set(self):
        self.state.set("key1", "value1")
        assert self.state.get("key1") == "value1"

    def test_has_delete(self):
        self.state.set("key1", "value1")
        assert self.state.has("key1")
        assert self.state.delete("key1")
        assert not self.state.has("key1")

    def test_watch(self):
        changes = []
        self.state.watch("key1", lambda k, o, n: changes.append((k, o, n)))
        self.state.set("key1", "new_value")
        assert len(changes) == 1
        assert changes[0] == ("key1", None, "new_value")

    def test_snapshot_restore(self):
        self.state.set("a", 1)
        snap = self.state.snapshot()
        self.state.clear()
        self.state.restore(snap)
        assert self.state.get("a") == 1

    def test_changelog(self):
        self.state.set("a", 1)
        self.state.set("b", 2)
        assert len(self.state.get_changelog()) == 2

    def test_thread_safety(self):
        def writer():
            for i in range(100):
                self.state.set(f"key_{i}", i)
        threads = [threading.Thread(target=writer) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert self.state.count() == 100


# ─── Module 17: Health Manager ─────────────────────────────────────
from layers.layer14_enterprise_integration.modules.health_manager.health_manager import HealthManager, HealthLevel


class TestHealthManager:
    def setup_method(self):
        self.hm = HealthManager()

    def test_register_check(self):
        self.hm.register("check1", lambda: {"healthy": True})
        assert self.hm.count() == 1

    def test_check_healthy(self):
        self.hm.register("check1", lambda: {"healthy": True})
        result = self.hm.check("check1")
        assert result["status"] == HealthLevel.HEALTHY.value

    def test_check_unhealthy(self):
        def bad_check():
            raise Exception("boom")
        self.hm.register("bad", bad_check, max_failures=1)
        result = self.hm.check("bad")
        assert result["status"] == HealthLevel.UNHEALTHY.value

    def test_check_all(self):
        self.hm.register("a", lambda: {"healthy": True})
        self.hm.register("b", lambda: {"healthy": True})
        result = self.hm.check_all()
        assert result["overall"] == HealthLevel.HEALTHY.value
        assert result["total"] == 2

    def test_get_unhealthy(self):
        def bad():
            raise Exception("fail")
        self.hm.register("bad", bad, max_failures=1)
        self.hm.check("bad")
        assert "bad" in self.hm.get_unhealthy()

    def test_unregister(self):
        self.hm.register("x", lambda: {"healthy": True})
        assert self.hm.unregister("x")
        assert self.hm.count() == 0

    def test_history(self):
        self.hm.register("a", lambda: {"healthy": True})
        self.hm.check("a")
        self.hm.check("a")
        assert len(self.hm.get_history("a")) == 2
