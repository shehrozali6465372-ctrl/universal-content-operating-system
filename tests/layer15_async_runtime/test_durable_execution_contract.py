"""Layer 15 durable-execution contract tests against real PostgreSQL."""
from __future__ import annotations

import uuid

import pytest

from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager
from layers.layer15_async_runtime.modules.durable_execution.durable_execution import DurableExecutionStore


def _manager() -> PostgreSQLManager:
    manager = PostgreSQLManager()
    assert manager.initialize() is True
    return manager


def _workflow(store: DurableExecutionStore) -> str:
    workflow = str(uuid.uuid4())
    store.ensure_workflow(
        workflow,
        f"tenant-{workflow}",
        f"workspace-{workflow}",
        f"brand-{workflow}",
        f"account-{workflow}",
        "facebook",
    )
    return workflow


@pytest.mark.integration
def test_durable_task_restart_safe_claim_complete_and_dedupe() -> None:
    manager = _manager()
    store = DurableExecutionStore(manager)
    workflow = _workflow(store)
    dedupe = f"task-{uuid.uuid4()}"
    try:
        first = store.enqueue(
            workflow_id=workflow,
            task_type="test.complete",
            payload={"value": 42},
            dedupe_key=dedupe,
        )
        same = store.enqueue(
            workflow_id=workflow,
            task_type="test.complete",
            payload={"value": 42},
            dedupe_key=dedupe,
        )
        assert same.task_id == first.task_id
        assert same.state == "READY"

        claimed = store.claim("worker-a", lease_seconds=60)
        assert claimed is not None
        assert claimed.task_id == first.task_id
        assert claimed.state == "RUNNING"
        assert claimed.attempt_count == 1

        assert store.complete(first.task_id, "worker-a", {"ok": True}) is True
        done = store.get(first.task_id)
        assert done is not None
        assert done.state == "COMPLETED"
    finally:
        pool = manager._pool
        if pool:
            with pool.transaction() as conn:
                conn.cursor().execute(
                    "DELETE FROM outbox_events WHERE aggregate_type='durable_task' "
                    "AND aggregate_id IN (SELECT task_id FROM durable_tasks WHERE workflow_id=%s)",
                    (uuid.UUID(workflow),),
                )
                conn.cursor().execute(
                    "DELETE FROM durable_tasks WHERE workflow_id=%s",
                    (uuid.UUID(workflow),),
                )
                conn.cursor().execute(
                    "DELETE FROM workflow_runs WHERE workflow_id=%s",
                    (uuid.UUID(workflow),),
                )
        manager.close()


@pytest.mark.integration
def test_durable_task_failure_retries_then_dead_letters() -> None:
    manager = _manager()
    store = DurableExecutionStore(manager)
    workflow = _workflow(store)
    task = None
    try:
        task = store.enqueue(
            workflow_id=workflow,
            task_type="test.retry",
            payload={"value": "x"},
            dedupe_key=f"retry-{uuid.uuid4()}",
            max_attempts=2,
            backoff_seconds=1,
        )
        first = store.claim("worker-a", lease_seconds=60)
        assert first is not None
        assert store.fail(first.task_id, "worker-a", RuntimeError("first failure")) == "RETRY_WAIT"

        pool = manager._pool
        assert pool is not None
        pool.execute(
            "UPDATE durable_tasks SET retry_at=CURRENT_TIMESTAMP - INTERVAL '1 second' WHERE task_id=%s",
            (uuid.UUID(task.task_id),),
        )
        second = store.claim("worker-b", lease_seconds=60)
        assert second is not None
        assert second.attempt_count == 2
        assert store.fail(second.task_id, "worker-b", RuntimeError("second failure")) == "DEAD_LETTER"
        assert store.get(task.task_id).state == "DEAD_LETTER"
    finally:
        pool = manager._pool
        if pool:
            with pool.transaction() as conn:
                conn.cursor().execute("DELETE FROM durable_tasks WHERE workflow_id=%s", (uuid.UUID(workflow),))
                conn.cursor().execute("DELETE FROM workflow_runs WHERE workflow_id=%s", (uuid.UUID(workflow),))
        manager.close()


@pytest.mark.integration
def test_lease_expiry_requeues_task_without_loss() -> None:
    manager = _manager()
    store = DurableExecutionStore(manager)
    workflow = _workflow(store)
    task = None
    try:
        task = store.enqueue(
            workflow_id=workflow,
            task_type="test.lease",
            payload={},
            dedupe_key=f"lease-{uuid.uuid4()}",
            max_attempts=3,
        )
        claimed = store.claim("worker-a", lease_seconds=60)
        assert claimed is not None
        pool = manager._pool
        assert pool is not None
        pool.execute(
            "UPDATE durable_tasks SET lease_expires_at=CURRENT_TIMESTAMP - INTERVAL '1 second' WHERE task_id=%s",
            (uuid.UUID(task.task_id),),
        )
        assert store.reap_expired() == 1
        recovered = store.claim("worker-b", lease_seconds=60)
        assert recovered is not None
        assert recovered.task_id == task.task_id
        assert recovered.attempt_count == 2
    finally:
        pool = manager._pool
        if pool:
            with pool.transaction() as conn:
                conn.cursor().execute("DELETE FROM durable_tasks WHERE workflow_id=%s", (uuid.UUID(workflow),))
                conn.cursor().execute("DELETE FROM workflow_runs WHERE workflow_id=%s", (uuid.UUID(workflow),))
        manager.close()
