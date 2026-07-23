"""Enterprise Niche Intelligence Engine Tests — Phase 9."""
import sys
import unittest

sys.path.insert(0, ".")

from layers.layer02_research.modules.niche_intelligence.niche_research_engine import (
    NicheResearchEngine, NicheProfile, get_niche_research_engine,
)
from layers.layer02_research.modules.niche_intelligence.product_intelligence import (
    ProductIntelligence, ProductProfile, get_product_intelligence,
)
from layers.layer02_research.modules.niche_intelligence.keyword_intelligence import (
    KeywordIntelligence, KeywordEntry, get_keyword_intelligence,
)
from layers.layer02_research.modules.niche_intelligence.competitor_intelligence import (
    CompetitorIntelligence, CompetitorProfile, get_competitor_intelligence,
)
from layers.layer02_research.modules.niche_intelligence.content_opportunity_finder import (
    ContentOpportunityFinder, ContentOpportunity, get_content_opportunity_finder,
)
from layers.layer02_research.modules.niche_intelligence.revenue_prediction_engine import (
    RevenuePredictionEngine, NicheRevenuePrediction, get_revenue_prediction_engine,
)
from layers.layer02_research.modules.niche_intelligence.niche_intelligence_manager import (
    NicheIntelligenceManager, get_niche_intelligence,
)


# ─── Niche Research Engine ──────────────────────────────────────
class TestNicheResearchEngine(unittest.TestCase):
    def setUp(self):
        NicheResearchEngine._instance = None
        self.engine = get_niche_research_engine()

    def tearDown(self):
        NicheResearchEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.engine, get_niche_research_engine())

    def test_defaults_loaded(self):
        self.assertGreaterEqual(len(self.engine.list_niches()), 10)

    def test_add_niche(self):
        np = self.engine.add_niche("AI Tools", "ai_tools", market_size=500_000_000, growth_rate=30)
        self.assertEqual(np.name, "AI Tools")
        self.assertGreater(np.opportunity_score, 0)

    def test_get_niche(self):
        np = self.engine.get_niche("tech")
        self.assertIsNotNone(np)
        self.assertEqual(np.name, "Technology & Gadgets")

    def test_add_keywords(self):
        result = self.engine.add_keywords("tech", [
            {"keyword": "best laptop 2024", "volume": 5000},
            {"keyword": "top phones", "volume": 8000},
        ])
        self.assertTrue(result)

    def test_add_trend(self):
        trend = self.engine.add_trend("tech", "AI", interest=85, direction="rising")
        self.assertEqual(trend.keyword, "AI")

    def test_get_top_niches(self):
        top = self.engine.get_top_niches(3)
        self.assertEqual(len(top), 3)
        self.assertGreaterEqual(top[0].score, top[-1].score)

    def test_research_report(self):
        report = self.engine.get_research_report()
        self.assertIn("total_niches", report)
        self.assertIn("niches", report)

    def test_niche_score(self):
        np = NicheProfile("Test", "test")
        np.market_size_usd = 1_000_000_000
        np.growth_rate = 20
        np.competition_level = "low"
        np.opportunity_score = 75
        np.monetization_potential = "high"
        self.assertGreater(np.score, 50)

    def test_stats(self):
        s = self.engine.stats()
        self.assertIn("niches", s)


# ─── Product Intelligence ────────────────────────────────────────
class TestProductIntelligence(unittest.TestCase):
    def setUp(self):
        ProductIntelligence._instance = None
        self.pi = get_product_intelligence()

    def tearDown(self):
        ProductIntelligence._instance = None

    def test_singleton(self):
        self.assertIs(self.pi, get_product_intelligence())

    def test_add_product(self):
        p = self.pi.add_product("MacBook Pro", "tech", "Apple", price=1999,
                                  commission_rate=3.0, program="amazon", rating=4.8,
                                  review_count=2500)
        self.assertIsNotNone(p.id)
        self.assertGreater(p.score, 0)

    def test_commission_per_sale(self):
        p = self.pi.add_product("Test", "tech", price=100, commission_rate=10)
        self.assertEqual(p.commission_per_sale, 10.0)

    def test_fixed_commission(self):
        p = self.pi.add_product("Test", "saas", price=99, commission_rate=58,
                                  commission_type="fixed")
        self.assertEqual(p.commission_per_sale, 58.0)

    def test_recurring_product(self):
        p = self.pi.add_product("SaaS Tool", "saas", price=49, commission_rate=30,
                                  recurring=True, recurring_value=15)
        self.assertTrue(p.recurring)
        self.assertEqual(p.annual_recurring_value, 180.0)

    def test_get_by_category(self):
        self.pi.add_product("A", "tech", price=100)
        self.pi.add_product("B", "tech", price=200)
        self.pi.add_product("C", "health", price=50)
        tech = self.pi.get_by_category("tech")
        self.assertEqual(len(tech), 2)

    def test_get_top_products(self):
        self.pi.add_product("Premium", "tech", price=500, commission_rate=10, rating=4.9)
        self.pi.add_product("Basic", "tech", price=50, commission_rate=5, rating=3.0)
        top = self.pi.get_top_products(1)
        self.assertEqual(top[0].name, "Premium")

    def test_high_commission(self):
        self.pi.add_product("A", "tech", price=100, commission_rate=25)
        self.pi.add_product("B", "tech", price=100, commission_rate=5)
        high = self.pi.get_high_commission(min_rate=20)
        self.assertEqual(len(high), 1)

    def test_intelligence_report(self):
        self.pi.add_product("P1", "tech", price=100, commission_rate=10)
        report = self.pi.get_intelligence_report()
        self.assertEqual(report["total_products"], 1)

    def test_stats(self):
        s = self.pi.stats()
        self.assertIn("products", s)


# ─── Keyword Intelligence ────────────────────────────────────────
class TestKeywordIntelligence(unittest.TestCase):
    def setUp(self):
        KeywordIntelligence._instance = None
        self.ki = get_keyword_intelligence()

    def tearDown(self):
        KeywordIntelligence._instance = None

    def test_singleton(self):
        self.assertIs(self.ki, get_keyword_intelligence())

    def test_add_keyword(self):
        k = self.ki.add_keyword("best budget gaming laptop under 500", niche="tech",
                                  intent_type="commercial", volume=5000, cpc=2.50)
        self.assertEqual(k.keyword, "best budget gaming laptop under 500")
        self.assertTrue(k.long_tail)

    def test_question_detection(self):
        k = self.ki.add_keyword("how to invest in bitcoin", niche="crypto")
        self.assertTrue(k.question)
        self.assertEqual(k.intent_type, "informational")

    def test_get_buyer_intent(self):
        self.ki.add_keyword("buy laptop online", niche="tech", intent_type="transactional")
        self.ki.add_keyword("what is bitcoin", niche="crypto", intent_type="informational")
        buyer = self.ki.get_buyer_intent()
        self.assertEqual(len(buyer), 1)

    def test_get_long_tail(self):
        self.ki.add_keyword("best budget gaming laptop under 500", niche="tech")
        self.ki.add_keyword("laptop", niche="tech")
        long_tail = self.ki.get_long_tail()
        self.assertEqual(len(long_tail), 1)

    def test_get_questions(self):
        self.ki.add_keyword("is crypto safe", niche="crypto")
        self.ki.add_keyword("bitcoin", niche="crypto")
        q = self.ki.get_questions()
        self.assertEqual(len(q), 1)

    def test_get_commercial(self):
        self.ki.add_keyword("shopify review", niche="saas", intent_type="commercial", cpc=5.0)
        comm = self.ki.get_commercial_keywords()
        self.assertEqual(len(comm), 1)

    def test_get_by_niche(self):
        self.ki.add_keyword("k1", niche="tech")
        self.ki.add_keyword("k2", niche="tech")
        self.ki.add_keyword("k3", niche="health")
        tech = self.ki.get_by_niche("tech")
        self.assertEqual(len(tech), 2)

    def test_search(self):
        self.ki.add_keyword("best gaming mouse")
        self.ki.add_keyword("best keyboard")
        results = self.ki.search("gaming")
        self.assertEqual(len(results), 1)

    def test_opportunity_score(self):
        k = self.ki.add_keyword("best laptop 2024", niche="tech",
                                  intent_type="transactional", volume=10000, cpc=3.0)
        self.assertGreater(k.opportunity_score, 0)

    def test_keyword_report(self):
        self.ki.add_keyword("test kw", niche="tech", intent_type="commercial")
        report = self.ki.get_keyword_report()
        self.assertIn("total_keywords", report)

    def test_stats(self):
        s = self.ki.stats()
        self.assertIn("keywords", s)


# ─── Competitor Intelligence ─────────────────────────────────────
class TestCompetitorIntelligence(unittest.TestCase):
    def setUp(self):
        CompetitorIntelligence._instance = None
        self.ci = get_competitor_intelligence()

    def tearDown(self):
        CompetitorIntelligence._instance = None

    def test_singleton(self):
        self.assertIs(self.ci, get_competitor_intelligence())

    def test_add_competitor(self):
        c = self.ci.add_competitor("TechCrunch", "techcrunch.com", "tech",
                                     traffic=5000000, da=92, backlinks=500000,
                                     content_count=100000, threat="high")
        self.assertIsNotNone(c.id)
        self.assertGreater(c.score, 0)

    def test_threat_levels(self):
        self.ci.add_competitor("Big", "big.com", "tech", traffic=10000000, da=90, threat="high")
        self.ci.add_competitor("Small", "small.com", "tech", traffic=10000, da=20, threat="low")
        high = self.ci.get_high_threat()
        self.assertEqual(len(high), 1)

    def test_by_niche(self):
        self.ci.add_competitor("A", "a.com", "crypto", traffic=100000)
        self.ci.add_competitor("B", "b.com", "crypto", traffic=50000)
        crypto = self.ci.get_by_niche("crypto")
        self.assertEqual(len(crypto), 2)

    def test_analyze_gaps(self):
        self.ci.add_competitor("A", "a.com", "tech",
                                 strengths=["good SEO", "great content"],
                                 weaknesses=["no video", "slow site"])
        self.ci.add_competitor("B", "b.com", "tech",
                                 strengths=["great content", "social"],
                                 weaknesses=["no video", "poor design"])
        gaps = self.ci.analyze_gaps("tech")
        self.assertIn("competitors", gaps)
        self.assertIn("no video", gaps["gaps"])

    def test_monetization_overlap(self):
        self.ci.add_competitor("A", "a.com", "tech",
                                 programs=["amazon", "shareasale"])
        self.ci.add_competitor("B", "b.com", "tech",
                                 programs=["cj"])
        amazon_comps = self.ci.get_monetization_overlap("amazon")
        self.assertEqual(len(amazon_comps), 1)

    def test_top_competitors(self):
        self.ci.add_competitor("Big", "big.com", "tech", traffic=5000000, da=80)
        self.ci.add_competitor("Small", "small.com", "tech", traffic=1000, da=10)
        top = self.ci.get_top_competitors(1)
        self.assertEqual(top[0].name, "Big")

    def test_estimated_revenue(self):
        c = self.ci.add_competitor("X", "x.com", "tech", traffic=1000000)
        self.assertGreater(c.estimated_monthly_revenue, 0)

    def test_intelligence_report(self):
        self.ci.add_competitor("X", "x.com", "tech")
        report = self.ci.get_intelligence_report()
        self.assertEqual(report["total_competitors"], 1)

    def test_stats(self):
        s = self.ci.stats()
        self.assertIn("competitors", s)


# ─── Content Opportunity Finder ──────────────────────────────────
class TestContentOpportunityFinder(unittest.TestCase):
    def setUp(self):
        ContentOpportunityFinder._instance = None
        self.cof = get_content_opportunity_finder()

    def tearDown(self):
        ContentOpportunityFinder._instance = None

    def test_singleton(self):
        self.assertIs(self.cof, get_content_opportunity_finder())

    def test_find_opportunity(self):
        o = self.cof.find_opportunity("Best Laptops 2024", niche="tech",
                                        platform="blog", estimated_traffic=50000,
                                        estimated_revenue=200, competition="low",
                                        difficulty=30)
        self.assertIsNotNone(o.id)
        self.assertGreater(o.opportunity_score, 0)

    def test_quick_wins(self):
        self.cof.find_opportunity("Quick Win", niche="tech",
                                    estimated_traffic=100000, estimated_revenue=500,
                                    competition="low", difficulty=25)
        self.cof.find_opportunity("Hard Topic", niche="tech",
                                    estimated_traffic=1000, estimated_revenue=10,
                                    competition="high", difficulty=90)
        wins = self.cof.get_quick_wins()
        self.assertEqual(len(wins), 1)

    def test_by_niche(self):
        self.cof.find_opportunity("T1", niche="tech")
        self.cof.find_opportunity("T2", niche="tech")
        self.cof.find_opportunity("T3", niche="health")
        tech = self.cof.get_by_niche("tech")
        self.assertEqual(len(tech), 2)

    def test_by_platform(self):
        self.cof.find_opportunity("P1", platform="youtube")
        self.cof.find_opportunity("P2", platform="youtube")
        self.cof.find_opportunity("P3", platform="blog")
        yt = self.cof.get_by_platform("youtube")
        self.assertEqual(len(yt), 2)

    def test_top_opportunities(self):
        self.cof.find_opportunity("A", estimated_traffic=100000, estimated_revenue=500)
        self.cof.find_opportunity("B", estimated_traffic=1000, estimated_revenue=5)
        top = self.cof.get_top_opportunities(1)
        self.assertEqual(top[0].topic, "A")

    def test_platform_recommendations(self):
        self.cof.find_opportunity("Video Topic", platform="youtube", estimated_traffic=50000)
        recs = self.cof.get_platform_recommendations()
        self.assertIn("youtube", recs)

    def test_opportunity_report(self):
        self.cof.find_opportunity("Test", niche="tech", estimated_traffic=10000)
        report = self.cof.get_opportunity_report()
        self.assertIn("total_opportunities", report)

    def test_stats(self):
        s = self.cof.stats()
        self.assertIn("opportunities", s)


# ─── Revenue Prediction Engine ───────────────────────────────────
class TestRevenuePredictionEngine(unittest.TestCase):
    def setUp(self):
        RevenuePredictionEngine._instance = None
        self.rpe = get_revenue_prediction_engine()

    def tearDown(self):
        RevenuePredictionEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.rpe, get_revenue_prediction_engine())

    def test_predict_niche(self):
        p = self.rpe.predict_niche_revenue("tech", monthly_traffic=100000,
                                              avg_cpc=2.0, conversion_rate=3.0,
                                              avg_commission=15.0,
                                              best_affiliate="amazon",
                                              best_platform="blog")
        self.assertEqual(p.niche, "tech")
        self.assertGreater(p.predicted_monthly_revenue, 0)

    def test_predict_affiliate(self):
        p = self.rpe.predict_affiliate_revenue("amazon", "tech",
                                                 conversion_rate=3.0,
                                                 avg_commission=15.0,
                                                 monthly_clicks=5000)
        self.assertEqual(p.affiliate, "amazon")
        self.assertGreater(p.monthly_revenue_predicted, 0)

    def test_predict_platform(self):
        p = self.rpe.predict_platform_revenue("blog", "tech",
                                                avg_reach=50000,
                                                engagement_rate=3.0,
                                                affiliate_click_rate=5.0,
                                                monthly_content=30)
        self.assertEqual(p.platform, "blog")
        self.assertGreater(p.predicted_monthly_revenue, 0)

    def test_total_predictions(self):
        self.rpe.predict_niche_revenue("tech", 100000, 2.0, 3.0, 15.0)
        self.rpe.predict_niche_revenue("health", 50000, 1.5, 2.0, 10.0)
        total = self.rpe.get_total_predicted_revenue()
        self.assertGreater(total["monthly"], 0)
        self.assertGreater(total["annual"], total["monthly"])

    def test_best_affiliates(self):
        self.rpe.predict_affiliate_revenue("amazon", "tech", 3.0, 15.0, 5000)
        self.rpe.predict_affiliate_revenue("cj", "tech", 2.0, 10.0, 3000)
        best = self.rpe.get_best_affiliates("tech")
        self.assertEqual(len(best), 2)

    def test_prediction_report(self):
        self.rpe.predict_niche_revenue("tech", 100000, 2.0, 3.0, 15.0)
        report = self.rpe.get_prediction_report()
        self.assertIn("total_predicted_monthly", report)

    def test_stats(self):
        s = self.rpe.stats()
        self.assertIn("niche_predictions", s)


# ─── Niche Intelligence Manager ──────────────────────────────────
class TestNicheIntelligenceManager(unittest.TestCase):
    def setUp(self):
        for cls in [NicheResearchEngine, ProductIntelligence, KeywordIntelligence,
                     CompetitorIntelligence, ContentOpportunityFinder,
                     RevenuePredictionEngine, NicheIntelligenceManager]:
            cls._instance = None
        self.ni = get_niche_intelligence()

    def tearDown(self):
        for cls in [NicheResearchEngine, ProductIntelligence, KeywordIntelligence,
                     CompetitorIntelligence, ContentOpportunityFinder,
                     RevenuePredictionEngine, NicheIntelligenceManager]:
            cls._instance = None

    def test_singleton(self):
        self.assertIs(self.ni, get_niche_intelligence())

    def test_submodules(self):
        self.assertIsNotNone(self.ni.research)
        self.assertIsNotNone(self.ni.products)
        self.assertIsNotNone(self.ni.keywords)
        self.assertIsNotNone(self.ni.competitors)
        self.assertIsNotNone(self.ni.opportunities)
        self.assertIsNotNone(self.ni.predictions)

    def test_analyze_niche(self):
        result = self.ni.analyze_niche("tech")
        self.assertIn("niche", result)
        self.assertIn("keywords", result)

    def test_niche_rankings(self):
        rankings = self.ni.get_niche_rankings()
        self.assertGreater(len(rankings), 0)
        self.assertGreaterEqual(rankings[0]["score"], rankings[-1]["score"])

    def test_full_intelligence(self):
        status = self.ni.get_full_intelligence()
        self.assertEqual(status["overall"], "Active")
        self.assertIn("research", status)
        self.assertIn("products", status)
        self.assertIn("keywords", status)
        self.assertIn("competitors", status)
        self.assertIn("opportunities", status)
        self.assertIn("predictions", status)

    def test_executive_summary(self):
        summary = self.ni.get_executive_summary()
        self.assertIn("total_niches", summary)
        self.assertIn("predicted_monthly_revenue", summary)

    def test_stats(self):
        s = self.ni.stats()
        self.assertIn("research", s)
        self.assertIn("products", s)


# ─── Full Enterprise Stack ───────────────────────────────────────
class TestFullEnterpriseStack(unittest.TestCase):
    """End-to-end: All 7 modules working together."""
    def setUp(self):
        for cls in [NicheResearchEngine, ProductIntelligence, KeywordIntelligence,
                     CompetitorIntelligence, ContentOpportunityFinder,
                     RevenuePredictionEngine, NicheIntelligenceManager]:
            cls._instance = None
        self.ni = get_niche_intelligence()

    def tearDown(self):
        for cls in [NicheResearchEngine, ProductIntelligence, KeywordIntelligence,
                     CompetitorIntelligence, ContentOpportunityFinder,
                     RevenuePredictionEngine, NicheIntelligenceManager]:
            cls._instance = None

    def test_full_niche_intelligence_flow(self):
        # 1. Research niches
        self.ni.research.add_niche("AI Tools", "ai", market_size=2_000_000_000,
                                     growth_rate=30, competition="medium")
        ai_niche = self.ni.research.get_niche("ai")
        self.assertIsNotNone(ai_niche)
        self.assertGreater(ai_niche.opportunity_score, 0)

        # 2. Add products
        self.ni.products.add_product("Jasper AI", "ai", "Jasper", price=59,
                                       commission_rate=30, recurring=True, recurring_value=18)
        self.ni.products.add_product("Copy.ai", "ai", "Copy", price=49,
                                       commission_rate=25, recurring=True, recurring_value=12)
        products = self.ni.products.get_by_category("ai")
        self.assertEqual(len(products), 2)

        # 3. Research keywords
        self.ni.keywords.add_keyword("best AI writing tools", niche="ai",
                                       intent_type="commercial", volume=8000, cpc=3.50)
        self.ni.keywords.add_keyword("how to use AI for content", niche="ai",
                                       intent_type="informational", volume=5000)
        buyer = self.ni.keywords.get_buyer_intent()
        self.assertGreater(len(buyer), 0)

        # 4. Analyze competitors
        self.ni.competitors.add_competitor("Writesonic", "writesonic.com", "ai",
                                             traffic=2000000, da=75, threat="high")
        self.ni.competitors.add_competitor("Rytr", "rytr.me", "ai",
                                             traffic=500000, da=55, threat="medium")
        ai_comps = self.ni.competitors.get_by_niche("ai")
        self.assertEqual(len(ai_comps), 2)

        # 5. Find content opportunities
        self.ni.opportunities.find_opportunity(
            "Top 10 AI Writing Tools Compared", niche="ai",
            platform="blog", estimated_traffic=30000, estimated_revenue=300,
            competition="low", difficulty=35, keywords=["ai writing tools", "best ai tools"],
        )
        wins = self.ni.opportunities.get_quick_wins()
        self.assertGreater(len(wins), 0)

        # 6. Predict revenue
        self.ni.predictions.predict_niche_revenue(
            "ai", monthly_traffic=100000, avg_cpc=3.50,
            conversion_rate=5.0, avg_commission=15.0,
            best_affiliate="shareasale", best_platform="blog",
        )
        pred = self.ni.predictions.get_niche_prediction("ai")
        self.assertIsNotNone(pred)
        self.assertGreater(pred.predicted_monthly_revenue, 0)

        # 7. Verify full intelligence
        status = self.ni.get_full_intelligence()
        self.assertEqual(status["overall"], "Active")
        self.assertGreater(status["research"]["total_niches"], 0)

        # 8. Verify executive summary
        summary = self.ni.get_executive_summary()
        self.assertGreater(summary["total_niches"], 0)
        self.assertGreater(summary["predicted_monthly_revenue"], 0)

        # 9. Verify niche rankings
        rankings = self.ni.get_niche_rankings()
        self.assertGreater(len(rankings), 0)

        # 10. Verify gap analysis
        gaps = self.ni.competitors.analyze_gaps("ai")
        self.assertIn("competitors", gaps)


if __name__ == "__main__":
    unittest.main()
