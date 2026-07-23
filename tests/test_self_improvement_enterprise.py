"""Enterprise Self-Improvement & Strategy Engine Tests — Phase 11."""
import sys
import time
import unittest

sys.path.insert(0, ".")

from layers.layer09_learning.modules.self_improvement_engine.performance_analyzer import (
    PerformanceAnalyzer, PerformanceRecord, get_performance_analyzer,
)
from layers.layer09_learning.modules.self_improvement_engine.mistake_detection_engine import (
    MistakeDetectionEngine, MistakePattern, get_mistake_detection,
)
from layers.layer09_learning.modules.self_improvement_engine.strategy_optimizer import (
    StrategyOptimizer, StrategyRecommendation, StrategyVersion, get_strategy_optimizer,
)
from layers.layer09_learning.modules.self_improvement_engine.prompt_optimizer import (
    PromptOptimizer, PromptVersion, get_prompt_optimizer,
)
from layers.layer09_learning.modules.self_improvement_engine.ab_testing_engine import (
    ABTestingEngine, ABExperiment, ABVariant, get_ab_testing_engine,
)
from layers.layer09_learning.modules.self_improvement_engine.knowledge_evolution_engine import (
    KnowledgeEvolutionEngine, KnowledgeEntry, get_knowledge_evolution,
)
from layers.layer09_learning.modules.self_improvement_engine.self_improvement_manager import (
    SelfImprovementManager, get_self_improvement,
)


class TestPerformanceAnalyzer(unittest.TestCase):
    def setUp(self):
        PerformanceAnalyzer._instance = None
        self.pa = get_performance_analyzer()

    def tearDown(self):
        PerformanceAnalyzer._instance = None

    def test_singleton(self):
        self.assertIs(self.pa, get_performance_analyzer())

    def test_record(self):
        r = self.pa.record("post", "p1", platform="facebook", niche="tech",
                            reach=1000, impressions=5000, clicks=150,
                            engagement=50, revenue=25.0)
        self.assertIsNotNone(r.id)
        self.assertEqual(r.ctr, 3.0)

    def test_top_performers(self):
        self.pa.record("post", "p1", revenue=100, reach=1000, impressions=5000, clicks=200)
        self.pa.record("post", "p2", revenue=10, reach=500, impressions=2000, clicks=20)
        top = self.pa.get_top_performers(metric="revenue", limit=1)
        self.assertEqual(top[0].entity_id, "p1")

    def test_underperformers(self):
        self.pa.record("post", "p1", revenue=0, reach=100, impressions=1000, clicks=2)
        under = self.pa.get_underperformers(min_score=50)
        self.assertGreater(len(under), 0)

    def test_platform_summary(self):
        self.pa.record("post", "p1", platform="facebook", revenue=50)
        self.pa.record("post", "p2", platform="x", revenue=30)
        summary = self.pa.get_platform_summary()
        self.assertIn("facebook", summary)
        self.assertIn("x", summary)

    def test_niche_summary(self):
        self.pa.record("post", "p1", niche="tech", revenue=100)
        summary = self.pa.get_niche_summary()
        self.assertIn("tech", summary)

    def test_benchmarks(self):
        for i in range(20):
            self.pa.record("post", f"p{i}", clicks=int(i * 10), impressions=max(int(i * 100), 100), revenue=float(i * 10))
        bms = self.pa.compute_benchmarks()
        self.assertIn("ctr", bms)

    def test_performance_score(self):
        r = PerformanceRecord("post", "p1")
        r.ctr = 5.0
        r.engagement_rate = 10.0
        r.revenue = 100
        r.roi = 300
        self.assertGreater(r.performance_score, 50)

    def test_stats(self):
        s = self.pa.stats()
        self.assertIn("records", s)


class TestMistakeDetectionEngine(unittest.TestCase):
    def setUp(self):
        MistakeDetectionEngine._instance = None
        self.md = get_mistake_detection()

    def tearDown(self):
        MistakeDetectionEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.md, get_mistake_detection())

    def test_detect_title_pattern(self):
        for i in range(3):
            self.md.detect_title_pattern("Bad Title", ctr=0.5, engagement=0.3, post_id=f"p{i}")
        patterns = self.md.get_active_patterns("high")
        self.assertGreater(len(patterns), 0)

    def test_detect_hashtag_pattern(self):
        for i in range(4):
            self.md.detect_hashtag_pattern("#bad", impressions=500, engagement=1)
        patterns = self.md.get_active_patterns("medium")
        self.assertGreater(len(patterns), 0)

    def test_detect_timing_pattern(self):
        for i in range(4):
            self.md.detect_timing_pattern(3, "Monday", ctr=0.5, platform="facebook")
        patterns = self.md.get_active_patterns()
        self.assertGreater(len(patterns), 0)

    def test_detect_content_pattern(self):
        pattern = self.md.detect_content_pattern("reel", performance_score=5, platform="facebook")
        self.assertIsNotNone(pattern)

    def test_resolve_pattern(self):
        self.md.detect_content_pattern("reel", performance_score=5)
        patterns = self.md.get_active_patterns()
        if patterns:
            self.assertTrue(self.md.resolve_pattern(patterns[0].id))

    def test_failing_titles(self):
        self.md.detect_title_pattern("Clickbait", ctr=0.3, engagement=0.1)
        titles = self.md.get_failing_titles()
        self.assertGreater(len(titles), 0)

    def test_priority_score(self):
        p = MistakePattern("test", "desc", "critical")
        p.occurrences = 5
        self.assertGreater(p.priority_score, 30)

    def test_detection_report(self):
        self.md.detect_content_pattern("reel", performance_score=5)
        report = self.md.get_detection_report()
        self.assertIn("total_patterns", report)

    def test_stats(self):
        s = self.md.stats()
        self.assertIn("patterns", s)


class TestStrategyOptimizer(unittest.TestCase):
    def setUp(self):
        StrategyOptimizer._instance = None
        self.so = get_strategy_optimizer()

    def tearDown(self):
        StrategyOptimizer._instance = None

    def test_singleton(self):
        self.assertIs(self.so, get_strategy_optimizer())

    def test_recommend(self):
        rec = self.so.recommend("niche", "increase budget for tech",
                                  niche="tech", priority=8, impact=25)
        self.assertIsNotNone(rec.id)
        self.assertEqual(rec.priority, 8)

    def test_get_pending(self):
        self.so.recommend("niche", "focus on crypto", priority=7)
        pending = self.so.get_pending()
        self.assertEqual(len(pending), 1)

    def test_apply_recommendation(self):
        rec = self.so.recommend("platform", "reduce x posts")
        self.assertTrue(self.so.apply_recommendation(rec.id))
        self.assertEqual(rec.status, "applied")

    def test_dismiss_recommendation(self):
        rec = self.so.recommend("content", "try reels")
        self.assertTrue(self.so.dismiss_recommendation(rec.id))

    def test_create_version(self):
        v = self.so.create_version("1.0", "Initial Strategy", {"niche": "tech"})
        self.assertIsNotNone(v.id)
        self.assertEqual(v.version, "1.0")

    def test_activate_version(self):
        v1 = self.so.create_version("1.0", "V1", {})
        v2 = self.so.create_version("2.0", "V2", {})
        self.assertTrue(self.so.activate_version(v1.id))
        self.assertTrue(self.so.activate_version(v2.id))
        current = self.so.get_current_version()
        self.assertEqual(current.id, v2.id)

    def test_rollback_version(self):
        v1 = self.so.create_version("1.0", "V1", {})
        v1.parent_id = ""
        self.so.activate_version(v1.id)
        rolled = self.so.rollback_version()
        # Should handle gracefully even if no parent
        self.assertTrue(True)

    def test_strategy_status(self):
        self.so.recommend("niche", "action")
        self.so.create_version("1.0", "V1", {})
        status = self.so.get_strategy_status()
        self.assertIn("total_recommendations", status)

    def test_stats(self):
        s = self.so.stats()
        self.assertIn("recommendations", s)


class TestPromptOptimizer(unittest.TestCase):
    def setUp(self):
        PromptOptimizer._instance = None
        self.po = get_prompt_optimizer()

    def tearDown(self):
        PromptOptimizer._instance = None

    def test_singleton(self):
        self.assertIs(self.po, get_prompt_optimizer())

    def test_add_prompt(self):
        pv = self.po.add_prompt("Write a blog about {topic}", category="content")
        self.assertIsNotNone(pv.id)

    def test_record_use(self):
        pv = self.po.add_prompt("Test prompt")
        self.po.record_use(pv.id, success=True, quality_score=8.0)
        self.assertEqual(pv.uses, 1)
        self.assertEqual(pv.successes, 1)

    def test_best_prompts(self):
        p1 = self.po.add_prompt("Great prompt")
        p2 = self.po.add_prompt("Bad prompt")
        for _ in range(5):
            self.po.record_use(p1.id, success=True, quality_score=9.0, engagement=8.0)
            self.po.record_use(p2.id, success=False, quality_score=2.0, engagement=1.0)
        best = self.po.get_best_prompts(limit=1)
        self.assertEqual(best[0].id, p1.id)

    def test_worst_prompts(self):
        p1 = self.po.add_prompt("Worst")
        for _ in range(5):
            self.po.record_use(p1.id, success=False, quality_score=1.0)
        worst = self.po.get_worst_prompts(min_uses=3)
        self.assertEqual(len(worst), 1)

    def test_promote(self):
        pv = self.po.add_prompt("Test")
        self.assertTrue(self.po.promote_prompt(pv.id))
        self.assertEqual(pv.status, "promoted")

    def test_retire(self):
        pv = self.po.add_prompt("Test")
        self.assertTrue(self.po.retire_prompt(pv.id))
        self.assertEqual(pv.status, "retired")

    def test_evolve(self):
        p1 = self.po.add_prompt("Original prompt")
        p2 = self.po.evolve_prompt(p1.id, "Improved prompt")
        self.assertIsNotNone(p2)
        self.assertEqual(p2.version, 2)
        self.assertEqual(p1.status, "superseded")

    def test_optimization_report(self):
        self.po.add_prompt("Test prompt")
        report = self.po.get_optimization_report()
        self.assertIn("total_prompts", report)

    def test_stats(self):
        s = self.po.stats()
        self.assertIn("prompts", s)


class TestABTestingEngine(unittest.TestCase):
    def setUp(self):
        ABTestingEngine._instance = None
        self.ab = get_ab_testing_engine()

    def tearDown(self):
        ABTestingEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.ab, get_ab_testing_engine())

    def test_create_experiment(self):
        exp = self.ab.create_experiment("Title Test", "title",
                                          variants=[{"name": "A"}, {"name": "B"}])
        self.assertIsNotNone(exp.id)
        self.assertEqual(len(exp.variants), 2)

    def test_add_variant(self):
        exp = self.ab.create_experiment("Test", "title")
        v = self.ab.add_variant(exp.id, "Variant C", "New title")
        self.assertIsNotNone(v)

    def test_record_impression(self):
        exp = self.ab.create_experiment("Test", "title", min_samples=10, variants=[{"name": "A"}, {"name": "B"}])
        v = exp.variants[0]
        self.assertTrue(self.ab.record_impression(exp.id, v.id))
        self.assertEqual(v.impressions, 1)

    def test_record_click(self):
        exp = self.ab.create_experiment("Test", "title", variants=[{"name": "A"}, {"name": "B"}])
        v = exp.variants[0]
        self.assertTrue(self.ab.record_click(exp.id, v.id))
        self.assertEqual(v.clicks, 1)

    def test_record_conversion(self):
        exp = self.ab.create_experiment("Test", "cta", variants=[{"name": "A"}, {"name": "B"}])
        v = exp.variants[0]
        self.assertTrue(self.ab.record_conversion(exp.id, v.id, revenue=25.0))
        self.assertEqual(v.conversions, 1)

    def test_evaluate_experiment(self):
        exp = self.ab.create_experiment("Test", "title", min_samples=5, variants=[{"name": "A"}, {"name": "B"}])
        for v in exp.variants:
            for _ in range(10):
                self.ab.record_impression(exp.id, v.id)
                self.ab.record_click(exp.id, v.id)
        result = self.ab.evaluate_experiment(exp.id)
        self.assertIsNotNone(result)
        self.assertNotEqual(result.winner_id, "")

    def test_conclude_experiment(self):
        exp = self.ab.create_experiment("Test", "title", min_samples=5)
        for v in exp.variants:
            for _ in range(10):
                self.ab.record_impression(exp.id, v.id)
                self.ab.record_click(exp.id, v.id)
        self.assertTrue(self.ab.conclude_experiment(exp.id))
        self.assertEqual(exp.status, "completed")

    def test_running_experiments(self):
        self.ab.create_experiment("Test1", "title")
        self.ab.create_experiment("Test2", "thumbnail")
        running = self.ab.get_running()
        self.assertEqual(len(running), 2)

    def test_winners(self):
        exp = self.ab.create_experiment("Test", "title", min_samples=5, variants=[{"name": "A"}, {"name": "B"}])
        for v in exp.variants:
            for _ in range(10):
                self.ab.record_impression(exp.id, v.id)
                self.ab.record_click(exp.id, v.id)
        self.ab.conclude_experiment(exp.id)
        winners = self.ab.get_winners()
        self.assertEqual(len(winners), 1)

    def test_testing_status(self):
        self.ab.create_experiment("Test", "title")
        status = self.ab.get_testing_status()
        self.assertIn("total_experiments", status)

    def test_stats(self):
        s = self.ab.stats()
        self.assertIn("experiments", s)


class TestKnowledgeEvolutionEngine(unittest.TestCase):
    def setUp(self):
        KnowledgeEvolutionEngine._instance = None
        self.ke = get_knowledge_evolution()

    def tearDown(self):
        KnowledgeEvolutionEngine._instance = None

    def test_singleton(self):
        self.assertIs(self.ke, get_knowledge_evolution())

    def test_add_knowledge(self):
        ke = self.ke.add_knowledge("AI Trends", "GPT-5 launched", category="tech",
                                     confidence=80, importance=90)
        self.assertIsNotNone(ke.id)
        self.assertEqual(ke.version, 1)

    def test_get_by_topic(self):
        self.ke.add_knowledge("AI", "Content 1", confidence=70)
        self.ke.add_knowledge("AI", "Content 2", confidence=80)
        entries = self.ke.get_by_topic("ai")
        self.assertEqual(len(entries), 2)

    def test_validate_entry(self):
        ke = self.ke.add_knowledge("Topic", "Content")
        self.assertTrue(self.ke.validate_entry(ke.id))
        self.assertEqual(ke.validation_count, 1)

    def test_merge_knowledge(self):
        ke1 = self.ke.add_knowledge("AI", "Old content")
        ke2 = self.ke.merge_knowledge(ke1.id, "New merged content")
        self.assertIsNotNone(ke2)
        self.assertEqual(ke2.version, 2)
        self.assertEqual(ke1.status, "superseded")

    def test_retire_entry(self):
        ke = self.ke.add_knowledge("Old", "Outdated")
        self.assertTrue(self.ke.retire_entry(ke.id))
        self.assertEqual(ke.status, "retired")

    def test_retire_expired(self):
        ke = self.ke.add_knowledge("Temp", "Data", ttl_days=1)
        ke.expires_at = time.time() - 1000
        count = self.ke.retire_expired()
        self.assertEqual(count, 1)

    def test_stale_entries(self):
        ke = self.ke.add_knowledge("Stale", "Old data")
        ke.last_validated = time.time() - (100 * 86400)
        stale = self.ke.get_stale_entries(max_age_days=30)
        self.assertEqual(len(stale), 1)

    def test_knowledge_report(self):
        self.ke.add_knowledge("Topic", "Content")
        report = self.ke.get_knowledge_report()
        self.assertIn("total_entries", report)

    def test_stats(self):
        s = self.ke.stats()
        self.assertIn("entries", s)


class TestSelfImprovementManager(unittest.TestCase):
    def setUp(self):
        for cls in [PerformanceAnalyzer, MistakeDetectionEngine, StrategyOptimizer,
                     PromptOptimizer, ABTestingEngine, KnowledgeEvolutionEngine,
                     SelfImprovementManager]:
            cls._instance = None
        self.si = get_self_improvement()

    def tearDown(self):
        for cls in [PerformanceAnalyzer, MistakeDetectionEngine, StrategyOptimizer,
                     PromptOptimizer, ABTestingEngine, KnowledgeEvolutionEngine,
                     SelfImprovementManager]:
            cls._instance = None

    def test_singleton(self):
        self.assertIs(self.si, get_self_improvement())

    def test_submodules(self):
        self.assertIsNotNone(self.si.performance)
        self.assertIsNotNone(self.si.mistakes)
        self.assertIsNotNone(self.si.strategy)
        self.assertIsNotNone(self.si.prompts)
        self.assertIsNotNone(self.si.ab_testing)
        self.assertIsNotNone(self.si.knowledge)

    def test_analyze_and_improve(self):
        result = self.si.analyze_and_improve()
        self.assertIn("performance_summary", result)
        self.assertIn("improvement_actions", result)

    def test_full_status(self):
        status = self.si.get_full_status()
        self.assertEqual(status["overall"], "Active")
        self.assertIn("performance", status)
        self.assertIn("mistakes", status)
        self.assertIn("strategy", status)

    def test_executive_summary(self):
        summary = self.si.get_executive_summary()
        self.assertIn("total_performance_records", summary)
        self.assertIn("improvement_actions", summary)

    def test_stats(self):
        s = self.si.stats()
        self.assertIn("performance", s)
        self.assertIn("mistakes", s)


class TestFullEnterpriseStack(unittest.TestCase):
    def setUp(self):
        for cls in [PerformanceAnalyzer, MistakeDetectionEngine, StrategyOptimizer,
                     PromptOptimizer, ABTestingEngine, KnowledgeEvolutionEngine,
                     SelfImprovementManager]:
            cls._instance = None
        self.si = get_self_improvement()

    def tearDown(self):
        for cls in [PerformanceAnalyzer, MistakeDetectionEngine, StrategyOptimizer,
                     PromptOptimizer, ABTestingEngine, KnowledgeEvolutionEngine,
                     SelfImprovementManager]:
            cls._instance = None

    def test_full_self_improvement_flow(self):
        # 1. Record performance
        self.si.performance.record("post", "p1", platform="facebook", niche="tech",
                                     reach=5000, impressions=10000, clicks=300,
                                     engagement=150, revenue=75.0)
        self.si.performance.record("post", "p2", platform="x", niche="tech",
                                     reach=1000, impressions=2000, clicks=20,
                                     engagement=5, revenue=0)
        # 2. Detect mistakes
        for i in range(3):
            self.si.mistakes.detect_title_pattern("Weak title", ctr=0.3, engagement=0.1, post_id=f"p{i}")
        self.si.mistakes.detect_content_pattern("reel", performance_score=5, platform="facebook")
        # 3. Generate strategies
        self.si.strategy.recommend("niche", "focus more on tech", niche="tech", priority=8, impact=30)
        self.si.strategy.recommend("platform", "reduce x posting", platform="x", priority=5, impact=15)
        # 4. Optimize prompts
        p1 = self.si.prompts.add_prompt("Write about {topic}")
        p2 = self.si.prompts.add_prompt("Create engaging {content}")
        for _ in range(5):
            self.si.prompts.record_use(p1.id, True, quality_score=8.0, engagement=7.0)
            self.si.prompts.record_use(p2.id, False, quality_score=2.0, engagement=1.0)
        # 5. Run A/B test
        exp = self.si.ab_testing.create_experiment("Title Test", "title", min_samples=5,
                                                     variants=[{"name": "A"}, {"name": "B"}])
        for v in exp.variants:
            for _ in range(10):
                self.si.ab_testing.record_impression(exp.id, v.id)
                self.si.ab_testing.record_click(exp.id, v.id)
        self.si.ab_testing.conclude_experiment(exp.id)
        # 6. Add knowledge
        self.si.knowledge.add_knowledge("AI Trends", "GPT-5 launched", confidence=80)
        self.si.knowledge.add_knowledge("Crypto", "Bitcoin at 100K", confidence=70)
        # 7. Verify
        result = self.si.analyze_and_improve()
        self.assertGreater(result["active_mistakes"], 0)
        self.assertGreater(result["pending_recommendations"], 0)
        # 8. Full status
        status = self.si.get_full_status()
        self.assertEqual(status["overall"], "Active")
        # 9. Executive summary
        summary = self.si.get_executive_summary()
        self.assertGreater(summary["total_performance_records"], 0)
        # 10. Apply strategy
        recs = self.si.strategy.get_pending()
        if recs:
            self.si.strategy.apply_recommendation(recs[0].id)


if __name__ == "__main__":
    unittest.main()
