"""Tests for Layer 10 Module 2 — Workflow Coordinator Engine."""
from layers.layer10_monetization.modules.workflow_coordinator.exceptions import (
    WorkflowCoordinatorError, StageExecutionError, SynchronizationError,
    CheckpointError, StateError, TimeoutError, RetryLimitExceeded,
)
from layers.layer10_monetization.modules.workflow_coordinator.workflow_definition import WorkflowDefinition
from layers.layer10_monetization.modules.workflow_coordinator.workflow_stage import WorkflowStage
from layers.layer10_monetization.modules.workflow_coordinator.execution_controller import ExecutionController
from layers.layer10_monetization.modules.workflow_coordinator.state_manager import StateManager
from layers.layer10_monetization.modules.workflow_coordinator.synchronization_manager import (
    SynchronizationManager, SyncLock,
)
from layers.layer10_monetization.modules.workflow_coordinator.checkpoint_manager import CheckpointManager
from layers.layer10_monetization.modules.workflow_coordinator.workflow_events import (
    WorkflowEventBus, WorkflowEvent,
)
from layers.layer10_monetization.modules.workflow_coordinator.workflow_metrics import WorkflowMetrics
from layers.layer10_monetization.modules.workflow_coordinator.workflow_report import WorkflowReport
from layers.layer10_monetization.modules.workflow_coordinator.workflow_coordinator import WorkflowCoordinator


# ─── Exceptions Tests ─────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        with raise_ctx(WorkflowCoordinatorError("test")):
            raise WorkflowCoordinatorError("test")

    def test_stage_execution(self):
        with raise_ctx(StageExecutionError("test")):
            raise StageExecutionError("test")

    def test_synchronization(self):
        with raise_ctx(SynchronizationError("test")):
            raise SynchronizationError("test")

    def test_checkpoint(self):
        with raise_ctx(CheckpointError("test")):
            raise CheckpointError("test")

    def test_state(self):
        with raise_ctx(StateError("test")):
            raise StateError("test")

    def test_timeout(self):
        with raise_ctx(TimeoutError("test")):
            raise TimeoutError("test")

    def test_retry_limit(self):
        with raise_ctx(RetryLimitExceeded("test")):
            raise RetryLimitExceeded("test")

    def test_inheritance(self):
        assert issubclass(StageExecutionError, WorkflowCoordinatorError)
        assert issubclass(SynchronizationError, WorkflowCoordinatorError)
        assert issubclass(CheckpointError, WorkflowCoordinatorError)
        assert issubclass(StateError, WorkflowCoordinatorError)
        assert issubclass(TimeoutError, WorkflowCoordinatorError)
        assert issubclass(RetryLimitExceeded, WorkflowCoordinatorError)


# ─── WorkflowDefinition Tests ─────────────────────────────────────
class TestWorkflowDefinition:
    def test_create(self):
        wd = WorkflowDefinition("test_workflow", ["s1", "s2", "s3"])
        assert wd.workflow_id.startswith("wfdef_")
        assert wd.name == "test_workflow"
        assert len(wd.stages) == 3

    def test_add_stage(self):
        wd = WorkflowDefinition("test", ["s1"])
        wd.add_stage("s2", depends_on=["s1"])
        assert "s2" in wd.stages
        assert wd.dependencies["s2"] == ["s1"]

    def test_add_stage_no_duplicate(self):
        wd = WorkflowDefinition("test", ["s1"])
        wd.add_stage("s1")
        assert wd.stages.count("s1") == 1

    def test_remove_stage(self):
        wd = WorkflowDefinition("test", ["s1", "s2"])
        result = wd.remove_stage("s2")
        assert result is True
        assert "s2" not in wd.stages

    def test_remove_nonexistent(self):
        wd = WorkflowDefinition("test", ["s1"])
        result = wd.remove_stage("nonexistent")
        assert result is False

    def test_validate(self):
        wd = WorkflowDefinition("test", ["s1", "s2"])
        assert wd.validate() is True

    def test_validate_empty(self):
        wd = WorkflowDefinition("test", [])
        assert wd.validate() is False

    def test_get_execution_order(self):
        wd = WorkflowDefinition("test", ["s1", "s2", "s3"])
        wd.dependencies["s2"] = ["s1"]
        wd.dependencies["s3"] = ["s2"]
        batches = wd.get_execution_order()
        assert len(batches) == 3

    def test_clone(self):
        wd = WorkflowDefinition("test", ["s1", "s2"])
        clone = wd.clone()
        assert clone.name == wd.name
        assert clone.stages == wd.stages
        clone.stages.append("s3")
        assert len(wd.stages) == 2

    def test_to_dict(self):
        wd = WorkflowDefinition("test", ["s1", "s2"])
        d = wd.to_dict()
        assert "workflow_id" in d
        assert "stage_count" in d
        assert d["stage_count"] == 2


# ─── WorkflowStage Tests ──────────────────────────────────────────
class TestWorkflowStage:
    def test_create(self):
        stage = WorkflowStage("layer04_writing", 0)
        assert stage.stage_id.startswith("stage_")
        assert stage.layer == "layer04_writing"
        assert stage.status == "pending"

    def test_start(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        assert stage.status == "running"
        assert stage.started_at > 0

    def test_finish(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.finish({"draft": "text"})
        assert stage.status == "completed"
        assert stage.result == {"draft": "text"}

    def test_fail(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.fail("API error")
        assert stage.status == "failed"
        assert stage.error == "API error"

    def test_reset(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.finish()
        stage.reset()
        assert stage.status == "pending"
        assert stage.result is None

    def test_can_retry(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.fail("error")
        assert stage.can_retry() is True

    def test_cannot_retry_when_completed(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.finish()
        assert stage.can_retry() is False

    def test_retry(self):
        stage = WorkflowStage("layer04_writing")
        stage.start()
        stage.fail("error")
        result = stage.retry()
        assert result is True
        assert stage.retry_count == 1
        assert stage.status == "pending"

    def test_retry_limit_exceeded(self):
        stage = WorkflowStage("layer04_writing")
        stage.max_retries = 1
        stage.start()
        stage.fail("error")
        stage.retry()
        stage.start()
        stage.fail("error")
        assert stage.can_retry() is False

    def test_is_terminal(self):
        stage = WorkflowStage("layer04_writing")
        assert stage.is_terminal is False
        stage.start()
        assert stage.is_terminal is False
        stage.finish()
        assert stage.is_terminal is True

    def test_to_dict(self):
        stage = WorkflowStage("layer04_writing")
        d = stage.to_dict()
        assert "stage_id" in d
        assert "layer" in d
        assert "status" in d


# ─── ExecutionController Tests ────────────────────────────────────
class TestExecutionController:
    def setup_method(self):
        self.controller = ExecutionController()

    def test_sequential(self):
        stages = [WorkflowStage("layer01", 0), WorkflowStage("layer02", 1)]
        results = self.controller.execute_sequential(stages, lambda l: {"ok": True})
        assert len(results) == 2
        assert all(s.status == "completed" for s in results)

    def test_sequential_failure(self):
        def executor(layer):
            if layer == "layer02":
                raise ValueError("fail")
            return {"ok": True}
        stages = [WorkflowStage("layer01", 0), WorkflowStage("layer02", 1)]
        results = self.controller.execute_sequential(stages, executor)
        assert results[0].status == "completed"
        assert results[1].status == "failed"

    def test_parallel(self):
        stages = [WorkflowStage("layer01", 0), WorkflowStage("layer02", 1)]
        results = self.controller.execute_parallel(stages, lambda l: {"ok": True})
        assert len(results) == 2
        assert all(s.status == "completed" for s in results)

    def test_conditional_skip(self):
        stage = WorkflowStage("layer01")
        result = self.controller.execute_conditional(
            stage, lambda l: False, lambda l: {"ok": True})
        assert result.status == "skipped"

    def test_conditional_execute(self):
        stage = WorkflowStage("layer01")
        result = self.controller.execute_conditional(
            stage, lambda l: True, lambda l: {"ok": True})
        assert result.status == "completed"

    def test_retry_success(self):
        call_count = [0]
        def executor(layer):
            call_count[0] += 1
            if call_count[0] < 2:
                raise ValueError("transient")
            return {"ok": True}
        stage = WorkflowStage("layer01")
        result = self.controller.execute_with_retry(stage, executor, max_retries=3)
        assert result.status == "completed"
        assert result.retry_count == 1

    def test_retry_exhausted(self):
        def executor(layer):
            raise ValueError("permanent")
        stage = WorkflowStage("layer01")
        result = self.controller.execute_with_retry(stage, executor, max_retries=2)
        assert result.status == "failed"
        assert result.retry_count == 2

    def test_execution_stats(self):
        stages = [WorkflowStage("layer01", 0), WorkflowStage("layer02", 1)]
        self.controller.execute_sequential(stages, lambda l: {"ok": True})
        stats = self.controller.get_execution_stats()
        assert stats["total_executions"] == 2
        assert stats["successful"] == 2


# ─── StateManager Tests ───────────────────────────────────────────
class TestStateManager:
    def setup_method(self):
        self.manager = StateManager()

    def test_initial_state(self):
        assert self.manager.get_state() == "created"

    def test_set_state(self):
        result = self.manager.set_state("running")
        assert result is True
        assert self.manager.get_state() == "running"

    def test_invalid_state(self):
        result = self.manager.set_state("invalid")
        assert result is False

    def test_set_current_stage(self):
        self.manager.set_current_stage("layer04_writing")
        assert self.manager._current_stage == "layer04_writing"

    def test_complete_stage(self):
        self.manager.complete_stage("layer01")
        assert "layer01" in self.manager.get_completed_stages()

    def test_snapshot(self):
        self.manager.set_state("running")
        self.manager.set_current_stage("layer04_writing")
        snap = self.manager.snapshot()
        assert snap.state == "running"
        assert snap.current_stage == "layer04_writing"

    def test_restore(self):
        self.manager.set_state("running")
        snap = self.manager.snapshot()
        self.manager.set_state("paused")
        result = self.manager.restore(snap.snapshot_id)
        assert result is True
        assert self.manager.get_state() == "running"

    def test_restore_nonexistent(self):
        result = self.manager.restore("nonexistent")
        assert result is False

    def test_rollback(self):
        self.manager.set_state("running")
        self.manager.snapshot()
        self.manager.set_state("failed")
        result = self.manager.rollback()
        assert result is True
        assert self.manager.get_state() == "running"

    def test_get_history(self):
        self.manager.set_state("running")
        self.manager.set_state("paused")
        history = self.manager.get_history()
        assert len(history) == 2

    def test_reset(self):
        self.manager.set_state("running")
        self.manager.complete_stage("layer01")
        self.manager.reset()
        assert self.manager.get_state() == "created"
        assert len(self.manager.get_completed_stages()) == 0


# ─── SynchronizationManager Tests ─────────────────────────────────
class TestSynchronizationManager:
    def setup_method(self):
        self.sync = SynchronizationManager()

    def test_create_barrier(self):
        barrier = self.sync.create_barrier("b1", expected_count=3)
        assert barrier.expected_count == 3

    def test_arrive_at_barrier(self):
        self.sync.create_barrier("b1", expected_count=2)
        assert self.sync.arrive_at_barrier("b1") is False
        assert self.sync.arrive_at_barrier("b1") is True
        assert self.sync.is_barrier_released("b1") is True

    def test_acquire_lock(self):
        result = self.sync.acquire_lock("resource1", "worker1")
        assert result is True
        assert self.sync.is_locked("resource1") is True

    def test_lock_already_held(self):
        self.sync.acquire_lock("resource1", "worker1")
        result = self.sync.acquire_lock("resource1", "worker2")
        assert result is False

    def test_release_lock(self):
        self.sync.acquire_lock("resource1", "worker1")
        result = self.sync.release_lock("resource1")
        assert result is True
        assert self.sync.is_locked("resource1") is False

    def test_set_shared(self):
        self.sync.set_shared("key1", "value1")
        assert self.sync.get_shared("key1") == "value1"

    def test_get_shared_default(self):
        assert self.sync.get_shared("nonexistent", "default") == "default"

    def test_clear_shared(self):
        self.sync.set_shared("key1", "value1")
        self.sync.clear_shared()
        assert self.sync.get_shared("key1") is None

    def test_join_results(self):
        results = [{"a": 1}, {"b": 2}, {"c": 3}]
        merged = self.sync.join_results(results)
        assert merged == {"a": 1, "b": 2, "c": 3}

    def test_diagnostics(self):
        self.sync.create_barrier("b1", 2)
        self.sync.acquire_lock("l1")
        diag = self.sync.get_diagnostics()
        assert diag["barriers"] == 1
        assert diag["locks"] == 1

    def test_sync_lock_class(self):
        lock = SyncLock("test")
        assert lock.is_locked is False
        lock.acquire("owner")
        assert lock.is_locked is True
        lock.release()
        assert lock.is_locked is False


# ─── CheckpointManager Tests ──────────────────────────────────────
class TestCheckpointManager:
    def setup_method(self):
        self.manager = CheckpointManager()

    def test_create(self):
        cp = self.manager.create("wf1", "stage1", state={"key": "val"})
        assert cp.checkpoint_id.startswith("cp_")
        assert cp.workflow_id == "wf1"
        assert cp.state["key"] == "val"

    def test_restore(self):
        cp = self.manager.create("wf1", "stage1")
        restored = self.manager.restore(cp.checkpoint_id)
        assert restored is not None
        assert restored.checkpoint_id == cp.checkpoint_id

    def test_restore_nonexistent(self):
        result = self.manager.restore("nonexistent")
        assert result is None

    def test_get_latest(self):
        self.manager.create("wf1", "stage1")
        cp2 = self.manager.create("wf1", "stage2")
        latest = self.manager.get_latest("wf1")
        assert latest.checkpoint_id == cp2.checkpoint_id

    def test_delete(self):
        cp = self.manager.create("wf1", "stage1")
        result = self.manager.delete(cp.checkpoint_id)
        assert result is True
        assert self.manager.restore(cp.checkpoint_id) is None

    def test_delete_nonexistent(self):
        result = self.manager.delete("nonexistent")
        assert result is False

    def test_delete_workflow_checkpoints(self):
        self.manager.create("wf1", "s1")
        self.manager.create("wf1", "s2")
        self.manager.create("wf2", "s1")
        count = self.manager.delete_workflow_checkpoints("wf1")
        assert count == 2

    def test_get_all(self):
        self.manager.create("wf1", "s1")
        self.manager.create("wf2", "s1")
        all_cps = self.manager.get_all()
        assert len(all_cps) == 2

    def test_get_stats(self):
        self.manager.create("wf1", "s1")
        stats = self.manager.get_stats()
        assert stats["total"] == 1

    def test_max_checkpoints(self):
        mgr = CheckpointManager(max_checkpoints=3)
        for i in range(5):
            mgr.create("wf1", f"stage{i}")
        assert len(mgr.get_all()) == 3


# ─── WorkflowEventBus Tests ───────────────────────────────────────
class TestWorkflowEventBus:
    def setup_method(self):
        self.bus = WorkflowEventBus()

    def test_publish(self):
        event = WorkflowEvent(event_type="test", workflow_id="wf1")
        count = self.bus.publish(event)
        assert count == 0
        assert self.bus.get_event_count() == 1

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe("test", lambda e: received.append(e))
        event = WorkflowEvent(event_type="test", workflow_id="wf1")
        count = self.bus.publish(event)
        assert count == 1
        assert len(received) == 1

    def test_unsubscribe(self):
        handler = lambda e: None
        self.bus.subscribe("test", handler)
        result = self.bus.unsubscribe("test", handler)
        assert result is True

    def test_get_events_filtered(self):
        self.bus.publish(WorkflowEvent(event_type="a", workflow_id="wf1"))
        self.bus.publish(WorkflowEvent(event_type="b", workflow_id="wf2"))
        self.bus.publish(WorkflowEvent(event_type="a", workflow_id="wf1"))
        events = self.bus.get_events(event_type="a")
        assert len(events) == 2

    def test_get_events_by_workflow(self):
        self.bus.publish(WorkflowEvent(event_type="a", workflow_id="wf1"))
        self.bus.publish(WorkflowEvent(event_type="a", workflow_id="wf2"))
        events = self.bus.get_events(workflow_id="wf1")
        assert len(events) == 1

    def test_event_to_dict(self):
        event = WorkflowEvent(event_type="test", workflow_id="wf1")
        d = event.to_dict()
        assert "event_id" in d
        assert "event_type" in d


# ─── WorkflowMetrics Tests ────────────────────────────────────────
class TestWorkflowMetrics:
    def setup_method(self):
        self.metrics = WorkflowMetrics()

    def test_record_run(self):
        self.metrics.record_run(success=True, duration_ms=100, retries=1)
        assert self.metrics._total_runs == 1

    def test_record_run_failure(self):
        self.metrics.record_run(success=False)
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
        self.metrics.record_run(retries=2)
        self.metrics.record_run(retries=4)
        assert self.metrics.get_avg_retries() == 3.0

    def test_record_stage(self):
        self.metrics.record_stage("layer01", 100, success=True)
        assert self.metrics.get_stage_avg_duration("layer01") == 100.0

    def test_record_stage_failure(self):
        self.metrics.record_stage("layer01", 100, success=False)
        assert self.metrics.get_failed_stages()["layer01"] == 1

    def test_summary(self):
        self.metrics.record_run(success=True, duration_ms=100)
        summary = self.metrics.get_summary()
        assert "total_runs" in summary
        assert "success_rate" in summary

    def test_reset(self):
        self.metrics.record_run(success=True)
        self.metrics.reset()
        assert self.metrics._total_runs == 0


# ─── WorkflowReport Tests ─────────────────────────────────────────
class TestWorkflowReport:
    def setup_method(self):
        self.report = WorkflowReport(workflow_id="wf1", name="test")

    def test_create(self):
        assert self.report.report_id.startswith("wrep_")
        assert self.report.workflow_id == "wf1"
        assert self.report.success is True

    def test_add_stage_completed(self):
        self.report.add_stage("s1", "layer01", "completed", duration_ms=50)
        assert "layer01" in self.report.stages_executed
        assert self.report.success is True

    def test_add_stage_failed(self):
        self.report.add_stage("s1", "layer01", "failed", error="API error")
        assert "layer01" in self.report.stages_failed
        assert self.report.success is False

    def test_add_warning(self):
        self.report.add_warning("slow response")
        assert len(self.report.warnings) == 1

    def test_add_recommendation(self):
        self.report.add_recommendation("optimize hooks")
        assert len(self.report.recommendations) == 1

    def test_get_summary(self):
        self.report.add_stage("s1", "layer01", "completed")
        summary = self.report.get_summary()
        assert "report_id" in summary
        assert summary["stages_executed"] == 1

    def test_export_dict(self):
        self.report.add_stage("s1", "layer01", "completed")
        d = self.report.export_dict()
        assert "stage_details" in d
        assert "warnings" in d


# ─── WorkflowCoordinator Tests ────────────────────────────────────
class TestWorkflowCoordinator:
    def setup_method(self):
        self.coordinator = WorkflowCoordinator()

    def test_start(self):
        wd = WorkflowDefinition("test", ["layer01", "layer02"])
        wf_id = self.coordinator.start(wd)
        assert wf_id.startswith("wfdef_")
        assert self.coordinator.get_state() == "running"

    def test_execute(self):
        wd = WorkflowDefinition("test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        report = self.coordinator.execute(lambda l: {"ok": True})
        assert report.success is True
        assert len(report.stages_executed) > 0

    def test_execute_no_workflow(self):
        try:
            self.coordinator.execute(lambda l: {"ok": True})
            assert False
        except ValueError:
            pass

    def test_execute_with_handler(self):
        wd = WorkflowDefinition("test", ["layer04_writing"])
        self.coordinator.start(wd)
        report = self.coordinator.execute(lambda l: {"draft": "content"})
        assert report.success is True

    def test_execute_with_failure(self):
        def executor(layer):
            if layer == "layer02":
                raise ValueError("fail")
            return {"ok": True}
        wd = WorkflowDefinition("test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        report = self.coordinator.execute(executor)
        assert report.success is False

    def test_pause(self):
        wd = WorkflowDefinition("test", ["layer01"])
        self.coordinator.start(wd)
        result = self.coordinator.pause()
        assert result is True
        assert self.coordinator.get_state() == "paused"

    def test_resume(self):
        wd = WorkflowDefinition("test", ["layer01"])
        self.coordinator.start(wd)
        self.coordinator.pause()
        result = self.coordinator.resume()
        assert result is True

    def test_cancel(self):
        wd = WorkflowDefinition("test", ["layer01"])
        self.coordinator.start(wd)
        result = self.coordinator.cancel()
        assert result is True
        assert self.coordinator.get_state() == "cancelled"

    def test_get_stage_status(self):
        wd = WorkflowDefinition("test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        status = self.coordinator.get_stage_status()
        assert len(status) == 2

    def test_get_health(self):
        wd = WorkflowDefinition("test", ["layer01"])
        self.coordinator.start(wd)
        health = self.coordinator.get_health()
        assert "state" in health
        assert "stages" in health

    def test_get_recent_reports(self):
        wd = WorkflowDefinition("test", ["layer01"])
        for _ in range(3):
            self.coordinator.start(wd)
            self.coordinator.execute(lambda l: {"ok": True})
        reports = self.coordinator.get_recent_reports(2)
        assert len(reports) == 2

    def test_parallel_execution(self):
        wd = WorkflowDefinition("test", ["layer01", "layer02", "layer03"])
        self.coordinator.start(wd)
        report = self.coordinator.execute(
            lambda l: {"ok": True},
            parallel_stages=["layer01", "layer02"],
        )
        assert report.success is True

    def test_event_bus_tracking(self):
        wd = WorkflowDefinition("test", ["layer01"])
        self.coordinator.start(wd)
        self.coordinator.execute(lambda l: {"ok": True})
        events = self.coordinator.event_bus.get_events()
        assert len(events) > 0

    def test_checkpoint_created(self):
        wd = WorkflowDefinition("test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        self.coordinator.execute(lambda l: {"ok": True})
        cps = self.coordinator.checkpoint_manager.get_all(wd.workflow_id)
        assert len(cps) > 0


# ─── Integration Tests ────────────────────────────────────────────
class TestWorkflowCoordinatorIntegration:
    def setup_method(self):
        self.coordinator = WorkflowCoordinator()

    def test_full_workflow(self):
        wd = WorkflowDefinition("content_pipeline", [
            "layer01_core", "layer02_research", "layer03_intelligence",
            "layer04_writing", "layer06_quality", "layer07_publishing",
        ])
        self.coordinator.start(wd)
        report = self.coordinator.execute(lambda l: {"result": "ok", "layer": l})
        assert report.success is True
        assert len(report.stages_executed) >= 4
        assert report.total_duration_ms > 0

    def test_workflow_with_dependencies(self):
        wd = WorkflowDefinition("dep_test", ["s1", "s2", "s3"])
        wd.dependencies["s2"] = ["s1"]
        wd.dependencies["s3"] = ["s2"]
        self.coordinator.start(wd)
        report = self.coordinator.execute(lambda l: {"ok": True})
        assert report.success is True

    def test_workflow_with_failures_and_recovery(self):
        call_count = [0]
        def executor(layer):
            call_count[0] += 1
            if layer == "layer02" and call_count[0] <= 3:
                raise ValueError("transient error")
            return {"ok": True}

        wd = WorkflowDefinition("retry_test", ["layer01", "layer02", "layer03"])
        self.coordinator.start(wd)
        report = self.coordinator.execute(executor)
        assert report.success is True

    def test_cancel_and_check_state(self):
        wd = WorkflowDefinition("cancel_test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        self.coordinator.cancel()
        assert self.coordinator.get_state() == "cancelled"

    def test_pause_resume_continue(self):
        wd = WorkflowDefinition("pause_test", ["layer01", "layer02"])
        self.coordinator.start(wd)
        self.coordinator.pause()
        assert self.coordinator.get_state() == "paused"
        self.coordinator.resume()
        assert self.coordinator.get_state() == "running"

    def test_metrics_tracking(self):
        wd = WorkflowDefinition("metrics_test", ["layer01", "layer02"])
        for _ in range(3):
            self.coordinator.start(wd)
            self.coordinator.execute(lambda l: {"ok": True})
        metrics = self.coordinator.metrics.get_summary()
        assert metrics["total_runs"] == 3

    def test_event_bus_full_lifecycle(self):
        wd = WorkflowDefinition("event_test", ["layer01"])
        self.coordinator.start(wd)
        self.coordinator.execute(lambda l: {"ok": True})
        events = self.coordinator.event_bus.get_events()
        event_types = [e.event_type for e in events]
        assert "workflow_started" in event_types
        assert "workflow_completed" in event_types


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
