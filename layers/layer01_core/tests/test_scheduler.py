"""
Tests for Scheduler Module
Layer 1: Core System — Module 7

Run: python -m pytest layers/layer01_core/tests/test_scheduler.py -v
"""

import pytest
from datetime import datetime
from layers.layer01_core.modules.scheduler.cron_parser import CronParser
from layers.layer01_core.modules.scheduler.task_queue import Task, TaskQueue, TaskPriority, TaskStatus
from layers.layer01_core.modules.scheduler.retry_manager import RetryManager
from layers.layer01_core.modules.scheduler.scheduler_manager import SchedulerManager


@pytest.fixture
def scheduler():
    s = SchedulerManager()
    return s


# ── Test 1: Cron Parser ────────────────────

class TestCronParser:
    def test_valid_expression(self):
        cron = CronParser("0 20 * * 1-5")
        assert len(cron._minute) == 1
        assert 20 in cron._hour

    def test_wildcard_all(self):
        cron = CronParser("* * * * *")
        assert len(cron._minute) == 60

    def test_is_match(self):
        cron = CronParser("0 14 * * *")
        dt = datetime(2026, 7, 13, 14, 0)
        assert cron.is_match(dt) is True
        dt2 = datetime(2026, 7, 13, 15, 0)
        assert cron.is_match(dt2) is False

    def test_get_next_run(self):
        cron = CronParser("0 20 * * *")
        now = datetime(2026, 7, 13, 10, 0)
        nxt = cron.get_next_run(now)
        assert nxt.hour == 20
        assert nxt >= now

    def test_describe(self):
        cron = CronParser("0 20 * * 1-5")
        desc = cron.describe()
        assert "20" in desc

    def test_invalid_expression(self):
        with pytest.raises(ValueError):
            CronParser("invalid")


# ── Test 2: Task Queue ─────────────────────

class TestTaskQueue:
    def test_add_task(self):
        q = TaskQueue()
        t = Task(name="test", job_type="dummy")
        tid = q.add(t)
        assert q.get(tid) is not None

    def test_priority_ordering(self):
        q = TaskQueue()
        q.add(Task(name="low", job_type="d", priority=TaskPriority.LOW))
        q.add(Task(name="high", job_type="d", priority=TaskPriority.HIGH))
        q.add(Task(name="normal", job_type="d", priority=TaskPriority.NORMAL))
        nxt = q.next_task()
        assert nxt.name == "high"

    def test_dependencies_met(self):
        q = TaskQueue()
        dep_id = q.add(Task(name="dep", job_type="d"))
        main_id = q.add(Task(name="main", job_type="d", dependencies=[dep_id]))
        # dep not done yet
        assert q.next_task().name == "dep"
        # Complete dep
        q.update_status(dep_id, TaskStatus.SUCCESS)
        nxt = q.next_task()
        assert nxt.name == "main"

    def test_cancel(self):
        q = TaskQueue()
        tid = q.add(Task(name="c", job_type="d"))
        q.cancel(tid)
        assert q.get(tid).status == TaskStatus.CANCELLED

    def test_stats(self):
        q = TaskQueue()
        q.add(Task(name="a", job_type="d"))
        q.add(Task(name="b", job_type="d"))
        assert q.pending_count == 2
        assert q.total_count == 2


# ── Test 3: Retry Manager ──────────────────

class TestRetryManager:
    def test_record_failure(self):
        rm = RetryManager()
        info = rm.record_failure("t1")
        assert info["attempt"] == 1
        assert info["delay_seconds"] > 0

    def test_exponential_backoff(self):
        rm = RetryManager(base_delay=1.0)
        rm.record_failure("t1")
        info2 = rm.record_failure("t1")
        info3 = rm.record_failure("t1")
        assert info3["delay_seconds"] > info2["delay_seconds"]

    def test_should_retry(self):
        rm = RetryManager()
        assert rm.should_retry("t1", max_retries=3) is True
        rm.record_failure("t1")
        rm.record_failure("t1")
        rm.record_failure("t1")
        assert rm.should_retry("t1", max_retries=3) is False

    def test_record_success(self):
        rm = RetryManager()
        rm.record_failure("t1")
        rm.record_success("t1")
        assert rm.get_retry_count("t1") == 0


# ── Test 4: Scheduler Manager ──────────────

class TestSchedulerManager:
    def test_add_task(self, scheduler):
        tid = scheduler.add_task("test_job", "test_type")
        assert scheduler.get_task(tid) is not None

    def test_register_and_run(self, scheduler):
        results = {"called": False}
        def handler(params):
            results["called"] = True
        scheduler.register_handler("my_job", handler)
        tid = scheduler.add_task("test", "my_job")
        result = scheduler.run_next()
        assert result["status"] == "SUCCESS"
        assert results["called"] is True

    def test_run_with_dependency(self, scheduler):
        order = []
        scheduler.register_handler("step1", lambda p: order.append("step1"))
        scheduler.register_handler("step2", lambda p: order.append("step2"))
        dep_id = scheduler.add_task("step1", "step1", priority="HIGH")
        scheduler.add_task("step2", "step2", dependencies=[dep_id])
        scheduler.run_all()
        assert order == ["step1", "step2"]

    def test_run_all(self, scheduler):
        scheduler.register_handler("noop", lambda p: None)
        scheduler.add_task("a", "noop")
        scheduler.add_task("b", "noop")
        scheduler.add_task("c", "noop")
        results = scheduler.run_all()
        assert len(results) == 3
        assert all(r["status"] == "SUCCESS" for r in results)

    def test_handler_failure(self, scheduler):
        def bad_handler(params):
            raise ValueError("boom")
        scheduler.register_handler("bad", bad_handler)
        scheduler.add_task("fail", "bad", max_retries=0)
        result = scheduler.run_next()
        assert result["status"] == "FAILED"
        assert "boom" in result["error"]

    def test_retry_on_failure(self, scheduler):
        attempt = {"count": 0}
        def flaky(params):
            attempt["count"] += 1
            if attempt["count"] < 2:
                raise ValueError("temporary")
        scheduler.register_handler("flaky", flaky)
        scheduler.add_task("retry_task", "flaky", max_retries=3)
        result = scheduler.run_next()
        assert result["status"] == "RETRY"

    def test_no_handler_registered(self, scheduler):
        scheduler.add_task("orphan", "nonexistent_type")
        result = scheduler.run_next()
        assert result["status"] == "FAILED"

    def test_decision_conditions(self, scheduler):
        scheduler.register_handler("cond", lambda p: None)
        # Condition: engagement > 100, actual = 50 → skip
        scheduler.add_task("low_engagement", "cond", conditions={
            "engagement": {"op": "gt", "value": 100, "actual": 50}
        })
        result = scheduler.run_next()
        assert result["status"] == "SKIPPED"

    def test_conditions_met(self, scheduler):
        scheduler.register_handler("cond", lambda p: None)
        scheduler.add_task("high_engagement", "cond", conditions={
            "engagement": {"op": "gt", "value": 100, "actual": 150}
        })
        result = scheduler.run_next()
        assert result["status"] == "SUCCESS"


# ── Test 5: Cron Jobs ──────────────────────

class TestCronJobs:
    def test_add_cron_job(self, scheduler):
        tid = scheduler.add_cron_job("daily_post", "0 20 * * *", "my_job")
        assert scheduler._cron_jobs[tid] is not None


# ── Test 6: History & Stats ────────────────

class TestHistoryStats:
    def test_history_recorded(self, scheduler):
        scheduler.register_handler("noop", lambda p: None)
        scheduler.add_task("tracked", "noop")
        scheduler.run_all()
        history = scheduler.get_history()
        assert len(history) == 1

    def test_queue_stats(self, scheduler):
        scheduler.register_handler("noop", lambda p: None)
        scheduler.add_task("a", "noop")
        scheduler.add_task("b", "noop")
        stats = scheduler.get_queue_stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2


# ── Test 7: Health Check ───────────────────

class TestHealthCheck:
    def test_health_check(self, scheduler):
        report = scheduler.health_check()
        assert "checks" in report
        assert "overall" in report
