from __future__ import annotations

import threading
import uuid

from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionConfig, ConnectionPool
from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager


def _config() -> ConnectionConfig:
    return ConnectionConfig.from_env()


def test_real_postgresql_lifecycle_schema_crud_and_rollback() -> None:
    pool = ConnectionPool(_config())
    assert pool.initialize() is True

    marker = f"layer13_cert_{uuid.uuid4().hex}"
    try:
        with pool.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agent_config (key, value, category) VALUES (%s, %s, %s)",
                (marker, "before_rollback", "layer13_cert"),
            )
            raise RuntimeError("forced rollback")
    except RuntimeError:
        pass

    assert pool.query_one(
        "SELECT key FROM agent_config WHERE key = %s", (marker,)
    ) is None

    inserted_id = pool.insert(
        "agent_config",
        {"key": marker, "value": "created", "category": "layer13_cert"},
    )
    assert inserted_id > 0

    updated = pool.update(
        "agent_config",
        {"value": "updated"},
        "key = %s",
        (marker,),
    )
    assert updated == 1

    row = pool.query_one(
        "SELECT value FROM agent_config WHERE key = %s", (marker,)
    )
    assert row == {"value": "updated"}

    assert pool.delete("agent_config", "key = %s", (marker,)) == 1
    assert pool.query_one(
        "SELECT key FROM agent_config WHERE key = %s", (marker,)
    ) is None
    pool.close()


def test_real_postgresql_concurrent_queries_leave_no_borrowed_connections() -> None:
    pool = ConnectionPool(_config())
    assert pool.initialize() is True

    errors: list[BaseException] = []

    def worker() -> None:
        try:
            assert pool.query_one("SELECT 1 AS ok") == {"ok": 1}
        except BaseException as exc:
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert errors == []
    metrics = pool.get_pool_metrics()
    assert metrics["active_connections"] == 0
    assert metrics["idle_connections"] == pool._config.min_connections
    assert metrics["postgresql_available"] is True
    pool.close()


def test_manager_owns_single_pool_and_can_reinitialize() -> None:
    manager = PostgreSQLManager(_config())
    assert manager.initialize() is True
    first_pool = manager._pool
    assert first_pool is not None
    assert manager._postgresql_available is True
    assert manager.health_check()["overall"] == "PASS"

    manager.close()
    assert manager._pool is None
    assert manager._initialized is False
    assert manager._postgresql_available is False

    assert manager.initialize() is True
    assert manager._pool is not None
    assert manager._pool is not first_pool
    manager.close()
