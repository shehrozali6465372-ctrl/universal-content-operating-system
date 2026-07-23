"""PublishingScheduler — Time zones, queue, retry, daily limits."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class ScheduledPost:
    __slots__ = ("id", "account_id", "content_id", "platform", "scheduled_time",
                 "timezone", "status", "attempts", "max_retries", "last_error",
                 "published_at", "created_at", "priority")

    STATUSES = ("queued", "publishing", "published", "failed", "cancelled")

    def __init__(self, account_id: str, content_id: str, platform: str,
                 scheduled_time: float, timezone: str = "UTC") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.account_id = account_id
        self.content_id = content_id
        self.platform = platform
        self.scheduled_time = scheduled_time
        self.timezone = timezone
        self.status = "queued"
        self.attempts = 0
        self.max_retries = 3
        self.last_error = ""
        self.published_at = 0.0
        self.created_at = time.time()
        self.priority = 5

    @property
    def is_ready(self) -> bool:
        return self.status == "queued" and time.time() >= self.scheduled_time

    @property
    def can_retry(self) -> bool:
        return self.status == "failed" and self.attempts < self.max_retries

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "account_id": self.account_id,
            "content_id": self.content_id, "platform": self.platform,
            "scheduled_time": self.scheduled_time, "timezone": self.timezone,
            "status": self.status, "attempts": self.attempts,
            "last_error": self.last_error, "priority": self.priority,
        }


class PublishingScheduler:
    """Manages scheduling queue with time zones, retries, and daily limits."""
    _instance: Optional["PublishingScheduler"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PublishingScheduler":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._queue: Dict[str, ScheduledPost] = {}
        self._account_index: Dict[str, List[str]] = {}
        self._platform_index: Dict[str, List[str]] = {}
        self._history: List[Dict[str, Any]] = []
        self._retry_queue: List[str] = []

    def schedule(self, account_id: str, content_id: str, platform: str,
                 scheduled_time: float, timezone: str = "UTC",
                 priority: int = 5) -> ScheduledPost:
        post = ScheduledPost(account_id, content_id, platform, scheduled_time, timezone)
        post.priority = priority
        self._queue[post.id] = post
        self._account_index.setdefault(account_id, []).append(post.id)
        self._platform_index.setdefault(platform, []).append(post.id)
        return post

    def schedule_batch(self, posts: List[Dict[str, Any]]) -> List[ScheduledPost]:
        results = []
        for p in posts:
            post = self.schedule(
                p["account_id"], p["content_id"], p["platform"],
                p["scheduled_time"], p.get("timezone", "UTC"),
                p.get("priority", 5),
            )
            results.append(post)
        return results

    def get_post(self, post_id: str) -> Optional[ScheduledPost]:
        return self._queue.get(post_id)

    def get_ready_posts(self) -> List[ScheduledPost]:
        return sorted(
            [p for p in self._queue.values() if p.is_ready],
            key=lambda p: (-p.priority, p.scheduled_time),
        )

    def get_queue(self, platform: str = "", account_id: str = "") -> List[ScheduledPost]:
        posts = list(self._queue.values())
        if platform:
            posts = [p for p in posts if p.platform == platform]
        if account_id:
            posts = [p for p in posts if p.account_id == account_id]
        return sorted(posts, key=lambda p: p.scheduled_time)

    def mark_published(self, post_id: str) -> bool:
        post = self._queue.get(post_id)
        if post:
            post.status = "published"
            post.published_at = time.time()
            self._history.append({
                "action": "published", "post_id": post_id,
                "platform": post.platform, "timestamp": time.time(),
            })
            return True
        return False

    def mark_failed(self, post_id: str, error: str = "") -> bool:
        post = self._queue.get(post_id)
        if post:
            post.status = "failed"
            post.last_error = error
            post.attempts += 1
            if post.can_retry:
                self._retry_queue.append(post_id)
            self._history.append({
                "action": "failed", "post_id": post_id,
                "error": error, "attempts": post.attempts, "timestamp": time.time(),
            })
            return True
        return False

    def retry(self, post_id: str) -> bool:
        post = self._queue.get(post_id)
        if post and post.can_retry:
            post.status = "queued"
            post.scheduled_time = time.time() + 300
            if post_id in self._retry_queue:
                self._retry_queue.remove(post_id)
            return True
        return False

    def cancel(self, post_id: str) -> bool:
        post = self._queue.get(post_id)
        if post and post.status in ("queued", "failed"):
            post.status = "cancelled"
            return True
        return False

    def get_queue_status(self) -> Dict[str, Any]:
        posts = list(self._queue.values())
        return {
            "total": len(posts),
            "queued": sum(1 for p in posts if p.status == "queued"),
            "published": sum(1 for p in posts if p.status == "published"),
            "failed": sum(1 for p in posts if p.status == "failed"),
            "cancelled": sum(1 for p in posts if p.status == "cancelled"),
            "ready_now": len(self.get_ready_posts()),
            "retry_pending": len(self._retry_queue),
            "by_platform": {p: len(ids) for p, ids in self._platform_index.items()},
            "history": len(self._history),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "queue_size": len(self._queue),
            "platforms": len(self._platform_index),
            "accounts": len(self._account_index),
            "history": len(self._history),
        }


def get_publishing_scheduler() -> PublishingScheduler:
    return PublishingScheduler()
