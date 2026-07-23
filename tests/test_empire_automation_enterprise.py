"""Enterprise Empire Automation Engine Tests — Phase 10."""
import sys
import time
import unittest

sys.path.insert(0, ".")

from layers.layer07_publishing.modules.empire_engine.account_registry import (
    AccountRegistry, AccountEntry, get_account_registry,
)
from layers.layer07_publishing.modules.empire_engine.account_assignment_engine import (
    AccountAssignmentEngine, AssignmentRule, WorkloadInfo, get_assignment_engine,
)
from layers.layer07_publishing.modules.empire_engine.content_distribution_engine import (
    ContentDistributionEngine, ContentPiece, AdaptedContent, get_content_distribution,
)
from layers.layer07_publishing.modules.empire_engine.publishing_scheduler import (
    PublishingScheduler, ScheduledPost, get_publishing_scheduler,
)
from layers.layer07_publishing.modules.empire_engine.cross_platform_sync import (
    CrossPlatformSync, SyncRule, SyncEvent, get_cross_platform_sync,
)
from layers.layer07_publishing.modules.empire_engine.account_health_monitor import (
    AccountHealthMonitor, HealthMetric, get_account_health_monitor,
)
from layers.layer07_publishing.modules.empire_engine.scaling_engine import (
    ScalingEngine, ScalingTier, ScalingPlan, get_scaling_engine,
)
from layers.layer07_publishing.modules.empire_engine.empire_engine_manager import (
    EmpireEngineManager, get_empire_engine,
)


# ─── Account Registry ────────────────────────────────────────────
class TestAccountRegistry(unittest.TestCase):
    def setUp(self):
        AccountRegistry._instance = None
        self.reg = get_account_registry()

    def tearDown(self):
        AccountRegistry._instance = None

    def test_singleton(self):
        self.assertIs(self.reg, get_account_registry())

    def test_register(self):
        acc = self.reg.register("facebook", "testuser", niche="tech")
        self.assertIsNotNone(acc.id)
        self.assertEqual(acc.platform, "facebook")

    def test_get_by_platform(self):
        self.reg.register("facebook", "f1")
        self.reg.register("facebook", "f2")
        self.reg.register("instagram", "i1")
        fb = self.reg.get_by_platform("facebook")
        self.assertEqual(len(fb), 2)

    def test_get_by_niche(self):
        self.reg.register("facebook", "f1", niche="tech")
        self.reg.register("instagram", "i1", niche="tech")
        self.reg.register("x", "x1", niche="health")
        tech = self.reg.get_by_niche("tech")
        self.assertEqual(len(tech), 2)

    def test_update_status(self):
        acc = self.reg.register("facebook", "f1")
        self.assertTrue(self.reg.update_status(acc.id, "paused"))
        self.assertEqual(acc.status, "paused")

    def test_record_post(self):
        acc = self.reg.register("facebook", "f1", daily_limit=3)
        self.assertTrue(self.reg.record_post(acc.id))
        self.assertEqual(acc.posts_today, 1)
        self.assertEqual(acc.total_posts, 1)

    def test_daily_limit(self):
        acc = self.reg.register("facebook", "f1", daily_limit=2)
        self.assertTrue(self.reg.record_post(acc.id))
        self.assertTrue(self.reg.record_post(acc.id))
        self.assertFalse(self.reg.record_post(acc.id))

    def test_reset_daily(self):
        acc = self.reg.register("facebook", "f1", daily_limit=5)
        self.reg.record_post(acc.id)
        count = self.reg.reset_daily_counts()
        self.assertEqual(count, 1)
        self.assertEqual(acc.posts_today, 0)

    def test_registry_status(self):
        self.reg.register("facebook", "f1")
        self.reg.register("instagram", "i1", niche="tech")
        status = self.reg.get_registry_status()
        self.assertEqual(status["total_accounts"], 2)

    def test_get_by_region(self):
        self.reg.register("facebook", "f1", region="us")
        self.reg.register("facebook", "f2", region="uk")
        us = self.reg.get_by_region("us")
        self.assertEqual(len(us), 1)

    def test_get_by_language(self):
        self.reg.register("facebook", "f1", language="ur")
        self.reg.register("facebook", "f2", language="en")
        ur = self.reg.get_by_language("ur")
        self.assertEqual(len(ur), 1)


class TestAccountEntry(unittest.TestCase):
    def test_can_post(self):
        acc = AccountEntry("facebook", "test")
        acc.daily_post_limit = 5
        self.assertTrue(acc.can_post)

    def test_cannot_post_when_paused(self):
        acc = AccountEntry("facebook", "test")
        acc.status = "paused"
        acc.daily_post_limit = 5
        self.assertFalse(acc.can_post)

    def test_to_dict(self):
        acc = AccountEntry("facebook", "test", niche="tech")
        d = acc.to_dict()
        self.assertEqual(d["platform"], "facebook")


# ─── Account Assignment ──────────────────────────────────────────
class TestAccountAssignmentEngine(unittest.TestCase):
    def setUp(self):
        AccountRegistry._instance = None
        AccountAssignmentEngine._instance = None
        self.ae = get_assignment_engine()
        self.reg = get_account_registry()

    def tearDown(self):
        AccountRegistry._instance = None
        AccountAssignmentEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.ae, get_assignment_engine())

    def test_add_rule(self):
        rule = self.ae.add_rule("tech", platforms=["facebook", "instagram"])
        self.assertIsNotNone(rule.id)

    def test_assign_niche(self):
        acc = self.reg.register("facebook", "f1")
        self.assertTrue(self.ae.assign_niche(acc.id, "tech"))
        self.assertEqual(acc.niche, "tech")

    def test_auto_assign(self):
        for i in range(5):
            self.reg.register("facebook", f"f{i}")
        assigned = self.ae.auto_assign("crypto", limit=3)
        self.assertEqual(len(assigned), 3)

    def test_workload(self):
        acc = self.reg.register("facebook", "f1", daily_limit=5)
        self.reg.record_post(acc.id)
        workload = self.ae.get_workload()
        self.assertEqual(len(workload), 1)
        self.assertEqual(workload[0].posts_today, 1)

    def test_least_loaded(self):
        a1 = self.reg.register("facebook", "f1", daily_limit=5)
        a2 = self.reg.register("facebook", "f2", daily_limit=5)
        self.reg.record_post(a1.id)
        self.reg.record_post(a1.id)
        least = self.ae.get_least_loaded(platform="facebook", limit=1)
        self.assertEqual(least[0].account_id, a2.id)

    def test_workload_summary(self):
        self.reg.register("facebook", "f1", daily_limit=5)
        self.reg.register("instagram", "i1", daily_limit=3)
        summary = self.ae.get_workload_summary()
        self.assertEqual(summary["total_accounts"], 2)

    def test_assignment_status(self):
        status = self.ae.get_assignment_status()
        self.assertIn("rules", status)
        self.assertIn("workload", status)


# ─── Content Distribution ────────────────────────────────────────
class TestContentDistributionEngine(unittest.TestCase):
    def setUp(self):
        ContentDistributionEngine._instance = None
        self.cde = get_content_distribution()

    def tearDown(self):
        ContentDistributionEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.cde, get_content_distribution())

    def test_create_content(self):
        piece = self.cde.create_content("Title", "Content body", niche="tech")
        self.assertIsNotNone(piece.id)

    def test_adapt_for_platform(self):
        piece = self.cde.create_content("Title", "Content body")
        adapted = self.cde.adapt_for_platform(piece.id, "x")
        self.assertIsNotNone(adapted)
        self.assertEqual(adapted.platform, "x")
        self.assertEqual(adapted.format, "tweet")

    def test_adapt_instagram(self):
        piece = self.cde.create_content("Title", "Content body")
        adapted = self.cde.adapt_for_platform(piece.id, "instagram")
        self.assertTrue(adapted.image_required)

    def test_distribute(self):
        piece = self.cde.create_content("Title", "Content body", niche="tech", tags=["ai"])
        results = self.cde.distribute(piece.id, ["facebook", "x", "instagram"])
        self.assertEqual(len(results), 3)

    def test_adapt_wordpress(self):
        piece = self.cde.create_content("Blog Post", "Long content here")
        adapted = self.cde.adapt_for_platform(piece.id, "wordpress")
        self.assertEqual(adapted.format, "blog_post")

    def test_hashtags(self):
        piece = self.cde.create_content("Title", "Content", niche="crypto", tags=["bitcoin"])
        adapted = self.cde.adapt_for_platform(piece.id, "instagram")
        self.assertGreater(len(adapted.hashtags), 0)

    def test_distribution_status(self):
        piece = self.cde.create_content("Title", "Content")
        self.cde.distribute(piece.id, ["facebook", "x"])
        status = self.cde.get_distribution_status()
        self.assertEqual(status["total_content"], 1)

    def test_get_adapted(self):
        piece = self.cde.create_content("Title", "Content")
        self.cde.distribute(piece.id, ["facebook", "x"])
        adapted = self.cde.get_adapted(piece.id)
        self.assertEqual(len(adapted), 2)


# ─── Publishing Scheduler ────────────────────────────────────────
class TestPublishingScheduler(unittest.TestCase):
    def setUp(self):
        PublishingScheduler._instance = None
        self.ps = get_publishing_scheduler()

    def tearDown(self):
        PublishingScheduler._instance = None

    def test_singleton(self):
        self.assertIs(self.ps, get_publishing_scheduler())

    def test_schedule(self):
        post = self.ps.schedule("acc1", "content1", "facebook", time.time())
        self.assertIsNotNone(post.id)
        self.assertEqual(post.status, "queued")

    def test_get_ready(self):
        post = self.ps.schedule("acc1", "c1", "fb", time.time() - 1)
        ready = self.ps.get_ready_posts()
        self.assertEqual(len(ready), 1)

    def test_mark_published(self):
        post = self.ps.schedule("acc1", "c1", "fb", time.time())
        self.assertTrue(self.ps.mark_published(post.id))
        self.assertEqual(post.status, "published")

    def test_mark_failed(self):
        post = self.ps.schedule("acc1", "c1", "fb", time.time())
        self.assertTrue(self.ps.mark_failed(post.id, "error"))
        self.assertEqual(post.attempts, 1)

    def test_retry(self):
        post = self.ps.schedule("acc1", "c1", "fb", time.time())
        self.ps.mark_failed(post.id, "error")
        self.assertTrue(self.ps.retry(post.id))
        self.assertEqual(post.status, "queued")

    def test_cancel(self):
        post = self.ps.schedule("acc1", "c1", "fb", time.time())
        self.assertTrue(self.ps.cancel(post.id))
        self.assertEqual(post.status, "cancelled")

    def test_batch_schedule(self):
        posts = self.ps.schedule_batch([
            {"account_id": "a1", "content_id": "c1", "platform": "fb", "scheduled_time": time.time()},
            {"account_id": "a2", "content_id": "c2", "platform": "x", "scheduled_time": time.time()},
        ])
        self.assertEqual(len(posts), 2)

    def test_queue_status(self):
        self.ps.schedule("a1", "c1", "fb", time.time())
        status = self.ps.get_queue_status()
        self.assertEqual(status["total"], 1)

    def test_get_queue_by_platform(self):
        self.ps.schedule("a1", "c1", "fb", time.time())
        self.ps.schedule("a2", "c2", "x", time.time())
        fb_queue = self.ps.get_queue(platform="fb")
        self.assertEqual(len(fb_queue), 1)


class TestScheduledPost(unittest.TestCase):
    def test_is_ready(self):
        post = ScheduledPost("a1", "c1", "fb", time.time() - 10)
        self.assertTrue(post.is_ready)

    def test_can_retry(self):
        post = ScheduledPost("a1", "c1", "fb", time.time())
        post.status = "failed"
        post.attempts = 1
        self.assertTrue(post.can_retry)

    def test_to_dict(self):
        post = ScheduledPost("a1", "c1", "fb", time.time())
        d = post.to_dict()
        self.assertIn("id", d)


# ─── Cross-Platform Sync ─────────────────────────────────────────
class TestCrossPlatformSync(unittest.TestCase):
    def setUp(self):
        CrossPlatformSync._instance = None
        self.sync = get_cross_platform_sync()

    def tearDown(self):
        CrossPlatformSync._instance = None

    def test_singleton(self):
        self.assertIs(self.sync, get_cross_platform_sync())

    def test_default_rules(self):
        rules = self.sync.get_rules()
        self.assertGreater(len(rules), 0)

    def test_add_rule(self):
        rule = self.sync.add_rule("tiktok", "instagram")
        self.assertIsNotNone(rule.id)

    def test_get_rules_by_source(self):
        rules = self.sync.get_rules("blog")
        self.assertGreater(len(rules), 0)

    def test_trigger_sync(self):
        events = self.sync.trigger_sync("blog", "post_001")
        self.assertGreater(len(events), 0)

    def test_complete_sync(self):
        events = self.sync.trigger_sync("youtube", "yt_001")
        self.assertTrue(self.sync.complete_sync(events[0].id))

    def test_pending_syncs(self):
        self.sync.trigger_sync("blog", "post_001")
        pending = self.sync.get_pending_syncs()
        self.assertGreater(len(pending), 0)

    def test_sync_status(self):
        status = self.sync.get_sync_status()
        self.assertIn("total_rules", status)
        self.assertIn("active_rules", status)

    def test_sync_history(self):
        self.sync.trigger_sync("blog", "post1")
        history = self.sync.get_sync_history("post1")
        self.assertGreater(len(history), 0)


# ─── Account Health Monitor ──────────────────────────────────────
class TestAccountHealthMonitor(unittest.TestCase):
    def setUp(self):
        AccountHealthMonitor._instance = None
        self.hm = get_account_health_monitor()

    def tearDown(self):
        AccountHealthMonitor._instance = None

    def test_singleton(self):
        self.assertIs(self.hm, get_account_health_monitor())

    def test_check_healthy(self):
        m = self.hm.check_account("a1", "facebook", posting_frequency=2.0,
                                    avg_engagement=5.0, follower_growth=2.0)
        self.assertEqual(m.health_score, 100.0)
        self.assertEqual(m.status, "healthy")

    def test_check_unhealthy(self):
        m = self.hm.check_account("a1", "facebook", posting_frequency=0.01,
                                    avg_engagement=0.1, error_count=15,
                                    warning_count=5)
        self.assertLess(m.health_score, 50)
        self.assertEqual(m.status, "unhealthy")

    def test_shadow_ban_detection(self):
        m = self.hm.check_account("a1", "facebook", posting_frequency=2.0, avg_engagement=0.05,
                                    follower_growth=-15, error_count=12)
        self.assertGreaterEqual(m.shadow_ban_score, 50)

    def test_issues_detected(self):
        m = self.hm.check_account("a1", "facebook", posting_frequency=0.01,
                                    avg_engagement=0.1, error_count=10)
        self.assertGreater(len(m.issues), 0)

    def test_health_summary(self):
        self.hm.check_account("a1", "fb", avg_engagement=5.0)
        self.hm.check_account("a2", "x", avg_engagement=0.1, error_count=10)
        summary = self.hm.get_health_summary()
        self.assertIn("healthy", summary)
        self.assertIn("unhealthy", summary)

    def test_get_unhealthy(self):
        self.hm.check_account("a1", "fb", avg_engagement=5.0)
        self.hm.check_account("a2", "x", avg_engagement=0.01, error_count=10)
        unhealthy = self.hm.get_unhealthy_accounts()
        self.assertEqual(len(unhealthy), 1)

    def test_shadow_ban_suspects(self):
        self.hm.check_account("a1", "fb", posting_frequency=2.0, avg_engagement=0.05, follower_growth=-15, error_count=15)
        suspects = self.hm.get_shadow_ban_suspects()
        self.assertGreaterEqual(len(suspects), 1)


class TestHealthMetric(unittest.TestCase):
    def test_status_healthy(self):
        m = HealthMetric("a1")
        m.health_score = 85
        self.assertEqual(m.status, "healthy")

    def test_status_degraded(self):
        m = HealthMetric("a1")
        m.health_score = 60
        self.assertEqual(m.status, "degraded")

    def test_to_dict(self):
        m = HealthMetric("a1", "facebook")
        d = m.to_dict()
        self.assertIn("health_score", d)


# ─── Scaling Engine ──────────────────────────────────────────────
class TestScalingEngine(unittest.TestCase):
    def setUp(self):
        ScalingEngine._instance = None
        self.se = get_scaling_engine()

    def tearDown(self):
        ScalingEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.se, get_scaling_engine())

    def test_tiers_loaded(self):
        self.assertEqual(len(self.se.TIERS), 5)

    def test_get_tier_starter(self):
        tier = self.se.get_tier(50)
        self.assertEqual(tier.name, "starter")

    def test_get_tier_growth(self):
        tier = self.se.get_tier(200)
        self.assertEqual(tier.name, "growth")

    def test_get_tier_enterprise(self):
        tier = self.se.get_tier(5000)
        self.assertEqual(tier.name, "enterprise")

    def test_get_tier_empire(self):
        tier = self.se.get_tier(15000)
        self.assertEqual(tier.name, "empire")

    def test_set_account_count(self):
        self.se.set_account_count(250)
        self.assertEqual(self.se._current_accounts, 250)

    def test_create_scaling_plan(self):
        self.se.set_account_count(80)
        plan = self.se.create_scaling_plan(600)
        self.assertEqual(plan.current_tier, "starter")
        self.assertGreater(len(plan.steps), 0)

    def test_scaling_status(self):
        self.se.set_account_count(150)
        status = self.se.get_scaling_status()
        self.assertEqual(status["current_accounts"], 150)
        self.assertIn("current_tier", status)
        self.assertIn("all_tiers", status)

    def test_recommendations(self):
        self.se.set_account_count(90)
        recs = self.se.get_recommendations()
        self.assertGreater(len(recs), 0)

    def test_scaling_history(self):
        self.se.set_account_count(50)
        self.se.set_account_count(150)
        status = self.se.get_scaling_status()
        self.assertEqual(status["scaling_events"], 1)

    def test_tier_to_dict(self):
        tier = ScalingTier("test", 0, 100)
        d = tier.to_dict()
        self.assertEqual(d["name"], "test")


# ─── Empire Engine Manager ───────────────────────────────────────
class TestEmpireEngineManager(unittest.TestCase):
    def setUp(self):
        for cls in [AccountRegistry, AccountAssignmentEngine, ContentDistributionEngine,
                     PublishingScheduler, CrossPlatformSync, AccountHealthMonitor,
                     ScalingEngine, EmpireEngineManager]:
            cls._instance = None
        self.emp = get_empire_engine()

    def tearDown(self):
        for cls in [AccountRegistry, AccountAssignmentEngine, ContentDistributionEngine,
                     PublishingScheduler, CrossPlatformSync, AccountHealthMonitor,
                     ScalingEngine, EmpireEngineManager]:
            cls._instance = None

    def test_singleton(self):
        self.assertIs(self.emp, get_empire_engine())

    def test_submodules(self):
        self.assertIsNotNone(self.emp.registry)
        self.assertIsNotNone(self.emp.assignment)
        self.assertIsNotNone(self.emp.distribution)
        self.assertIsNotNone(self.emp.scheduler)
        self.assertIsNotNone(self.emp.sync)
        self.assertIsNotNone(self.emp.health)
        self.assertIsNotNone(self.emp.scaling)

    def test_register_batch(self):
        accounts = [
            {"platform": "facebook", "username": "f1", "niche": "tech"},
            {"platform": "instagram", "username": "i1", "niche": "tech"},
            {"platform": "x", "username": "x1", "niche": "health"},
        ]
        count = self.emp.register_accounts_batch(accounts)
        self.assertEqual(count, 3)

    def test_publish_content(self):
        accounts = [
            {"platform": "facebook", "username": "f1", "niche": "tech"},
            {"platform": "x", "username": "x1", "niche": "tech"},
        ]
        self.emp.register_accounts_batch(accounts)
        result = self.emp.publish_content(
            "Best Tech Tools", "Here are the best tools...",
            niche="tech", platforms=["facebook", "x"],
        )
        self.assertIn("content_id", result)
        self.assertGreater(result["adapted_count"], 0)

    def test_empire_status(self):
        status = self.emp.get_empire_status()
        self.assertEqual(status["overall"], "Active")
        self.assertIn("registry", status)
        self.assertIn("scheduler", status)
        self.assertIn("scaling", status)

    def test_executive_summary(self):
        summary = self.emp.get_executive_summary()
        self.assertIn("total_accounts", summary)
        self.assertIn("current_tier", summary)

    def test_stats(self):
        s = self.emp.stats()
        self.assertIn("registry", s)
        self.assertIn("scheduler", s)
        self.assertIn("scaling", s)


# ─── Full Enterprise Stack ───────────────────────────────────────
class TestFullEnterpriseStack(unittest.TestCase):
    """End-to-end: All 7 empire modules working together."""
    def setUp(self):
        for cls in [AccountRegistry, AccountAssignmentEngine, ContentDistributionEngine,
                     PublishingScheduler, CrossPlatformSync, AccountHealthMonitor,
                     ScalingEngine, EmpireEngineManager]:
            cls._instance = None
        self.emp = get_empire_engine()

    def tearDown(self):
        for cls in [AccountRegistry, AccountAssignmentEngine, ContentDistributionEngine,
                     PublishingScheduler, CrossPlatformSync, AccountHealthMonitor,
                     ScalingEngine, EmpireEngineManager]:
            cls._instance = None

    def test_full_empire_flow(self):
        # 1. Register 60 accounts across platforms
        accounts = []
        platforms = ["facebook", "instagram", "x", "youtube", "pinterest", "tiktok"]
        niches = ["tech", "health", "finance", "crypto", "gaming"]
        for i in range(60):
            accounts.append({
                "platform": platforms[i % len(platforms)],
                "username": f"user_{i:03d}",
                "niche": niches[i % len(niches)],
                "language": "en",
                "region": "us" if i % 3 == 0 else "uk",
            })
        count = self.emp.register_accounts_batch(accounts)
        self.assertEqual(count, 60)

        # 2. Verify registry
        reg_status = self.emp.registry.get_registry_status()
        self.assertEqual(reg_status["total_accounts"], 60)
        self.assertGreater(reg_status["platforms_count"], 0)

        # 3. Assign niches
        for niche in niches:
            self.emp.assignment.auto_assign(niche, limit=12)

        # 4. Create and distribute content
        result = self.emp.publish_content(
            "Top 10 AI Tools in 2024",
            "Artificial intelligence is transforming every industry...",
            niche="tech",
            platforms=["facebook", "instagram", "x", "linkedin"],
        )
        self.assertIn("content_id", result)

        # 5. Check workload
        workload = self.emp.assignment.get_workload_summary()
        self.assertGreater(workload["total_accounts"], 0)

        # 6. Health checks
        for acc in self.emp.registry.get_active_accounts()[:10]:
            self.emp.health.check_account(
                acc.id, acc.platform, posting_frequency=1.5,
                avg_engagement=3.0, follower_growth=1.0,
            )
        health_summary = self.emp.health.get_health_summary()
        self.assertGreater(health_summary["total_checked"], 0)

        # 7. Cross-platform sync
        sync_status = self.emp.sync.get_sync_status()
        self.assertGreater(sync_status["active_rules"], 0)

        # 8. Scaling
        scaling_status = self.emp.scaling.get_scaling_status()
        self.assertEqual(scaling_status["current_accounts"], 60)
        self.assertEqual(scaling_status["current_tier"]["name"], "starter")

        # 9. Verify full status
        status = self.emp.get_empire_status()
        self.assertEqual(status["overall"], "Active")

        # 10. Executive summary
        summary = self.emp.get_executive_summary()
        self.assertEqual(summary["total_accounts"], 60)


if __name__ == "__main__":
    unittest.main()
