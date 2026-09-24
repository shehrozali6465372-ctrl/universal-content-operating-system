"""
Database Migrations Module
Layer 1: Core System — Module 4

Handles schema versioning and migrations.
Ensures old data is never lost when schema changes.
"""

import os
import sqlite3
from typing import List, Dict
from threading import RLock


class MigrationRegistry:
    """Registry of all schema migrations."""

    def __init__(self):
        self._migrations: List[Dict] = []

    def register(self, version: int, description: str, up_sql: str) -> None:
        """Register a migration exactly once; duplicate versions are invalid."""
        if not isinstance(version, int) or isinstance(version, bool) or version < 1:
            raise ValueError("migration version must be a positive integer")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("migration description must be non-empty")
        if not isinstance(up_sql, str) or not up_sql.strip():
            raise ValueError("migration SQL must be non-empty")
        if any(m["version"] == version for m in self._migrations):
            raise ValueError(f"duplicate migration version: {version}")
        self._migrations.append({
            "version": version,
            "description": description,
            "up_sql": up_sql,
        })
        self._migrations.sort(key=lambda m: m["version"])

    def get_pending(self, current_version: int) -> List[Dict]:
        """Get all migrations after current_version."""
        return [m for m in self._migrations if m["version"] > current_version]

    def get_all(self) -> List[Dict]:
        return list(self._migrations)


class MigrationManager:
    """Manages database schema migrations."""

    _path_locks: Dict[str, RLock] = {}
    _path_locks_guard = RLock()

    @staticmethod
    def _database_path(db_connection: sqlite3.Connection) -> str:
        row = db_connection.execute("PRAGMA database_list").fetchone()
        path = row[2] if row and len(row) > 2 else ""
        return os.path.abspath(path) if path else ":memory:"

    def __init__(self, db_connection: sqlite3.Connection):
        self._conn = db_connection
        self._registry = MigrationRegistry()
        self._lock = RLock()
        key = self._database_path(db_connection)
        with self._path_locks_guard:
            self._migration_lock = self._path_locks.setdefault(key, RLock())
        with self._migration_lock:
            self._ensure_version_table()
        self._register_migrations()

    def _ensure_version_table(self) -> None:
        """Create schema_version table if not exists."""
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._conn.commit()

    def _register_migrations(self) -> None:
        """Register all known migrations."""
        self._registry.register(
            version=1,
            description="Initial schema — all 8 tables",
            up_sql="""
                CREATE TABLE IF NOT EXISTS agent_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    category TEXT DEFAULT 'general',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS agent_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    importance REAL DEFAULT 0.5,
                    access_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category, key)
                );
                CREATE TABLE IF NOT EXISTS agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    level TEXT NOT NULL,
                    module TEXT NOT NULL,
                    message TEXT NOT NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS agent_versions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT NOT NULL,
                    component TEXT NOT NULL,
                    change_description TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS scheduled_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    job_type TEXT NOT NULL,
                    schedule_cron TEXT,
                    config_json TEXT,
                    enabled INTEGER DEFAULT 1,
                    last_run TIMESTAMP,
                    next_run TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS published_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    post_id TEXT,
                    content TEXT NOT NULL,
                    image_path TEXT,
                    status TEXT DEFAULT 'draft',
                    engagement_score REAL DEFAULT 0.0,
                    scheduled_at TIMESTAMP,
                    published_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS analytics_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    source TEXT,
                    period TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS learning_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lesson_type TEXT NOT NULL,
                    input_summary TEXT NOT NULL,
                    output_summary TEXT,
                    feedback_score REAL DEFAULT 0.0,
                    learned_from TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """,
        )
        self._registry.register(
            version=2,
            description="Add index on agent_memory for faster lookups",
            up_sql="CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_memory(category);",
        )

    def _validate_history(self) -> None:
        """Reject missing, unknown, or non-contiguous applied migration versions."""
        history = self._conn.execute(
            "SELECT version FROM schema_version ORDER BY version"
        ).fetchall()
        versions = [row[0] for row in history]
        if any(
            not isinstance(version, int) or isinstance(version, bool) or version < 1
            for version in versions
        ):
            raise RuntimeError("Invalid schema migration history: version must be a positive integer")
        expected = list(range(1, len(versions) + 1))
        if versions != expected:
            raise RuntimeError(
                f"Invalid schema migration history: expected contiguous versions {expected}, got {versions}"
            )
        registered = {migration["version"] for migration in self._registry.get_all()}
        unknown = [version for version in versions if version not in registered]
        if unknown:
            raise RuntimeError(
                f"Invalid schema migration history: unknown migration versions {unknown}"
            )

    def get_current_version(self) -> int:
        """Get current schema version after validating persisted history."""
        self._validate_history()
        cursor = self._conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_pending_migrations(self) -> List[Dict]:
        """Get migrations that haven't been applied yet."""
        current = self.get_current_version()
        return self._registry.get_pending(current)

    def migrate(self) -> List[int]:
        """Apply pending migrations transactionally and in strict version order."""
        with self._migration_lock:
            return self._migrate_locked()

    def _migrate_locked(self) -> List[int]:
        with self._lock:
            applied = []
            pending = self.get_pending_migrations()
            expected = self.get_current_version() + 1
            for migration in pending:
                version = migration["version"]
                if version != expected:
                    raise RuntimeError(
                        f"Migration ordering gap: expected v{expected}, got v{version}"
                    )
                try:
                    self._conn.execute("BEGIN IMMEDIATE")
                    statement = ""
                    for line in migration["up_sql"].splitlines():
                        statement += line + "\n"
                        if sqlite3.complete_statement(statement):
                            sql = statement.strip()
                            if sql:
                                self._conn.execute(sql)
                            statement = ""
                    if statement.strip():
                        self._conn.execute(statement)
                    self._conn.execute(
                        "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                        (version, migration["description"]),
                    )
                    self._conn.commit()
                    applied.append(version)
                    expected += 1
                except Exception as e:
                    self._conn.rollback()
                    raise RuntimeError(
                        f"Migration v{version} failed; transaction rolled back"
                    ) from e
            return applied

    def rollback(self, target_version: int, allow_data_loss: bool = False) -> None:
        """Rollback only reversible migrations under the migration lock."""
        if not isinstance(target_version, int) or isinstance(target_version, bool) or target_version < 0:
            raise ValueError("target_version must be a non-negative integer")
        with self._lock:
            current = self.get_current_version()
            if target_version >= current:
                return
            if target_version < 1:
                if not allow_data_loss:
                    raise RuntimeError("Rollback below v1 requires explicit allow_data_loss=True")
                raise RuntimeError("Initial schema rollback is not implemented safely")
            # v2 is index-only and therefore safely reversible.
            if current >= 2 and target_version == 1:
                try:
                    self._conn.execute("BEGIN IMMEDIATE")
                    self._conn.execute("DROP INDEX IF EXISTS idx_memory_category")
                    self._conn.execute("DELETE FROM schema_version WHERE version = 2")
                    self._conn.commit()
                except Exception as exc:
                    self._conn.rollback()
                    raise RuntimeError("Migration rollback failed; transaction rolled back") from exc
                return
            raise RuntimeError(
                f"Rollback from v{current} to v{target_version} is not safely reversible"
            )

    def migration_history(self) -> List[Dict]:
        """Get history of applied migrations."""
        cursor = self._conn.execute(
            "SELECT version, description, applied_at FROM schema_version ORDER BY version"
        )
        return [
            {"version": row[0], "description": row[1], "applied_at": row[2]}
            for row in cursor.fetchall()
        ]
