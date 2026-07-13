"""
Database Migrations Module
Layer 1: Core System — Module 4

Handles schema versioning and migrations.
Ensures old data is never lost when schema changes.
"""

import sqlite3
from typing import List, Dict, Callable
from datetime import datetime, timezone


class MigrationRegistry:
    """Registry of all schema migrations."""

    def __init__(self):
        self._migrations: List[Dict] = []

    def register(self, version: int, description: str, up_sql: str) -> None:
        """Register a new migration."""
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

    def __init__(self, db_connection: sqlite3.Connection):
        self._conn = db_connection
        self._registry = MigrationRegistry()
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
        # Example future migration (placeholder):
        self._registry.register(
            version=2,
            description="Add index on agent_memory for faster lookups",
            up_sql="CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_memory(category);",
        )

    def get_current_version(self) -> int:
        """Get current schema version."""
        cursor = self._conn.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()
        return result[0] if result[0] is not None else 0

    def get_pending_migrations(self) -> List[Dict]:
        """Get migrations that haven't been applied yet."""
        current = self.get_current_version()
        return self._registry.get_pending(current)

    def migrate(self) -> List[int]:
        """Apply all pending migrations. Returns list of applied versions."""
        applied = []
        pending = self.get_pending_migrations()

        for migration in pending:
            try:
                self._conn.executescript(migration["up_sql"])
                self._conn.execute(
                    "INSERT INTO schema_version (version, description) VALUES (?, ?)",
                    (migration["version"], migration["description"]),
                )
                self._conn.commit()
                applied.append(migration["version"])
            except Exception as e:
                self._conn.rollback()
                raise RuntimeError(
                    f"Migration v{migration['version']} failed: {e}"
                )

        return applied

    def rollback(self, target_version: int) -> None:
        """Rollback to a specific version (WARNING: may lose data)."""
        current = self.get_current_version()
        if target_version >= current:
            return
        self._conn.execute(
            "DELETE FROM schema_version WHERE version > ?", (target_version,)
        )
        self._conn.commit()

    def migration_history(self) -> List[Dict]:
        """Get history of applied migrations."""
        cursor = self._conn.execute(
            "SELECT version, description, applied_at FROM schema_version ORDER BY version"
        )
        return [
            {"version": row[0], "description": row[1], "applied_at": row[2]}
            for row in cursor.fetchall()
        ]
