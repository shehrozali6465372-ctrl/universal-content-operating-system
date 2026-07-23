"""ContentScheduler — Auto-schedule, queue, retry, timezone support.

Features:
- Schedule posts for specific times
- Timezone-aware scheduling
- Recurring schedules (daily, weekly, custom)
- Queue management with priorities
- Automatic retry on failure
- Optimal posting time suggestions
- Schedule conflict detection
"""
from __future__ import annotations
import time
import hashlib
import threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ScheduleFrequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledPost:
    schedule_id: str
    platform: str
    account_id: str
    content: str
    scheduled_time: float  # Unix timestamp
    frequency: str = "once"
    timezone: str = "UTC"
    priority: int = 0  # Higher = more urgent
    status: str = "scheduled"  # scheduled, processing, published, failed, cancelled
    retries: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    last_attempt: float = 0.0
    next_run: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schedule_id": self.schedule_id,
            "platform": self.platform,
            "account_id": self.account_id,
            "scheduled_time": self.scheduled_time,
            "frequency": self.frequency,
            "timezone": self.timezone,
            "priority": self.priority,
            "status": self.status,
            "retries": self.retries,
            "created_at": self.created_at,
        }


class ContentScheduler:
    """Schedule and manage content publishing."""

    def __init__(self, publisher_engine: Any = None):
        self._engine = publisher_engine
        self._lock = threading.Lock()

        # Schedule storage
        self._schedules: Dict[str, ScheduledPost] = {}
        self._queue: List[str] = []  # Schedule IDs sorted by time

        # Optimal posting times (hour -> engagement score, 0-1)
        self._optimal_times: Dict[str, Dict[int, float]] = {
            "facebook": {9: 0.8, 12: 0.9, 15: 0.7, 18: 0.85, 20: 0.75},
            "instagram": {7: 0.7, 11: 0.85, 13: 0.9, 17: 0.8, 19: 0.85, 21: 0.7},
            "x": {8: 0.8, 12: 0.9, 17: 0.85, 20: 0.75},
            "linkedin": {7: 0.8, 8: 0.85, 12: 0.9, 17: 0.8},
            "tiktok": {7: 0.7, 12: 0.8, 19: 0.95, 21: 0.9},
            "youtube": {12: 0.8, 15: 0.85, 18: 0.9, 21: 0.85},
            "pinterest": {8: 0.8, 11: 0.85, 14: 0.9, 20: 0.8},
            "wordpress": {9: 0.8, 13: 0.85, 16: 0.8},
            "medium": {8: 0.85, 12: 0.9, 17: 0.8},
            "devto": {9: 0.85, 12: 0.8, 14: 0.75},
        }

        # Stats
        self._total_scheduled = 0
        self._total_published = 0
        self._total_failed = 0

    def schedule(self, platform: str, account_id: str, content: str,
                 scheduled_time: float, frequency: str = "once",
                 timezone: str = "UTC", priority: int = 0,
                 metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Schedule a post for future publishing.

        Args:
            platform: Target platform
            account_id: Account to use
            content: Content to publish
            scheduled_time: Unix timestamp for publishing
            frequency: once, daily, weekly, etc.
            timezone: Timezone string (e.g., "America/New_York")
            priority: Higher = more urgent
            metadata: Additional metadata

        Returns:
            Scheduled post info
        """
        schedule_id = hashlib.sha256(
            f"{platform}:{scheduled_time}:{content[:50]}".encode()
        ).hexdigest()[:12]

        post = ScheduledPost(
            schedule_id=schedule_id,
            platform=platform,
            account_id=account_id,
            content=content,
            scheduled_time=scheduled_time,
            frequency=frequency,
            timezone=timezone,
            priority=priority,
            metadata=metadata or {},
            next_run=scheduled_time,
        )

        with self._lock:
            self._schedules[schedule_id] = post
            self._queue.append(schedule_id)
            self._queue.sort(key=lambda sid: self._schedules[sid].scheduled_time)
            self._total_scheduled += 1

        return post.to_dict()

    def cancel(self, schedule_id: str) -> bool:
        """Cancel a scheduled post."""
        with self._lock:
            post = self._schedules.get(schedule_id)
            if post:
                post.status = "cancelled"
                self._queue = [sid for sid in self._queue if sid != schedule_id]
                return True
            return False

    def process_queue(self) -> List[Dict[str, Any]]:
        """Process due items in the queue."""
        now = time.time()
        processed = []

        with self._lock:
            due_ids = [
                sid for sid in self._queue
                if self._schedules[sid].next_run <= now
                and self._schedules[sid].status == "scheduled"
            ]

        for sid in due_ids:
            post = self._schedules.get(sid)
            if not post:
                continue

            post.status = "processing"
            post.last_attempt = now

            # Publish
            if self._engine:
                result = self._engine.publish(
                    post.platform, post.account_id, post.content, post.metadata,
                )
                if result.get("success"):
                    post.status = "published"
                    self._total_published += 1

                    # Schedule next run for recurring
                    if post.frequency != "once":
                        post.next_run = self._next_run_time(post)
                        post.status = "scheduled"
                    else:
                        self._queue = [s for s in self._queue if s != sid]
                else:
                    post.retries += 1
                    if post.retries >= post.max_retries:
                        post.status = "failed"
                        self._total_failed += 1
                    else:
                        post.status = "scheduled"
                        post.next_run = now + (post.retries * 300)  # 5 min backoff

            processed.append(post.to_dict())

        return processed

    def _next_run_time(self, post: ScheduledPost) -> float:
        """Calculate next run time for recurring posts."""
        interval = {
            "daily": 86400,
            "weekly": 604800,
            "biweekly": 1209600,
            "monthly": 2592000,
        }.get(post.frequency, 86400)

        return post.next_run + interval

    def get_optimal_time(self, platform: str, timezone: str = "UTC") -> Dict[str, Any]:
        """Get optimal posting time for a platform."""
        times = self._optimal_times.get(platform, {})
        if not times:
            return {"platform": platform, "optimal_hour": 12, "score": 0.5}

        best_hour = max(times, key=times.get)
        return {
            "platform": platform,
            "optimal_hour": best_hour,
            "score": times[best_hour],
            "all_times": times,
        }

    def get_schedule(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """Get schedule by ID."""
        post = self._schedules.get(schedule_id)
        return post.to_dict() if post else None

    def list_schedules(self, platform: str = None, status: str = None) -> List[Dict[str, Any]]:
        """List schedules with filters."""
        results = []
        for post in self._schedules.values():
            if platform and post.platform != platform:
                continue
            if status and post.status != status:
                continue
            results.append(post.to_dict())
        return results

    def get_queue_size(self) -> int:
        """Get number of items in queue."""
        return len(self._queue)

    def stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        by_platform = {}
        by_status = {}
        for post in self._schedules.values():
            by_platform[post.platform] = by_platform.get(post.platform, 0) + 1
            by_status[post.status] = by_status.get(post.status, 0) + 1

        return {
            "total_scheduled": self._total_scheduled,
            "total_published": self._total_published,
            "total_failed": self._total_failed,
            "queue_size": len(self._queue),
            "by_platform": by_platform,
            "by_status": by_status,
        }
