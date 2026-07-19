"""Tests for Phase 2 — Async Runtime (15 modules)."""
from __future__ import annotations
import asyncio
import time
import threading
import pytest

# ─── Module 1: Async Scheduler ─────────────────────────────────────
from layers.layer15_async_runtime.modules.async_scheduler.async_scheduler import AsyncScheduler, TaskState


class TestAsyncScheduler:
    def setup_method(self):
        self.scheduler = AsyncScheduler(max_concurrent=3)

    def test_schedule_task(self):
        task = self.scheduler.schedule(lambda: "result")
        assert task.state == TaskState.SCHEDULED

    def test_execute_task(self):
        async def run():
            task = self.scheduler.schedule(lambda: "ok")
            result = await self.scheduler.execute_task(task)
            return result
        result = asyncio.get_event_loop().run_until_complete(run())
        assert result["state"] == "completed"

    def test_execute_with_retry(self):
        call_count = [0]
        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("not yet")
            return "ok"
        async def run():
            task = self.scheduler.schedule(flaky, max_retries=3)
            result = await self.scheduler.execute_task(task)
            return result
        result = asyncio.get_event_loop().run_until_complete(run())
        assert result["state"] == "completed"

    def test_cancel(self):
        task = self.scheduler.schedule(lambda: "ok")
        assert self.scheduler.cancel(task.task_id)
        assert task.state == TaskState.CANCELLED

    def test_stats(self):
        task = self.scheduler.schedule(lambda: "ok")
        stats = self.scheduler.stats()
        assert stats["total"] == 1

    def test_list_tasks(self):
        self.scheduler.schedule(lambda: "a")
        self.scheduler.schedule(lambda: "b")
        assert len(self.scheduler.list_tasks()) == 2


# ─── Module 2: Coroutine Manager ──────────────────────────────────
from layers.layer15_async_runtime.modules.coroutine_manager.coroutine_manager import CoroutineManager, CoroutineState


class TestCoroutineManager:
    def setup_method(self):
        self.cm = CoroutineManager()

    def test_create(self):
        coro = self.cm.create("test", lambda: 42)
        assert coro.name == "test"
        assert coro.state == CoroutineState.CREATED

    async def _start_coro(self):
        coro = self.cm.create("test", lambda: 42)
        result = await self.cm.start(coro.coro_id)
        return result

    def test_start(self):
        result = asyncio.get_event_loop().run_until_complete(self._start_coro())
        assert result["state"] == "completed"

    def test_cancel(self):
        coro = self.cm.create("test", lambda: 42)
        assert self.cm.cancel(coro.coro_id)
        assert coro.state == CoroutineState.CANCELLED

    def test_count(self):
        self.cm.create("a", lambda: 1)
        self.cm.create("b", lambda: 2)
        assert self.cm.count() == 2


# ─── Module 3: Task Queue ──────────────────────────────────────────
from layers.layer15_async_runtime.modules.task_queue.task_queue import TaskQueue, QueueState


class TestTaskQueue:
    def setup_method(self):
        self.tq = TaskQueue(max_size=100)

    async def _run(self):
        item = await self.tq.enqueue({"data": 1})
        assert item.item_id is not None
        dequeued = await self.tq.dequeue(timeout=1.0)
        return dequeued

    def test_enqueue_dequeue(self):
        item = asyncio.get_event_loop().run_until_complete(self._run())
        assert item is not None

    def test_stats(self):
        stats = self.tq.stats()
        assert stats["state"] == "active"
        assert stats["max_size"] == 100

    def test_pause_resume(self):
        self.tq.pause()
        assert self.tq.stats()["state"] == "paused"
        self.tq.resume()
        assert self.tq.stats()["state"] == "active"


# ─── Module 4: Priority Queue ─────────────────────────────────────
from layers.layer15_async_runtime.modules.priority_queue.priority_queue import PriorityQueue, Priority


class TestPriorityQueue:
    def setup_method(self):
        self.pq = PriorityQueue()

    def test_push_pop(self):
        self.pq.push("low", Priority.LOW)
        self.pq.push("high", Priority.HIGH)
        item = self.pq.pop()
        assert item.payload == "high"

    def test_peek(self):
        self.pq.push("normal", Priority.NORMAL)
        item = self.pq.peek()
        assert item.payload == "normal"
        assert self.pq.size() == 1

    def test_remove(self):
        item = self.pq.push("test", Priority.NORMAL)
        assert self.pq.remove(item.item_id)
        assert self.pq.is_empty()

    def test_update_priority(self):
        item = self.pq.push("test", Priority.LOW)
        assert self.pq.update_priority(item.item_id, Priority.CRITICAL)
        top = self.pq.peek()
        assert top.priority == Priority.CRITICAL

    def test_stats(self):
        self.pq.push("a", Priority.HIGH)
        self.pq.push("b", Priority.LOW)
        stats = self.pq.stats()
        assert stats["size"] == 2


# ─── Module 5: Background Jobs ────────────────────────────────────
from layers.layer15_async_runtime.modules.background_jobs.background_jobs import BackgroundJobs, JobState


class TestBackgroundJobs:
    def setup_method(self):
        self.bj = BackgroundJobs()

    def test_add_job(self):
        job = self.bj.add_job("test", lambda: 42)
        assert job.name == "test"
        assert job.state == JobState.QUEUED

    async def _run_job(self):
        job = self.bj.add_job("test", lambda: 42)
        result = await self.bj.execute_job(job)
        return result

    def test_execute_job(self):
        result = asyncio.get_event_loop().run_until_complete(self._run_job())
        assert result["state"] == "completed"

    def test_cancel_job(self):
        job = self.bj.add_job("test", lambda: 42)
        assert self.bj.cancel_job(job.job_id)
        assert job.state == JobState.CANCELLED

    def test_stats(self):
        self.bj.add_job("a", lambda: 1)
        stats = self.bj.stats()
        assert stats["total"] == 1


# ─── Module 6: Thread Pool ─────────────────────────────────────────
from layers.layer15_async_runtime.modules.thread_pool.thread_pool import ThreadPool


class TestThreadPool:
    def setup_method(self):
        self.pool = ThreadPool(max_workers=2)

    def test_submit_get_result(self):
        self.pool.start()
        task = self.pool.submit(lambda x: x * 2, 5)
        result = self.pool.get_result(task.task_id, timeout=5.0)
        assert result["status"] == "completed"
        assert result["result"] == 10
        self.pool.stop()

    def test_map(self):
        self.pool.start()
        results = self.pool.map(lambda x: x * 2, [1, 2, 3])
        assert results == [2, 4, 6]
        self.pool.stop()

    def test_stats(self):
        stats = self.pool.stats()
        assert stats["max_workers"] == 2


# ─── Module 7: Cancellation Engine ────────────────────────────────
from layers.layer15_async_runtime.modules.cancellation_engine.cancellation_engine import CancellationEngine, CancellationTokenState


class TestCancellationEngine:
    def setup_method(self):
        self.ce = CancellationEngine()

    def test_create_token(self):
        token = self.ce.create_token()
        assert token.state == CancellationTokenState.ACTIVE

    def test_cancel(self):
        token = self.ce.create_token()
        assert self.ce.cancel(token.token_id, reason="timeout")
        assert self.ce.is_cancelled(token.token_id)
        assert token.reason == "timeout"

    def test_cleanup(self):
        t1 = self.ce.create_token()
        t2 = self.ce.create_token()
        self.ce.cancel(t1.token_id)
        cleaned = self.ce.cleanup()
        assert cleaned == 1
        assert self.ce.count() == 1


# ─── Module 8: Timeout Engine ──────────────────────────────────────
from layers.layer15_async_runtime.modules.timeout_engine.timeout_engine import TimeoutEngine


class TestTimeoutEngine:
    def setup_method(self):
        self.te = TimeoutEngine()

    async def _run(self):
        return await self.te.run_with_timeout(lambda: "ok", timeout_seconds=5.0, name="test")

    def test_run_within_timeout(self):
        result = asyncio.get_event_loop().run_until_complete(self._run())
        assert result["status"] == "completed"

    async def _run_timeout(self):
        async def slow():
            await asyncio.sleep(10)
            return "slow"
        return await self.te.run_with_timeout(slow, timeout_seconds=0.01, name="slow")

    def test_run_timeout(self):
        result = asyncio.get_event_loop().run_until_complete(self._run_timeout())
        assert result["status"] == "timed_out"

    def test_stats(self):
        asyncio.get_event_loop().run_until_complete(self._run())
        stats = self.te.stats()
        assert stats["total"] == 1


# ─── Module 9: Retry Engine ────────────────────────────────────────
from layers.layer15_async_runtime.modules.retry_engine.retry_engine import RetryEngine, RetryConfig


class TestRetryEngine:
    def setup_method(self):
        self.re = RetryEngine()

    def test_sync_retry_success(self):
        call_count = [0]
        def flaky():
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("fail")
            return "ok"
        config = RetryConfig(max_retries=3, base_delay=0.01, jitter=False)
        result = self.re.execute_sync(flaky, config)
        assert result.success
        assert result.attempts == 2

    def test_sync_retry_exhausted(self):
        def always_fail():
            raise Exception("always")
        config = RetryConfig(max_retries=2, base_delay=0.01, jitter=False)
        result = self.re.execute_sync(always_fail, config)
        assert not result.success
        assert result.attempts == 3

    def test_stats(self):
        config = RetryConfig(max_retries=0)
        self.re.execute_sync(lambda: "ok", config)
        stats = self.re.stats()
        assert stats["total"] == 1
        assert stats["success"] == 1


# ─── Module 10: Resource Pool ──────────────────────────────────────
from layers.layer15_async_runtime.modules.resource_pool.resource_pool import ResourcePool


class TestResourcePool:
    def setup_method(self):
        self.pool = ResourcePool("test_pool")

    def test_add_resource(self):
        r = self.pool.add_resource("conn1")
        assert r.resource == "conn1"
        assert self.pool.size() == 1

    async def _acquire_release(self):
        self.pool.add_resource("conn1")
        self.pool.add_resource("conn2")
        self.pool.initialize()
        res = await self.pool.acquire(timeout=1.0)
        assert res is not None
        await self.pool.release(res)
        return True

    def test_acquire_release(self):
        result = asyncio.get_event_loop().run_until_complete(self._acquire_release())
        assert result

    def test_stats(self):
        self.pool.add_resource("a")
        self.pool.add_resource("b")
        stats = self.pool.stats()
        assert stats["total"] == 2


# ─── Module 11: Semaphore Manager ──────────────────────────────────
from layers.layer15_async_runtime.modules.semaphore_manager.semaphore_manager import SemaphoreManager


class TestSemaphoreManager:
    def setup_method(self):
        self.sm = SemaphoreManager()

    def test_create(self):
        sem = self.sm.create("db_pool", max_permits=5)
        assert sem.max_permits == 5

    def test_acquire_release(self):
        self.sm.create("test", max_permits=2)
        assert self.sm.acquire_sync("test")
        assert self.sm.acquire_sync("test")
        assert self.sm.release_sync("test")
        assert self.sm.count() == 1

    def test_remove(self):
        self.sm.create("test", max_permits=1)
        assert self.sm.remove("test")
        assert self.sm.count() == 0

    def test_stats(self):
        self.sm.create("a", max_permits=5)
        self.sm.create("b", max_permits=3)
        stats = self.sm.stats()
        assert stats["total_semaphores"] == 2
        assert stats["total_permits"] == 8


# ─── Module 12: Async Event Loop ──────────────────────────────────
from layers.layer15_async_runtime.modules.async_event_loop.async_event_loop import AsyncEventLoop, LoopState


class TestAsyncEventLoop:
    def setup_method(self):
        self.ael = AsyncEventLoop()

    def test_create_loop(self):
        info = self.ael.create_loop("main")
        assert info.loop_id == "main"

    def test_list_loops(self):
        self.ael.create_loop("a")
        self.ael.create_loop("b")
        assert len(self.ael.list_loops()) == 2

    def test_stop_loop(self):
        info = self.ael.create_loop("test")
        assert self.ael.stop_loop("test")
        assert info.state == LoopState.STOPPED

    def test_stats(self):
        self.ael.create_loop("a")
        stats = self.ael.stats()
        assert stats["total_loops"] == 1


# ─── Module 13: Future Manager ────────────────────────────────────
from layers.layer15_async_runtime.modules.future_manager.future_manager import FutureManager, FutureState


class TestFutureManager:
    def setup_method(self):
        self.fm = FutureManager()

    def test_stats(self):
        stats = self.fm.stats()
        assert stats["total"] == 0


# ─── Module 14: Promise Manager ───────────────────────────────────
from layers.layer15_async_runtime.modules.promise_manager.promise_manager import PromiseManager, PromiseState


class TestPromiseManager:
    def setup_method(self):
        self.pm = PromiseManager()

    def test_create_resolve(self):
        p = self.pm.create("test")
        assert p.state == PromiseState.PENDING
        assert self.pm.resolve(p.promise_id, result="done")
        assert p.state == PromiseState.RESOLVED
        assert p.result == "done"

    def test_create_reject(self):
        p = self.pm.create("test")
        assert self.pm.reject(p.promise_id, error="failed")
        assert p.state == PromiseState.REJECTED

    def test_list_by_state(self):
        p1 = self.pm.create("a")
        p2 = self.pm.create("b")
        self.pm.resolve(p1.promise_id)
        resolved = self.pm.list_promises(state=PromiseState.RESOLVED)
        assert len(resolved) == 1

    def test_stats(self):
        self.pm.create("a")
        self.pm.create("b")
        stats = self.pm.stats()
        assert stats["total"] == 2
        assert stats["pending"] == 2

    def test_clear_completed(self):
        p1 = self.pm.create("a")
        p2 = self.pm.create("b")
        self.pm.resolve(p1.promise_id)
        cleared = self.pm.clear_completed()
        assert cleared == 1
        assert self.pm.stats()["total"] == 1
