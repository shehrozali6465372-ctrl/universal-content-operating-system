"""Repository Pattern — Type-safe data access for each table.

Each repository handles CRUD operations for its table.
Uses ConnectionPool for database access.
"""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class BaseRepository:
    """Base repository with common CRUD operations."""

    def __init__(self, pool, table_name: str):
        self._pool = pool
        self._table = table_name

    def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        return self._pool.query_one(f"SELECT * FROM {self._table} WHERE id = %s", (id,))

    def get_all(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        return self._pool.query(f"SELECT * FROM {self._table} ORDER BY id LIMIT %s OFFSET %s", (limit, offset))

    def count(self, where: str = "1=1", params: tuple = ()) -> int:
        return self._pool.count(self._table, where, params)

    def delete_by_id(self, id: int) -> int:
        return self._pool.delete(self._table, "id = %s", (id,))

    def delete_all(self) -> int:
        return self._pool.delete(self._table, "1=1")


class ConfigRepository(BaseRepository):
    """Repository for agent_config table."""

    def __init__(self, pool):
        super().__init__(pool, "agent_config")

    def get(self, key: str) -> Optional[str]:
        row = self._pool.query_one("SELECT value FROM agent_config WHERE key = %s", (key,))
        return row["value"] if row else None

    def set(self, key: str, value: str, category: str = "general") -> int:
        existing = self._pool.query_one("SELECT id FROM agent_config WHERE key = %s", (key,))
        if existing:
            self._pool.update("agent_config", {"value": value, "updated_at": datetime.now(timezone.utc)}, "key = %s", (key,))
            return existing["id"]
        else:
            return self._pool.insert("agent_config", {"key": key, "value": value, "category": category})

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        return self._pool.query("SELECT * FROM agent_config WHERE category = %s", (category,))

    def delete(self, key: str) -> int:
        return self._pool.delete("agent_config", "key = %s", (key,))


class MemoryRepository(BaseRepository):
    """Repository for agent_memory table."""

    def __init__(self, pool):
        super().__init__(pool, "agent_memory")

    def save(self, level: str, category: str, key: str, value: str, tags: str = "", importance: float = 0.5) -> int:
        existing = self._pool.query_one(
            "SELECT id FROM agent_memory WHERE level = %s AND category = %s AND key = %s",
            (level, category, key)
        )
        if existing:
            self._pool.update("agent_memory", {
                "value": value, "tags": tags, "importance": importance,
                "updated_at": datetime.now(timezone.utc)
            }, "id = %s", (existing["id"],))
            return existing["id"]
        else:
            return self._pool.insert("agent_memory", {
                "level": level, "category": category, "key": key,
                "value": value, "tags": tags, "importance": importance,
            })

    def load(self, level: str, category: str, key: str) -> Optional[str]:
        row = self._pool.query_one(
            "SELECT value FROM agent_memory WHERE level = %s AND category = %s AND key = %s",
            (level, category, key)
        )
        return row["value"] if row else None

    def search(self, level: str, category: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        if category:
            return self._pool.query(
                "SELECT * FROM agent_memory WHERE level = %s AND category = %s ORDER BY importance DESC LIMIT %s",
                (level, category, limit)
            )
        return self._pool.query(
            "SELECT * FROM agent_memory WHERE level = %s ORDER BY importance DESC LIMIT %s",
            (level, limit)
        )

    def increment_access(self, id: int) -> None:
        self._pool.execute(
            "UPDATE agent_memory SET access_count = access_count + 1, last_accessed = %s WHERE id = %s",
            (datetime.now(timezone.utc), id)
        )

    def get_by_level(self, level: str) -> List[Dict[str, Any]]:
        return self._pool.query("SELECT * FROM agent_memory WHERE level = %s ORDER BY importance DESC", (level,))

    def delete_by_level(self, level: str) -> int:
        return self._pool.delete("agent_memory", "level = %s", (level,))


class LogRepository(BaseRepository):
    """Repository for agent_logs table."""

    def __init__(self, pool):
        super().__init__(pool, "agent_logs")

    def log(self, level: str, module: str, message: str, details: Optional[Dict] = None) -> int:
        return self._pool.insert("agent_logs", {
            "level": level, "module": module, "message": message,
            "details": json.dumps(details) if details else None,
        })

    def get_by_level(self, level: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM agent_logs WHERE level = %s ORDER BY created_at DESC LIMIT %s",
            (level, limit)
        )

    def get_by_module(self, module: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM agent_logs WHERE module = %s ORDER BY created_at DESC LIMIT %s",
            (module, limit)
        )

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM agent_logs ORDER BY created_at DESC LIMIT %s", (limit,)
        )

    def cleanup(self, days: int = 30) -> int:
        return self._pool.delete(
            "agent_logs", "created_at < NOW() - INTERVAL '%s days'", (days,)
        )


class PostRepository(BaseRepository):
    """Repository for published_posts table."""

    def __init__(self, pool):
        super().__init__(pool, "published_posts")

    def save_post(self, platform: str, post_id: str, content: str, status: str = "published", image_path: str = None) -> int:
        return self._pool.insert("published_posts", {
            "platform": platform, "post_id": post_id, "content": content,
            "status": status, "image_path": image_path,
            "published_at": datetime.now(timezone.utc),
        })

    def get_by_platform(self, platform: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM published_posts WHERE platform = %s ORDER BY published_at DESC LIMIT %s",
            (platform, limit)
        )

    def get_by_status(self, status: str) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM published_posts WHERE status = %s ORDER BY created_at DESC",
            (status,)
        )

    def update_engagement(self, id: int, score: float) -> int:
        return self._pool.update("published_posts", {"engagement_score": score}, "id = %s", (id,))


class AnalyticsRepository(BaseRepository):
    """Repository for analytics_cache table."""

    def __init__(self, pool):
        super().__init__(pool, "analytics_cache")

    def record(self, metric_name: str, metric_value: float, dimensions: Optional[Dict] = None) -> int:
        return self._pool.insert("analytics_cache", {
            "metric_name": metric_name, "metric_value": metric_value,
            "dimensions": json.dumps(dimensions) if dimensions else "{}",
        })

    def get_metric(self, metric_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM analytics_cache WHERE metric_name = %s ORDER BY recorded_at DESC LIMIT %s",
            (metric_name, limit)
        )

    def get_latest(self, metric_name: str) -> Optional[Dict[str, Any]]:
        return self._pool.query_one(
            "SELECT * FROM analytics_cache WHERE metric_name = %s ORDER BY recorded_at DESC LIMIT 1",
            (metric_name,)
        )


class LearningRepository(BaseRepository):
    """Repository for learning_history table."""

    def __init__(self, pool):
        super().__init__(pool, "learning_history")

    def save_lesson(self, lesson_type: str, content: str, source: str = None, confidence: float = 0.5) -> int:
        return self._pool.insert("learning_history", {
            "lesson_type": lesson_type, "content": content,
            "source": source, "confidence": confidence,
        })

    def get_by_type(self, lesson_type: str, limit: int = 50) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM learning_history WHERE lesson_type = %s ORDER BY confidence DESC LIMIT %s",
            (lesson_type, limit)
        )

    def mark_applied(self, id: int) -> int:
        return self._pool.update("learning_history", {"applied": True}, "id = %s", (id,))

    def get_unapplied(self, limit: int = 20) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM learning_history WHERE applied = FALSE ORDER BY confidence DESC LIMIT %s",
            (limit,)
        )


class JobRepository(BaseRepository):
    """Repository for scheduled_jobs table."""

    def __init__(self, pool):
        super().__init__(pool, "scheduled_jobs")

    def save_job(self, name: str, job_type: str, schedule_cron: str = None, config_json: Dict = None) -> int:
        return self._pool.insert("scheduled_jobs", {
            "name": name, "job_type": job_type,
            "schedule_cron": schedule_cron,
            "config_json": json.dumps(config_json) if config_json else None,
        })

    def get_by_type(self, job_type: str) -> List[Dict[str, Any]]:
        return self._pool.query(
            "SELECT * FROM scheduled_jobs WHERE job_type = %s AND enabled = TRUE",
            (job_type,)
        )

    def get_enabled(self) -> List[Dict[str, Any]]:
        return self._pool.query("SELECT * FROM scheduled_jobs WHERE enabled = TRUE")

    def update_last_run(self, id: int) -> int:
        return self._pool.update("scheduled_jobs", {"last_run": datetime.now(timezone.utc)}, "id = %s", (id,))
