"""Real SQL database engine abstraction.

Production uses PostgreSQL; SQLite is an explicit development/test engine.
No operation in this class is simulated: connect/execute/stats reflect the
actual database connection and transaction state.
"""
from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterator, Optional


class DatabaseEngine:
    """Small, real database engine used by persistence infrastructure."""

    SUPPORTED = {"postgresql", "sqlite"}

    def __init__(self, engine_type: str = "postgresql") -> None:
        engine_type = str(engine_type).strip().lower()
        if engine_type not in self.SUPPORTED:
            raise ValueError(f"unsupported database engine: {engine_type}")
        self._type = engine_type
        self._connected = False
        self._config: Dict[str, Any] = {}
        self._conn: Any = None
        self._transaction_depth = 0

    def configure(self, config: Dict[str, Any]) -> None:
        if not isinstance(config, dict):
            raise TypeError("database configuration must be a mapping")
        self._config = dict(config)

    def connect(self) -> bool:
        if self._connected:
            return True
        if self._type == "sqlite":
            path = self._config.get("path") or os.environ.get("UCOS_SQLITE_PATH", "data/agent.db")
            parent = os.path.dirname(os.path.abspath(path))
            os.makedirs(parent, exist_ok=True)
            self._conn = sqlite3.connect(path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys=ON")
        else:
            try:
                import psycopg2
            except ImportError as exc:
                raise RuntimeError("PostgreSQL driver psycopg2 is required") from exc
            cfg = {
                "host": self._config.get("host", os.environ.get("PG_HOST", "localhost")),
                "port": int(self._config.get("port", os.environ.get("PG_PORT", 5432))),
                "dbname": self._config.get("database", os.environ.get("PG_DATABASE", "ai_content_os")),
                "user": self._config.get("user", os.environ.get("PG_USER", "postgres")),
                "password": self._config.get("password", os.environ.get("PG_PASSWORD", "")),
                "connect_timeout": int(self._config.get("connect_timeout", 30)),
            }
            self._conn = psycopg2.connect(**cfg)
        self._connected = True
        return True

    def disconnect(self) -> bool:
        if self._conn is not None:
            self._conn.close()
        self._conn = None
        self._connected = False
        self._transaction_depth = 0
        return True

    def is_connected(self) -> bool:
        return self._connected and self._conn is not None

    def get_type(self) -> str:
        return self._type

    def _ensure_connected(self) -> None:
        if not self.is_connected():
            raise RuntimeError("database engine is not connected")

    def execute(self, sql: str, params: Any = None) -> Dict[str, Any]:
        self._ensure_connected()
        if not isinstance(sql, str) or not sql.strip():
            raise ValueError("sql must be a non-empty string")
        cursor = self._conn.cursor()
        try:
            cursor.execute(sql, params or ())
            rows = cursor.fetchall() if cursor.description else []
            if self._transaction_depth == 0:
                self._conn.commit()
            return {"rows": [dict(r) if isinstance(r, sqlite3.Row) else dict(zip([d[0] for d in cursor.description], r)) for r in rows],
                    "affected": max(cursor.rowcount, 0)}
        except Exception:
            if self._transaction_depth == 0:
                self._conn.rollback()
            raise
        finally:
            cursor.close()

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        self._ensure_connected()
        self._transaction_depth += 1
        try:
            yield self._conn
            if self._transaction_depth == 1:
                self._conn.commit()
        except Exception:
            if self._transaction_depth == 1:
                self._conn.rollback()
            raise
        finally:
            self._transaction_depth = max(0, self._transaction_depth - 1)

    def stats(self) -> Dict[str, Any]:
        self._ensure_connected()
        return {"type": self._type, "connected": True, "transaction_depth": self._transaction_depth}
