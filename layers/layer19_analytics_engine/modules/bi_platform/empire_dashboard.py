"""EmpireDashboard — Account health, queue, alerts, growth metrics."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional


class EmpireSnapshot:
    __slots__ = ("total_accounts", "active_accounts", "healthy_accounts",
                 "shadow_ban_alerts", "banned_accounts", "queued_posts",
                 "published_today", "failed_posts", "scheduled_posts",
                 "total_followers", "follower_growth_today", "timestamp")

    def __init__(self) -> None:
        self.total_accounts = 0
        self.active_accounts = 0
        self.healthy_accounts = 0
        self.shadow_ban_alerts = 0
        self.banned_accounts = 0
        self.queued_posts = 0
        self.published_today = 0
        self.failed_posts = 0
        self.scheduled_posts = 0
        self.total_followers = 0
        self.follower_growth_today = 0
        self.timestamp = time.time()

    @property
    def health_rate(self) -> float:
        return (self.healthy_accounts / self.active_accounts * 100) if self.active_accounts > 0 else 0.0

    @property
    def success_rate(self) -> float:
        total = self.published_today + self.failed_posts
        return (self.published_today / total * 100) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_accounts": self.total_accounts,
            "active_accounts": self.active_accounts,
            "healthy_accounts": self.healthy_accounts,
            "health_rate": round(self.health_rate, 1),
            "shadow_ban_alerts": self.shadow_ban_alerts,
            "banned_accounts": self.banned_accounts,
            "queued_posts": self.queued_posts,
            "published_today": self.published_today,
            "failed_posts": self.failed_posts,
            "success_rate": round(self.success_rate, 1),
            "scheduled_posts": self.scheduled_posts,
            "total_followers": self.total_followers,
            "follower_growth": self.follower_growth_today,
        }


class EmpireDashboard:
    """Empire-wide monitoring: accounts, health, queue, growth."""
    _instance: Optional["EmpireDashboard"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmpireDashboard":
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
        self._current = EmpireSnapshot()
        self._history: List[Dict[str, Any]] = []

    def update(self, **kwargs) -> EmpireSnapshot:
        snap = EmpireSnapshot()
        for k, v in kwargs.items():
            if hasattr(snap, k):
                setattr(snap, k, v)
        self._current = snap
        self._history.append(snap.to_dict())
        return snap

    def get_current(self) -> EmpireSnapshot:
        return self._current

    def get_dashboard(self) -> Dict[str, Any]:
        return {
            "current": self._current.to_dict(),
            "history_size": len(self._history),
            "recent": self._history[-7:] if self._history else [],
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "snapshots": len(self._history),
        }


def get_empire_dashboard() -> EmpireDashboard:
    return EmpireDashboard()
