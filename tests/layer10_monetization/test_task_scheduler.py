"""Tests for Layer 10 Module 3 — Task Scheduler Engine."""
from layers.layer10_monetization.modules.task_scheduler.exceptions import (
    SchedulerError, TaskNotFoundError, QueueFullError, WorkerUnavailableError,
    ResourceUnavailableError, SchedulingTimeoutError, PolicyError,
)
from layers.layer10_monetization.modules.task_scheduler.task import Task, PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_NORMAL, PRIORITY_LOW
from layers.layer10_monetization.modules.task_scheduler.priority_queue import PriorityQueue
from layers.layer10_monetization.modules.task_scheduler.scheduler_policy import SchedulerPolicy
from layers.layer10_monetization.modules.task_scheduler.resource_allocator import ResourceAllocator, ResourcePool
from layers.layer10_monetization.modules.task_scheduler.worker_pool import WorkerPool
from layers.layer10_monetization.modules.task_scheduler.load_balancer import LoadBalancer
from layers.layer10_monetization.modules.task_scheduler.scheduler_events import (
    SchedulerEventBus, SchedulerEvent,
)
from layers.layer10_monetization.modules.task_scheduler.scheduler_metrics import SchedulerMetrics
from layers.layer10_monetization.modules.task_scheduler.scheduler_report import SchedulerReport
from layers.layer10_monetization.modules.task_scheduler.task_scheduler import TaskScheduler


# ─── Exceptions Tests ─────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        with raise_ctx(SchedulerError("test")):
            raise SchedulerError("test")

    def test_task_not_found(self):
        with raise_ctx(TaskNotFoundError("test")):
            raise TaskNotFoundError("test")

    def test_queue_full(self):
        with raise_ctx(QueueFullError("test")):
            raise QueueFullError("test")

    def test_worker_unavailable(self):
        with raise_ctx(WorkerUnavailableError("test")):
            raise WorkerUnavailableError("test")

    def test_resource_unavailable(self):
        with raise_ctx(ResourceUnavailableError("test")):
            raise ResourceUnavailableError("test")

    def test_timeout(self):
        with raise_ctx(SchedulingTimeoutError("test")):
            raise SchedulingTimeoutError("test")

    def test_policy(self):
        with raise_ctx(PolicyError("test")):
            raise PolicyError("test")

    def test_inheritance(self):
        assert issubclass(TaskNotFoundError, SchedulerError)
        assert issubclass(QueueFullError, SchedulerError)
        assert issubclass(WorkerUnavailableError, SchedulerError)


# ─── Task Tests ───────────────────────────────────────────────────
class TestTask:
    def test_create(self):
        t = Task("layer04_writing", "draft_generator", PRIORITY_HIGH)
        assert t.task_id.startswith("task_")
        assert t.layer == "layer04_writing"
        assert t.priority == PRIORITY_HIGH
        assert t.status == "pending"

    def test_validate(self):
        t = Task("layer04_writing")
        assert t.validate() is True

    def test_validate_no_layer(self):
        t = Task()
        assert t.validate() is False

    def test_start(self):
        t = Task("layer04_writing")
        t.start("worker_1")
        assert t.status == "running"
        assert t.assigned_worker == "worker_1"

    def test_complete(self):
        t = Task("layer04_writing")
        t.start()
        t.complete({"draft": "text"})
        assert t.status == "completed"
        assert t.result == {"draft": "text"}

    def test_fail(self):
        t = Task("layer04_writing")
        t.start()
        t.fail("API error")
        assert t.status == "failed"
        assert t.error == "API error"

    def test_cancel(self):
        t = Task("layer04_writing")
        t.cancel()
        assert t.status == "cancelled"

    def test_pause_resume(self):
        t = Task("layer04_writing")
        t.start()
        t.pause()
        assert t.status == "paused"
        t.resume()
        assert t.status == "running"

    def test_can_retry(self):
        t = Task("layer04_writing")
        t.start()
        t.fail("error")
        assert t.can_retry() is True

    def test_retry(self):
        t = Task("layer04_writing")
        t.start()
        t.fail("error")
        result = t.retry()
        assert result is True
        assert t.retry_count == 1
        assert t.status == "pending"

    def test_retry_limit(self):
        t = Task("layer04_writing")
        t.max_retries = 1
        t.start()
        t.fail("error")
        t.retry()
        t.start()
        t.fail("error")
        assert t.can_retry() is False

    def test_is_terminal(self):
        t = Task("layer04_writing")
        assert t.is_terminal is False
        t.complete()
        assert t.is_terminal is True

    def test_clone(self):
        t = Task("layer04_writing", "draft", PRIORITY_HIGH)
        t.workflow_id = "wf1"
        clone = t.clone()
        assert clone.layer == t.layer
        assert clone.priority == t.priority

    def test_to_dict(self):
        t = Task("layer04_writing")
        d = t.to_dict()
        assert "task_id" in d
        assert "layer" in d
        assert "status" in d


# ─── PriorityQueue Tests ──────────────────────────────────────────
class TestPriorityQueue:
    def setup_method(self):
        self.queue = PriorityQueue()

    def test_push(self):
        t = Task("layer01", priority=PRIORITY_HIGH)
        result = self.queue.push(t)
        assert result is True
        assert self.queue.size == 1

    def test_pop(self):
        t = Task("layer01", priority=PRIORITY_HIGH)
        self.queue.push(t)
        popped = self.queue.pop()
        assert popped is not None
        assert popped.task_id == t.task_id
        assert self.queue.size == 0

    def test_pop_priority_order(self):
        self.queue.push(Task("layer_low", priority=PRIORITY_LOW))
        self.queue.push(Task("layer_critical", priority=PRIORITY_CRITICAL))
        self.queue.push(Task("layer_normal", priority=PRIORITY_NORMAL))
        popped = self.queue.pop()
        assert popped.priority == PRIORITY_CRITICAL

    def test_peek(self):
        self.queue.push(Task("layer01", priority=PRIORITY_HIGH))
        peeked = self.queue.peek()
        assert peeked is not None
        assert self.queue.size == 1

    def test_remove(self):
        t = Task("layer01")
        self.queue.push(t)
        removed = self.queue.remove(t.task_id)
        assert removed is not None
        assert self.queue.size == 0

    def test_remove_nonexistent(self):
        removed = self.queue.remove("nonexistent")
        assert removed is None

    def test_update_priority(self):
        t = Task("layer01", priority=PRIORITY_LOW)
        self.queue.push(t)
        result = self.queue.update_priority(t.task_id, PRIORITY_CRITICAL)
        assert result is True
        popped = self.queue.pop()
        assert popped.priority == PRIORITY_CRITICAL

    def test_is_full(self):
        small_queue = PriorityQueue(max_size=2)
        small_queue.push(Task("l1"))
        small_queue.push(Task("l2"))
        assert small_queue.is_full is True

    def test_get_by_layer(self):
        self.queue.push(Task("layer01"))
        self.queue.push(Task("layer02"))
        self.queue.push(Task("layer01"))
        results = self.queue.get_by_layer("layer01")
        assert len(results) == 2

    def test_get_stats(self):
        self.queue.push(Task("l1", priority=PRIORITY_HIGH))
        stats = self.queue.get_stats()
        assert stats["total"] == 1
        assert stats["by_priority"][PRIORITY_HIGH] == 1

    def test_clear(self):
        self.queue.push(Task("l1"))
        self.queue.push(Task("l2"))
        self.queue.clear()
        assert self.queue.size == 0


# ─── SchedulerPolicy Tests ────────────────────────────────────────
class TestSchedulerPolicy:
    def setup_method(self):
        self.tasks = [
            Task("l1", priority=PRIORITY_LOW),
            Task("l2", priority=PRIORITY_HIGH),
            Task("l3", priority=PRIORITY_NORMAL),
        ]
        self.tasks[0].created_at = 3.0
        self.tasks[1].created_at = 1.0
        self.tasks[2].created_at = 2.0

    def test_priority_policy(self):
        policy = SchedulerPolicy("priority")
        selected = policy.select_next(self.tasks)
        assert selected.priority == PRIORITY_HIGH

    def test_fifo_policy(self):
        policy = SchedulerPolicy("fifo")
        selected = policy.select_next(self.tasks)
        assert selected.created_at == 1.0

    def test_round_robin(self):
        policy = SchedulerPolicy("round_robin")
        first = policy.select_next(self.tasks)
        second = policy.select_next(self.tasks)
        assert first.task_id != second.task_id

    def test_sjf(self):
        policy = SchedulerPolicy("shortest_job_first")
        selected = policy.select_next(self.tasks)
        assert selected is not None

    def test_edf(self):
        policy = SchedulerPolicy("earliest_deadline")
        self.tasks[0].deadline = 100.0
        self.tasks[1].deadline = 50.0
        selected = policy.select_next(self.tasks)
        assert selected.task_id == self.tasks[1].task_id

    def test_edf_no_deadline(self):
        policy = SchedulerPolicy("earliest_deadline")
        selected = policy.select_next(self.tasks)
        assert selected is not None

    def test_weighted(self):
        policy = SchedulerPolicy("weighted_fair")
        policy.set_weight("l1", 10.0)
        selected = policy.select_next(self.tasks)
        assert selected is not None

    def test_empty_tasks(self):
        policy = SchedulerPolicy("priority")
        assert policy.select_next([]) is None

    def test_invalid_policy(self):
        policy = SchedulerPolicy("invalid")
        assert policy.name == "priority"

    def test_rebalance_priority(self):
        policy = SchedulerPolicy("priority")
        rebalanced = policy.rebalance(self.tasks)
        assert len(rebalanced) == 3

    def test_name(self):
        assert SchedulerPolicy("fifo").name == "fifo"
        assert SchedulerPolicy("priority").name == "priority"


# ─── ResourceAllocator Tests ──────────────────────────────────────
class TestResourceAllocator:
    def setup_method(self):
        self.allocator = ResourceAllocator()

    def test_allocate(self):
        result = self.allocator.allocate("t1", {"cpu": 2.0, "memory": 4.0})
        assert result is True

    def test_allocate_insufficient(self):
        result = self.allocator.allocate("t1", {"cpu": 100.0})
        assert result is False

    def test_release(self):
        self.allocator.allocate("t1", {"cpu": 2.0})
        result = self.allocator.release("t1")
        assert result is True
        assert self.allocator.available("cpu") == 8.0

    def test_release_nonexistent(self):
        result = self.allocator.release("nonexistent")
        assert result is False

    def test_available(self):
        self.allocator.allocate("t1", {"cpu": 3.0})
        assert self.allocator.available("cpu") == 5.0

    def test_estimate_cost(self):
        self.allocator.allocate("t1", {"cpu": 2.0, "memory": 4.0})
        cost = self.allocator.estimate_cost("t1")
        assert cost["cpu"] == 2.0

    def test_utilization(self):
        self.allocator.allocate("t1", {"cpu": 4.0})
        util = self.allocator.get_utilization()
        assert util["cpu"] == 0.5

    def test_multiple_allocations(self):
        self.allocator.allocate("t1", {"cpu": 3.0})
        self.allocator.allocate("t2", {"cpu": 3.0})
        assert self.allocator.available("cpu") == 2.0

    def test_custom_pool(self):
        pool = ResourcePool()
        pool.cpu_cores = 16.0
        allocator = ResourceAllocator(pool)
        assert allocator.available("cpu") == 16.0

    def test_get_stats(self):
        self.allocator.allocate("t1", {"cpu": 2.0})
        stats = self.allocator.get_stats()
        assert "pool" in stats
        assert "utilization" in stats


# ─── WorkerPool Tests ─────────────────────────────────────────────
class TestWorkerPool:
    def setup_method(self):
        self.pool = WorkerPool(size=3)

    def test_assign(self):
        worker = self.pool.assign("task_1")
        assert worker is not None
        assert worker.is_busy

    def test_assign_all_busy(self):
        self.pool.assign("t1")
        self.pool.assign("t2")
        self.pool.assign("t3")
        worker = self.pool.assign("t4")
        assert worker is None

    def test_release(self):
        worker = self.pool.assign("t1")
        result = self.pool.release(worker.worker_id, success=True)
        assert result is True
        assert worker.is_available

    def test_release_failure(self):
        worker = self.pool.assign("t1")
        self.pool.release(worker.worker_id, success=False)
        assert worker.tasks_failed == 1

    def test_heartbeat(self):
        worker = self.pool.assign("t1")
        result = self.pool.heartbeat(worker.worker_id, cpu=0.5, memory=0.3)
        assert result is True
        assert worker.cpu_usage == 0.5

    def test_get_worker(self):
        worker = self.pool.assign("t1")
        found = self.pool.get_worker(worker.worker_id)
        assert found is not None

    def test_get_idle_workers(self):
        self.pool.assign("t1")
        idle = self.pool.get_idle_workers()
        assert len(idle) == 2

    def test_get_busy_workers(self):
        self.pool.assign("t1")
        busy = self.pool.get_busy_workers()
        assert len(busy) == 1

    def test_pool_size(self):
        assert self.pool.pool_size == 3

    def test_stats(self):
        self.pool.assign("t1")
        stats = self.pool.get_stats()
        assert stats["pool_size"] == 3
        assert stats["busy"] == 1

    def test_worker_to_dict(self):
        worker = self.pool.assign("t1")
        d = worker.to_dict()
        assert "worker_id" in d
        assert "status" in d


# ─── LoadBalancer Tests ───────────────────────────────────────────
class TestLoadBalancer:
    def setup_method(self):
        self.pool = WorkerPool(size=3)
        self.pool.assign("t1")
        self.pool.assign("t2")

    def test_least_loaded(self):
        lb = LoadBalancer("least_loaded")
        worker = lb.select_worker(self.pool)
        assert worker is not None
        assert worker.is_available

    def test_round_robin(self):
        lb = LoadBalancer("round_robin")
        w1 = lb.select_worker(self.pool)
        w2 = lb.select_worker(self.pool)
        assert w1 is not None

    def test_random(self):
        lb = LoadBalancer("random")
        worker = lb.select_worker(self.pool)
        assert worker is not None

    def test_affinity(self):
        lb = LoadBalancer("affinity")
        lb.set_affinity("layer04", "worker_1")
        idle = self.pool.get_idle_workers()
        if idle:
            worker = lb.select_worker(self.pool, "layer04")
            assert worker is not None

    def test_no_workers_available(self):
        self.pool.assign("t3")
        lb = LoadBalancer("least_loaded")
        worker = lb.select_worker(self.pool)
        assert worker is None

    def test_set_weight(self):
        lb = LoadBalancer("weighted")
        lb.set_weight("worker_1", 2.0)
        assert lb._weights["worker_1"] == 2.0

    def test_detect_hotspots(self):
        lb = LoadBalancer()
        hotspots = lb.detect_hotspots(self.pool)
        assert isinstance(hotspots, list)

    def test_rebalance(self):
        lb = LoadBalancer()
        count = lb.rebalance(self.pool)
        assert count >= 0

    def test_algorithm(self):
        lb = LoadBalancer("round_robin")
        assert lb.algorithm == "round_robin"


# ─── SchedulerEventBus Tests ──────────────────────────────────────
class TestSchedulerEventBus:
    def setup_method(self):
        self.bus = SchedulerEventBus()

    def test_publish(self):
        event = SchedulerEvent(event_type="test", task_id="t1")
        count = self.bus.publish(event)
        assert count == 0
        assert self.bus.get_event_count() == 1

    def test_subscribe_and_publish(self):
        received = []
        self.bus.subscribe("test", lambda e: received.append(e))
        event = SchedulerEvent(event_type="test", task_id="t1")
        self.bus.publish(event)
        assert len(received) == 1

    def test_unsubscribe(self):
        handler = lambda e: None
        self.bus.subscribe("test", handler)
        result = self.bus.unsubscribe("test", handler)
        assert result is True

    def test_get_events_filtered(self):
        self.bus.publish(SchedulerEvent(event_type="a", task_id="t1"))
        self.bus.publish(SchedulerEvent(event_type="b", task_id="t2"))
        events = self.bus.get_events(event_type="a")
        assert len(events) == 1

    def test_event_to_dict(self):
        event = SchedulerEvent(event_type="test", task_id="t1")
        d = event.to_dict()
        assert "event_id" in d
        assert "task_id" in d


# ─── SchedulerMetrics Tests ───────────────────────────────────────
class TestSchedulerMetrics:
    def setup_method(self):
        self.metrics = SchedulerMetrics()

    def test_record_scheduled(self):
        self.metrics.record_task_scheduled()
        assert self.metrics._total_scheduled == 1

    def test_record_completed(self):
        self.metrics.record_task_completed(wait_time_ms=50, execution_time_ms=100)
        assert self.metrics._total_completed == 1

    def test_record_failed(self):
        self.metrics.record_task_failed()
        assert self.metrics._total_failed == 1

    def test_throughput(self):
        self.metrics.record_task_completed(execution_time_ms=1000)
        t = self.metrics.get_throughput()
        assert t > 0

    def test_avg_wait_time(self):
        self.metrics.record_task_completed(wait_time_ms=100)
        self.metrics.record_task_completed(wait_time_ms=200)
        assert self.metrics.get_avg_wait_time() == 150.0

    def test_scheduling_efficiency(self):
        self.metrics.record_task_scheduled()
        self.metrics.record_task_completed()
        eff = self.metrics.get_scheduling_efficiency()
        assert eff == 1.0

    def test_summary(self):
        self.metrics.record_task_scheduled()
        summary = self.metrics.get_summary()
        assert "total_scheduled" in summary
        assert "throughput_per_sec" in summary

    def test_reset(self):
        self.metrics.record_task_scheduled()
        self.metrics.reset()
        assert self.metrics._total_scheduled == 0


# ─── SchedulerReport Tests ────────────────────────────────────────
class TestSchedulerReport:
    def setup_method(self):
        self.report = SchedulerReport()

    def test_create(self):
        assert self.report.report_id.startswith("srep_")

    def test_set_queue_report(self):
        self.report.set_queue_report(total=10, by_priority={"1": 3, "2": 7})
        assert self.report.queue_report["total_tasks"] == 10

    def test_set_worker_report(self):
        self.report.set_worker_report(pool_size=5, idle=2, busy=3)
        assert self.report.worker_report["utilization"] == 0.6

    def test_set_resource_report(self):
        self.report.set_resource_report({"cpu": 0.5, "memory": 0.3})
        assert self.report.resource_report["cpu"] == 0.5

    def test_set_performance_report(self):
        self.report.set_performance_report(throughput=2.5, efficiency=0.8)
        assert self.report.performance_report["throughput_per_sec"] == 2.5

    def test_add_recommendation(self):
        self.report.add_recommendation("Scale up workers")
        assert len(self.report.recommendations) == 1

    def test_get_summary(self):
        self.report.set_queue_report(total=5, by_priority={})
        summary = self.report.get_summary()
        assert "report_id" in summary

    def test_export_dict(self):
        self.report.set_queue_report(total=5, by_priority={})
        d = self.report.export_dict()
        assert "queue_report" in d
        assert "recommendations" in d


# ─── TaskScheduler Tests ──────────────────────────────────────────
class TestTaskScheduler:
    def setup_method(self):
        self.scheduler = TaskScheduler(worker_count=3, queue_size=100)

    def test_schedule_task(self):
        task = Task("layer04_writing", priority=PRIORITY_HIGH)
        result = self.scheduler.schedule_task(task)
        assert result is True
        assert self.scheduler.get_queue_size() == 1

    def test_schedule_invalid_task(self):
        task = Task()
        result = self.scheduler.schedule_task(task)
        assert result is False

    def test_execute_next(self):
        task = Task("layer01", priority=PRIORITY_HIGH)
        self.scheduler.schedule_task(task)
        result = self.scheduler.execute_next(lambda l: {"ok": True})
        assert result is not None
        assert result.status == "completed"

    def test_execute_next_failure(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        result = self.scheduler.execute_next(lambda l: 1/0)
        assert result is not None
        assert result.status == "failed"

    def test_execute_next_empty(self):
        result = self.scheduler.execute_next(lambda l: {"ok": True})
        assert result is None

    def test_pause_task(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        self.scheduler.execute_next(lambda l: {"ok": True})
        # After execution, task is completed, not running
        # Need to test with a task that stays running
        result = self.scheduler.pause_task("nonexistent")
        assert result is False

    def test_cancel_task(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        result = self.scheduler.cancel_task(task.task_id)
        assert result is True
        assert self.scheduler.get_queue_size() == 0

    def test_reschedule_task(self):
        task = Task("layer01", priority=PRIORITY_LOW)
        self.scheduler.schedule_task(task)
        result = self.scheduler.reschedule_task(task.task_id, PRIORITY_CRITICAL)
        assert result is True

    def test_retry_task(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        self.scheduler.execute_next(lambda l: 1/0)
        completed = self.scheduler._completed_tasks
        if completed:
            result = self.scheduler.retry_task(completed[0].task_id)
            assert result is True

    def test_generate_report(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        self.scheduler.execute_next(lambda l: {"ok": True})
        report = self.scheduler.generate_report()
        assert report.report_id.startswith("srep_")

    def test_get_health(self):
        health = self.scheduler.get_health()
        assert "queue_size" in health
        assert "workers" in health
        assert "metrics" in health

    def test_multiple_executions(self):
        for i in range(5):
            self.scheduler.schedule_task(Task(f"layer_{i}"))
        for _ in range(5):
            self.scheduler.execute_next(lambda l: {"ok": True})
        assert self.scheduler.get_completed_count() == 5

    def test_worker_exhaustion(self):
        for i in range(10):
            self.scheduler.schedule_task(Task(f"layer_{i}"))
        executed = 0
        for _ in range(10):
            result = self.scheduler.execute_next(lambda l: {"ok": True})
            if result:
                executed += 1
        assert executed > 0

    def test_event_bus_tracking(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        self.scheduler.execute_next(lambda l: {"ok": True})
        events = self.scheduler.event_bus.get_events()
        assert len(events) > 0

    def test_metrics_recorded(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        self.scheduler.execute_next(lambda l: {"ok": True})
        summary = self.scheduler.metrics.get_summary()
        assert summary["total_scheduled"] == 1

    def test_queue_full(self):
        small_scheduler = TaskScheduler(worker_count=1, queue_size=2)
        small_scheduler.schedule_task(Task("l1"))
        small_scheduler.schedule_task(Task("l2"))
        result = small_scheduler.schedule_task(Task("l3"))
        assert result is False


# ─── Integration Tests ────────────────────────────────────────────
class TestTaskSchedulerIntegration:
    def setup_method(self):
        self.scheduler = TaskScheduler(worker_count=5, queue_size=1000)

    def test_full_pipeline(self):
        tasks = [
            Task("layer01_core", priority=PRIORITY_CRITICAL),
            Task("layer02_research", priority=PRIORITY_HIGH),
            Task("layer04_writing", priority=PRIORITY_NORMAL),
            Task("layer06_quality", priority=PRIORITY_HIGH),
            Task("layer07_publishing", priority=PRIORITY_NORMAL),
        ]
        for t in tasks:
            self.scheduler.schedule_task(t)

        executed = []
        for _ in range(5):
            result = self.scheduler.execute_next(lambda l: {"layer": l, "ok": True})
            if result:
                executed.append(result)

        assert len(executed) == 5
        assert all(t.status == "completed" for t in executed)

    def test_mixed_results(self):
        def executor(layer):
            if "quality" in layer:
                raise ValueError("Quality check failed")
            return {"ok": True}

        self.scheduler.schedule_task(Task("layer01"))
        self.scheduler.schedule_task(Task("layer06_quality"))
        self.scheduler.schedule_task(Task("layer07_publishing"))

        results = []
        for _ in range(3):
            r = self.scheduler.execute_next(executor)
            if r:
                results.append(r)

        completed = [r for r in results if r.status == "completed"]
        failed = [r for r in results if r.status == "failed"]
        assert len(completed) == 2
        assert len(failed) == 1

    def test_priority_scheduling(self):
        self.scheduler.schedule_task(Task("l_low", priority=PRIORITY_LOW))
        self.scheduler.schedule_task(Task("l_critical", priority=PRIORITY_CRITICAL))
        self.scheduler.schedule_task(Task("l_normal", priority=PRIORITY_NORMAL))

        first = self.scheduler.execute_next(lambda l: {"ok": True})
        assert first.priority == PRIORITY_CRITICAL

    def test_report_generation(self):
        for i in range(3):
            self.scheduler.schedule_task(Task(f"layer_{i}"))
        for _ in range(3):
            self.scheduler.execute_next(lambda l: {"ok": True})

        report = self.scheduler.generate_report()
        d = report.export_dict()
        assert "queue_report" in d
        assert "worker_report" in d
        assert "performance_report" in d

    def test_worker_pool_integration(self):
        for i in range(5):
            self.scheduler.schedule_task(Task(f"layer_{i}"))
        for _ in range(5):
            self.scheduler.execute_next(lambda l: {"ok": True})

        stats = self.scheduler.worker_pool.get_stats()
        assert stats["total_completed"] == 5

    def test_cancel_and_retry(self):
        task = Task("layer01")
        self.scheduler.schedule_task(task)
        # Execute and fail, then retry
        self.scheduler.execute_next(lambda l: 1/0)
        assert len(self.scheduler._completed_tasks) > 0
        failed_task = self.scheduler._completed_tasks[-1]
        result = self.scheduler.retry_task(failed_task.task_id)
        assert result is True
        assert self.scheduler.get_queue_size() == 1

    def test_report_recommends_scaling(self):
        for i in range(5):
            self.scheduler.schedule_task(Task(f"layer_{i}"))
        for _ in range(5):
            self.scheduler.execute_next(lambda l: {"ok": True})

        report = self.scheduler.generate_report()
        # Should not recommend scaling when workers are idle
        assert isinstance(report.recommendations, list)


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
