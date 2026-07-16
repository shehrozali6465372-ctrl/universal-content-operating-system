"""Tests for Layer 7 Module 4 — Scheduler & Queue."""
import time
from layers.layer07_publishing.modules.scheduler_queue.publish_job import (
    PublishJob, JOB_PRIORITIES, JOB_STATUSES,
)
from layers.layer07_publishing.modules.scheduler_queue.job_queue import JobQueue
from layers.layer07_publishing.modules.scheduler_queue.retry_manager import (
    RetryManager, RetryPolicy,
)
from layers.layer07_publishing.modules.scheduler_queue.dead_letter_queue import (
    DeadLetterQueue, DeadLetterEntry,
)
from layers.layer07_publishing.modules.scheduler_queue.timezone_manager import (
    TimezoneManager,
)
from layers.layer07_publishing.modules.scheduler_queue.queue_metrics import QueueMetrics
from layers.layer07_publishing.modules.scheduler_queue.batch_publisher import (
    BatchPublisher, BatchResult,
)
from layers.layer07_publishing.modules.scheduler_queue.worker_manager import (
    WorkerManager, Worker,
)
from layers.layer07_publishing.modules.scheduler_queue.queue_orchestrator import (
    QueueOrchestrator,
)
from layers.layer07_publishing.modules.scheduler_queue.exceptions import (
    QueueError, JobNotFoundError, QueueFullError,
)


# ─── PublishJob Tests ────────────────────────────────────────────────
class TestPublishJob:
    def test_create_default(self):
        j = PublishJob()
        assert j.job_id == ""
        assert j.status == "pending"
        assert j.priority == JOB_PRIORITIES["normal"]
        assert j.attempts == 0
        assert j.max_retries == 3

    def test_create_with_args(self):
        j = PublishJob(job_id="j1", content_id="c1", platform="facebook", content="Hello")
        assert j.job_id == "j1"
        assert j.content_id == "c1"
        assert j.platform == "facebook"
        assert j.content == "Hello"

    def test_default_values(self):
        j = PublishJob()
        assert j.content_type == "post"
        assert j.media_paths == []
        assert j.scheduled_time is None
        assert j.last_error == ""
        assert j.metadata == {}
        assert j.started_at is None
        assert j.completed_at is None

    def test_is_ready_pending(self):
        j = PublishJob()
        j.scheduled_time = time.time() - 1
        assert j.is_ready() is False

    def test_is_ready_scheduled_past(self):
        j = PublishJob()
        j.status = "scheduled"
        j.scheduled_time = time.time() - 10
        assert j.is_ready() is True

    def test_is_ready_scheduled_future(self):
        j = PublishJob()
        j.status = "scheduled"
        j.scheduled_time = time.time() + 3600
        assert j.is_ready() is False

    def test_is_ready_no_scheduled_time(self):
        j = PublishJob()
        j.status = "scheduled"
        assert j.is_ready() is False

    def test_to_dict(self):
        j = PublishJob(job_id="j1", content_id="c1", platform="facebook")
        d = j.to_dict()
        assert d["job_id"] == "j1"
        assert d["content_id"] == "c1"
        assert d["platform"] == "facebook"
        assert d["status"] == "pending"
        assert d["priority"] == 5
        assert "created_at" in d

    def test_to_dict_truncates_error(self):
        j = PublishJob()
        j.last_error = "x" * 300
        d = j.to_dict()
        assert len(d["last_error"]) <= 100

    def test_job_statuses_defined(self):
        assert "pending" in JOB_STATUSES
        assert "completed" in JOB_STATUSES
        assert "dead" in JOB_STATUSES

    def test_job_priorities_defined(self):
        assert JOB_PRIORITIES["critical"] == 1
        assert JOB_PRIORITIES["high"] == 3
        assert JOB_PRIORITIES["normal"] == 5
        assert JOB_PRIORITIES["low"] == 7
        assert JOB_PRIORITIES["background"] == 10


# ─── JobQueue Tests ──────────────────────────────────────────────────
class TestJobQueue:
    def setup_method(self):
        self.q = JobQueue()

    def test_enqueue(self):
        j = PublishJob(job_id="j1")
        assert self.q.enqueue(j) is True
        assert self.q.size == 1

    def test_enqueue_returns_false_when_full(self):
        q = JobQueue(max_size=2)
        q.enqueue(PublishJob(job_id="j1"))
        q.enqueue(PublishJob(job_id="j2"))
        assert q.enqueue(PublishJob(job_id="j3")) is False
        assert q.size == 2

    def test_enqueue_batch(self):
        jobs = [PublishJob(job_id=f"j{i}") for i in range(5)]
        count = self.q.enqueue_batch(jobs)
        assert count == 5
        assert self.q.size == 5

    def test_dequeue_empty(self):
        assert self.q.dequeue() is None

    def test_dequeue_ready_scheduled(self):
        j = PublishJob(job_id="j1")
        j.status = "scheduled"
        j.scheduled_time = time.time() - 1
        self.q.enqueue(j)
        result = self.q.dequeue()
        assert result is not None
        assert result.job_id == "j1"
        assert result.status == "running"

    def test_dequeue_by_platform(self):
        j1 = PublishJob(job_id="j1", platform="facebook")
        j1.status = "scheduled"
        j1.scheduled_time = time.time() - 1
        j2 = PublishJob(job_id="j2", platform="linkedin")
        j2.status = "scheduled"
        j2.scheduled_time = time.time() - 1
        self.q.enqueue_batch([j1, j2])
        result = self.q.dequeue(platform="linkedin")
        assert result is not None
        assert result.platform == "linkedin"

    def test_dequeue_priority_order(self):
        j_low = PublishJob(job_id="j_low", platform="a")
        j_low.priority = 7
        j_low.status = "scheduled"
        j_low.scheduled_time = time.time() - 1
        j_high = PublishJob(job_id="j_high", platform="a")
        j_high.priority = 1
        j_high.status = "scheduled"
        j_high.scheduled_time = time.time() - 1
        self.q.enqueue_batch([j_low, j_high])
        result = self.q.dequeue()
        assert result.job_id == "j_high"

    def test_dequeue_many(self):
        for i in range(5):
            j = PublishJob(job_id=f"j{i}")
            j.status = "scheduled"
            j.scheduled_time = time.time() - 1
            self.q.enqueue(j)
        results = self.q.dequeue_many(3)
        assert len(results) == 3

    def test_dequeue_many_exhausts(self):
        j = PublishJob(job_id="j1")
        j.status = "scheduled"
        j.scheduled_time = time.time() - 1
        self.q.enqueue(j)
        results = self.q.dequeue_many(10)
        assert len(results) == 1

    def test_peek(self):
        j = PublishJob(job_id="j1")
        j.status = "scheduled"
        j.scheduled_time = time.time() - 1
        self.q.enqueue(j)
        result = self.q.peek()
        assert result is not None
        assert self.q.size == 1  # peek doesn't remove

    def test_peek_empty(self):
        assert self.q.peek() is None

    def test_get_job(self):
        j = PublishJob(job_id="j1")
        self.q.enqueue(j)
        assert self.q.get_job("j1") is not None
        assert self.q.get_job("missing") is None

    def test_remove(self):
        j = PublishJob(job_id="j1")
        self.q.enqueue(j)
        assert self.q.remove("j1") is True
        assert self.q.size == 0

    def test_remove_nonexistent(self):
        assert self.q.remove("missing") is False

    def test_cancel_pending(self):
        j = PublishJob(job_id="j1")
        self.q.enqueue(j)
        assert self.q.cancel("j1") is True
        assert j.status == "cancelled"

    def test_cancel_scheduled(self):
        j = PublishJob(job_id="j1")
        j.status = "scheduled"
        self.q.enqueue(j)
        assert self.q.cancel("j1") is True
        assert j.status == "cancelled"

    def test_cancel_running_fails(self):
        j = PublishJob(job_id="j1")
        j.status = "running"
        self.q.enqueue(j)
        assert self.q.cancel("j1") is False

    def test_count_by_status(self):
        j1 = PublishJob(job_id="j1")
        j2 = PublishJob(job_id="j2")
        j1.status = "completed"
        self.q.enqueue_batch([j1, j2])
        assert self.q.count_by_status("completed") == 1
        assert self.q.count_by_status("pending") == 1

    def test_clear_completed(self):
        j1 = PublishJob(job_id="j1")
        j2 = PublishJob(job_id="j2")
        j1.status = "completed"
        self.q.enqueue_batch([j1, j2])
        removed = self.q.clear_completed()
        assert removed == 1
        assert self.q.size == 1

    def test_is_full(self):
        q = JobQueue(max_size=1)
        q.enqueue(PublishJob(job_id="j1"))
        assert q.is_full is True

    def test_enqueue_dequeue_counts(self):
        j = PublishJob(job_id="j1")
        j.status = "scheduled"
        j.scheduled_time = time.time() - 1
        self.q.enqueue(j)
        assert self.q.enqueue_count == 1
        self.q.dequeue()
        assert self.q.dequeue_count == 1

    def test_peek_by_platform(self):
        j1 = PublishJob(job_id="j1", platform="a")
        j1.status = "scheduled"
        j1.scheduled_time = time.time() - 1
        j2 = PublishJob(job_id="j2", platform="b")
        j2.status = "scheduled"
        j2.scheduled_time = time.time() - 1
        self.q.enqueue_batch([j1, j2])
        result = self.q.peek(platform="b")
        assert result is not None
        assert result.platform == "b"


# ─── RetryManager Tests ──────────────────────────────────────────────
class TestRetryPolicy:
    def test_default_policy(self):
        p = RetryPolicy()
        assert p.max_retries == 3
        assert p.base_delay == 1.0
        assert p.backoff_factor == 2.0
        assert p.max_delay == 300.0

    def test_get_delay_exponential(self):
        p = RetryPolicy(base_delay=1.0, backoff_factor=2.0, max_delay=300.0)
        assert p.get_delay(0) == 1.0
        assert p.get_delay(1) == 2.0
        assert p.get_delay(2) == 4.0
        assert p.get_delay(3) == 8.0

    def test_get_delay_capped(self):
        p = RetryPolicy(base_delay=10.0, backoff_factor=3.0, max_delay=100.0)
        assert p.get_delay(10) == 100.0  # capped


class TestRetryManager:
    def setup_method(self):
        self.rm = RetryManager()

    def test_should_retry(self):
        j = PublishJob()
        j.max_retries = 3
        j.attempts = 0
        assert self.rm.should_retry(j) is True

    def test_should_not_retry_exhausted(self):
        j = PublishJob()
        j.max_retries = 3
        j.attempts = 3
        assert self.rm.should_retry(j) is False

    def test_get_next_delay(self):
        j = PublishJob()
        j.attempts = 0
        delay = self.rm.get_next_delay(j)
        assert delay == 1.0

    def test_record_failure(self):
        j = PublishJob()
        self.rm.record_failure(j, "timeout error")
        assert j.attempts == 1
        assert j.last_error == "timeout error"
        assert self.rm.retry_count == 1

    def test_record_failure_truncates_error(self):
        j = PublishJob()
        self.rm.record_failure(j, "x" * 300)
        assert len(j.last_error) <= 200

    def test_retry_history(self):
        j1 = PublishJob(job_id="j1")
        j1.attempts = 2
        j1.last_error = "error1"
        j2 = PublishJob(job_id="j2")
        j2.attempts = 0
        history = self.rm.get_retry_history([j1, j2])
        assert len(history) == 1
        assert history[0]["job_id"] == "j1"
        assert history[0]["attempts"] == 2

    def test_custom_policy(self):
        policy = RetryPolicy(max_retries=5, base_delay=2.0)
        rm = RetryManager(policy)
        j = PublishJob()
        j.attempts = 0
        assert rm.policy.max_retries == 5
        assert rm.get_next_delay(j) == 2.0


# ─── DeadLetterQueue Tests ───────────────────────────────────────────
class TestDeadLetterQueue:
    def setup_method(self):
        self.dlq = DeadLetterQueue()

    def test_add(self):
        j = PublishJob(job_id="j1")
        entry = self.dlq.add(j, "permanent failure")
        assert entry.job.job_id == "j1"
        assert entry.failure_reason == "permanent failure"
        assert j.status == "dead"
        assert self.dlq.size == 1

    def test_list_entries_all(self):
        self.dlq.add(PublishJob(job_id="j1", platform="facebook"))
        self.dlq.add(PublishJob(job_id="j2", platform="linkedin"))
        entries = self.dlq.list_entries()
        assert len(entries) == 2

    def test_list_entries_by_platform(self):
        self.dlq.add(PublishJob(job_id="j1", platform="facebook"))
        self.dlq.add(PublishJob(job_id="j2", platform="linkedin"))
        entries = self.dlq.list_entries(platform="facebook")
        assert len(entries) == 1
        assert entries[0].job.platform == "facebook"

    def test_recover(self):
        j = PublishJob(job_id="j1")
        self.dlq.add(j, "error")
        recovered = self.dlq.recover(0)
        assert recovered is not None
        assert recovered.status == "pending"
        assert recovered.attempts == 0

    def test_recover_invalid_index(self):
        self.dlq.add(PublishJob(job_id="j1"), "error")
        assert self.dlq.recover(5) is None
        assert self.dlq.recover(-1) is None

    def test_remove(self):
        self.dlq.add(PublishJob(job_id="j1"), "error")
        assert self.dlq.remove(0) is True
        assert self.dlq.size == 0

    def test_remove_invalid_index(self):
        assert self.dlq.remove(99) is False

    def test_recovered_count(self):
        self.dlq.add(PublishJob(job_id="j1"), "e1")
        self.dlq.add(PublishJob(job_id="j2"), "e2")
        self.dlq.recover(0)
        assert self.dlq.recovered_count == 1

    def test_dead_letter_entry_to_dict(self):
        j = PublishJob(job_id="j1", platform="facebook")
        j.attempts = 3
        entry = DeadLetterEntry(j, "API rate limit")
        d = entry.to_dict()
        assert d["job_id"] == "j1"
        assert d["platform"] == "facebook"
        assert d["failure_reason"] == "API rate limit"
        assert d["attempts"] == 3
        assert "timestamp" in d


# ─── TimezoneManager Tests ───────────────────────────────────────────
class TestTimezoneManager:
    def setup_method(self):
        self.tz = TimezoneManager()

    def test_to_utc(self):
        ts = 1000000.0
        utc = self.tz.to_utc(ts, "US/Eastern")
        assert utc == ts - (-5 * 3600)

    def test_to_local(self):
        ts = 1000000.0
        local = self.tz.to_local(ts, "Asia/Tokyo")
        assert local == ts + (9 * 3600)

    def test_convert(self):
        ts = 1000000.0
        result = self.tz.convert(ts, "US/Pacific", "Asia/Tokyo")
        # UTC = ts - (-8*3600) = ts + 8*3600; local = UTC + 9*3600
        expected = ts + (8 * 3600) + (9 * 3600)
        assert result == expected

    def test_convert_same_tz(self):
        ts = 1000000.0
        result = self.tz.convert(ts, "UTC", "UTC")
        assert result == ts

    def test_get_local_hour(self):
        # Fixed timestamp: 2024-01-01 12:00:00 UTC
        ts = 1704110400.0
        hour = self.tz.get_local_hour(ts, "UTC")
        assert 0 <= hour <= 23

    def test_is_business_hours(self):
        # 10:00 UTC should be business hours
        ts = 1704110400.0
        assert self.tz.is_business_hours(ts, "UTC", start=9, end=17) is True

    def test_not_business_hours(self):
        # 03:00 UTC (night)
        ts = 1704085200.0
        assert self.tz.is_business_hours(ts, "UTC", start=9, end=17) is False

    def test_list_timezones(self):
        tzs = TimezoneManager.list_timezones()
        assert "UTC" in tzs
        assert "US/Eastern" in tzs
        assert "Asia/Karachi" in tzs
        assert len(tzs) >= 10

    def test_unknown_tz_defaults_to_zero(self):
        ts = 1000000.0
        result = self.tz.to_utc(ts, "Nonexistent/Zone")
        assert result == ts

    def test_default_tz(self):
        tz = TimezoneManager(default_tz="US/Pacific")
        assert tz._default_tz == "US/Pacific"


# ─── QueueMetrics Tests ──────────────────────────────────────────────
class TestQueueMetrics:
    def setup_method(self):
        self.metrics = QueueMetrics()

    def test_snapshot_empty(self):
        snap = self.metrics.snapshot([])
        assert snap["total"] == 0
        assert snap["completed"] == 0
        assert snap["failed"] == 0

    def test_snapshot_with_jobs(self):
        jobs = []
        for i in range(5):
            j = PublishJob(job_id=f"j{i}")
            j.status = "completed" if i < 3 else "failed"
            jobs.append(j)
        snap = self.metrics.snapshot(jobs)
        assert snap["total"] == 5
        assert snap["completed"] == 3
        assert snap["failed"] == 2
        assert snap["success_rate"] > 0

    def test_snapshot_with_durations(self):
        j1 = PublishJob(job_id="j1")
        j1.status = "completed"
        j1.started_at = time.time() - 2.0
        j1.completed_at = time.time()
        snap = self.metrics.snapshot([j1])
        assert snap["avg_duration_ms"] > 0

    def test_snapshot_retry_rate(self):
        j = PublishJob(job_id="j1")
        j.attempts = 3
        snap = self.metrics.snapshot([j])
        assert snap["retry_rate"] > 0

    def test_get_history(self):
        self.metrics.snapshot([])
        self.metrics.snapshot([])
        history = self.metrics.get_history()
        assert len(history) == 2

    def test_get_latest(self):
        self.metrics.snapshot([])
        latest = self.metrics.get_latest()
        assert "total" in latest

    def test_get_latest_empty(self):
        assert self.metrics.get_latest() == {}

    def test_snapshot_pending_counting(self):
        j1 = PublishJob()
        j1.status = "pending"
        j2 = PublishJob()
        j2.status = "scheduled"
        j3 = PublishJob()
        j3.status = "running"
        snap = self.metrics.snapshot([j1, j2, j3])
        assert snap["pending"] == 2
        assert snap["running"] == 1


# ─── BatchPublisher Tests ────────────────────────────────────────────
class TestBatchResult:
    def test_to_dict(self):
        r = BatchResult("b1")
        r.total_jobs = 5
        r.completed = 4
        r.failed = 1
        d = r.to_dict()
        assert d["batch_id"] == "b1"
        assert d["total_jobs"] == 5
        assert d["completed"] == 4
        assert d["success_rate"] > 0


class TestBatchPublisher:
    def setup_method(self):
        self.bp = BatchPublisher()

    def test_execute_batch_all_success(self):
        jobs = [PublishJob(job_id=f"j{i}") for i in range(3)]
        result = self.bp.execute_batch(jobs, lambda j: True)
        assert result.completed == 3
        assert result.failed == 0
        assert all(r["status"] == "completed" for r in result.results)

    def test_execute_batch_all_fail(self):
        jobs = [PublishJob(job_id=f"j{i}") for i in range(3)]
        result = self.bp.execute_batch(jobs, lambda j: False)
        assert result.completed == 0
        assert result.failed == 3

    def test_execute_batch_mixed(self):
        def executor(j):
            return j.job_id != "j1"
        jobs = [PublishJob(job_id=f"j{i}") for i in range(3)]
        result = self.bp.execute_batch(jobs, executor)
        assert result.completed == 2
        assert result.failed == 1

    def test_execute_batch_exception(self):
        def bad_executor(j):
            raise RuntimeError("API down")
        jobs = [PublishJob(job_id="j1")]
        result = self.bp.execute_batch(jobs, bad_executor)
        assert result.failed == 1
        assert jobs[0].last_error == "API down"

    def test_execute_batch_empty(self):
        result = self.bp.execute_batch([], lambda j: True)
        assert result.total_jobs == 0
        assert result.completed == 0

    def test_execute_batch_sets_status(self):
        j = PublishJob(job_id="j1")
        self.bp.execute_batch([j], lambda j: True)
        assert j.status == "completed"
        assert j.started_at is not None
        assert j.completed_at is not None

    def test_group_by_platform(self):
        jobs = [
            PublishJob(job_id="j1", platform="facebook"),
            PublishJob(job_id="j2", platform="linkedin"),
            PublishJob(job_id="j3", platform="facebook"),
        ]
        groups = self.bp.group_by_platform(jobs)
        assert len(groups) == 2
        assert len(groups["facebook"]) == 2
        assert len(groups["linkedin"]) == 1

    def test_batch_count_increments(self):
        self.bp.execute_batch([], lambda j: True)
        self.bp.execute_batch([], lambda j: True)
        assert self.bp.batch_count == 2

    def test_execute_batch_duration(self):
        result = self.bp.execute_batch([PublishJob()], lambda j: True)
        assert result.duration_ms >= 0

    def test_batch_ids_increment(self):
        r1 = self.bp.execute_batch([], lambda j: True)
        r2 = self.bp.execute_batch([], lambda j: True)
        assert r1.batch_id == "batch_0"
        assert r2.batch_id == "batch_1"


# ─── WorkerManager Tests ─────────────────────────────────────────────
class TestWorker:
    def test_to_dict(self):
        w = Worker("w1")
        d = w.to_dict()
        assert d["worker_id"] == "w1"
        assert d["busy"] is False
        assert d["jobs_processed"] == 0


class TestWorkerManager:
    def setup_method(self):
        self.wm = WorkerManager(pool_size=3)

    def test_pool_size(self):
        assert self.wm.pool_size == 3

    def test_all_idle_initially(self):
        assert self.wm.idle_count() == 3
        assert self.wm.busy_count() == 0

    def test_get_idle_worker(self):
        w = self.wm.get_idle_worker()
        assert w is not None
        assert w.busy is False

    def test_assign_job(self):
        j = PublishJob(job_id="j1")
        w = self.wm.get_idle_worker()
        assert self.wm.assign_job(w.worker_id, j) is True
        assert w.busy is True
        assert w.current_job == "j1"

    def test_assign_to_busy_worker(self):
        j = PublishJob(job_id="j1")
        w = self.wm.get_idle_worker()
        self.wm.assign_job(w.worker_id, j)
        assert self.wm.assign_job(w.worker_id, PublishJob(job_id="j2")) is False

    def test_complete_job(self):
        j = PublishJob(job_id="j1")
        w = self.wm.get_idle_worker()
        self.wm.assign_job(w.worker_id, j)
        self.wm.complete_job(w.worker_id)
        assert w.busy is False
        assert w.current_job is None
        assert w.jobs_processed == 1

    def test_total_processed(self):
        w = self.wm.get_idle_worker()
        self.wm.assign_job(w.worker_id, PublishJob(job_id="j1"))
        self.wm.complete_job(w.worker_id)
        self.wm.assign_job(w.worker_id, PublishJob(job_id="j2"))
        self.wm.complete_job(w.worker_id)
        assert self.wm.total_processed == 2

    def test_get_workers(self):
        workers = self.wm.get_workers()
        assert len(workers) == 3
        assert all("worker_id" in w for w in workers)

    def test_no_idle_when_all_busy(self):
        for i in range(3):
            w = self.wm.get_idle_worker()
            self.wm.assign_job(w.worker_id, PublishJob(job_id=f"j{i}"))
        assert self.wm.get_idle_worker() is None
        assert self.wm.idle_count() == 0

    def test_assign_nonexistent_worker(self):
        assert self.wm.assign_job("fake_worker", PublishJob()) is False


# ─── QueueOrchestrator Tests ─────────────────────────────────────────
class TestQueueOrchestrator:
    def setup_method(self):
        self.orch = QueueOrchestrator()

    def test_submit_job(self):
        job = self.orch.submit_job("c1", "facebook", "Hello")
        assert job.job_id.startswith("job_")
        assert job.platform == "facebook"
        assert job.status == "scheduled"
        assert self.orch.queue.size == 1

    def test_submit_with_priority(self):
        job = self.orch.submit_job("c1", "fb", "Hi", priority="critical")
        assert job.priority == JOB_PRIORITIES["critical"]

    def test_submit_scheduled(self):
        future = time.time() + 3600
        job = self.orch.submit_job("c1", "fb", "Hi", scheduled_time=future)
        assert job.scheduled_time == future
        assert job.status == "scheduled"

    def test_submit_with_media(self):
        job = self.orch.submit_job("c1", "fb", "Hi", media_paths=["/img.png"])
        assert job.media_paths == ["/img.png"]

    def test_process_next_success(self):
        self.orch.submit_job("c1", "facebook", "Hello")
        result = self.orch.process_next(lambda j: True)
        assert result is not None
        assert result["status"] == "completed"

    def test_process_next_failure_retries(self):
        self.orch.submit_job("c1", "facebook", "Hello")
        result = self.orch.process_next(lambda j: False)
        assert result is not None
        assert result["status"] == "pending"  # re-queued for retry

    def test_process_next_failure_exhausted(self):
        job = self.orch.submit_job("c1", "facebook", "Hello")
        job.max_retries = 1
        self.orch.process_next(lambda j: False)
        result = self.orch.process_next(lambda j: False)
        # after max retries, should be in dead letter
        assert self.orch.dead_letter.size >= 1

    def test_process_next_exception(self):
        self.orch.submit_job("c1", "fb", "Hi")
        def boom(j):
            raise ValueError("boom")
        result = self.orch.process_next(boom)
        assert result is not None
        assert result["status"] in ("pending", "dead")

    def test_process_next_empty_queue(self):
        assert self.orch.process_next(lambda j: True) is None

    def test_process_batch(self):
        for i in range(3):
            self.orch.submit_job(f"c{i}", "fb", f"msg{i}")
        result = self.orch.process_batch(lambda j: True, max_jobs=10)
        assert result["total_jobs"] == 3
        assert result["completed"] == 3

    def test_process_batch_empty(self):
        result = self.orch.process_batch(lambda j: True)
        assert result["processed"] == 0

    def test_get_status(self):
        self.orch.submit_job("c1", "fb", "Hi")
        status = self.orch.get_status()
        assert status["queue_size"] == 1
        assert "workers" in status
        assert "dead_letter_size" in status

    def test_take_metrics_snapshot(self):
        self.orch.submit_job("c1", "fb", "Hi")
        snap = self.orch.take_metrics_snapshot()
        assert "total" in snap

    def test_cancel_job(self):
        job = self.orch.submit_job("c1", "fb", "Hi")
        assert self.orch.cancel_job(job.job_id) is True

    def test_recover_from_dead_letter(self):
        job = self.orch.submit_job("c1", "fb", "Hi")
        job.max_retries = 0
        self.orch.process_next(lambda j: False)
        assert self.orch.dead_letter.size == 1
        recovered = self.orch.recover_from_dead_letter(0)
        assert recovered is not None
        assert recovered.status == "pending"
        assert self.orch.queue.size == 1

    def test_events_recorded(self):
        self.orch.submit_job("c1", "fb", "Hi")
        self.orch.process_next(lambda j: True)
        events = self.orch.events
        assert len(events) >= 2
        assert events[0]["event"] == "job_submitted"
        assert events[1]["event"] == "job_completed"

    def test_events_retry_recorded(self):
        self.orch.submit_job("c1", "fb", "Hi")
        self.orch.process_next(lambda j: False)
        events = self.orch.events
        retry_events = [e for e in events if e["event"] == "job_retrying"]
        assert len(retry_events) == 1

    def test_custom_components(self):
        q = JobQueue(max_size=50)
        rm = RetryManager(RetryPolicy(max_retries=5))
        dlq = DeadLetterQueue()
        orch = QueueOrchestrator(queue=q, retry_manager=rm, dead_letter=dlq)
        assert orch.queue._max_size == 50
        assert orch.retry.policy.max_retries == 5


# ─── Exceptions Tests ────────────────────────────────────────────────
class TestExceptions:
    def test_queue_error(self):
        assert issubclass(QueueError, Exception)
        try:
            raise QueueError("test")
        except QueueError:
            pass

    def test_job_not_found(self):
        assert issubclass(JobNotFoundError, QueueError)

    def test_queue_full(self):
        assert issubclass(QueueFullError, QueueError)

    def test_exceptions_inherit(self):
        assert issubclass(JobNotFoundError, Exception)
        assert issubclass(QueueFullError, Exception)
