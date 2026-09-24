"""
Database Manager Module
Layer 1: Core System — Module 4
"""

import sqlite3
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from contextlib import contextmanager
from threading import RLock, local

from layers.layer01_core.modules.models import get_all_table_names
from layers.layer01_core.modules.migrations import MigrationManager


class DatabaseManager:
    _path_locks: Dict[str, RLock] = {}
    _path_locks_guard = RLock()
    def __init__(self, db_path: str = "data/agent.db", project_root: Optional[str] = None):
        self._project_root = Path(project_root).resolve() if project_root else None
        self._db_path = self._safe_path(db_path, "database path")
        with self._path_locks_guard:
            self._lifecycle_lock = self._path_locks.setdefault(
                str(self._db_path), RLock()
            )
        self._conn: Optional[sqlite3.Connection] = None
        self._migration_manager: Optional[MigrationManager] = None
        self._initialized = False
        self._tx_local = local()
        self._lock = RLock()

    def _safe_path(self, path: str, label: str) -> Path:
        raw = Path(path)
        if raw.is_absolute():
            candidate = raw.resolve()
            if self._project_root is not None:
                try:
                    candidate.relative_to(self._project_root)
                except ValueError as exc:
                    raise ValueError(f"{label} escapes project root: {path}") from exc
            return candidate
        root = self._project_root or Path.cwd().resolve()
        candidate = (root / raw).resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"{label} escapes project root: {path}") from exc
        return candidate

    @property
    def _in_transaction(self) -> bool:
        return bool(getattr(self._tx_local, "active", False))

    @_in_transaction.setter
    def _in_transaction(self, value: bool) -> None:
        self._tx_local.active = bool(value)

    @property
    def db_path(self) -> Path:
        return self._db_path

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> "DatabaseManager":
        if os.environ.get("APP_ENV", "development").lower() in {"production", "prod"}:
            raise RuntimeError(
                "Layer 1 local SQLite is development/test-only; production persistence is owned by Layer 13 PostgreSQL"
            )
        with self._lifecycle_lock:
            with self._lock:
                if self._initialized and self._conn is not None:
                    return self
                self._db_path.parent.mkdir(parents=True, exist_ok=True)
                conn = sqlite3.connect(
                    str(self._db_path), check_same_thread=False, timeout=30.0
                )
                try:
                    conn.row_factory = sqlite3.Row
                    conn.execute("PRAGMA busy_timeout=30000")
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA foreign_keys=ON")
                    migration_manager = MigrationManager(conn)
                    migration_manager.migrate()
                except Exception:
                    conn.close()
                    raise
                self._conn = conn
                self._migration_manager = migration_manager
                self._initialized = True
                return self

    def close(self) -> None:
        with self._lifecycle_lock:
            with self._lock:
                if self._conn:
                    self._conn.close()
                    self._conn = None
                    self._initialized = False

    @contextmanager
    def transaction(self):
        with self._lock:
            if not self._initialized or self._conn is None:
                raise RuntimeError("Database not initialized.")
            if self._in_transaction:
                yield self._conn
                return
            self._in_transaction = True
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                self._in_transaction = False

    def _run(self, sql: str, params=()):
        with self._lock:
            if self._in_transaction:
                return self._conn.execute(sql, params)
            with self.transaction():
                return self._conn.execute(sql, params)

    _IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    @classmethod
    def _identifier(cls, value: str) -> str:
        if not isinstance(value, str) or not cls._IDENT.fullmatch(value):
            raise ValueError(f"unsafe SQL identifier: {value}")
        return value

    @classmethod
    def _where_clause(cls, where: str) -> str:
        """Allow only parameterized, identifier-based predicates."""
        if not isinstance(where, str) or not where.strip():
            raise ValueError("WHERE clause cannot be empty")
        atom = r"(?:[A-Za-z_][A-Za-z0-9_]*\s*(?:=|!=|<>|<=|>=|<|>|LIKE)\s*\?|[A-Za-z_][A-Za-z0-9_]*\s+IS(?:\s+NOT)?\s+NULL|[0-9]+\s*=\s*[0-9]+)"
        pattern = rf"^\s*{atom}(?:\s+(?:AND|OR)\s+{atom})*\s*$"
        if not re.fullmatch(pattern, where, flags=re.IGNORECASE):
            raise ValueError("unsafe or unsupported SQL WHERE clause")
        return where

    # ── CRUD ────────────────────────────────

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        self._ensure_init()
        if not isinstance(data, dict) or not data:
            raise ValueError("insert data must be a non-empty dictionary")
        table = self._identifier(table)
        cols = ", ".join(self._identifier(k) for k in data.keys())
        phs = ", ".join(["?" for _ in data])
        cur = self._run(f"INSERT INTO {table} ({cols}) VALUES ({phs})", list(data.values()))
        return cur.lastrowid

    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        self._ensure_init()
        if not rows:
            return 0
        if not all(isinstance(row, dict) and row for row in rows):
            raise ValueError("insert_many rows must be non-empty dictionaries")
        keys = tuple(rows[0].keys())
        if any(tuple(row.keys()) != keys for row in rows[1:]):
            raise ValueError("insert_many rows must have identical columns")
        table = self._identifier(table)
        cols = ", ".join(self._identifier(k) for k in keys)
        phs = ", ".join(["?" for _ in rows[0]])
        sql = f"INSERT INTO {table} ({cols}) VALUES ({phs})"
        data = [list(r.values()) for r in rows]
        if self._in_transaction:
            self._conn.executemany(sql, data)
        else:
            with self.transaction():
                self._conn.executemany(sql, data)
        return len(rows)

    def query(self, sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
        with self._lock:
            self._ensure_init()
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._ensure_init()
            row = self._conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        self._ensure_init()
        if not isinstance(data, dict) or not data:
            raise ValueError("update data must be a non-empty dictionary")
        table = self._identifier(table)
        sets = ", ".join(f"{self._identifier(k)} = ?" for k in data)
        cur = self._run(f"UPDATE {table} SET {sets} WHERE {self._where_clause(where)}", list(data.values()) + list(where_params))
        return cur.rowcount

    def delete(self, table: str, where: str, where_params: tuple = ()) -> int:
        self._ensure_init()
        table = self._identifier(table)
        cur = self._run(f"DELETE FROM {table} WHERE {self._where_clause(where)}", where_params)
        return cur.rowcount

    def count(self, table: str, where: str = "1=1", params: tuple = ()) -> int:
        self._ensure_init()
        table = self._identifier(table)
        with self._lock:
            return self._conn.execute(f"SELECT COUNT(*) as c FROM {table} WHERE {self._where_clause(where)}", params).fetchone()["c"]

    def table_exists(self, name: str) -> bool:
        self._ensure_init()
        name = self._identifier(name)
        with self._lock:
            return self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

    def get_tables(self) -> List[str]:
        self._ensure_init()
        with self._lock:
            return [r["name"] for r in self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version'").fetchall()]

    # ── Backup & Restore ────────────────────

    def backup(self, backup_path: str) -> Path:
        self._ensure_init()
        dest = self._safe_path(backup_path, "backup path")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            with sqlite3.connect(str(dest)) as bc:
                self._conn.backup(bc)
        return dest

    def restore(self, backup_path: str) -> None:
        """Atomically replace the live DB after validating the backup."""
        bf = self._safe_path(backup_path, "backup path")
        if not bf.exists() or not bf.is_file():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        try:
            with sqlite3.connect(str(bf)) as check_conn:
                if check_conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Backup integrity check failed")
        except sqlite3.DatabaseError as exc:
            raise RuntimeError("Backup integrity check failed") from exc
        with self._lock:
            was_initialized = self._initialized
            if self._conn is not None:
                self._conn.close()
                self._conn = None
                self._initialized = False
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            fd, staged_name = tempfile.mkstemp(dir=str(self._db_path.parent), suffix=".restore.tmp")
            os.close(fd)
            staged = Path(staged_name)
            old_name = None
            try:
                shutil.copy2(str(bf), str(staged))
                with sqlite3.connect(str(staged)) as check_conn:
                    if check_conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                        raise RuntimeError("Staged backup integrity check failed")
                if self._db_path.exists():
                    fd, old_name = tempfile.mkstemp(dir=str(self._db_path.parent), suffix=".pre_restore.tmp")
                    os.close(fd)
                    os.replace(str(self._db_path), old_name)
                os.replace(str(staged), str(self._db_path))
                staged = None
                if was_initialized or self._conn is None:
                    try:
                        self.initialize()
                    except Exception:
                        if self._db_path.exists():
                            os.unlink(self._db_path)
                        if old_name and os.path.exists(old_name):
                            os.replace(old_name, str(self._db_path))
                        self.initialize()
                        raise
                if old_name and os.path.exists(old_name):
                    os.unlink(old_name)
            except Exception:
                if staged and staged.exists():
                    staged.unlink()
                if old_name and os.path.exists(old_name) and not self._db_path.exists():
                    os.replace(old_name, str(self._db_path))
                if was_initialized and not self._initialized:
                    self.initialize()
                raise

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        with self._lock:
            try:
                self._ensure_init()
                self._conn.execute("SELECT 1")
                report["checks"]["connection"] = {
                    "status": "PASS",
                    "message": "Connected",
                }
                expected = set(get_all_table_names())
                existing = {
                    row["name"]
                    for row in self._conn.execute(
                        "SELECT name FROM sqlite_master "
                        "WHERE type='table' AND name != 'schema_version'"
                    ).fetchall()
                }
                missing = expected - existing
                report["checks"]["tables"] = {
                    "status": "PASS" if not missing else "FAIL",
                    "message": (
                        f"All {len(expected)} tables exist"
                        if not missing
                        else f"Missing: {', '.join(sorted(missing))}"
                    ),
                }
                mode = self._conn.execute("PRAGMA journal_mode").fetchone()[0]
                report["checks"]["wal_mode"] = {
                    "status": "PASS" if mode == "wal" else "WARN",
                    "message": f"Journal mode: {mode}",
                }
            except Exception as exc:
                report["checks"]["connection"] = {
                    "status": "FAIL",
                    "message": str(exc)[:300],
                }
                report["overall"] = "FAIL"
                return report

            sz = self._db_path.stat().st_size if self._db_path.exists() else 0
            report["checks"]["file_size"] = {
                "status": "PASS",
                "message": f"{sz / 1024:.1f} KB",
            }

        statuses = [check["status"] for check in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report

    # ── Stats ───────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            self._ensure_init()
            tables = [
                row["name"]
                for row in self._conn.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name != 'schema_version'"
                ).fetchall()
            ]
            stats = {"tables": len(tables), "row_counts": {}, "total_rows": 0}
            for table in tables:
                stats["row_counts"][table] = self._conn.execute(
                    f"SELECT COUNT(*) AS c FROM {self._identifier(table)}"
                ).fetchone()["c"]
            stats["total_rows"] = sum(stats["row_counts"].values())
            stats["db_size_kb"] = (
                self._db_path.stat().st_size / 1024
                if self._db_path.exists()
                else 0
            )
            return stats

    def _ensure_init(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized.")
