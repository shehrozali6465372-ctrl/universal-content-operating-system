"""EmpireEngineManager — Master integrator for all 7 empire automation modules."""
from __future__ import annotations
import threading
import time
from typing import Any, Dict, List, Optional

from .account_registry import AccountRegistry, get_account_registry
from .account_assignment_engine import AccountAssignmentEngine, get_assignment_engine
from .content_distribution_engine import ContentDistributionEngine, get_content_distribution
from .publishing_scheduler import PublishingScheduler, get_publishing_scheduler
from .cross_platform_sync import CrossPlatformSync, get_cross_platform_sync
from .account_health_monitor import AccountHealthMonitor, get_account_health_monitor
from .scaling_engine import ScalingEngine, get_scaling_engine


class EmpireEngineManager:
    """Master integrator for Empire Automation Engine."""
    _instance: Optional["EmpireEngineManager"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "EmpireEngineManager":
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
        self._registry = get_account_registry()
        self._assignment = get_assignment_engine()
        self._distribution = get_content_distribution()
        self._scheduler = get_publishing_scheduler()
        self._sync = get_cross_platform_sync()
        self._health = get_account_health_monitor()
        self._scaling = get_scaling_engine()
        self._initialized_at = time.time()

    @property
    def registry(self) -> AccountRegistry:
        return self._registry

    @property
    def assignment(self) -> AccountAssignmentEngine:
        return self._assignment

    @property
    def distribution(self) -> ContentDistributionEngine:
        return self._distribution

    @property
    def scheduler(self) -> PublishingScheduler:
        return self._scheduler

    @property
    def sync(self) -> CrossPlatformSync:
        return self._sync

    @property
    def health(self) -> AccountHealthMonitor:
        return self._health

    @property
    def scaling(self) -> ScalingEngine:
        return self._scaling

    def register_accounts_batch(self, accounts: List[Dict[str, Any]]) -> int:
        count = 0
        for acc in accounts:
            self._registry.register(
                platform=acc["platform"], username=acc["username"],
                niche=acc.get("niche", ""), language=acc.get("language", "en"),
                region=acc.get("region", "global"),
                account_type=acc.get("type", "personal"),
                daily_limit=acc.get("daily_limit", 5),
            )
            count += 1
        self._scaling.set_account_count(self._registry.stats()["accounts"])
        return count

    def publish_content(self, title: str, content: str, niche: str = "",
                        platforms: List[str] = None) -> Dict[str, Any]:
        piece = self._distribution.create_content(title, content, niche=niche)
        adapted = self._distribution.distribute(piece.id, platforms or [])
        scheduled = []
        for a in adapted:
            accounts = self._registry.get_by_platform(a.platform)
            postable = [acc for acc in accounts if acc.can_post and (not niche or acc.niche == niche)]
            if postable:
                acc = postable[0]
                post = self._scheduler.schedule(
                    acc.id, piece.id, a.platform, time.time()
                )
                scheduled.append(post.to_dict())
                self._registry.record_post(acc.id)
                sync_events = self._sync.trigger_sync(a.platform, piece.id)
        return {
            "content_id": piece.id,
            "adapted_count": len(adapted),
            "scheduled_count": len(scheduled),
            "scheduled": scheduled,
        }

    def get_empire_status(self) -> Dict[str, Any]:
        return {
            "overall": "Active",
            "uptime_seconds": round(time.time() - self._initialized_at, 2),
            "registry": self._registry.get_registry_status(),
            "assignment": self._assignment.get_assignment_status(),
            "distribution": self._distribution.get_distribution_status(),
            "scheduler": self._scheduler.get_queue_status(),
            "sync": self._sync.get_sync_status(),
            "health": self._health.get_health_summary(),
            "scaling": self._scaling.get_scaling_status(),
        }

    def get_executive_summary(self) -> Dict[str, Any]:
        reg = self._registry.get_registry_status()
        sched = self._scheduler.get_queue_status()
        health = self._health.get_health_summary()
        scaling = self._scaling.get_scaling_status()
        return {
            "total_accounts": reg["total_accounts"],
            "active_accounts": reg["active"],
            "platforms": reg["platforms_count"],
            "niches": reg["niches_count"],
            "regions": reg["regions_count"],
            "total_followers": reg["total_followers"],
            "queued_posts": sched["queued"],
            "published_today": sched["published"],
            "healthy_accounts": health.get("healthy", 0),
            "unhealthy_accounts": health.get("unhealthy", 0),
            "current_tier": scaling["current_tier"]["name"],
            "can_scale_to": scaling.get("next_tier", {}).get("accounts", "max") if scaling.get("next_tier") else "max",
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "registry": self._registry.stats(),
            "assignment": self._assignment.stats(),
            "distribution": self._distribution.stats(),
            "scheduler": self._scheduler.stats(),
            "sync": self._sync.stats(),
            "health": self._health.stats(),
            "scaling": self._scaling.stats(),
        }


def get_empire_engine() -> EmpireEngineManager:
    return EmpireEngineManager()
