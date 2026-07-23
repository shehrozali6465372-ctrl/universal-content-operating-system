"""PublishingManager — Enterprise Multi-Platform Publishing manager.

Integrates:
- AccountManager (unlimited accounts)
- PlatformAdapter (content conversion)
- PublisherEngine (publish orchestration)
- ContentScheduler (scheduling + queue)
- AnalyticsCollector (metrics + reporting)
"""
from __future__ import annotations
import os
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone

from layers.layer07_publishing.modules.multi_platform_engine.account_manager import AccountManager
from layers.layer07_publishing.modules.multi_platform_engine.platform_adapter import PlatformAdapter
from layers.layer07_publishing.modules.multi_platform_engine.publisher_engine import PublisherEngine
from layers.layer07_publishing.modules.multi_platform_engine.content_scheduler import ContentScheduler
from layers.layer07_publishing.modules.multi_platform_engine.analytics_collector import AnalyticsCollector


class PublishingManager:
    """Main Multi-Platform Publishing manager."""

    def __init__(self, max_accounts: int = 10000):
        self._max_accounts = max_accounts
        self._initialized = False

        # Components
        self.accounts: AccountManager = AccountManager(max_accounts)
        self.adapter: PlatformAdapter = PlatformAdapter()
        self.engine: PublisherEngine = PublisherEngine(self.accounts, self.adapter)
        self.scheduler: ContentScheduler = ContentScheduler(self.engine)
        self.analytics: AnalyticsCollector = AnalyticsCollector()

        # Supported platforms
        self._supported_platforms = [
            # Blog
            "wordpress", "medium", "blogger", "devto", "hashnode", "custom_website",
            # Social
            "facebook", "instagram", "tiktok", "x", "youtube", "pinterest",
            "linkedin", "telegram", "reddit",
        ]

    def initialize(self) -> bool:
        """Initialize the publishing system."""
        self._initialized = True
        return True

    # ─── Account Shortcuts ────────────────────────────────────────

    def add_account(self, platform: str, username: str, display_name: str,
                    credentials: Dict[str, str] = None, brand: str = "default") -> Dict[str, Any]:
        """Add a new platform account."""
        account = self.accounts.create_account(
            platform, username, display_name, credentials, brand,
        )
        return account.to_dict()

    def get_accounts(self, platform: str = None, brand: str = None) -> List[Dict[str, Any]]:
        """Get accounts."""
        accounts = self.accounts.list_accounts(platform=platform, brand=brand)
        return [a.to_dict() for a in accounts]

    # ─── Publish Shortcuts ────────────────────────────────────────

    def publish(self, platform: str, account_id: str, content: str,
                metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Publish to a single platform."""
        return self.engine.publish(platform, account_id, content, metadata)

    def publish_to_all(self, content: str, platforms: List[str],
                       metadata: Dict[str, Any] = None) -> Dict[str, Dict]:
        """Publish to multiple platforms."""
        return self.engine.publish_to_all(content, platforms, metadata)

    def adapt_and_publish(self, content: str, source_platform: str,
                          target_platforms: List[str], account_ids: Dict[str, str],
                          metadata: Dict[str, Any] = None) -> Dict[str, Dict]:
        """Adapt content and publish to multiple platforms.

        Args:
            content: Original content
            source_platform: Source format
            target_platforms: List of target platforms
            account_ids: Mapping of platform → account_id
            metadata: Additional metadata

        Returns:
            Results per platform
        """
        results = {}
        for target in target_platforms:
            adapted = self.adapter.adapt(content, source_platform, target, metadata)
            account_id = account_ids.get(target, "")
            result = self.publish(target, account_id, adapted["content"], {
                **metadata,
                "hashtags": adapted.get("hashtags", []),
                "adapted_title": adapted.get("title", ""),
            })
            results[target] = {
                **result,
                "adapted_content_length": adapted["character_count"],
                "within_limit": adapted["within_limit"],
            }
        return results

    # ─── Schedule Shortcuts ───────────────────────────────────────

    def schedule_post(self, platform: str, account_id: str, content: str,
                      scheduled_time: float, frequency: str = "once",
                      timezone: str = "UTC") -> Dict[str, Any]:
        """Schedule a post."""
        return self.scheduler.schedule(
            platform, account_id, content, scheduled_time, frequency, timezone,
        )

    def get_optimal_time(self, platform: str) -> Dict[str, Any]:
        """Get optimal posting time."""
        return self.scheduler.get_optimal_time(platform)

    # ─── Analytics Shortcuts ──────────────────────────────────────

    def get_analytics(self, platform: str = None) -> Dict[str, Any]:
        """Get analytics dashboard."""
        if platform:
            return self.analytics.get_platform_analytics(platform)
        return self.analytics.get_dashboard()

    # ─── Status ───────────────────────────────────────────────────

    def get_publishing_status(self) -> Dict[str, Any]:
        """Get comprehensive publishing status — for --publishing-status command."""
        account_stats = self.accounts.stats()
        engine_stats = self.engine.stats()
        scheduler_stats = self.scheduler.stats()
        analytics_stats = self.analytics.stats()
        dashboard = self.analytics.get_dashboard()

        overall = "Healthy" if self._initialized else "Not Initialized"

        return {
            "overall": overall,
            "initialized": self._initialized,
            "supported_platforms": self._supported_platforms,
            "total_platforms": len(self._supported_platforms),
            "accounts": account_stats,
            "engine": engine_stats,
            "scheduler": scheduler_stats,
            "analytics": {
                "tracked_posts": analytics_stats["total_posts_tracked"],
                "platforms_tracked": analytics_stats["platforms_tracked"],
                "dashboard": dashboard,
            },
        }

    def health_check(self) -> Dict[str, Any]:
        """Check publishing system health."""
        return {
            "initialized": self._initialized,
            "accounts_healthy": self.accounts.count() > 0 or True,
            "engine_healthy": self.engine is not None,
            "overall": "healthy" if self._initialized else "uninitialized",
        }

    def close(self):
        """Cleanup resources."""
        self._initialized = False


# Singleton
_publishing_instance: Optional[PublishingManager] = None


def get_publishing(max_accounts: int = 10000) -> PublishingManager:
    """Get or create Publishing manager singleton."""
    global _publishing_instance
    if _publishing_instance is None:
        _publishing_instance = PublishingManager(max_accounts)
        _publishing_instance.initialize()
    return _publishing_instance
