"""PipelinePersistence — Saves pipeline results to SQLite.

Connects PipelineWiring to DatabaseManager so every run is persisted:
- Generated content → published_posts
- Quality scores → analytics_cache
- Learning entries → learning_history
- Pipeline logs → agent_logs
- Config → agent_config
"""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from layers.layer01_core.modules.database_manager import DatabaseManager


class PipelinePersistence:
    """Persist pipeline execution results to SQLite database."""

    def __init__(self, db_path: str = "data/agent.db") -> None:
        self._db = DatabaseManager(db_path=db_path)
        self._db.initialize()

    def save_content(self, topic: str, platform: str, content: str,
                     image_prompt: str = "", quality_score: float = 0.0,
                     status: str = "draft", metadata: Optional[Dict] = None) -> int:
        """Save generated content to published_posts table."""
        return self._db.insert("published_posts", {
            "platform": platform,
            "content": content,
            "image_path": image_prompt,
            "status": status,
            "engagement_score": quality_score,
            "scheduled_at": None,
            "published_at": None,
        })

    def save_analytics(self, metric_name: str, metric_value: float,
                       source: str = "pipeline", period: str = "daily") -> int:
        """Save analytics metric to analytics_cache table."""
        return self._db.insert("analytics_cache", {
            "metric_name": metric_name,
            "metric_value": metric_value,
            "source": source,
            "period": period,
        })

    def save_learning(self, lesson_type: str, input_summary: str,
                      output_summary: str = "", feedback_score: float = 0.0,
                      learned_from: str = "pipeline") -> int:
        """Save learning entry to learning_history table."""
        return self._db.insert("learning_history", {
            "lesson_type": lesson_type,
            "input_summary": input_summary,
            "output_summary": output_summary,
            "feedback_score": feedback_score,
            "learned_from": learned_from,
        })

    def save_log(self, level: str, module: str, message: str,
                 details: Optional[str] = None) -> int:
        """Save log entry to agent_logs table."""
        return self._db.insert("agent_logs", {
            "level": level,
            "module": module,
            "message": message,
            "details": details,
        })

    def save_config(self, key: str, value: str, category: str = "general") -> None:
        """Save or update config in agent_config table."""
        existing = self._db.query_one(
            "SELECT key FROM agent_config WHERE key = ?", (key,)
        )
        if existing:
            self._db.update("agent_config", {"value": value}, "key = ?", (key,))
        else:
            self._db.insert("agent_config", {
                "key": key, "value": value, "category": category,
            })

    def save_pipeline_run(self, response_dict: Dict[str, Any]) -> int:
        """Save complete pipeline execution result.

        Stores:
        - Content in published_posts
        - Quality score in analytics_cache
        - Learning entry in learning_history
        - Pipeline log in agent_logs
        Returns the content_id from published_posts.
        """
        topic = response_dict.get("topic", "")
        platform = response_dict.get("platform", "facebook")
        content_length = response_dict.get("content_length", 0)
        quality_score = response_dict.get("quality_score", 0.0)

        # Save content
        content_id = self.save_content(
            topic=topic,
            platform=platform,
            content=f"[Pipeline Run] {topic}",
            quality_score=quality_score,
            status="generated",
        )

        # Save quality metric
        if quality_score > 0:
            self.save_analytics("quality_score", quality_score,
                               source=f"pipeline_{platform}")

        # Save content length metric
        self.save_analytics("content_length", float(content_length),
                           source=f"pipeline_{platform}")

        # Save step count metric
        steps_completed = response_dict.get("steps_completed", 0)
        self.save_analytics("steps_completed", float(steps_completed),
                           source="pipeline")

        # Save learning entry
        self.save_learning(
            lesson_type="pipeline_execution",
            input_summary=f"Topic: {topic} | Platform: {platform}",
            output_summary=f"Quality: {quality_score}/10, Length: {content_length} chars",
            feedback_score=quality_score / 10.0,
        )

        # Save log
        self.save_log("INFO", "pipeline", f"Pipeline completed: {topic} → {platform}")

        return content_id

    def get_content_history(self, platform: Optional[str] = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent content from published_posts."""
        if platform:
            return self._db.query(
                "SELECT * FROM published_posts WHERE platform = ? ORDER BY created_at DESC LIMIT ?",
                (platform, limit)
            )
        return self._db.query(
            "SELECT * FROM published_posts ORDER BY created_at DESC LIMIT ?", (limit,)
        )

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary from analytics_cache."""
        rows = self._db.query(
            "SELECT metric_name, AVG(metric_value) as avg_val, COUNT(*) as count "
            "FROM analytics_cache GROUP BY metric_name"
        )
        return {r["metric_name"]: {"avg": r["avg_val"], "count": r["count"]} for r in rows}

    def get_learning_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent learning entries."""
        return self._db.query(
            "SELECT * FROM learning_history ORDER BY created_at DESC LIMIT ?", (limit,)
        )

    def get_db_stats(self) -> Dict[str, Any]:
        """Get database statistics."""
        return self._db.get_stats()

    def close(self) -> None:
        """Close database connection."""
        self._db.close()
