"""
Database Manager Module
Layer 1: Core System — Module 4
"""

import sqlite3
import re
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from contextlib import contextmanager
from threading import RLock

from layers.layer01_core.modules.models import get_all_table_names
from layers.layer01_core.modules.migrations import MigrationManager


class DatabaseManager:
    def __init__(self, db_path: str = "data/agent.db", project_root: Optional[str] = None):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._db_path = self._project_root / db_path
        self._conn: Optional[sqlite3.Connection] = None
        self._migration_manager: Optional[MigrationManager] = None
        self._initialized = False
        self._in_transaction = False
        self._lock = RLock()

    @property
    def db_path(self) -> Path:
        return self._db_path

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self) -> "DatabaseManager":
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False, timeout=30.0)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._migration_manager = MigrationManager(self._conn)
        self._migration_manager.migrate()
        self._initialized = True
        return self

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
            self._initialized = False

    @contextmanager
    def transaction(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized.")
        old_flag = self._in_transaction
        self._in_transaction = True
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                self._in_transaction = old_flag

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

    @staticmethod
    def _where_clause(where: str) -> str:
        if not isinstance(where, str) or not where.strip():
            raise ValueError("WHERE clause cannot be empty")
        if ";" in where or "--" in where or "/*" in where or "*/" in where:
            raise ValueError("unsafe SQL in WHERE clause")
        return where

    # ── CRUD ────────────────────────────────

    def insert(self, table: str, data: Dict[str, Any]) -> int:
        self._ensure_init()
        table = self._identifier(table)
        cols = ", ".join(self._identifier(k) for k in data.keys())
        phs = ", ".join(["?" for _ in data])
        cur = self._run(f"INSERT INTO {table} ({cols}) VALUES ({phs})", list(data.values()))
        return cur.lastrowid

    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> int:
        self._ensure_init()
        if not rows:
            return 0
        table = self._identifier(table)
        cols = ", ".join(self._identifier(k) for k in rows[0].keys())
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
        self._ensure_init()
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, params).fetchall()]

    def query_one(self, sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        self._ensure_init()
        with self._lock:
            row = self._conn.execute(sql, params).fetchone()
            return dict(row) if row else None

    def update(self, table: str, data: Dict[str, Any], where: str, where_params: tuple = ()) -> int:
        self._ensure_init()
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
        return self._conn.execute(f"SELECT COUNT(*) as c FROM {table} WHERE {self._where_clause(where)}", params).fetchone()["c"]

    def table_exists(self, name: str) -> bool:
        self._ensure_init()
        name = self._identifier(name)
        return self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

    def get_tables(self) -> List[str]:
        self._ensure_init()
        return [r["name"] for r in self._conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != 'schema_version'").fetchall()]

    # ── Backup & Restore ────────────────────

    def backup(self, backup_path: str) -> Path:
        self._ensure_init()
        dest = self._project_root / backup_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(str(dest)) as bc:
            self._conn.backup(bc)
        return dest

    def restore(self, backup_path: str) -> None:
        bf = Path(backup_path) if Path(backup_path).is_absolute() else self._project_root / backup_path
        if not bf.exists():
            raise FileNotFoundError(f"Backup not found: {backup_path}")
        self.close()
        shutil.copy2(str(bf), str(self._db_path))
        self.initialize()

    # ── Health Check ────────────────────────

    def health_check(self) -> Dict[str, Any]:
        report = {"timestamp": datetime.now(timezone.utc).isoformat(), "checks": {}, "overall": "PASS"}
        try:
            self._ensure_init()
            self._conn.execute("SELECT 1")
            report["checks"]["connection"] = {"status": "PASS", "message": "Connected"}
        except Exception as e:
            report["checks"]["connection"] = {"status": "FAIL", "message": str(e)}
            report["overall"] = "FAIL"
            return report

        expected = set(get_all_table_names())
        missing = expected - set(self.get_tables())
        report["checks"]["tables"] = {
            "status": "PASS" if not missing else "FAIL",
            "message": f"All {len(expected)} tables exist" if not missing else f"Missing: {', '.join(missing)}",
        }

        mode = self._conn.execute("PRAGMA journal_mode").fetchone()[0]
        report["checks"]["wal_mode"] = {"status": "PASS" if mode == "wal" else "WARN", "message": f"Journal mode: {mode}"}

        sz = self._db_path.stat().st_size if self._db_path.exists() else 0
        report["checks"]["file_size"] = {"status": "PASS", "message": f"{sz / 1024:.1f} KB"}

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report

    # ── Stats ───────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        self._ensure_init()
        tables = self.get_tables()
        stats = {"tables": len(tables), "row_counts": {}, "total_rows": 0}
        for t in tables:
            stats["row_counts"][t] = self.count(t)
        stats["total_rows"] = sum(stats["row_counts"].values())
        stats["db_size_kb"] = self._db_path.stat().st_size / 1024 if self._db_path.exists() else 0
        return stats

    def _ensure_init(self):
        if not self._initialized:
            raise RuntimeError("Database not initialized.")
