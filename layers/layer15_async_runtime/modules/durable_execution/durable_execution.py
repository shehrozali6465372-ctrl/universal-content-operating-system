"""Durable Layer 15 execution owner backed by L13 PostgreSQL.

Transient async helpers in this layer may execute work in memory, but all
workflow/task state required for restart, retry, lease recovery, cancellation
and DLQ semantics is persisted here.
"""
from __future__ import annotations

import asyncio
import inspect
import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Optional
from uuid import UUID, uuid4


_ACTIVE_STATES = {"READY", "RUNNING", "RETRY_WAIT"}
_TERMINAL_STATES = {"COMPLETED", "CANCELLED", "DEAD_LETTER"}


@dataclass(frozen=True)
class DurableTask:
    task_id: str
    workflow_id: str
    task_type: str
    state: str
    attempt_count: int
    max_attempts: int
    lease_owner: str
    lease_expires_at: Any
    retry_at: Any
    cancel_requested: bool
    payload: Dict[str, Any]


class DurableExecutionStore:
    """L15 durable state machine over the L13 PostgreSQL persistence boundary."""

    def __init__(self, database: Any = None) -> None:
        if database is None:
            from layers.layer13_persistence.modules.postgresql.manager import get_database
            database = get_database()
        self._database = database
        self._pool = getattr(database, "_pool", None)
        if self._pool is None or not getattr(database, "_postgresql_available", False):
            raise RuntimeError("DurableExecutionStore requires canonical PostgreSQL")

    @staticmethod
    def _uuid(value: str, field: str) -> UUID:
        try:
            return UUID(str(value))
        except (ValueError, TypeError, AttributeError) as exc:
            raise ValueError(f"{field} must be a UUID") from exc

    @staticmethod
    def _json(value: Any) -> str:
        return json.dumps(value or {}, sort_keys=True, separators=(",", ":"), default=str)

    def ensure_workflow(
        self,
        workflow_id: str,
        tenant_id: str,
        workspace_id: str,
        brand_id: str,
        account_id: str = "",
        platform: str = "",
    ) -> None:
        workflow_uuid = self._uuid(workflow_id, "workflow_id")
        if not all(str(x).strip() for x in (tenant_id, workspace_id, brand_id)):
            raise ValueError("tenant_id, workspace_id and brand_id are required")
        with self._pool.transaction() as conn:
            conn.cursor().execute(
                """
                INSERT INTO workflow_runs(
                  workflow_id,tenant_id,workspace_id,brand_id,account_id,platform,status
                ) VALUES (%s,%s,%s,%s,%s,%s,'RUNNING')
                ON CONFLICT (workflow_id) DO UPDATE SET
                  tenant_id=EXCLUDED.tenant_id,
                  workspace_id=EXCLUDED.workspace_id,
                  brand_id=EXCLUDED.brand_id,
                  account_id=EXCLUDED.account_id,
                  platform=EXCLUDED.platform,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (workflow_uuid, tenant_id, workspace_id, brand_id, account_id or None, platform or None),
            )

    def enqueue(
        self,
        *,
        workflow_id: str,
        task_type: str,
        payload: Optional[Dict[str, Any]] = None,
        dedupe_key: Optional[str] = None,
        max_attempts: int = 3,
        backoff_seconds: int = 5,
        delay_seconds: int = 0,
    ) -> DurableTask:
        workflow_uuid = self._uuid(workflow_id, "workflow_id")
        if not task_type.strip():
            raise ValueError("task_type is required")
        if not isinstance(max_attempts, int) or max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        if not isinstance(backoff_seconds, int) or backoff_seconds < 1:
            raise ValueError("backoff_seconds must be a positive integer")
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            if dedupe_key:
                cur.execute(
                    """
                    SELECT task_id,workflow_id,task_type,state,attempt_count,max_attempts,
                           COALESCE(lease_owner,'') AS lease_owner,lease_expires_at,retry_at,cancel_requested,payload
                    FROM durable_tasks WHERE dedupe_key=%s
                    FOR UPDATE
                    """,
                    (dedupe_key,),
                )
                existing = cur.fetchone()
                if existing:
                    row = dict(zip([d[0] for d in cur.description], existing))
                    return DurableTask(
                        task_id=str(row["task_id"]),
                        workflow_id=str(row["workflow_id"]),
                        task_type=str(row["task_type"]),
                        state=str(row["state"]),
                        attempt_count=int(row["attempt_count"]),
                        max_attempts=int(row["max_attempts"]),
                        lease_owner=str(row.get("lease_owner") or ""),
                        lease_expires_at=row.get("lease_expires_at"),
                        retry_at=row.get("retry_at"),
                        cancel_requested=bool(row["cancel_requested"]),
                        payload=row.get("payload") if isinstance(row.get("payload"), dict) else {},
                    )
            task_id = uuid4()
            if delay_seconds > 0:
                cur.execute(
                    """
                    INSERT INTO durable_tasks(
                      task_id,workflow_id,dedupe_key,task_type,state,available_at,
                      max_attempts,backoff_seconds,payload
                    ) VALUES (
                      %s,%s,%s,%s,'READY',
                      CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                      %s,%s,%s::jsonb
                    )
                    """,
                    (task_id, workflow_uuid, dedupe_key, task_type, delay_seconds,
                     max_attempts, backoff_seconds, self._json(payload)),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO durable_tasks(
                      task_id,workflow_id,dedupe_key,task_type,state,available_at,
                      max_attempts,backoff_seconds,payload
                    ) VALUES (
                      %s,%s,%s,%s,'READY',CURRENT_TIMESTAMP,
                      %s,%s,%s::jsonb
                    )
                    """,
                    (task_id, workflow_uuid, dedupe_key, task_type,
                     max_attempts, backoff_seconds, self._json(payload)),
                )
            cur.execute(
                """
                INSERT INTO outbox_events(
                  outbox_id,event_type,aggregate_type,aggregate_id,idempotency_key,
                  payload_hash,payload,status
                ) VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,'PENDING')
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (
                    uuid4(),
                    "durable_task.enqueued",
                    "durable_task",
                    task_id,
                    f"durable-task:{dedupe_key or task_id}",
                    __import__("hashlib").sha256(self._json(payload).encode()).hexdigest(),
                    self._json({"task_id": str(task_id), "task_type": task_type}),
                ),
            )
        return DurableTask(
            task_id=str(task_id),
            workflow_id=str(workflow_uuid),
            task_type=task_type,
            state="READY",
            attempt_count=0,
            max_attempts=max_attempts,
            lease_owner="",
            lease_expires_at=None,
            retry_at=None,
            cancel_requested=False,
            payload=payload or {},
        )

    def claim(self, worker_id: str, lease_seconds: int = 60) -> Optional[DurableTask]:
        if not worker_id.strip():
            raise ValueError("worker_id is required")
        if lease_seconds < 1:
            raise ValueError("lease_seconds must be positive")
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT task_id,workflow_id,task_type,state,attempt_count,max_attempts,
                       lease_owner,lease_expires_at,retry_at,cancel_requested,payload
                FROM durable_tasks
                WHERE state IN ('READY','RETRY_WAIT')
                  AND available_at <= CURRENT_TIMESTAMP
                  AND (retry_at IS NULL OR retry_at <= CURRENT_TIMESTAMP)
                  AND cancel_requested=FALSE
                ORDER BY available_at,created_at
                FOR UPDATE SKIP LOCKED
                LIMIT 1
                """
            )
            row = cur.fetchone()
            if not row:
                return None
            values = dict(zip([d[0] for d in cur.description], row))
            next_attempt = int(values["attempt_count"]) + 1
            cur.execute(
                """
                UPDATE durable_tasks
                   SET state='RUNNING',
                       attempt_count=%s,
                       lease_owner=%s,
                       lease_expires_at=CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                       updated_at=CURRENT_TIMESTAMP
                 WHERE task_id=%s
                """,
                (next_attempt, worker_id, lease_seconds, values["task_id"]),
            )
            return DurableTask(
                task_id=str(values["task_id"]),
                workflow_id=str(values["workflow_id"]),
                task_type=str(values["task_type"]),
                state="RUNNING",
                attempt_count=next_attempt,
                max_attempts=int(values["max_attempts"]),
                lease_owner=worker_id,
                lease_expires_at=None,
                retry_at=values["retry_at"],
                cancel_requested=bool(values["cancel_requested"]),
                payload=values["payload"] if isinstance(values["payload"], dict) else {},
            )

    def heartbeat(self, task_id: str, worker_id: str, lease_seconds: int = 60) -> bool:
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE durable_tasks
                   SET lease_expires_at=CURRENT_TIMESTAMP + (%s * INTERVAL '1 second'),
                       updated_at=CURRENT_TIMESTAMP
                 WHERE task_id=%s AND state='RUNNING' AND lease_owner=%s
                """,
                (lease_seconds, self._uuid(task_id, "task_id"), worker_id),
            )
            return cur.rowcount == 1

    def complete(self, task_id: str, worker_id: str, result: Any = None) -> bool:
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE durable_tasks
                   SET state='COMPLETED',payload=%s::jsonb,lease_owner=NULL,
                       lease_expires_at=NULL,updated_at=CURRENT_TIMESTAMP
                 WHERE task_id=%s AND state='RUNNING' AND lease_owner=%s
                """,
                (self._json({"result": result}), self._uuid(task_id, "task_id"), worker_id),
            )
            return cur.rowcount == 1

    def cancel(self, task_id: str, reason: str = "") -> bool:
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE durable_tasks
                   SET cancel_requested=TRUE,
                       last_error=%s,
                       updated_at=CURRENT_TIMESTAMP
                 WHERE task_id=%s AND state NOT IN ('COMPLETED','CANCELLED','DEAD_LETTER')
                """,
                (reason[:2000], self._uuid(task_id, "task_id")),
            )
            changed = cur.rowcount == 1
            if changed:
                cur.execute(
                    """
                    UPDATE durable_tasks
                       SET state='CANCELLED',lease_owner=NULL,lease_expires_at=NULL,
                           updated_at=CURRENT_TIMESTAMP
                     WHERE task_id=%s AND state IN ('READY','RETRY_WAIT')
                    """,
                    (self._uuid(task_id, "task_id"),),
                )
            return changed

    def fail(self, task_id: str, worker_id: str, error: Exception | str) -> str:
        message = str(error)[:2000]
        error_class = type(error).__name__ if isinstance(error, Exception) else "RuntimeError"
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT attempt_count,max_attempts,backoff_seconds,cancel_requested "
                "FROM durable_tasks WHERE task_id=%s AND state='RUNNING' AND lease_owner=%s FOR UPDATE",
                (self._uuid(task_id, "task_id"), worker_id),
            )
            row = cur.fetchone()
            if not row:
                raise ValueError("durable task is not owned by this worker")
            attempt_count, max_attempts, backoff_seconds, cancelled = row
            if cancelled:
                next_state = "CANCELLED"
                retry_at = None
                dlq_reason = None
            elif int(attempt_count) >= int(max_attempts):
                next_state = "DEAD_LETTER"
                retry_at = None
                dlq_reason = message
            else:
                delay = min(3600, int(backoff_seconds) * (2 ** max(0, int(attempt_count) - 1)))
                next_state = "RETRY_WAIT"
                retry_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
                dlq_reason = None
            cur.execute(
                """
                UPDATE durable_tasks
                   SET state=%s,retry_at=%s,lease_owner=NULL,lease_expires_at=NULL,
                       last_error=%s,error_class=%s,dlq_reason=%s,updated_at=CURRENT_TIMESTAMP
                 WHERE task_id=%s
                """,
                (
                    next_state, retry_at, message, error_class, dlq_reason,
                    self._uuid(task_id, "task_id"),
                ),
            )
            return next_state

    def reap_expired(self) -> int:
        """Recover expired leases while preserving attempt and retry accounting."""
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute("""
                SELECT task_id,attempt_count,max_attempts,backoff_seconds,last_error
                  FROM durable_tasks
                 WHERE state='RUNNING'
                   AND lease_expires_at IS NOT NULL
                   AND lease_expires_at < CURRENT_TIMESTAMP
                 FOR UPDATE SKIP LOCKED
            """)
            rows = cur.fetchall()
            for task_id, attempt_count, max_attempts, backoff_seconds, last_error in rows:
                if int(attempt_count) >= int(max_attempts):
                    cur.execute("""
                        UPDATE durable_tasks
                           SET state='DEAD_LETTER',retry_at=NULL,lease_owner=NULL,
                               lease_expires_at=NULL,
                               dlq_reason=COALESCE(last_error,'lease expired'),
                               updated_at=CURRENT_TIMESTAMP
                         WHERE task_id=%s AND state='RUNNING'
                    """, (task_id,))
                else:
                    delay = min(3600, int(backoff_seconds) * (2 ** max(0, int(attempt_count) - 1)))
                    cur.execute("""
                        UPDATE durable_tasks
                           SET state='RETRY_WAIT',
                               retry_at=CURRENT_TIMESTAMP,
                               available_at=CURRENT_TIMESTAMP,
                               lease_owner=NULL,lease_expires_at=NULL,
                               last_error=COALESCE(last_error,'lease expired'),
                               error_class='LeaseExpired',
                               updated_at=CURRENT_TIMESTAMP
                         WHERE task_id=%s AND state='RUNNING'
                    """, (delay, delay, task_id))
            return len(rows)

    def get(self, task_id: str) -> Optional[DurableTask]:
        row = self._pool.query_one(
            """
            SELECT task_id,workflow_id,task_type,state,attempt_count,max_attempts,
                   lease_owner,lease_expires_at,retry_at,cancel_requested,payload
            FROM durable_tasks WHERE task_id=%s
            """,
            (self._uuid(task_id, "task_id"),),
        )
        if not row:
            return None
        return DurableTask(
            task_id=str(row["task_id"]),
            workflow_id=str(row["workflow_id"]),
            task_type=str(row["task_type"]),
            state=str(row["state"]),
            attempt_count=int(row["attempt_count"]),
            max_attempts=int(row["max_attempts"]),
            lease_owner=str(row.get("lease_owner") or ""),
            lease_expires_at=row.get("lease_expires_at"),
            retry_at=row.get("retry_at"),
            cancel_requested=bool(row.get("cancel_requested")),
            payload=row.get("payload") if isinstance(row.get("payload"), dict) else {},
        )


class DurableWorker:
    """Restart-safe L15 worker; external authorization remains outside the worker."""

    def __init__(
        self,
        store: DurableExecutionStore,
        worker_id: Optional[str] = None,
        lease_seconds: int = 60,
        poll_seconds: float = 1.0,
    ) -> None:
        self.store = store
        self.worker_id = worker_id or f"{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"
        self.lease_seconds = lease_seconds
        self.poll_seconds = poll_seconds
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._running = False

    def register(self, task_type: str, handler: Callable[..., Any]) -> None:
        if not task_type.strip() or not callable(handler):
            raise ValueError("task_type and callable handler are required")
        self._handlers[task_type] = handler

    async def run_once(self) -> Optional[str]:
        self.store.reap_expired()
        task = self.store.claim(self.worker_id, self.lease_seconds)
        if task is None:
            return None
        handler = self._handlers.get(task.task_type)
        if handler is None:
            state = self.store.fail(task.task_id, self.worker_id, f"no handler registered for {task.task_type}")
            return state
        heartbeat_task = asyncio.create_task(self._heartbeat(task.task_id))
        try:
            value = handler(task)
            if inspect.isawaitable(value):
                value = await value
            if not self.store.complete(task.task_id, self.worker_id, value):
                raise RuntimeError("durable task completion lost lease ownership")
            return "COMPLETED"
        except asyncio.CancelledError:
            self.store.fail(task.task_id, self.worker_id, "worker coroutine cancelled")
            raise
        except Exception as exc:
            return self.store.fail(task.task_id, self.worker_id, exc)
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

    async def _heartbeat(self, task_id: str) -> None:
        interval = max(1.0, self.lease_seconds / 3)
        while True:
            await asyncio.sleep(interval)
            if not self.store.heartbeat(task_id, self.worker_id, self.lease_seconds):
                return

    async def run_forever(self) -> None:
        self._running = True
        try:
            while self._running:
                await self.run_once()
                await asyncio.sleep(self.poll_seconds)
        finally:
            self._running = False

    def stop(self) -> None:
        self._running = False
