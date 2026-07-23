"""PostgreSQL Schema — All table definitions for the Universal AI Content OS."""
from __future__ import annotations
from typing import List, Dict, Any


SCHEMA_VERSION = "1.0.0"

TABLES = [
    {
        "name": "agent_config",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "key VARCHAR(255) UNIQUE NOT NULL",
            "value TEXT NOT NULL",
            "category VARCHAR(100) DEFAULT 'general'",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_config_category ON agent_config(category)",
        ],
    },
    {
        "name": "agent_memory",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "level VARCHAR(50) NOT NULL",
            "category VARCHAR(100) NOT NULL",
            "key VARCHAR(255) NOT NULL",
            "value TEXT NOT NULL",
            "tags TEXT DEFAULT ''",
            "importance REAL DEFAULT 0.5",
            "access_count INTEGER DEFAULT 0",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE(level, category, key)",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_memory_level ON agent_memory(level)",
            "CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_memory(category)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON agent_memory(importance DESC)",
        ],
    },
    {
        "name": "agent_logs",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "level VARCHAR(20) NOT NULL",
            "module VARCHAR(100) NOT NULL",
            "message TEXT NOT NULL",
            "details JSONB",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON agent_logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_logs_module ON agent_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_logs_created ON agent_logs(created_at DESC)",
        ],
    },
    {
        "name": "agent_versions",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "version VARCHAR(50) NOT NULL",
            "component VARCHAR(100) NOT NULL",
            "change_description TEXT NOT NULL",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_versions_component ON agent_versions(component)",
        ],
    },
    {
        "name": "scheduled_jobs",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "name VARCHAR(255) UNIQUE NOT NULL",
            "job_type VARCHAR(100) NOT NULL",
            "schedule_cron VARCHAR(100)",
            "config_json JSONB",
            "enabled BOOLEAN DEFAULT TRUE",
            "last_run TIMESTAMP",
            "next_run TIMESTAMP",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_jobs_type ON scheduled_jobs(job_type)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON scheduled_jobs(enabled)",
        ],
    },
    {
        "name": "published_posts",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "platform VARCHAR(50) NOT NULL",
            "post_id VARCHAR(255)",
            "content TEXT NOT NULL",
            "image_path TEXT",
            "status VARCHAR(50) DEFAULT 'draft'",
            "engagement_score REAL DEFAULT 0.0",
            "scheduled_at TIMESTAMP",
            "published_at TIMESTAMP",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_posts_platform ON published_posts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_posts_status ON published_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_posts_published ON published_posts(published_at DESC)",
        ],
    },
    {
        "name": "analytics_cache",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "metric_name VARCHAR(255) NOT NULL",
            "metric_value REAL NOT NULL",
            "dimensions JSONB DEFAULT '{}'",
            "recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_analytics_metric ON analytics_cache(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_recorded ON analytics_cache(recorded_at DESC)",
        ],
    },
    {
        "name": "learning_history",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "lesson_type VARCHAR(100) NOT NULL",
            "content TEXT NOT NULL",
            "source VARCHAR(100)",
            "confidence REAL DEFAULT 0.5",
            "applied BOOLEAN DEFAULT FALSE",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_history(lesson_type)",
            "CREATE INDEX IF NOT EXISTS idx_learning_confidence ON learning_history(confidence DESC)",
        ],
    },
]


def get_create_table_sql(table):
    cols = ",\n            ".join(table["columns"])
    return f"CREATE TABLE IF NOT EXISTS {table['name']} (\n            {cols}\n        )"


def get_all_create_sql():
    return [get_create_table_sql(t) for t in TABLES]


def get_all_indexes_sql():
    indexes = []
    for t in TABLES:
        indexes.extend(t.get("indexes", []))
    return indexes
