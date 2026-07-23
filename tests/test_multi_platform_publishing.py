"""Tests for Multi-Platform Publishing Engine.

Covers:
- AccountManager (create, get, update, delete, list, health)
- PlatformAdapter (adapt to all platforms, validation, hashtags)
- PublisherEngine (publish, retry, circuit breaker, multi)
- ContentScheduler (schedule, cancel, process, optimal time)
- AnalyticsCollector (record, update, dashboard, time series)
- PublishingManager (integration, adapt_and_publish, status)
"""
from __future__ import annotations
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── AccountManager Tests ────────────────────────────────────────

class TestAccountManager:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.account_manager import AccountManager
        self.manager = AccountManager(max_accounts=1000)

    def test_create_account(self):
        account = self.manager.create_account("facebook", "user1", "User One")
        assert account.platform == "facebook"
        assert account.username == "user1"
        assert account.is_active is True

    def test_get_account(self):
        account = self.manager.create_account("instagram", "user2", "User Two")
        fetched = self.manager.get_account(account.account_id)
        assert fetched.username == "user2"

    def test_update_account(self):
        account = self.manager.create_account("x", "user3", "User Three")
        self.manager.update_account(account.account_id, display_name="Updated Name")
        updated = self.manager.get_account(account.account_id)
        assert updated.display_name == "Updated Name"

    def test_delete_account(self):
        account = self.manager.create_account("tiktok", "user4", "User Four")
        assert self.manager.delete_account(account.account_id) is True
        assert self.manager.get_account(account.account_id) is None

    def test_list_accounts(self):
        self.manager.create_account("facebook", "f1", "F1")
        self.manager.create_account("facebook", "f2", "F2")
        self.manager.create_account("instagram", "i1", "I1")
        fb_accounts = self.manager.list_accounts(platform="facebook")
        assert len(fb_accounts) == 2

    def test_list_by_brand(self):
        self.manager.create_account("facebook", "f1", "F1", brand="brand_a")
        self.manager.create_account("instagram", "i1", "I1", brand="brand_a")
        self.manager.create_account("x", "x1", "X1", brand="brand_b")
        brand_a = self.manager.list_accounts(brand="brand_a")
        assert len(brand_a) == 2

    def test_get_by_username(self):
        self.manager.create_account("facebook", "unique_user", "Unique")
        found = self.manager.get_account_by_username("facebook", "unique_user")
        assert found is not None

    def test_record_post(self):
        account = self.manager.create_account("facebook", "poster", "Poster")
        self.manager.record_post(account.account_id)
        updated = self.manager.get_account(account.account_id)
        assert updated.total_posts == 1

    def test_get_available_accounts(self):
        self.manager.create_account("facebook", "active", "Active")
        available = self.manager.get_available_accounts("facebook")
        assert len(available) == 1

    def test_count(self):
        self.manager.create_account("facebook", "f1", "F1")
        self.manager.create_account("instagram", "i1", "I1")
        assert self.manager.count() == 2
        assert self.manager.count(platform="facebook") == 1

    def test_max_accounts_limit(self):
        manager = __import__('layers.layer07_publishing.modules.multi_platform_engine.account_manager', fromlist=['AccountManager']).AccountManager(max_accounts=2)
        manager.create_account("fb", "u1", "U1")
        manager.create_account("fb", "u2", "U2")
        with pytest.raises(ValueError):
            manager.create_account("fb", "u3", "U3")

    def test_stats(self):
        self.manager.create_account("facebook", "f1", "F1", brand="brand_a")
        self.manager.create_account("instagram", "i1", "I1", brand="brand_a")
        stats = self.manager.stats()
        assert stats["total_accounts"] == 2
        assert "facebook" in stats["platforms"]
        assert "brand_a" in stats["brands"]


# ─── PlatformAdapter Tests ───────────────────────────────────────

class TestPlatformAdapter:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.platform_adapter import PlatformAdapter
        self.adapter = PlatformAdapter()

    def test_adapt_facebook(self):
        result = self.adapter.adapt("This is great content about AI.", "generic", "facebook",
                                     {"title": "AI Update", "hashtags": ["ai", "tech"]})
        assert result["platform"] == "facebook"
        assert result["within_limit"] is True
        assert "ai" in result["hashtags"]

    def test_adapt_instagram(self):
        result = self.adapter.adapt("Amazing AI breakthrough!", "generic", "instagram",
                                     {"hashtags": ["ai", "future", "tech"]})
        assert result["platform"] == "instagram"
        assert len(result["hashtags"]) <= 15

    def test_adapt_twitter_thread(self):
        long_text = "Thread about AI. " * 50
        result = self.adapter.adapt(long_text, "generic", "x",
                                     {"title": "AI Thread", "hashtags": ["ai"]})
        assert result["platform"] == "x"
        assert result["metadata"]["is_thread"] is True

    def test_adapt_tiktok(self):
        result = self.adapter.adapt("Short catchy caption about AI!", "generic", "tiktok",
                                     {"hashtags": ["fyp", "ai", "viral"]})
        assert result["platform"] == "tiktok"

    def test_adapt_wordpress(self):
        result = self.adapter.adapt("Full article content here.", "generic", "wordpress",
                                     {"title": "My Blog Post"})
        assert "My Blog Post" in result["content"]

    def test_adapt_medium(self):
        result = self.adapter.adapt("Thoughtful article.", "generic", "medium",
                                     {"title": "Medium Post"})
        assert "# Medium Post" in result["content"]

    def test_adapt_linkedin(self):
        result = self.adapter.adapt("Professional update about industry trends.", "generic", "linkedin",
                                     {"hashtags": ["business", "growth"]})
        assert result["platform"] == "linkedin"

    def test_adapt_pinterest(self):
        result = self.adapter.adapt("Beautiful design inspiration.", "generic", "pinterest",
                                     {"hashtags": ["design", "inspo"]})
        assert result["platform"] == "pinterest"

    def test_adapt_to_all(self):
        platforms = ["facebook", "instagram", "x", "linkedin"]
        results = self.adapter.adapt_to_all("Great content!", platforms)
        assert len(results) == 4
        assert all(p in results for p in platforms)

    def test_validate(self):
        result = self.adapter.validate("x" * 300, "x")
        assert result["valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_pass(self):
        result = self.adapter.validate("Short post", "x")
        assert result["valid"] is True

    def test_get_optimal_hashtags(self):
        tags = self.adapter.get_optimal_hashtags("python programming", "instagram")
        assert len(tags) > 0

    def test_stats(self):
        stats = self.adapter.stats()
        assert stats["total_platforms"] >= 14


# ─── PublisherEngine Tests ───────────────────────────────────────

class TestPublisherEngine:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.account_manager import AccountManager
        from layers.layer07_publishing.modules.multi_platform_engine.platform_adapter import PlatformAdapter
        from layers.layer07_publishing.modules.multi_platform_engine.publisher_engine import PublisherEngine
        self.accounts = AccountManager()
        self.adapter = PlatformAdapter()
        self.engine = PublisherEngine(self.accounts, self.adapter)

        # Register mock handlers
        self.engine.register_handler("facebook", lambda aid, content, meta: {"success": True, "post_id": "fb_123"})
        self.engine.register_handler("instagram", lambda aid, content, meta: {"success": True, "post_id": "ig_456"})

    def test_publish(self):
        account = self.accounts.create_account("facebook", "user1", "User 1")
        result = self.engine.publish("facebook", account.account_id, "Hello world!")
        assert result["status"] == "published"
        assert result["post_id"] == "fb_123"

    def test_publish_no_handler(self):
        account = self.accounts.create_account("reddit", "user1", "User 1")
        result = self.engine.publish("reddit", account.account_id, "Hello")
        assert result["status"] == "failed"

    def test_publish_multi(self):
        account = self.accounts.create_account("facebook", "user1", "User 1")
        account2 = self.accounts.create_account("instagram", "user2", "User 2")
        items = [
            {"platform": "facebook", "account_id": account.account_id, "content": "Post 1"},
            {"platform": "instagram", "account_id": account2.account_id, "content": "Post 2"},
        ]
        results = self.engine.publish_multi(items)
        assert len(results) == 2
        assert all(r["status"] == "published" for r in results)

    def test_publish_to_all(self):
        self.accounts.create_account("facebook", "user1", "User 1")
        self.accounts.create_account("instagram", "user2", "User 2")
        results = self.engine.publish_to_all("Cross-post content", ["facebook", "instagram"])
        assert len(results) == 2

    def test_retry_on_failure(self):
        call_count = [0]
        def failing_handler(aid, content, meta):
            call_count[0] += 1
            if call_count[0] < 2:
                raise Exception("Temporary error")
            return {"success": True, "post_id": "retry_123"}

        self.engine.register_handler("twitter", failing_handler)
        account = self.accounts.create_account("twitter", "user1", "User 1")
        result = self.engine.publish("twitter", account.account_id, "Retry test")
        assert result["status"] == "published"
        assert result["retries"] >= 1

    def test_circuit_breaker(self):
        def always_fail(aid, content, meta):
            raise Exception("Always fails")

        self.engine.register_handler("broken", always_fail)
        account = self.accounts.create_account("broken", "user1", "User 1")

        # Trigger circuit breaker with no retries to avoid delays
        for _ in range(6):
            job = self.engine.publish("broken", account.account_id, "Fail")
            # Override max retries for speed
            job_id = job["job_id"]
            if job_id in self.engine._jobs:
                self.engine._jobs[job_id].max_retries = 0

        circuit = self.engine.get_circuit_status()
        assert circuit["broken"]["open"] is True

    def test_history(self):
        account = self.accounts.create_account("facebook", "user1", "User 1")
        self.engine.publish("facebook", account.account_id, "Test")
        history = self.engine.get_history()
        assert len(history) >= 1

    def test_stats(self):
        stats = self.engine.stats()
        assert "total_published" in stats
        assert "registered_handlers" in stats


# ─── ContentScheduler Tests ──────────────────────────────────────

class TestContentScheduler:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.publisher_engine import PublisherEngine
        from layers.layer07_publishing.modules.multi_platform_engine.content_scheduler import ContentScheduler
        self.publisher = PublisherEngine()
        self.publisher.register_handler("facebook", lambda aid, c, m: {"success": True, "post_id": "sch_123"})
        self.scheduler = ContentScheduler(self.publisher)

    def test_schedule(self):
        future = time.time() + 3600
        result = self.scheduler.schedule("facebook", "acc1", "Scheduled post", future)
        assert result["status"] == "scheduled"
        assert result["scheduled_time"] == future

    def test_cancel(self):
        result = self.scheduler.schedule("facebook", "acc1", "Cancel me", time.time() + 3600)
        assert self.scheduler.cancel(result["schedule_id"]) is True
        cancelled = self.scheduler.get_schedule(result["schedule_id"])
        assert cancelled["status"] == "cancelled"

    def test_process_queue(self):
        # Schedule for now
        result = self.scheduler.schedule("facebook", "acc1", "Ready to go", time.time() - 1)
        processed = self.scheduler.process_queue()
        assert len(processed) >= 1

    def test_optimal_time(self):
        result = self.scheduler.get_optimal_time("facebook")
        assert "optimal_hour" in result
        assert result["score"] > 0

    def test_list_schedules(self):
        self.scheduler.schedule("facebook", "acc1", "Post 1", time.time() + 3600)
        self.scheduler.schedule("instagram", "acc2", "Post 2", time.time() + 7200)
        fb = self.scheduler.list_schedules(platform="facebook")
        assert len(fb) == 1

    def test_stats(self):
        self.scheduler.schedule("facebook", "acc1", "Test", time.time() + 3600)
        stats = self.scheduler.stats()
        assert stats["total_scheduled"] == 1


# ─── AnalyticsCollector Tests ────────────────────────────────────

class TestAnalyticsCollector:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.analytics_collector import AnalyticsCollector
        self.collector = AnalyticsCollector()

    def test_record_post(self):
        self.collector.record_post("p1", "facebook", "acc1")
        analytics = self.collector.get_post_analytics("p1")
        assert analytics is not None
        assert analytics["platform"] == "facebook"

    def test_update_metrics(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.update_metrics("p1", views=1000, clicks=50, likes=200)
        analytics = self.collector.get_post_analytics("p1")
        assert analytics["views"] == 1000
        assert analytics["clicks"] == 50
        assert analytics["likes"] == 200

    def test_engagement_rate(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.update_metrics("p1", views=1000, likes=100, comments=50, shares=25)
        analytics = self.collector.get_post_analytics("p1")
        assert analytics["engagement_rate"] > 0

    def test_ctr(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.update_metrics("p1", impressions=10000, clicks=500)
        analytics = self.collector.get_post_analytics("p1")
        assert analytics["ctr"] == 0.05

    def test_platform_analytics(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.record_post("p2", "facebook", "acc1")
        self.collector.update_metrics("p1", views=500, likes=50)
        self.collector.update_metrics("p2", views=300, likes=30)
        platform = self.collector.get_platform_analytics("facebook")
        assert platform["posts"] == 2
        assert platform["total_views"] == 800

    def test_dashboard(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.update_metrics("p1", views=1000, clicks=50, likes=200)
        dashboard = self.collector.get_dashboard()
        assert dashboard["total_posts"] == 1
        assert dashboard["total_views"] == 1000

    def test_affiliate_tracking(self):
        self.collector.record_post("p1", "facebook", "acc1")
        self.collector.update_metrics("p1", affiliate_clicks=25, affiliate_revenue=12.50)
        analytics = self.collector.get_post_analytics("p1")
        assert analytics["affiliate_clicks"] == 25
        assert analytics["affiliate_revenue"] == 12.50

    def test_stats(self):
        self.collector.record_post("p1", "facebook", "acc1")
        stats = self.collector.stats()
        assert stats["total_posts_tracked"] == 1


# ─── PublishingManager Integration Tests ─────────────────────────

class TestPublishingManager:
    def setup_method(self):
        from layers.layer07_publishing.modules.multi_platform_engine.publishing_manager import PublishingManager
        self.pub = PublishingManager(max_accounts=1000)
        self.pub.initialize()

        # Register mock handlers
        self.pub.engine.register_handler("facebook", lambda a, c, m: {"success": True, "post_id": "fb_1"})
        self.pub.engine.register_handler("instagram", lambda a, c, m: {"success": True, "post_id": "ig_1"})
        self.pub.engine.register_handler("x", lambda a, c, m: {"success": True, "post_id": "x_1"})

    def test_initialize(self):
        assert self.pub._initialized is True

    def test_add_account(self):
        result = self.pub.add_account("facebook", "user1", "User 1")
        assert result["platform"] == "facebook"

    def test_get_accounts(self):
        self.pub.add_account("facebook", "f1", "F1")
        self.pub.add_account("instagram", "i1", "I1")
        accounts = self.pub.get_accounts()
        assert len(accounts) == 2

    def test_publish(self):
        account = self.pub.add_account("facebook", "poster", "Poster")
        result = self.pub.publish("facebook", account["account_id"], "Hello!")
        assert result["status"] == "published"

    def test_publish_to_all(self):
        self.pub.add_account("facebook", "f1", "F1")
        self.pub.add_account("instagram", "i1", "I1")
        results = self.pub.publish_to_all("Cross-post", ["facebook", "instagram"])
        assert len(results) == 2

    def test_adapt_and_publish(self):
        fb = self.pub.add_account("facebook", "f1", "F1")
        ig = self.pub.add_account("instagram", "i1", "I1")
        results = self.pub.adapt_and_publish(
            "Great article about AI trends.",
            "generic",
            ["facebook", "instagram"],
            {"facebook": fb["account_id"], "instagram": ig["account_id"]},
            {"hashtags": ["ai", "tech"], "title": "AI Trends"},
        )
        assert len(results) == 2
        assert all(r["status"] == "published" for r in results.values())

    def test_schedule_post(self):
        self.pub.add_account("facebook", "f1", "F1")
        account = self.pub.get_accounts(platform="facebook")[0]
        result = self.pub.schedule_post("facebook", account["account_id"], "Scheduled!",
                                        time.time() + 3600)
        assert result["status"] == "scheduled"

    def test_get_optimal_time(self):
        result = self.pub.get_optimal_time("facebook")
        assert "optimal_hour" in result

    def test_get_analytics(self):
        dashboard = self.pub.get_analytics()
        assert "total_posts" in dashboard

    def test_get_publishing_status(self):
        status = self.pub.get_publishing_status()
        assert status["overall"] == "Healthy"
        assert status["total_platforms"] >= 14
        assert "accounts" in status
        assert "engine" in status
        assert "scheduler" in status
        assert "analytics" in status

    def test_health_check(self):
        health = self.pub.health_check()
        assert health["overall"] == "healthy"

    def test_full_enterprise_stack(self):
        """Test all components working together."""
        # Add accounts for multiple platforms and brands
        fb = self.pub.add_account("facebook", "brand_a_fb", "Brand A FB", brand="brand_a")
        ig = self.pub.add_account("instagram", "brand_a_ig", "Brand A IG", brand="brand_a")
        x = self.pub.add_account("x", "brand_a_x", "Brand A X", brand="brand_a")
        wp = self.pub.add_account("wordpress", "brand_a_wp", "Brand A WP", brand="brand_a")
        li = self.pub.add_account("linkedin", "brand_a_li", "Brand A LI", brand="brand_a")

        # Adapt and publish across platforms
        results = self.pub.adapt_and_publish(
            "Excited to announce our new AI-powered content system! "
            "This革命性platform creates, adapts, and publishes content "
            "across 15+ platforms automatically.",
            "generic",
            ["facebook", "instagram", "x", "linkedin", "wordpress"],
            {
                "facebook": fb["account_id"],
                "instagram": ig["account_id"],
                "x": x["account_id"],
                "linkedin": li["account_id"],
                "wordpress": wp["account_id"],
            },
            {
                "title": "AI Content System Launch",
                "hashtags": ["ai", "content", "automation", "marketing", "tech"],
                "cta": "Try it now! Link in bio.",
            },
        )

        assert len(results) == 5
        published_count = sum(1 for r in results.values() if r["status"] == "published")
        assert published_count >= 3

        # Verify accounts
        accounts = self.pub.get_accounts()
        assert len(accounts) == 5

        # Verify brand grouping
        brand_a = self.pub.get_accounts(brand="brand_a")
        assert len(brand_a) == 5

        # Check status
        status = self.pub.get_publishing_status()
        assert status["accounts"]["total_accounts"] == 5
        assert status["engine"]["total_published"] >= 3
