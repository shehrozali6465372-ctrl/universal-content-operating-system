from __future__ import annotations

import builtins
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from layers.layer13_persistence.modules.postgresql.connection.pool import (
    ConnectionConfig,
    ConnectionPool,
)
from layers.layer13_persistence.modules.postgresql.manager import PostgreSQLManager


class _FakeConnection:
    def __init__(self) -> None:
        self.rollback_count = 0

    def rollback(self) -> None:
        self.rollback_count += 1


class _FakePgPool:
    def __init__(self, conn: _FakeConnection) -> None:
        self.conn = conn
        self.returned = []

    def getconn(self):
        return self.conn

    def putconn(self, conn, close=False):
        self.returned.append((conn, close))


class _FakeCursor:
    def __init__(self) -> None:
        self.statements = []

    def execute(self, sql: str) -> None:
        self.statements.append(sql)


class _FakeTransactionConnection:
    def __init__(self) -> None:
        self.cursor_obj = _FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class _FakeManagerPool:
    def __init__(self) -> None:
        self.conn = _FakeTransactionConnection()

    @contextmanager
    def transaction(self):
        yield self.conn
        self.conn.commit()


class Layer13PostgreSQLHardeningTests(unittest.TestCase):
    def test_borrowed_connection_is_returned_transaction_clean(self) -> None:
        pool = ConnectionPool(ConnectionConfig(min_connections=1, max_connections=1))
        conn = _FakeConnection()
        fake_pool = _FakePgPool(conn)
        pool._pg_available = True
        pool._initialized = True
        pool._pg_conn_pool = fake_pool

        with pool.connection():
            pass

        self.assertGreaterEqual(conn.rollback_count, 1)
        self.assertEqual(fake_pool.returned, [(conn, False)])
        self.assertEqual(pool._active_conns, 0)

    def test_non_transient_errors_are_not_retryable(self) -> None:
        self.assertFalse(ConnectionPool._is_retryable_error(ValueError("bad SQL")))

    def test_production_never_falls_back_when_driver_is_unavailable(self) -> None:
        real_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name == "psycopg2" or name.startswith("psycopg2."):
                raise ImportError("blocked for production fallback test")
            return real_import(name, *args, **kwargs)

        pool = ConnectionPool(ConnectionConfig(min_connections=1, max_connections=1))
        with patch.dict(os.environ, {"APP_ENV": "production"}, clear=False):
            with patch("builtins.__import__", side_effect=blocked_import):
                with self.assertRaises(RuntimeError):
                    pool.initialize()

    def test_schema_creation_uses_one_atomic_transaction(self) -> None:
        manager = PostgreSQLManager(ConnectionConfig(min_connections=1, max_connections=1))
        fake_pool = _FakeManagerPool()
        manager._pool = fake_pool
        manager._postgresql_available = True

        manager._create_tables()

        self.assertTrue(fake_pool.conn.committed)
        self.assertFalse(fake_pool.conn.rolled_back)
        self.assertGreater(len(fake_pool.conn.cursor_obj.statements), 0)


if __name__ == "__main__":
    unittest.main()
