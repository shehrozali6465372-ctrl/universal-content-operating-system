"""Enterprise Affiliate & Monetization Engine Tests — Phase 8."""
import sys
import time
import unittest

sys.path.insert(0, ".")

from layers.layer10_monetization.modules.affiliate_engine.affiliate_manager import (
    AffiliateManager, AffiliateProgram, AffiliateLink, get_affiliate_manager,
)
from layers.layer10_monetization.modules.affiliate_engine.link_intelligence import (
    LinkIntelligence, TrackedLink, LinkVariant, get_link_intelligence,
)
from layers.layer10_monetization.modules.affiliate_engine.revenue_analytics import (
    RevenueAnalytics, PostRevenue, NicheRevenue, get_revenue_analytics,
)
from layers.layer10_monetization.modules.affiliate_engine.campaign_manager import (
    CampaignManager, Campaign, get_campaign_manager,
)
from layers.layer10_monetization.modules.affiliate_engine.ai_monetization_optimizer import (
    AIMonetizationOptimizer, NichePerformance, ContentScore,
    StrategyRecommendation, get_monetization_optimizer,
)
from layers.layer10_monetization.modules.affiliate_engine.affiliate_engine_manager import (
    AffiliateEngineManager, get_affiliate_engine,
)


# ─── Affiliate Manager ───────────────────────────────────────────
class TestAffiliateManager(unittest.TestCase):
    def setUp(self):
        AffiliateManager._instance = None
        self.mgr = get_affiliate_manager()

    def tearDown(self):
        AffiliateManager._instance = None

    def test_singleton(self):
        self.assertIs(self.mgr, get_affiliate_manager())

    def test_presets_loaded(self):
        programs = self.mgr.list_programs()
        self.assertGreaterEqual(len(programs), 6)

    def test_amazon_program(self):
        p = self.mgr.get_program("amazon")
        self.assertIsNotNone(p)
        self.assertEqual(p.platform, "amazon")
        self.assertEqual(p.commission_rate, 4.0)

    def test_binance_program(self):
        p = self.mgr.get_program("binance")
        self.assertIsNotNone(p)
        self.assertEqual(p.commission_rate, 20.0)

    def test_add_program(self):
        p = self.mgr.add_program("Custom", "custom", "https://custom.com",
                                   commission_rate=15.0)
        self.assertEqual(p.name, "Custom")
        self.assertEqual(p.commission_rate, 15.0)

    def test_add_link(self):
        link = self.mgr.add_link("amazon", "https://product.com",
                                  "https://amzn.to/xyz", niche="tech")
        self.assertIsNotNone(link.id)
        self.assertEqual(link.niche, "tech")

    def test_get_links_by_niche(self):
        self.mgr.add_link("amazon", "url1", "aff1", niche="tech")
        self.mgr.add_link("amazon", "url2", "aff2", niche="tech")
        self.mgr.add_link("amazon", "url3", "aff3", niche="health")
        tech_links = self.mgr.get_links_by_niche("tech")
        self.assertEqual(len(tech_links), 2)

    def test_record_click(self):
        link = self.mgr.add_link("amazon", "url", "aff", niche="tech")
        event = self.mgr.record_click(link.id, source="facebook")
        self.assertIsNotNone(event)
        self.assertEqual(link.clicks, 1)

    def test_record_conversion(self):
        link = self.mgr.add_link("amazon", "url", "aff", niche="tech")
        self.mgr.record_click(link.id)
        event = self.mgr.record_conversion(link.id, revenue=25.50)
        self.assertIsNotNone(event)
        self.assertEqual(link.revenue, 25.50)

    def test_revenue_summary(self):
        self.mgr.add_link("amazon", "url", "aff", niche="tech")
        summary = self.mgr.get_revenue_summary()
        self.assertIn("total_programs", summary)
        self.assertIn("total_revenue", summary)
        self.assertEqual(summary["total_programs"], 6)

    def test_click_increments_program(self):
        link = self.mgr.add_link("amazon", "url", "aff")
        self.mgr.record_click(link.id)
        p = self.mgr.get_program("amazon")
        self.assertEqual(p.total_clicks, 1)

    def test_conversion_increments_program(self):
        link = self.mgr.add_link("amazon", "url", "aff")
        self.mgr.record_conversion(link.id, revenue=10.0)
        p = self.mgr.get_program("amazon")
        self.assertEqual(p.total_conversions, 1)
        self.assertEqual(p.total_revenue, 10.0)

    def test_stats(self):
        s = self.mgr.stats()
        self.assertIn("programs", s)
        self.assertIn("links", s)


class TestAffiliateProgram(unittest.TestCase):
    def test_epc(self):
        p = AffiliateProgram("Test", "test")
        p.total_clicks = 100
        p.total_revenue = 50.0
        self.assertEqual(p.epc, 0.5)

    def test_conversion_rate(self):
        p = AffiliateProgram("Test", "test")
        p.total_clicks = 200
        p.total_conversions = 10
        self.assertEqual(p.conversion_rate, 5.0)

    def test_to_dict(self):
        p = AffiliateProgram("Test", "test", commission_rate=5.0)
        d = p.to_dict()
        self.assertEqual(d["name"], "Test")
        self.assertEqual(d["commission_rate"], 5.0)


# ─── Link Intelligence ───────────────────────────────────────────
class TestLinkIntelligence(unittest.TestCase):
    def setUp(self):
        LinkIntelligence._instance = None
        self.li = get_link_intelligence()

    def tearDown(self):
        LinkIntelligence._instance = None

    def test_singleton(self):
        self.assertIs(self.li, get_link_intelligence())

    def test_create_link(self):
        link = self.li.create_link("https://product.com", niche="tech")
        self.assertIsNotNone(link)
        self.assertEqual(link.niche, "tech")

    def test_get_link(self):
        link = self.li.create_link("https://product.com")
        found = self.li.get_link(link.id)
        self.assertIs(link, found)

    def test_resolve_link(self):
        link = self.li.create_link("https://product.com")
        url = self.li.resolve_link(link.short_slug)
        self.assertEqual(url, "https://product.com")
        self.assertEqual(link.total_clicks, 1)

    def test_resolve_nonexistent(self):
        url = self.li.resolve_link("nonexistent")
        self.assertIsNone(url)

    def test_add_variant(self):
        link = self.li.create_link("https://original.com")
        v = self.li.add_variant(link.id, "https://variant2.com", weight=5)
        self.assertIsNotNone(v)
        self.assertEqual(len(link.variants), 2)

    def test_ab_test_enabled(self):
        link = self.li.create_link("https://original.com")
        self.li.add_variant(link.id, "https://variant2.com")
        self.assertTrue(link.ab_test_enabled)

    def test_weighted_rotation(self):
        link = self.li.create_link("https://original.com", rotation="weighted")
        link.add_variant("https://v2.com", weight=100)
        results = set()
        for _ in range(50):
            v = link._weighted_choice(link.variants)
            results.add(v.url)
        self.assertIn("https://v2.com", results)

    def test_best_performer_rotation(self):
        link = self.li.create_link("https://original.com", rotation="best_performer")
        v1 = link.variants[0]
        v1.clicks = 100
        v1.conversions = 50
        v2 = link.add_variant("https://v2.com")
        v2.clicks = 100
        v2.conversions = 10
        best = link.get_best_variant()
        self.assertEqual(best.id, v1.id)

    def test_top_links(self):
        l1 = self.li.create_link("https://a.com", niche="tech")
        l2 = self.li.create_link("https://b.com", niche="tech")
        l1.total_revenue = 100
        l2.total_revenue = 50
        top = self.li.get_top_links("revenue", limit=1)
        self.assertEqual(top[0].id, l1.id)

    def test_links_by_niche(self):
        self.li.create_link("https://a.com", niche="crypto")
        self.li.create_link("https://b.com", niche="crypto")
        self.li.create_link("https://c.com", niche="health")
        crypto = self.li.get_links_by_niche("crypto")
        self.assertEqual(len(crypto), 2)

    def test_link_stats(self):
        self.li.create_link("https://a.com", niche="tech")
        stats = self.li.get_link_stats()
        self.assertEqual(stats["total_links"], 1)

    def test_get_by_slug(self):
        link = self.li.create_link("https://test.com")
        found = self.li.get_by_slug(link.short_slug)
        self.assertEqual(found.id, link.id)


# ─── Revenue Analytics ───────────────────────────────────────────
class TestRevenueAnalytics(unittest.TestCase):
    def setUp(self):
        RevenueAnalytics._instance = None
        self.ra = get_revenue_analytics()

    def tearDown(self):
        RevenueAnalytics._instance = None

    def test_singleton(self):
        self.assertIs(self.ra, get_revenue_analytics())

    def test_record_click(self):
        evt = self.ra.record_click("post1", niche="tech")
        self.assertEqual(evt.event_type, "click")

    def test_record_impression(self):
        evt = self.ra.record_impression("post1", niche="tech")
        self.assertEqual(evt.event_type, "impression")

    def test_record_conversion(self):
        evt = self.ra.record_conversion("post1", amount=99.99, commission=10.0)
        self.assertEqual(evt.event_type, "conversion")
        self.assertEqual(evt.amount, 99.99)

    def test_post_revenue_tracking(self):
        self.ra.record_click("post1", niche="tech")
        self.ra.record_click("post1", niche="tech")
        self.ra.record_conversion("post1", amount=50.0, niche="tech")
        post = self.ra.get_post_revenue("post1")
        self.assertIsNotNone(post)
        self.assertEqual(post.clicks, 2)
        self.assertEqual(post.conversions, 1)
        self.assertEqual(post.revenue, 50.0)

    def test_top_posts_by_revenue(self):
        self.ra.record_conversion("p1", amount=100)
        self.ra.record_conversion("p2", amount=50)
        top = self.ra.get_top_posts("revenue", limit=2)
        self.assertEqual(top[0].post_id, "p1")

    def test_niche_revenue(self):
        self.ra.record_click("p1", niche="tech")
        self.ra.record_conversion("p1", amount=30, niche="tech")
        self.ra.record_click("p2", niche="health")
        niches = self.ra.get_niche_revenue()
        self.assertEqual(len(niches), 2)

    def test_analytics_summary(self):
        self.ra.record_click("p1")
        self.ra.record_impression("p1")
        self.ra.record_conversion("p1", amount=25.0)
        s = self.ra.get_analytics_summary()
        self.assertEqual(s["total_clicks"], 1)
        self.assertEqual(s["total_revenue"], 25.0)

    def test_ctr(self):
        self.ra.record_click("p1")
        self.ra.record_click("p1")
        self.ra.record_impression("p1")
        self.ra.record_impression("p1")
        self.ra.record_impression("p1")
        self.ra.record_impression("p1")
        post = self.ra.get_post_revenue("p1")
        self.assertAlmostEqual(post.ctr, 50.0)

    def test_daily_revenue(self):
        self.ra.record_conversion("p1", amount=10)
        daily = self.ra.get_daily_revenue()
        self.assertGreater(len(daily), 0)

    def test_epc(self):
        self.ra.record_click("p1")
        self.ra.record_conversion("p1", amount=20)
        post = self.ra.get_post_revenue("p1")
        self.assertEqual(post.epc, 20.0)

    def test_stats(self):
        s = self.ra.stats()
        self.assertIn("events", s)
        self.assertIn("posts", s)


class TestPostRevenue(unittest.TestCase):
    def test_ctr_no_impressions(self):
        p = PostRevenue("p1")
        p.clicks = 10
        self.assertEqual(p.ctr, 0.0)

    def test_epc_no_clicks(self):
        p = PostRevenue("p1")
        self.assertEqual(p.epc, 0.0)

    def test_to_dict(self):
        p = PostRevenue("p1", title="Test", niche="tech")
        d = p.to_dict()
        self.assertEqual(d["post_id"], "p1")
        self.assertEqual(d["niche"], "tech")


# ─── Campaign Manager ───────────────────────────────────────────
class TestCampaignManager(unittest.TestCase):
    def setUp(self):
        CampaignManager._instance = None
        self.cm = get_campaign_manager()

    def tearDown(self):
        CampaignManager._instance = None

    def test_singleton(self):
        self.assertIs(self.cm, get_campaign_manager())

    def test_create_campaign(self):
        c = self.cm.create_campaign("Tech Promo", "tech", budget=100)
        self.assertEqual(c.name, "Tech Promo")
        self.assertEqual(c.budget, 100)

    def test_get_campaign(self):
        c = self.cm.create_campaign("Test", "niche1")
        found = self.cm.get_campaign(c.id)
        self.assertIs(c, found)

    def test_pause_resume(self):
        c = self.cm.create_campaign("Test", "niche1")
        self.assertTrue(self.cm.pause_campaign(c.id))
        self.assertEqual(c.status, "paused")
        self.assertTrue(self.cm.resume_campaign(c.id))
        self.assertEqual(c.status, "active")

    def test_complete(self):
        c = self.cm.create_campaign("Test", "niche1")
        self.assertTrue(self.cm.complete_campaign(c.id))
        self.assertEqual(c.status, "completed")

    def test_record_click(self):
        c = self.cm.create_campaign("Test", "niche1")
        self.cm.record_click(c.id, cost=0.50)
        self.assertEqual(c.total_clicks, 1)
        self.assertEqual(c.spent, 0.50)

    def test_record_conversion(self):
        c = self.cm.create_campaign("Test", "niche1")
        self.cm.record_conversion(c.id, revenue=75.0)
        self.assertEqual(c.total_conversions, 1)
        self.assertEqual(c.actual_revenue, 75.0)

    def test_top_campaigns(self):
        c1 = self.cm.create_campaign("A", "tech")
        c2 = self.cm.create_campaign("B", "tech")
        self.cm.record_conversion(c1.id, revenue=200)
        self.cm.record_conversion(c2.id, revenue=50)
        top = self.cm.get_top_campaigns("revenue", limit=1)
        self.assertEqual(top[0].id, c1.id)

    def test_niche_summary(self):
        c = self.cm.create_campaign("A", "tech")
        self.cm.record_click(c.id, cost=10)
        self.cm.record_conversion(c.id, revenue=50)
        summary = self.cm.get_niche_summary()
        self.assertIn("tech", summary)

    def test_campaign_status(self):
        self.cm.create_campaign("A", "niche1")
        status = self.cm.get_campaign_status()
        self.assertEqual(status["total_campaigns"], 1)

    def test_add_link(self):
        c = self.cm.create_campaign("A", "niche1")
        self.assertTrue(self.cm.add_link(c.id, "link1"))
        self.assertIn("link1", c.link_ids)

    def test_get_by_niche(self):
        self.cm.create_campaign("A", "crypto")
        self.cm.create_campaign("B", "crypto")
        self.cm.create_campaign("C", "health")
        crypto = self.cm.get_campaigns_by_niche("crypto")
        self.assertEqual(len(crypto), 2)


class TestCampaign(unittest.TestCase):
    def test_roi(self):
        c = Campaign("Test", "tech", budget=100)
        c.spent = 50
        c.actual_revenue = 200
        self.assertEqual(c.roi, 300.0)

    def test_conversion_rate(self):
        c = Campaign("Test", "tech")
        c.total_clicks = 100
        c.total_conversions = 5
        self.assertEqual(c.conversion_rate, 5.0)

    def test_epc(self):
        c = Campaign("Test", "tech")
        c.total_clicks = 100
        c.actual_revenue = 75
        self.assertEqual(c.epc, 0.75)

    def test_revenue_progress(self):
        c = Campaign("Test", "tech", target_revenue=1000)
        c.actual_revenue = 250
        self.assertEqual(c.revenue_progress, 25.0)

    def test_to_dict(self):
        c = Campaign("Test", "tech")
        d = c.to_dict()
        self.assertEqual(d["name"], "Test")


# ─── AI Monetization Optimizer ───────────────────────────────────
class TestAIMonetizationOptimizer(unittest.TestCase):
    def setUp(self):
        AIMonetizationOptimizer._instance = None
        self.opt = get_monetization_optimizer()

    def tearDown(self):
        AIMonetizationOptimizer._instance = None

    def test_singleton(self):
        self.assertIs(self.opt, get_monetization_optimizer())

    def test_record_niche_data(self):
        np = self.opt.record_niche_data("tech", clicks=500, conversions=25, revenue=500, posts=20)
        self.assertEqual(np.niche, "tech")
        self.assertEqual(np.total_clicks, 500)

    def test_analyze_niches(self):
        self.opt.record_niche_data("tech", clicks=1000, conversions=50, revenue=1000, posts=30)
        self.opt.record_niche_data("health", clicks=200, conversions=5, revenue=50, posts=5)
        niches = self.opt.analyze_niches()
        self.assertEqual(len(niches), 2)
        self.assertEqual(niches[0].niche, "tech")

    def test_score_content(self):
        cs = self.opt.score_content("p1", "Best Laptop", "tech",
                                      clicks=500, impressions=10000,
                                      conversions=25, revenue=500)
        self.assertEqual(cs.overall_category if hasattr(cs, "overall_category") else cs.category, "star")
        self.assertGreater(cs.overall_score, 70)

    def test_content_categories(self):
        self.opt.score_content("star", "Great", "tech", 500, 10000, 25, 500)
        self.opt.score_content("avg", "OK", "tech", 10, 1000, 1, 10)
        self.opt.score_content("weak", "Bad", "tech", 1, 1000, 0, 0)
        report = self.opt.get_optimization_report()
        cats = report["content_categories"]
        self.assertGreaterEqual(cats["star"], 1)

    def test_generate_recommendations(self):
        self.opt.record_niche_data("tech", clicks=1000, conversions=50, revenue=1000, posts=30)
        self.opt.score_content("p1", "Top 10", "tech", 500, 10000, 25, 500)
        recs = self.opt.generate_recommendations()
        self.assertIsInstance(recs, list)

    def test_optimization_report(self):
        self.opt.record_niche_data("crypto", clicks=500, conversions=20, revenue=400, posts=10)
        report = self.opt.get_optimization_report()
        self.assertIn("total_niches", report)
        self.assertIn("recommendations", report)

    def test_top_content(self):
        self.opt.score_content("p1", "Great", "tech", 500, 10000, 25, 500)
        self.opt.score_content("p2", "OK", "tech", 10, 1000, 1, 10)
        top = self.opt.get_top_content(limit=1)
        self.assertEqual(top[0].post_id, "p1")

    def test_stats(self):
        s = self.opt.stats()
        self.assertIn("niches", s)
        self.assertIn("content_scored", s)


class TestNichePerformance(unittest.TestCase):
    def test_to_dict(self):
        np = NichePerformance("tech")
        np.total_clicks = 100
        d = np.to_dict()
        self.assertEqual(d["niche"], "tech")


class TestContentScore(unittest.TestCase):
    def test_to_dict(self):
        cs = ContentScore("p1", title="Test", niche="tech")
        cs.clicks = 100
        d = cs.to_dict()
        self.assertEqual(d["post_id"], "p1")


# ─── Affiliate Engine Manager ────────────────────────────────────
class TestAffiliateEngineManager(unittest.TestCase):
    def setUp(self):
        AffiliateManager._instance = None
        LinkIntelligence._instance = None
        RevenueAnalytics._instance = None
        CampaignManager._instance = None
        AIMonetizationOptimizer._instance = None
        AffiliateEngineManager._instance = None
        self.engine = get_affiliate_engine()

    def tearDown(self):
        AffiliateManager._instance = None
        LinkIntelligence._instance = None
        RevenueAnalytics._instance = None
        CampaignManager._instance = None
        AIMonetizationOptimizer._instance = None
        AffiliateEngineManager._instance = None

    def test_singleton(self):
        self.assertIs(self.engine, get_affiliate_engine())

    def test_submodules(self):
        self.assertIsNotNone(self.engine.affiliate)
        self.assertIsNotNone(self.engine.links)
        self.assertIsNotNone(self.engine.revenue)
        self.assertIsNotNone(self.engine.campaigns)
        self.assertIsNotNone(self.engine.optimizer)

    def test_create_niche_campaign(self):
        result = self.engine.create_niche_campaign("Tech Promo", "tech", budget=500)
        self.assertIn("campaign", result)
        self.assertEqual(result["campaign"]["niche"], "tech")

    def test_track_click(self):
        link = self.engine.links.create_link("https://product.com", niche="tech")
        result = self.engine.track_click(link.id, post_id="p1", niche="tech")
        self.assertIn("link_id", result)

    def test_track_conversion(self):
        result = self.engine.track_conversion("p1", revenue=99.99, commission=10.0, niche="tech")
        self.assertIn("revenue_event", result)

    def test_full_status(self):
        status = self.engine.get_full_status()
        self.assertEqual(status["overall"], "Active")
        self.assertIn("affiliate", status)
        self.assertIn("links", status)
        self.assertIn("revenue", status)
        self.assertIn("campaigns", status)
        self.assertIn("optimizer", status)

    def test_executive_summary(self):
        summary = self.engine.get_executive_summary()
        self.assertIn("total_programs", summary)
        self.assertIn("total_revenue", summary)

    def test_stats(self):
        s = self.engine.stats()
        self.assertIn("affiliate", s)
        self.assertIn("links", s)
        self.assertIn("revenue", s)

    def test_best_program_for_niche(self):
        result = self.engine._find_best_program_for_niche("crypto")
        self.assertIsNotNone(result)
        self.assertEqual(result["platform"], "binance")


class TestFullEnterpriseStack(unittest.TestCase):
    """End-to-end: All 6 modules working together."""
    def setUp(self):
        for cls in [AffiliateManager, LinkIntelligence, RevenueAnalytics,
                     CampaignManager, AIMonetizationOptimizer, AffiliateEngineManager]:
            cls._instance = None
        self.engine = get_affiliate_engine()

    def tearDown(self):
        for cls in [AffiliateManager, LinkIntelligence, RevenueAnalytics,
                     CampaignManager, AIMonetizationOptimizer, AffiliateEngineManager]:
            cls._instance = None

    def test_full_monetization_flow(self):
        # 1. Register affiliate programs
        self.engine.affiliate.add_program("Custom", "custom", commission_rate=15.0)
        programs = self.engine.affiliate.list_programs()
        self.assertGreaterEqual(len(programs), 7)

        # 2. Create tracked links
        link = self.engine.links.create_link(
            "https://product.com/laptop", niche="tech", category="electronics"
        )
        self.engine.links.add_variant(link.id, "https://alt.com/laptop", weight=5)
        self.assertTrue(link.ab_test_enabled)

        # 3. Create campaign
        result = self.engine.create_niche_campaign(
            "Tech Laptop Campaign", "tech", budget=500, target_revenue=2000
        )
        camp_id = result["campaign"]["id"]

        # 4. Simulate clicks
        self.engine.track_click(
            link.id, post_id="post_001", source="facebook",
            platform="facebook", niche="tech", campaign_id=camp_id,
        )

        # 5. Simulate conversions
        self.engine.track_conversion(
            "post_001", revenue=150.0, commission=15.0,
            niche="tech", platform="facebook", campaign_id=camp_id,
            link_id=link.id,
        )

        # 6. Record niche data for optimizer
        self.engine.optimizer.record_niche_data(
            "tech", clicks=500, conversions=25, revenue=5000, posts=20
        )
        self.engine.optimizer.score_content(
            "post_001", "Best Laptop 2024", "tech",
            clicks=500, impressions=10000, conversions=25, revenue=5000
        )

        # 7. Verify full status
        status = self.engine.get_full_status()
        self.assertEqual(status["overall"], "Active")
        self.assertGreater(status["affiliate"]["total_programs"], 0)

        # 8. Verify executive summary
        summary = self.engine.get_executive_summary()
        self.assertGreater(summary["total_revenue"], 0)

        # 9. Optimization report
        report = self.engine.optimizer.get_optimization_report()
        self.assertGreater(report["total_niches"], 0)

        # 10. Campaign status
        camp_status = self.engine.campaigns.get_campaign_status()
        self.assertEqual(camp_status["active"], 1)


if __name__ == "__main__":
    unittest.main()
