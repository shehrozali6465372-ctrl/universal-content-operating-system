"""Production gate for Layer 15 async runtime primitives."""
from __future__ import annotations

import asyncio

import pytest

from layers.layer15_async_runtime.modules.async_event_loop.async_event_loop import AsyncEventLoop
from layers.layer15_async_runtime.modules.async_scheduler.async_scheduler import AsyncScheduler, TaskState
from layers.layer15_async_runtime.modules.background_jobs.background_jobs import BackgroundJobs, JobState
from layers.layer15_async_runtime.modules.coroutine_manager.coroutine_manager import CoroutineManager, CoroutineState
from layers.layer15_async_runtime.modules.resource_pool.resource_pool import ResourcePool
from layers.layer15_async_runtime.modules.retry_engine.retry_engine import RetryConfig, RetryEngine
from layers.layer15_async_runtime.modules.semaphore_manager.semaphore_manager import SemaphoreManager
from layers.layer15_async_runtime.modules.task_queue.task_queue import QueueState, TaskQueue
from layers.layer15_async_runtime.modules.timeout_engine.timeout_engine import TimeoutEngine
from layers.layer15_async_runtime.modules.worker_pool.worker_pool import WorkerPool


@pytest.mark.asyncio
async def test_event_loop_rejects_nested_run_and_tracks_failures() -> None:
    manager = AsyncEventLoop()
    info = manager.create_loop("gate")
    assert await manager.run_coroutine(asyncio.sleep(0, result=3)) == 3
    assert info.tasks_spawned == 1
    assert info.tasks_completed == 1

    async def nested() -> None:
        with pytest.raises(RuntimeError):
            manager.run_until_complete(asyncio.sleep(0))

    await nested()


@pytest.mark.asyncio
async def test_scheduler_bounds_concurrency_and_retries() -> None:
    scheduler = AsyncScheduler(max_concurrent=2)
    active = 0
    peak = 0
    attempts = 0

    async def work() -> int:
        nonlocal active, peak, attempts
        active += 1
        peak = max(peak, active)
        attempts += 1
        await asyncio.sleep(0)
        active -= 1
        if attempts == 1:
            raise ValueError("retry")
        return 7

    task = scheduler.schedule(work, max_retries=1)
    result = await scheduler.execute_task(task)
    assert result["state"] == TaskState.COMPLETED.value
    assert attempts == 2
    assert peak == 1


@pytest.mark.asyncio
async def test_scheduler_cancel_running_task() -> None:
    scheduler = AsyncScheduler()
    started = asyncio.Event()

    async def work() -> None:
        started.set()
        await asyncio.sleep(10)

    task = scheduler.schedule(work)
    runner = asyncio.create_task(scheduler.execute_task(task))
    await started.wait()
    assert scheduler.cancel(task.task_id) is True
    with pytest.raises(asyncio.CancelledError):
        await runner
    assert task.state == TaskState.CANCELLED


@pytest.mark.asyncio
async def test_background_job_retries_iteratively_and_records_history() -> None:
    jobs = BackgroundJobs()
    attempts = 0

    async def work() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("transient")
        return "ok"

    job = jobs.add_job("gate", work, max_retries=2)
    result = await jobs.execute_job(job)
    assert result["state"] == JobState.COMPLETED.value
    assert attempts == 3
    assert len(jobs.get_history()) == 1


@pytest.mark.asyncio
async def test_coroutine_manager_can_cancel_running_coroutine() -> None:
    manager = CoroutineManager()
    started = asyncio.Event()

    async def work() -> None:
        started.set()
        await asyncio.sleep(10)

    coro = manager.create("gate", work)
    task = asyncio.create_task(manager.start(coro.coro_id))
    await started.wait()
    assert manager.cancel(coro.coro_id) is True
    with pytest.raises(asyncio.CancelledError):
        await task
    assert coro.state == CoroutineState.CANCELLED


@pytest.mark.asyncio
async def test_semaphore_actually_consumes_and_releases_permit() -> None:
    manager = SemaphoreManager()
    manager.create("gate", 1)
    assert await manager.acquire("gate") is True
    assert await manager.acquire("gate", timeout=0.001) is False
    assert manager.release("gate") is True
    assert await manager.acquire("gate", timeout=0.1) is True
    assert manager.release("gate") is True


@pytest.mark.asyncio
async def test_task_queue_respects_stop_and_exact_completion() -> None:
    queue = TaskQueue(max_size=1)
    item = await queue.enqueue("x")
    assert queue.stats()["total_enqueued"] == 1
    got = await queue.dequeue()
    assert got is item
    assert queue.complete(item.item_id, "ok") is True
    assert queue.complete(item.item_id, "again") is False
    queue.stop()
    rejected = await queue.enqueue("y")
    assert rejected.status == "rejected"
    assert queue.stats()["state"] == QueueState.STOPPED.value


@pytest.mark.asyncio
async def test_resource_pool_does_not_duplicate_resources_on_reinitialize() -> None:
    pool = ResourcePool()
    resource = object()
    pool.add_resource(resource, "r1")
    pool.initialize()
    pool.initialize()
    assert pool.available() == 1
    acquired = await pool.acquire()
    assert acquired is resource
    assert pool.in_use() == 1
    assert await pool.release(resource) is True
    assert pool.available() == 1


@pytest.mark.asyncio
async def test_worker_pool_start_stop_is_idempotent() -> None:
    pool = WorkerPool(pool_size=2)
    await pool.start()
    await pool.start()
    async def work() -> str:
        return "ok"
    await pool.submit("t1", work)
    await asyncio.sleep(0.05)
    assert pool.get_result("t1") == {"status": "completed", "result": "ok"}
    await pool.stop()
    await pool.stop()
    assert all(w["state"] == "stopped" for w in pool.list_workers())


@pytest.mark.asyncio
async def test_timeout_engine_times_out_and_cancels_coroutine() -> None:
    engine = TimeoutEngine()

    async def slow() -> None:
        await asyncio.sleep(1)

    result = await engine.run_with_timeout(slow, 0.001, "gate")
    assert result["status"] == "timed_out"
    assert result["entry"]["result"] == "timed_out"


@pytest.mark.asyncio
async def test_retry_engine_does_not_retry_cancellation() -> None:
    engine = RetryEngine()

    async def cancelled() -> None:
        raise asyncio.CancelledError

    with pytest.raises(asyncio.CancelledError):
        await engine.execute_with_retry(cancelled, RetryConfig(max_retries=3))


def test_retry_config_rejects_invalid_bounds() -> None:
    with pytest.raises(ValueError):
        RetryConfig(base_delay=2, max_delay=1)


@pytest.mark.asyncio
async def test_layer15_modules_compile_and_basic_lifecycle() -> None:
    scheduler = AsyncScheduler()
    task = scheduler.schedule(lambda: 1)
    result = await scheduler.execute_task(task)
    assert result["state"] == TaskState.COMPLETED.value
