"""Comprehensive tests for Layer 23 — Module 11: Scheduler & Workflow Orchestrator."""
from __future__ import annotations
import time
import pytest
from typing import Any, Dict, List

from layers.layer23_website_manager.scheduler_orchestrator.scheduler_orchestrator import (
    SchedulerOrchestrator, get_scheduler,
)
from layers.layer23_website_manager.scheduler_orchestrator.models.scheduler_models import (
    WorkflowDefinition, WorkflowStep, ScheduledJob, JobStatus, WorkflowStatus,
    Priority, QueueItem, WorkflowResult, ExecutionLog, EventRecord, Notification,
    ResourceMetrics, WorkflowAnalytics, Dependency,
)
from layers.layer23_website_manager.scheduler_orchestrator.workflow.workflow_manager import (
    WorkflowManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.scheduler.task_scheduler import (
    TaskScheduler,
)
from layers.layer23_website_manager.scheduler_orchestrator.queue.job_queue_manager import (
    JobQueueManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.dependencies.dependency_manager import (
    DependencyManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.executor.workflow_executor import (
    WorkflowExecutor,
)
from layers.layer23_website_manager.scheduler_orchestrator.retry.retry_manager import (
    RetryManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.resources.resource_manager import (
    ResourceManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.events.event_manager import (
    EventManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.notifications.notification_manager import (
    NotificationManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.monitoring.monitoring_manager import (
    MonitoringManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.recovery.recovery_manager import (
    RecoveryManager,
)
from layers.layer23_website_manager.scheduler_orchestrator.analytics.workflow_analytics import (
    WorkflowAnalyticsCollector,
)
from layers.layer23_website_manager.scheduler_orchestrator.api.orchestrator_api import (
    OrchestratorAPI,
)
from layers.layer23_website_manager.scheduler_orchestrator.exceptions import (
    SchedulerError, WorkflowError, SchedulingError, QueueError, DependencyError,
    ExecutionError, RetryError, RecoveryError, MonitoringError,
)


# ══════════════════════════════════════════════════════════════════════
# Models Tests
# ══════════════════════════════════════════════════════════════════════

class TestModels:
    def test_workflow_step(self):
        step = WorkflowStep(name="Research", module="research", action="gather")
        assert step.step_id.startswith("step_")
        assert step.name == "Research"
        assert step.module == "research"
        assert step.depends_on == []
        assert step.status == "pending"
        d = step.to_dict()
        assert d["name"] == "Research"

    def test_workflow_step_with_deps(self):
        step = WorkflowStep(name="Write", module="writing", action="generate",
                            depends_on=["step_abc"], timeout=600, max_retries=5)
        assert "step_abc" in step.depends_on
        assert step.timeout == 600
        assert step.max_retries == 5

    def test_workflow_definition(self):
        wf = WorkflowDefinition(name="Test WF", description="A test workflow")
        assert wf.workflow_id.startswith("wf_")
        assert wf.status == WorkflowStatus.DRAFT
        assert wf.priority == Priority.NORMAL
        d = wf.to_dict()
        assert d["name"] == "Test WF"
        assert d["description"] == "A test workflow"

    def test_workflow_add_step(self):
        wf = WorkflowDefinition(name="Test")
        step = WorkflowStep(name="S1", module="m", action="a")
        wf.add_step(step)
        assert len(wf.steps) == 1
        assert wf.steps[0].name == "S1"

    def test_scheduled_job(self):
        job = ScheduledJob(workflow_id="wf_123", name="Test Job")
        assert job.job_id.startswith("job_")
        assert job.status == JobStatus.PENDING
        assert job.is_due is True  # scheduled_time is now by default
        assert job.duration_ms == 0.0
        d = job.to_dict()
        assert d["workflow_id"] == "wf_123"

    def test_scheduled_job_is_due_false(self):
        job = ScheduledJob(workflow_id="wf_1", scheduled_time=time.time() + 3600)
        assert job.is_due is False

    def test_scheduled_job_duration(self):
        job = ScheduledJob(workflow_id="wf_1")
        job.started_time = time.time() - 1.0
        job.completed_time = time.time()
        assert job.duration_ms > 0

    def test_queue_item(self):
        job = ScheduledJob(workflow_id="wf_1")
        qi = QueueItem(job=job, priority=Priority.HIGH)
        assert qi.item_id.startswith("qi_")
        assert qi.priority == Priority.HIGH

    def test_workflow_result(self):
        wr = WorkflowResult(workflow_id="wf_1", job_id="job_1")
        assert wr.status == "unknown"
        wr.complete("completed")
        assert wr.status == "completed"
        assert wr.duration_ms > 0
        d = wr.to_dict()
        assert d["status"] == "completed"

    def test_execution_log(self):
        log = ExecutionLog(job_id="job_1", workflow_id="wf_1",
                           step_name="Research", module="research", action="gather")
        assert log.log_id.startswith("log_")
        assert log.status == "pending"
        d = log.to_dict()
        assert d["step_name"] == "Research"

    def test_event_record(self):
        evt = EventRecord(event_type="workflow_completed", source="executor",
                          data={"status": "ok"})
        assert evt.event_id.startswith("evt_")
        assert evt.event_type == "workflow_completed"
        d = evt.to_dict()
        assert d["data"]["status"] == "ok"

    def test_notification(self):
        n = Notification(title="Test Alert", message="Something happened",
                         level="warning", source="monitor")
        assert n.notification_id.startswith("notif_")
        assert n.read is False
        d = n.to_dict()
        assert d["level"] == "warning"

    def test_resource_metrics(self):
        rm = ResourceMetrics(cpu_percent=45.5, memory_mb=512.0,
                              workers_active=5, workers_idle=3)
        assert rm.cpu_percent == 45.5
        d = rm.to_dict()
        assert d["workers_active"] == 5

    def test_workflow_analytics(self):
        wa = WorkflowAnalytics()
        assert wa.total_jobs == 0
        assert wa.success_rate == 100.0

    def test_dependency(self):
        dep = Dependency(source_step="step_a", target_step="step_b",
                         condition="completed", timeout=300)
        assert dep.dependency_id.startswith("dep_")
        assert dep.source_step == "step_a"
        assert dep.target_step == "step_b"


# ══════════════════════════════════════════════════════════════════════
# WorkflowManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestWorkflowManager:
    def setup_method(self):
        self.mgr = WorkflowManager()

    def test_create_workflow(self):
        wf = self.mgr.create_workflow("Test WF", "Description")
        assert wf.name == "Test WF"
        assert len(self.mgr.get_all_workflows()) == 1

    def test_get_workflow(self):
        wf = self.mgr.create_workflow("Get Test")
        assert self.mgr.get_workflow(wf.workflow_id) is wf
        assert self.mgr.get_workflow("nonexistent") is None

    def test_update_workflow(self):
        wf = self.mgr.create_workflow("Orig")
        assert self.mgr.update_workflow(wf.workflow_id, name="Updated") is True
        assert self.mgr.get_workflow(wf.workflow_id).name == "Updated"
        assert self.mgr.update_workflow("bad_id", name="X") is False

    def test_delete_workflow(self):
        wf = self.mgr.create_workflow("Del")
        assert self.mgr.delete_workflow(wf.workflow_id) is True
        assert len(self.mgr.get_all_workflows()) == 0
        assert self.mgr.delete_workflow("bad") is False

    def test_activate_pause(self):
        wf = self.mgr.create_workflow("AP")
        assert self.mgr.activate_workflow(wf.workflow_id) is True
        assert wf.status == WorkflowStatus.ACTIVE
        assert self.mgr.pause_workflow(wf.workflow_id) is True
        assert wf.status == WorkflowStatus.PAUSED
        assert self.mgr.activate_workflow("bad") is False
        assert self.mgr.pause_workflow("bad") is False

    def test_add_remove_step(self):
        wf = self.mgr.create_workflow("Steps")
        step = WorkflowStep(name="S1", module="m", action="a")
        assert self.mgr.add_step(wf.workflow_id, step) is True
        assert len(wf.steps) == 1
        assert self.mgr.add_step("bad", step) is False
        assert self.mgr.remove_step(wf.workflow_id, step.step_id) is True
        assert len(wf.steps) == 0
        assert self.mgr.remove_step("bad", step.step_id) is False

    def test_get_workflows_by_tag(self):
        self.mgr.create_workflow("A", tags=["publishing"])
        self.mgr.create_workflow("B", tags=["analytics"])
        assert len(self.mgr.get_workflows_by_tag("publishing")) == 1
        assert len(self.mgr.get_workflows_by_tag("unknown")) == 0

    def test_get_stats(self):
        wf = self.mgr.create_workflow("Stats")
        step = WorkflowStep(name="S1", module="m", action="a")
        wf.add_step(step)
        self.mgr.activate_workflow(wf.workflow_id)
        stats = self.mgr.get_stats()
        assert stats["total"] == 1
        assert stats["active"] == 1
        assert stats["total_steps"] == 1


# ══════════════════════════════════════════════════════════════════════
# TaskScheduler Tests
# ══════════════════════════════════════════════════════════════════════

class TestTaskScheduler:
    def setup_method(self):
        self.sched = TaskScheduler()

    def test_schedule_job(self):
        job = self.sched.schedule_job(workflow_id="wf_1", name="Job1")
        assert job.workflow_id == "wf_1"
        assert len(self.sched.get_all_jobs()) == 1

    def test_schedule_with_delay(self):
        job = self.sched.schedule_job(workflow_id="wf_1", delay_seconds=60)
        assert job.scheduled_time > time.time()

    def test_cancel_job(self):
        job = self.sched.schedule_job(workflow_id="wf_1")
        assert self.sched.cancel_job(job.job_id) is True
        assert job.status == JobStatus.CANCELLED
        assert self.sched.cancel_job("bad") is False

    def test_pause_resume_job(self):
        job = self.sched.schedule_job(workflow_id="wf_1")
        assert self.sched.pause_job(job.job_id) is True
        assert job.status == JobStatus.PAUSED
        assert self.sched.resume_job(job.job_id) is True
        assert job.status == JobStatus.PENDING
        # Cannot pause non-pending job
        self.sched.mark_running(job.job_id)
        assert self.sched.pause_job(job.job_id) is False
        assert self.sched.pause_job("bad") is False
        assert self.sched.resume_job("bad") is False

    def test_get_due_jobs(self):
        self.sched.schedule_job(workflow_id="wf_1")  # due now
        self.sched.schedule_job(workflow_id="wf_2", delay_seconds=3600)  # not due
        due = self.sched.get_due_jobs()
        assert len(due) == 1

    def test_get_job(self):
        job = self.sched.schedule_job(workflow_id="wf_1")
        assert self.sched.get_job(job.job_id) is job
        assert self.sched.get_job("bad") is None

    def test_get_jobs_by_status(self):
        self.sched.schedule_job(workflow_id="wf_1")
        assert len(self.sched.get_jobs_by_status(JobStatus.PENDING)) == 1
        assert len(self.sched.get_jobs_by_status(JobStatus.COMPLETED)) == 0

    def test_get_jobs_by_workflow(self):
        self.sched.schedule_job(workflow_id="wf_a")
        self.sched.schedule_job(workflow_id="wf_b")
        assert len(self.sched.get_jobs_by_workflow("wf_a")) == 1

    def test_mark_running_completed_failed(self):
        job = self.sched.schedule_job(workflow_id="wf_1")
        assert self.sched.mark_running(job.job_id) is True
        assert job.status == JobStatus.RUNNING
        assert job.started_time is not None
        assert self.sched.mark_completed(job.job_id) is True
        assert job.status == JobStatus.COMPLETED
        # Reset
        job2 = self.sched.schedule_job(workflow_id="wf_2")
        assert self.sched.mark_failed(job2.job_id, "Error!") is True
        assert job2.status == JobStatus.FAILED
        assert "Error!" in job2.error
        assert self.sched.mark_running("bad") is False

    def test_get_stats(self):
        self.sched.schedule_job(workflow_id="wf_1")
        self.sched.schedule_job(workflow_id="wf_2", delay_seconds=3600)
        job3 = self.sched.schedule_job(workflow_id="wf_3")
        self.sched.mark_completed(job3.job_id)
        stats = self.sched.get_stats()
        assert stats["total"] == 3
        assert stats["pending"] == 2
        assert stats["completed"] == 1


# ══════════════════════════════════════════════════════════════════════
# JobQueueManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestJobQueueManager:
    def setup_method(self):
        self.qm = JobQueueManager()

    def test_enqueue_dequeue(self):
        job = ScheduledJob(workflow_id="wf_1")
        item_id = self.qm.enqueue(job)
        assert item_id.startswith("qi_")
        dequeued = self.qm.dequeue()
        assert dequeued is job

    def test_dequeue_empty(self):
        assert self.qm.dequeue() is None

    def test_priority_ordering(self):
        low_job = ScheduledJob(workflow_id="low")
        high_job = ScheduledJob(workflow_id="high")
        self.qm.enqueue(low_job, Priority.LOW)
        self.qm.enqueue(high_job, Priority.HIGH)
        # HIGH should be dequeued first
        first = self.qm.dequeue()
        assert first is high_job
        second = self.qm.dequeue()
        assert second is low_job

    def test_retry_queue(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.qm.enqueue_retry(job)
        assert self.qm.dequeue_retry() is job
        assert self.qm.dequeue_retry() is None

    def test_mark_failed_completed(self):
        job1 = ScheduledJob(workflow_id="wf_1")
        job2 = ScheduledJob(workflow_id="wf_2")
        self.qm.mark_failed(job1)
        self.qm.mark_completed(job2)
        sizes = self.qm.get_queue_sizes()
        assert sizes["failed"] == 1
        assert sizes["completed"] == 1

    def test_clear_completed(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.qm.mark_completed(job)
        assert self.qm.clear_completed() == 1
        assert self.qm.clear_completed() == 0

    def test_get_stats(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.qm.enqueue(job, Priority.CRITICAL)
        stats = self.qm.get_stats()
        assert stats["critical"] == 1
        assert stats["total_active"] == 1


# ══════════════════════════════════════════════════════════════════════
# DependencyManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestDependencyManager:
    def setup_method(self):
        self.dm = DependencyManager()

    def test_add_remove_dependency(self):
        dep = self.dm.add_dependency("step_a", "step_b")
        assert dep.dependency_id.startswith("dep_")
        assert self.dm.remove_dependency(dep.dependency_id) is True
        assert self.dm.remove_dependency("bad") is False

    def test_get_dependencies(self):
        self.dm.add_dependency("a", "b")
        self.dm.add_dependency("a", "c")
        assert len(self.dm.get_dependencies_for("b")) == 1
        assert len(self.dm.get_dependencies_for("c")) == 1
        assert len(self.dm.get_dependents_of("a")) == 2

    def test_can_execute(self):
        step_a = WorkflowStep(name="A", module="m", action="a")
        step_b = WorkflowStep(name="B", module="m", action="a")
        self.dm.add_dependency(step_a.step_id, step_b.step_id)
        assert self.dm.can_execute(step_b, set(), set()) is False
        assert self.dm.can_execute(step_b, {step_a.step_id}, set()) is True
        assert self.dm.can_execute(step_b, set(), {step_a.step_id}) is False

    def test_optional_dependency(self):
        self.dm.add_dependency("step_a", "step_b", optional=True)
        step_b = WorkflowStep(name="B", module="m", action="a")
        assert self.dm.can_execute(step_b, set(), set()) is True

    def test_get_ready_steps(self):
        step_a = WorkflowStep(name="A", module="m", action="a")
        step_b = WorkflowStep(name="B", module="m", action="b")
        self.dm.add_dependency(step_a.step_id, step_b.step_id)
        steps = [step_a, step_b]
        ready = self.dm.get_ready_steps(steps, set(), set())
        assert len(ready) == 1
        assert ready[0] is step_a

    def test_validate_workflow(self):
        step = WorkflowStep(name="A", module="m", action="a")
        self.dm.add_dependency("nonexistent", step.step_id)
        errors = self.dm.validate_workflow([step])
        assert len(errors) > 0
        assert "nonexistent" in errors[0]

    def test_validate_circular(self):
        step_a = WorkflowStep(name="A", module="m", action="a")
        step_b = WorkflowStep(name="B", module="m", action="b")
        self.dm.add_dependency(step_a.step_id, step_b.step_id)
        self.dm.add_dependency(step_b.step_id, step_a.step_id)
        errors = self.dm.validate_workflow([step_a, step_b])
        assert any("Circular" in e for e in errors)

    def test_get_stats(self):
        self.dm.add_dependency("a", "b")
        self.dm.add_dependency("c", "d", optional=True)
        stats = self.dm.get_stats()
        assert stats["total"] == 2
        assert stats["optional"] == 1


# ══════════════════════════════════════════════════════════════════════
# WorkflowExecutor Tests
# ══════════════════════════════════════════════════════════════════════

class TestWorkflowExecutor:
    def setup_method(self):
        self.exec = WorkflowExecutor()
        self.dm = DependencyManager()

    def test_execute_empty_workflow(self):
        wf = WorkflowDefinition(name="Empty")
        self.dm.add_dependency("nonexistent", "nonexistent2")
        result = self.exec.execute(wf, self.dm)
        assert result.status == "completed"

    def test_execute_single_step(self):
        wf = WorkflowDefinition(name="Single")
        step = WorkflowStep(name="S1", module="m", action="a")
        wf.add_step(step)
        result = self.exec.execute(wf, self.dm)
        assert result.status == "completed"
        assert step.status == "completed"

    def test_execute_with_handler(self):
        wf = WorkflowDefinition(name="Handler")
        step = WorkflowStep(name="S1", module="m", action="custom")
        wf.add_step(step)
        self.exec.register_handler("custom",
                                    lambda s, ctx: {"custom_result": True})
        result = self.exec.execute(wf, self.dm)
        assert result.status == "completed"
        assert step.result.get("custom_result") is True

    def test_execute_ordered_steps(self):
        wf = WorkflowDefinition(name="Ordered")
        s1 = WorkflowStep(name="First", module="m", action="first")
        s2 = WorkflowStep(name="Second", module="m", action="second",
                          depends_on=[s1.step_id])
        self.dm.add_dependency(s1.step_id, s2.step_id)
        wf.add_step(s1)
        wf.add_step(s2)
        result = self.exec.execute(wf, self.dm)
        assert result.status == "completed"

    def test_execute_batch(self):
        wf1 = WorkflowDefinition(name="Batch1")
        wf1.add_step(WorkflowStep(name="S1", module="m", action="a"))
        wf2 = WorkflowDefinition(name="Batch2")
        wf2.add_step(WorkflowStep(name="S2", module="m", action="b"))
        results = self.exec.execute_batch([wf1, wf2], self.dm)
        assert len(results) == 2

    def test_get_execution_logs(self):
        wf = WorkflowDefinition(name="Logs")
        wf.add_step(WorkflowStep(name="S1", module="m", action="a"))
        self.exec.execute(wf, self.dm)
        logs = self.exec.get_execution_logs()
        assert len(logs) >= 1

    def test_get_active_executions(self):
        assert self.exec.get_active_executions() == 0

    def test_get_stats(self):
        wf = WorkflowDefinition(name="Stats")
        wf.add_step(WorkflowStep(name="S1", module="m", action="a"))
        self.exec.execute(wf, self.dm)
        stats = self.exec.get_stats()
        assert stats["total_executions"] >= 1
        assert stats["completed"] >= 1


# ══════════════════════════════════════════════════════════════════════
# RetryManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestRetryManager:
    def setup_method(self):
        self.rm = RetryManager()

    def test_should_retry(self):
        job = ScheduledJob(workflow_id="wf_1", max_retries=3)
        assert self.rm.should_retry(job) is True
        job.retry_count = 3
        assert self.rm.should_retry(job) is False

    def test_calculate_backoff(self):
        delay = self.rm.calculate_backoff(0, 5.0)
        assert delay >= 5.0
        delay2 = self.rm.calculate_backoff(2, 5.0)
        assert delay2 >= 20.0

    def test_record_retry(self):
        job = ScheduledJob(workflow_id="wf_1", max_retries=3)
        entry = self.rm.record_retry(job, "error msg")
        assert entry["retry"] == 1
        assert job.retry_count == 1

    def test_retry_history(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.rm.record_retry(job)
        self.rm.record_retry(job)
        history = self.rm.get_retry_history(job.job_id)
        assert len(history) == 2

    def test_reset_retries(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.rm.record_retry(job)
        assert self.rm.reset_retries(job.job_id) is True
        assert len(self.rm.get_retry_history(job.job_id)) == 0
        assert self.rm.reset_retries("bad") is False

    def test_get_stats(self):
        job = ScheduledJob(workflow_id="wf_1")
        self.rm.record_retry(job)
        stats = self.rm.get_stats()
        assert stats["total_retries"] == 1
        assert stats["jobs_with_retries"] == 1


# ══════════════════════════════════════════════════════════════════════
# ResourceManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestResourceManager:
    def setup_method(self):
        self.rsrc = ResourceManager(max_workers=5, max_queue_size=100)

    def test_acquire_release(self):
        assert self.rsrc.acquire_worker() is True
        assert self.rsrc._active_workers == 1
        self.rsrc.release_worker()
        assert self.rsrc._active_workers == 0

    def test_max_workers(self):
        for _ in range(5):
            assert self.rsrc.acquire_worker() is True
        assert self.rsrc.acquire_worker() is False  # max reached

    def test_get_metrics(self):
        self.rsrc.acquire_worker()
        metrics = self.rsrc.get_metrics()
        assert metrics.workers_active == 1
        assert metrics.workers_idle == 4

    def test_get_stats(self):
        stats = self.rsrc.get_stats()
        assert stats["max_workers"] == 5
        assert stats["max_queue_size"] == 100

    def test_max_workers_setter(self):
        self.rsrc.max_workers = 20
        assert self.rsrc.max_workers == 20


# ══════════════════════════════════════════════════════════════════════
# EventManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestEventManager:
    def setup_method(self):
        self.em = EventManager()

    def test_emit(self):
        evt = self.em.emit("test_event", "test_source", {"key": "val"})
        assert evt.event_type == "test_event"
        assert len(self.em.get_events()) == 1

    def test_register_handler(self):
        handled = []
        def handler(evt):
            handled.append(evt)
        self.em.register_handler("custom", handler)
        self.em.emit("custom", "src")
        assert len(handled) == 1

    def test_unregister_handler(self):
        def handler(evt):
            pass
        self.em.register_handler("test", handler)
        assert self.em.unregister_handler("test", handler) is True
        assert self.em.unregister_handler("test", handler) is False

    def test_get_events_filtered(self):
        self.em.emit("type_a")
        self.em.emit("type_b")
        self.em.emit("type_a")
        assert len(self.em.get_events("type_a")) == 2
        assert len(self.em.get_events("type_b")) == 1

    def test_clear_events(self):
        self.em.emit("test")
        assert self.em.clear_events() == 1
        assert len(self.em.get_events()) == 0

    def test_get_stats(self):
        self.em.emit("evt_a")
        self.em.emit("evt_a")
        self.em.emit("evt_b")
        stats = self.em.get_stats()
        assert stats["total_events"] == 3
        assert stats["event_types"]["evt_a"] == 2


# ══════════════════════════════════════════════════════════════════════
# NotificationManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestNotificationManager:
    def setup_method(self):
        self.nm = NotificationManager()

    def test_send(self):
        n = self.nm.send("Title", "Message", "warning", "src")
        assert n.title == "Title"
        assert n.level == "warning"

    def test_unread(self):
        self.nm.send("T1", "M1")
        self.nm.send("T2", "M2")
        assert len(self.nm.get_unread()) == 2

    def test_mark_read(self):
        n = self.nm.send("Test", "Msg")
        assert self.nm.mark_read(n.notification_id) is True
        assert n.read is True
        assert self.nm.mark_read("bad") is False

    def test_mark_all_read(self):
        self.nm.send("A", "a")
        self.nm.send("B", "b")
        assert self.nm.mark_all_read() == 2
        assert len(self.nm.get_unread()) == 0

    def test_get_all(self):
        self.nm.send("A", "a")
        self.nm.send("B", "b")
        assert len(self.nm.get_all()) == 2

    def test_register_channel(self):
        received = []
        def channel(n):
            received.append(n)
        self.nm.register_channel(channel)
        self.nm.send("Test", "Msg")
        assert len(received) == 1

    def test_get_stats(self):
        self.nm.send("Info", "Info msg", "info")
        self.nm.send("Warn", "Warn msg", "warning")
        stats = self.nm.get_stats()
        assert stats["total"] == 2
        assert stats["by_level"]["info"] == 1
        assert stats["by_level"]["warning"] == 1


# ══════════════════════════════════════════════════════════════════════
# MonitoringManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestMonitoringManager:
    def setup_method(self):
        self.mm = MonitoringManager()

    def test_record_metrics(self):
        m = ResourceMetrics(cpu_percent=50.0, memory_mb=256.0)
        self.mm.record_metrics(m)
        assert self.mm.get_latest_metrics() is m

    def test_get_metrics_history(self):
        self.mm.record_metrics(ResourceMetrics(cpu_percent=10))
        self.mm.record_metrics(ResourceMetrics(cpu_percent=20))
        history = self.mm.get_metrics_history()
        assert len(history) == 2

    def test_check_health_healthy(self):
        self.mm.record_metrics(ResourceMetrics(cpu_percent=30, memory_mb=256))
        health = self.mm.check_health({"completed": 10, "failed": 0})
        assert health["status"] == "healthy"

    def test_check_health_cpu_warning(self):
        self.mm.record_metrics(ResourceMetrics(cpu_percent=85, memory_mb=256))
        health = self.mm.check_health({})
        assert health["status"] == "warning"

    def test_check_health_cpu_critical(self):
        self.mm.record_metrics(ResourceMetrics(cpu_percent=96, memory_mb=256))
        health = self.mm.check_health({})
        assert health["status"] == "critical"

    def test_check_health_failure_rate(self):
        self.mm.record_metrics(ResourceMetrics(cpu_percent=30, memory_mb=256))
        health = self.mm.check_health({"completed": 5, "failed": 5})
        assert health["status"] == "warning"

    def test_get_stats(self):
        self.mm.record_metrics(ResourceMetrics())
        stats = self.mm.get_stats()
        assert stats["metrics_records"] == 1


# ══════════════════════════════════════════════════════════════════════
# RecoveryManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestRecoveryManager:
    def setup_method(self):
        self.rec = RecoveryManager()

    def test_recover_running_job(self):
        job = ScheduledJob(workflow_id="wf_1")
        job.status = JobStatus.RUNNING
        assert self.rec.recover_job(job) is True
        assert job.status == JobStatus.PENDING
        assert job.retry_count == 1

    def test_recover_failed_job(self):
        job = ScheduledJob(workflow_id="wf_1")
        job.status = JobStatus.FAILED
        assert self.rec.recover_job(job) is True

    def test_recover_pending_job(self):
        job = ScheduledJob(workflow_id="wf_1")
        # Pending jobs should not be recovered
        assert self.rec.recover_job(job) is False

    def test_recover_all_failed(self):
        jobs = []
        for i in range(3):
            j = ScheduledJob(workflow_id="wf_1")
            j.status = JobStatus.FAILED
            jobs.append(j)
        assert self.rec.recover_all_failed(jobs) == 3

    def test_get_recovery_history(self):
        job = ScheduledJob(workflow_id="wf_1")
        job.status = JobStatus.FAILED
        self.rec.recover_job(job)
        history = self.rec.get_recovery_history()
        assert len(history) == 1
        assert history[0]["action"] == "recovered"

    def test_get_stats(self):
        job = ScheduledJob(workflow_id="wf_1")
        job.status = JobStatus.FAILED
        self.rec.recover_job(job)
        stats = self.rec.get_stats()
        assert stats["total_recoveries"] == 1


# ══════════════════════════════════════════════════════════════════════
# WorkflowAnalyticsCollector Tests
# ══════════════════════════════════════════════════════════════════════

class TestWorkflowAnalyticsCollector:
    def setup_method(self):
        self.wa = WorkflowAnalyticsCollector()

    def test_record_execution(self):
        log = ExecutionLog(job_id="j1", workflow_id="w1",
                           step_name="S1", module="m", action="a")
        self.wa.record_execution(log)
        stats = self.wa.get_stats()
        assert stats["total_jobs"] == 1

    def test_get_analytics(self):
        log1 = ExecutionLog(job_id="j1", workflow_id="w1",
                            step_name="S1", module="m", action="a")
        log1.status = "completed"
        log1.duration_ms = 100.0
        log2 = ExecutionLog(job_id="j2", workflow_id="w1",
                            step_name="S2", module="m", action="b")
        log2.status = "failed"
        self.wa.record_execution(log1)
        self.wa.record_execution(log2)
        ana = self.wa.get_analytics()
        assert ana.total_jobs == 2
        assert ana.completed == 1
        assert ana.failed == 1
        assert ana.avg_duration_ms == 100.0

    def test_get_stats_empty(self):
        stats = self.wa.get_stats()
        assert stats["total_jobs"] == 0
        assert stats["success_rate"] == 100.0


# ══════════════════════════════════════════════════════════════════════
# OrchestratorAPI Tests
# ══════════════════════════════════════════════════════════════════════

class TestOrchestratorAPI:
    def setup_method(self):
        self.orch = SchedulerOrchestrator()
        self.api = self.orch.api

    def test_get_status(self):
        status = self.api.get_status()
        assert "workflows" in status
        assert "scheduler" in status
        assert "queue" in status
        assert "executor" in status
        assert "events" in status

    def test_get_health(self):
        health = self.api.get_health()
        assert "status" in health

    def test_get_summary(self):
        summary = self.api.get_summary()
        assert "total_jobs" in summary
        assert "active_jobs" in summary
        assert "completed_jobs" in summary
        assert "failed_jobs" in summary


# ══════════════════════════════════════════════════════════════════════
# SchedulerOrchestrator Tests
# ══════════════════════════════════════════════════════════════════════

class TestSchedulerOrchestrator:
    def setup_method(self):
        self.orch = SchedulerOrchestrator()

    def test_initialization(self):
        assert self.orch.workflows is not None
        assert self.orch.scheduler is not None
        assert self.orch.queue is not None
        assert self.orch.executor is not None
        assert self.orch.retry is not None
        assert self.orch.resources is not None
        assert self.orch.events is not None
        assert self.orch.notifications is not None
        assert self.orch.monitoring is not None
        assert self.orch.recovery is not None
        assert self.orch.analytics is not None
        assert self.orch.api is not None

    def test_default_workflow_exists(self):
        wfs = self.orch.workflows.get_all_workflows()
        assert len(wfs) >= 1
        assert wfs[0].name == "End-to-End Publishing"

    def test_default_workflow_steps(self):
        wfs = self.orch.workflows.get_all_workflows()
        wf = wfs[0]
        step_names = [s.name for s in wf.steps]
        assert "Research" in step_names
        assert "Writing" in step_names
        assert "Website" in step_names
        assert "Pinterest Account" in step_names
        assert "Pinterest Board" in step_names
        assert "Pin Creation" in step_names
        assert "Affiliate Mapping" in step_names
        assert "SEO Optimization" in step_names
        assert "Publish" in step_names
        assert "Traffic Tracking" in step_names
        assert "Analytics" in step_names
        assert "Revenue" in step_names

    def test_start_stop(self):
        result = self.orch.start()
        assert result["status"] == "started"
        result = self.orch.stop()
        assert result["status"] == "stopped"

    def test_submit_workflow(self):
        wfs = self.orch.workflows.get_all_workflows()
        wf = wfs[0]
        job_id = self.orch.submit_workflow(wf.workflow_id)
        assert job_id.startswith("job_")

    def test_submit_workflow_nonexistent(self):
        with pytest.raises(WorkflowError):
            self.orch.submit_workflow("nonexistent")

    def test_execute_default_publishing(self):
        result = self.orch.execute_default_publishing()
        assert "workflow_id" in result
        assert result["status"] in ("completed", "completed_with_errors")

    def test_get_status(self):
        status = self.orch.get_status()
        assert "module" in status
        assert "Scheduler & Workflow Orchestrator" in status["module"]
        assert "workflows" in status
        assert "scheduler" in status


# ══════════════════════════════════════════════════════════════════════
# Exception Classes Tests
# ══════════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_base(self):
        with pytest.raises(SchedulerError):
            raise SchedulerError("base")

    def test_workflow_error(self):
        with pytest.raises(WorkflowError):
            raise WorkflowError("wf")

    def test_scheduling_error(self):
        with pytest.raises(SchedulingError):
            raise SchedulingError("sched")

    def test_queue_error(self):
        with pytest.raises(QueueError):
            raise QueueError("queue")

    def test_dependency_error(self):
        with pytest.raises(DependencyError):
            raise DependencyError("dep")

    def test_execution_error(self):
        with pytest.raises(ExecutionError):
            raise ExecutionError("exec")

    def test_retry_error(self):
        with pytest.raises(RetryError):
            raise RetryError("retry")

    def test_recovery_error(self):
        with pytest.raises(RecoveryError):
            raise RecoveryError("rec")

    def test_monitoring_error(self):
        with pytest.raises(MonitoringError):
            raise MonitoringError("mon")


# ══════════════════════════════════════════════════════════════════════
# Singleton Tests
# ══════════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_scheduler(self):
        s1 = get_scheduler()
        s2 = get_scheduler()
        assert s1 is s2
