"""
Database Models
Layer 1: Core System — Module 4

Defines all table schemas for SQLite.
Each table has a CREATE statement and column definitions.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class TableSchema:
    """Definition of a database table."""
    name: str
    columns: List[str]
    create_sql: str
    description: str = ""


# ──────────────────────────────────────────────
# TABLE DEFINITIONS
# ──────────────────────────────────────────────

AGENT_CONFIG_TABLE = TableSchema(
    name="agent_config",
    columns=["key TEXT PRIMARY KEY", "value TEXT NOT NULL", "category TEXT DEFAULT 'general'",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP", "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
        CREATE TABLE IF NOT EXISTS agent_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    description="Stores agent configuration key-value pairs",
)

AGENT_MEMORY_TABLE = TableSchema(
    name="agent_memory",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "category TEXT NOT NULL",
             "key TEXT NOT NULL", "value TEXT NOT NULL", "importance REAL DEFAULT 0.5",
             "access_count INTEGER DEFAULT 0", "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
             "last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
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
        )
    """,
    description="Agent long-term memory storage",
)

AGENT_LOGS_TABLE = TableSchema(
    name="agent_logs",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "level TEXT NOT NULL",
             "module TEXT NOT NULL", "message TEXT NOT NULL", "details TEXT",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    description="System activity and error logs",
)

AGENT_VERSIONS_TABLE = TableSchema(
    name="agent_versions",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "version TEXT NOT NULL",
             "component TEXT NOT NULL", "change_description TEXT NOT NULL",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
        CREATE TABLE IF NOT EXISTS agent_versions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            component TEXT NOT NULL,
            change_description TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    description="Version history for all components",
)

SCHEDULED_JOBS_TABLE = TableSchema(
    name="scheduled_jobs",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "name TEXT NOT NULL UNIQUE",
             "job_type TEXT NOT NULL", "schedule_cron TEXT", "config_json TEXT",
             "enabled INTEGER DEFAULT 1", "last_run TIMESTAMP", "next_run TIMESTAMP",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
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
        )
    """,
    description="Scheduled task definitions",
)

PUBLISHED_POSTS_TABLE = TableSchema(
    name="published_posts",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "platform TEXT NOT NULL",
             "post_id TEXT", "content TEXT NOT NULL", "image_path TEXT",
             "status TEXT DEFAULT 'draft'", "engagement_score REAL DEFAULT 0.0",
             "scheduled_at TIMESTAMP", "published_at TIMESTAMP",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
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
        )
    """,
    description="All published or drafted posts",
)

ANALYTICS_CACHE_TABLE = TableSchema(
    name="analytics_cache",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "metric_name TEXT NOT NULL",
             "metric_value REAL NOT NULL", "source TEXT", "period TEXT",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            source TEXT,
            period TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    description="Cached analytics metrics",
)

LEARNING_HISTORY_TABLE = TableSchema(
    name="learning_history",
    columns=["id INTEGER PRIMARY KEY AUTOINCREMENT", "lesson_type TEXT NOT NULL",
             "input_summary TEXT NOT NULL", "output_summary TEXT",
             "feedback_score REAL DEFAULT 0.0", "learned_from TEXT",
             "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"],
    create_sql="""
        CREATE TABLE IF NOT EXISTS learning_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lesson_type TEXT NOT NULL,
            input_summary TEXT NOT NULL,
            output_summary TEXT,
            feedback_score REAL DEFAULT 0.0,
            learned_from TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """,
    description="AI learning history and feedback",
)


# ──────────────────────────────────────────────
# TABLE REGISTRY
# ──────────────────────────────────────────────

ALL_TABLES: List[TableSchema] = [
    AGENT_CONFIG_TABLE,
    AGENT_MEMORY_TABLE,
    AGENT_LOGS_TABLE,
    AGENT_VERSIONS_TABLE,
    SCHEDULED_JOBS_TABLE,
    PUBLISHED_POSTS_TABLE,
    ANALYTICS_CACHE_TABLE,
    LEARNING_HISTORY_TABLE,
]


def get_table(name: str) -> TableSchema:
    """Get table schema by name."""
    for table in ALL_TABLES:
        if table.name == name:
            return table
    raise ValueError(f"Unknown table: {name}")


def get_all_table_names() -> List[str]:
    """Return list of all table names."""
    return [t.name for t in ALL_TABLES]
