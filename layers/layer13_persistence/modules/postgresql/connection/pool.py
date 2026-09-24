"""PostgreSQL Connection Pool — Enterprise Edition.

Features:
- Thread-safe connection pooling
- PostgreSQL with SQLite fallback only outside production
- Retry with exponential backoff
- Auto-reconnect on connection loss
- Connection pool metrics (active, idle, queries, latency)
- Health check ping
"""
from __future__ import annotations
import os
import time
import threading
from typing import Any, Dict, List, Optional
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import re


@dataclass
class ConnectionConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "aios"
    user: str = "postgres"
    password: str = ""
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30
    idle_timeout: int = 300
    max_retries: int = 3
    retry_delays: tuple = (0.5, 1.0, 2.0)

    def __post_init__(self) -> None:
        integer_fields = {
            "port": self.port,
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "idle_timeout": self.idle_timeout,
            "max_retries": self.max_retries,
        }
        for name, value in integer_fields.items():
            if not isinstance(value, int) or isinstance(value, bool) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.min_connections > self.max_connections:
            raise ValueError("min_connections must not exceed max_connections")
        if not isinstance(self.retry_delays, tuple) or not self.retry_delays:
            raise ValueError("retry_delays must be a non-empty tuple")
        if any(
            not isinstance(delay, (int, float))
            or isinstance(delay, bool)
            or delay < 0
            for delay in self.retry_delays
        ):
            raise ValueError("retry_delays must contain non-negative numbers")

    @classmethod
    def from_env(cls) -> "ConnectionConfig":
        return cls(
            host=os.environ.get("POSTGRES_HOST", os.environ.get("PG_HOST", "localhost")),
            port=int(os.environ.get("POSTGRES_PORT", os.environ.get("PG_PORT", "5432"))),
            database=os.environ.get("POSTGRES_DB", os.environ.get("PG_DATABASE", "aios")),
            user=os.environ.get("POSTGRES_USER", os.environ.get("PG_USER", "postgres")),
            password=os.environ.get("POSTGRES_PASSWORD", os.environ.get("PG_PASSWORD", "")),
            min_connections=int(os.environ.get("PG_MIN_CONN", "2")),
            max_connections=int(os.environ.get("PG_MAX_CONN", "10")),
        )


class ConnectionPool:
    """Thread-safe PostgreSQL connection pool with retry, reconnect, and metrics."""

    _MAX_LATENCY_SAMPLES = 1000

    def __init__(self, config: Optional[ConnectionConfig] = None):
        self._config = config or ConnectionConfig.from_env()
        self._lock = threading.RLock()
        self._pg_available: Optional[bool] = None
        self._initialized = False
        self._closing = False

        # Retry state
        self._consecutive_failures = 0
        self._last_success_time: float = 0.0
        self._last_error: Optional[str] = None
        self._total_retries = 0

        # Pool metrics
        self._active_conns = 0
        self._idle_conns = 0
        self._total_queries = 0
        self._failed_queries = 0
        self._total_latency_ms = 0.0
        self._query_latencies: List[float] = []

    def initialize(self) -> bool:
        """Initialize pool. Returns True if PostgreSQL is available."""
        with self._lock:
            if self._initialized:
                return self._pg_available or False
            self._closing = False
            try:
                import psycopg2
                import psycopg2.pool

                self._pg_conn_pool = psycopg2.pool.ThreadedConnectionPool(
                    self._config.min_connections,
                    self._config.max_connections,
                    host=self._config.host,
                    port=self._config.port,
                    database=self._config.database,
                    user=self._config.user,
                    password=self._config.password,
                    connect_timeout=self._config.connection_timeout,
                )
                self._pg_available = True
                self._initialized = True
                self._last_success_time = time.time()
                return True
            except ImportError as exc:
                self._pg_available = False
                self._initialized = True
                self._last_error = f"PostgreSQL driver unavailable: {exc}"
                if os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
                    raise RuntimeError("PostgreSQL driver is unavailable in production") from exc
                return False
            except Exception as exc:
                self._pg_available = False
                self._initialized = True
                self._last_error = str(exc)
                if os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
                    raise RuntimeError("PostgreSQL initialization failed in production") from exc
                return False

    def _auto_reconnect(self) -> bool:
        """Reconnect only when no borrowed connections can be invalidated."""
        with self._lock:
            if self._active_conns:
                return False
            try:
                if self._pg_available and hasattr(self, "_pg_conn_pool"):
                    self._pg_conn_pool.closeall()
            except Exception:
                pass
            self._initialized = False
            self._pg_available = None
            return self.initialize()

    @contextmanager
    def connection(self):
        """Acquire a connection while preserving pool lifecycle ownership."""
        with self._lock:
            if self._closing:
                raise RuntimeError("PostgreSQL connection pool is closing")
            if not self._initialized:
                self.initialize()
            if self._closing:
                raise RuntimeError("PostgreSQL connection pool is closing")
            pg_available = self._pg_available
            if pg_available:
                conn = self._pg_conn_pool.getconn()
                self._active_conns += 1
                self._idle_conns = max(0, self._idle_conns - 1)
            else:
                if os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
                    raise RuntimeError("PostgreSQL is unavailable; SQLite fallback is disabled in production")
                import sqlite3
                db_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(
                        os.path.dirname(os.path.dirname(__file__))))),
                    "ai_content_os.db",
                )
                if not os.path.exists(os.path.dirname(db_path)):
                    db_path = os.path.join("/tmp", "ai_content_os.db")
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self._active_conns += 1
        try:
            yield conn
        finally:
            with self._lock:
                if pg_available:
                    self._pg_conn_pool.putconn(conn)
                    self._active_conns = max(0, self._active_conns - 1)
                    self._idle_conns += 1
                else:
                    conn.close()
                    self._active_conns = max(0, self._active_conns - 1)

    def _record_latency(self, latency_ms: float) -> None:
        with self._lock:
            if len(self._query_latencies) >= self._MAX_LATENCY_SAMPLES:
                self._total_latency_ms -= self._query_latencies.pop(0)
            self._query_latencies.append(latency_ms)
            self._total_latency_ms += latency_ms

    def _execute_with_retry(self, fn, *args, **kwargs):
        """Execute a function with bounded retry attempts."""
        max_attempts = self._config.max_retries
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool) or max_attempts < 1:
            raise ValueError("max_retries must be a positive integer")
        last_error = None
        for attempt in range(max_attempts):
            try:
                result = fn(*args, **kwargs)
                self._consecutive_failures = 0
                self._last_success_time = time.time()
                return result
            except Exception as exc:
                last_error = exc
                self._consecutive_failures += 1
                self._total_retries += 1
                self._last_error = str(exc)

                if attempt < max_attempts - 1:
                    delay = self._config.retry_delays[min(attempt, len(self._config.retry_delays) - 1)]
                    time.sleep(delay)

                # Auto-reconnect after max retries
                if attempt == max_attempts - 1 and self._consecutive_failures >= 3:
                    self._auto_reconnect()
                    try:
                        result = fn(*args, **kwargs)
                        self._consecutive_failures = 0
                        self._last_success_time = time.time()
                        return result
                    except Exception:
                        pass

        self._failed_queries += 1
        raise last_error

    def execute(self, sql: str, params: tuple = ()) -> int:
        """Execute a statement in an explicit transaction and return affected rows."""
        def _do():
            with self.connection() as conn:
                cursor = conn.cursor()
                exec_sql = sql if self._pg_available else sql.replace("%s", "?")
                cursor.execute(exec_sql, params)
                conn.commit()
                return cursor.rowcount
        return self._execute_with_retry(_do)

    def execute_and_fetch(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute query and fetch all results (with retry)."""
        def _do():
            with self.connection() as conn:
                cursor = conn.cursor()
                exec_sql = sql
                if not self._pg_available:
                    exec_sql = sql.replace("%s", "?")
                start = time.time()
                cursor.execute(exec_sql, params)
                latency = (time.time() - start) * 1000
                self._record_latency(latency)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                rows = cursor.fetchall()
                return [dict(zip(columns, row)) for row in rows]
        result = self._execute_with_retry(_do)
        self._total_queries += 1
        return result

    def execute_and_fetch_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one result (with retry)."""
        def _do():
            with self.connection() as conn:
                cursor = conn.cursor()
                exec_sql = sql
                if not self._pg_available:
                    exec_sql = sql.replace("%s", "?")
                start = time.time()
                cursor.execute(exec_sql, params)
                latency = (time.time() - start) * 1000
                self._record_latency(latency)
                columns = [desc[0] for desc in cursor.description] if cursor.description else []
                row = cursor.fetchone()
                return dict(zip(columns, row)) if row else None
        result = self._execute_with_retry(_do)
        self._total_queries += 1
        return result

    _IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    @classmethod
    def _identifier(cls, value: str) -> str:
        if not isinstance(value, str) or not cls._IDENT.fullmatch(value):
            raise ValueError(f"unsafe SQL identifier: {value}")
        return value

    def _placeholder(self) -> str:
        return "%s" if self._pg_available else "?"

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        """Insert a row and return the inserted ID (with retry)."""
        if not isinstance(data, dict) or not data:
            raise ValueError("insert data must be a non-empty dictionary")
        def _do():
            table_name = self._identifier(table)
            cols = ", ".join(self._identifier(k) for k in data.keys())
            ph = self._placeholder()
            phs = ", ".join([ph for _ in data])
            sql = f"INSERT INTO {table_name} ({cols}) VALUES ({phs})"
            with self.connection() as conn:
                cursor = conn.cursor()
                if self._pg_available:
                    cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({phs}) RETURNING id", list(data.values()))
                    result = cursor.fetchone()
                    conn.commit()
                    return result[0] if result else 0
                else:
                    cursor.execute(sql, list(data.values()))
                    conn.commit()
                    return cursor.lastrowid
        return self._execute_with_retry(_do)

    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """Insert multiple rows (with retry)."""
        if not rows:
            return 0
        if not all(isinstance(row, dict) and row for row in rows):
            raise ValueError("insert_many rows must be non-empty dictionaries")
        columns = tuple(rows[0].keys())
        if any(tuple(row.keys()) != columns for row in rows[1:]):
            raise ValueError("insert_many rows must have identical columns")
        def _do():
            table = self._identifier(table)
            cols = ", ".join(self._identifier(k) for k in columns)
            ph = self._placeholder()
            phs = ", ".join([ph for _ in rows[0]])
            sql = f"INSERT INTO {table} ({cols}) VALUES ({phs})"
            data = [list(r.values()) for r in rows]
            with self.connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(sql, data)
                conn.commit()
                return len(rows)
        return self._execute_with_retry(_do)

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        """Update rows and return affected count (with retry)."""
        def _do():
            ph = self._placeholder()
            table_name = self._identifier(table)
            sets = ", ".join(f"{self._identifier(k)} = {ph}" for k in data)
            sql = f"UPDATE {table_name} SET {sets} WHERE {where}"
            with self.connection() as conn:
                cursor = conn.cursor()
                exec_sql = sql
                if not self._pg_available:
                    exec_sql = sql.replace("%s", "?")
                cursor.execute(exec_sql, list(data.values()) + list(where_params))
                conn.commit()
                return cursor.rowcount
        return self._execute_with_retry(_do)

    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        """Delete rows and return affected count (with retry)."""
        def _do():
            table_name = self._identifier(table)
            sql = f"DELETE FROM {table_name} WHERE {where}"
            with self.connection() as conn:
                cursor = conn.cursor()
                exec_sql = sql
                if not self._pg_available:
                    exec_sql = sql.replace("%s", "?")
                cursor.execute(exec_sql, where_params)
                conn.commit()
                return cursor.rowcount
        return self._execute_with_retry(_do)

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """Execute SELECT query."""
        return self.execute_and_fetch(sql, params)

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        """Execute SELECT query and return one row."""
        return self.execute_and_fetch_one(sql, params)

    def count(self, table: str, where: str = "1=1", params: tuple = ()) -> int:
        """Count rows in a table."""
        table = self._identifier(table)
        sql = f"SELECT COUNT(*) as c FROM {table} WHERE {where}"
        exec_sql = sql
        if not self._pg_available:
            exec_sql = sql.replace("%s", "?")
        result = self.query_one(exec_sql, params)
        return result["c"] if result else 0

    def table_exists(self, name: str) -> bool:
        """Check if a table exists."""
        if self._pg_available:
            sql = "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = %s)"
            result = self.query_one(sql, (name,))
            return result["exists"] if result else False
        else:
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
            result = self.query_one(sql, (name,))
            return result is not None

    def get_tables(self) -> List[str]:
        """List all tables."""
        if self._pg_available:
            sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
            rows = self.query(sql)
            return [r["table_name"] for r in rows]
        else:
            sql = "SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version'"
            rows = self.query(sql)
            return [r["name"] for r in rows]

    @contextmanager
    def transaction(self):
        """Own one connection for an atomic transaction."""
        with self.connection() as conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def begin_transaction(self):
        """Reject unscoped transactions; use transaction() for ownership."""
        raise RuntimeError("Use ConnectionPool.transaction() to establish transaction ownership")

    def commit(self):
        """Reject unscoped commits; transaction() owns commit semantics."""
        raise RuntimeError("Use ConnectionPool.transaction() to establish transaction ownership")

    def rollback(self):
        """Reject unscoped rollbacks; transaction() owns rollback semantics."""
        raise RuntimeError("Use ConnectionPool.transaction() to establish transaction ownership")

    def is_healthy(self) -> bool:
        """Lightweight health ping — SELECT 1."""
        try:
            self.query_one("SELECT 1")
            return True
        except Exception:
            return False

    def get_pool_metrics(self) -> Dict[str, Any]:
        """Get comprehensive pool metrics."""
        with self._lock:
            if len(self._query_latencies) > self._MAX_LATENCY_SAMPLES:
                del self._query_latencies[:-self._MAX_LATENCY_SAMPLES]
            lats = list(self._query_latencies)
            active_conns = self._active_conns
            idle_conns = self._idle_conns
            total_queries = self._total_queries
            failed_queries = self._failed_queries
            total_retries = self._total_retries
            consecutive_failures = self._consecutive_failures
            last_error = self._last_error
            total_latency_ms = self._total_latency_ms
            pg_available = self._pg_available
            initialized = self._initialized
        avg_lat = sum(lats) / len(lats) if lats else 0.0
        sorted_lats = sorted(lats)
        p95 = sorted_lats[int(len(sorted_lats) * 0.95)] if len(sorted_lats) >= 2 else avg_lat
        p99 = sorted_lats[int(len(sorted_lats) * 0.99)] if len(sorted_lats) >= 2 else avg_lat

        return {
            "postgresql_available": pg_available,
            "initialized": initialized,
            "healthy": self.is_healthy() if initialized else False,
            "active_connections": active_conns,
            "idle_connections": idle_conns,
            "total_queries": total_queries,
            "failed_queries": failed_queries,
            "total_retries": total_retries,
            "consecutive_failures": consecutive_failures,
            "last_error": last_error,
            "latency": {
                "avg_ms": round(avg_lat, 2),
                "p95_ms": round(p95, 2),
                "p99_ms": round(p99, 2),
                "total_latency_ms": round(total_latency_ms, 2),
                "samples": len(lats),
            },
            "config": {
                "host": self._config.host,
                "port": self._config.port,
                "database": self._config.database,
                "max_retries": self._config.max_retries,
                "max_connections": self._config.max_connections,
            },
        }

    def health_check(self) -> Dict[str, Any]:
        """Check pool health."""
        return self.get_pool_metrics()

    def close(self):
        """Close all connections and reset lifecycle state."""
        with self._lock:
            if self._active_conns:
                raise RuntimeError(
                    f"Cannot close PostgreSQL pool with {self._active_conns} active connection(s)"
                )
            self._closing = True
            try:
                if self._pg_available and hasattr(self, "_pg_conn_pool"):
                    self._pg_conn_pool.closeall()
            finally:
                self._pg_available = None
                self._initialized = False
                self._active_conns = 0
                self._idle_conns = 0
                self._closing = False
