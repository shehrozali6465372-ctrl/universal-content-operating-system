"""Comprehensive tests for Layer 23 — Module 13: Learning Connector (Final Module)."""
from __future__ import annotations
import time
import pytest
from typing import Any, Dict, List

from layers.layer23_website_manager.learning_connector.learning_connector import (
    LearningConnector, get_learning_connector,
)
from layers.layer23_website_manager.learning_connector.models.learning_models import (
    LearningEvent, PerformanceMetric, MistakeRecord, StrategyVersion,
    LearnedPattern, Recommendation, ImprovementAction, KnowledgeEntry,
    DecisionResult, PromptTemplate, MemoryRecord, LearningSummary,
)
from layers.layer23_website_manager.learning_connector.collector.learning_collector import (
    LearningCollector,
)
from layers.layer23_website_manager.learning_connector.analyzer.performance_analyzer import (
    PerformanceAnalyzer,
)
from layers.layer23_website_manager.learning_connector.mistakes.mistake_detector import (
    MistakeDetector,
)
from layers.layer23_website_manager.learning_connector.strategy.strategy_learner import (
    StrategyLearner,
)
from layers.layer23_website_manager.learning_connector.prompts.prompt_optimizer import (
    PromptOptimizer,
)
from layers.layer23_website_manager.learning_connector.decisions.decision_engine import (
    DecisionEngine,
)
from layers.layer23_website_manager.learning_connector.patterns.pattern_recognizer import (
    PatternRecognizer,
)
from layers.layer23_website_manager.learning_connector.knowledge.knowledge_base_manager import (
    KnowledgeBaseManager,
)
from layers.layer23_website_manager.learning_connector.recommendations.recommendation_engine import (
    RecommendationEngine,
)
from layers.layer23_website_manager.learning_connector.improvement.self_improvement_manager import (
    SelfImprovementManager,
)
from layers.layer23_website_manager.learning_connector.versions.version_manager import (
    VersionManager,
)
from layers.layer23_website_manager.learning_connector.memory.universal_memory_connector import (
    UniversalMemoryConnector,
)
from layers.layer23_website_manager.learning_connector.api.learning_api import (
    LearningAPI,
)
from layers.layer23_website_manager.learning_connector.exceptions import (
    LearningError, KnowledgeError, PatternRecognitionError, MemoryError,
    VersionError, RecommendationError, ImprovementError, CollectionError,
    AnalysisError, DecisionError, StrategyError,
)


# ══════════════════════════════════════════════════════════════════════
# Models Tests
# ══════════════════════════════════════════════════════════════════════

class TestModels:
    def test_learning_event(self):
        e = LearningEvent("pins", "publish", 0.95, {"pin_id": "123"}, True, "pinterest")
        assert e.event_id.startswith("lev_")
        assert e.module == "pins"
        assert e.score == 0.95
        d = e.to_dict()
        assert d["module"] == "pins"

    def test_learning_event_defaults(self):
        e = LearningEvent("web", "page_view")
        assert e.success is True
        assert e.score == 0.0

    def test_performance_metric(self):
        m = PerformanceMetric("ctr", "pins", 3.5, 5.0, "up")
        assert m.metric_id.startswith("pm_")
        assert m.name == "ctr"
        assert m.status == "needs_improvement"
        assert m.trend == "up"
        d = m.to_dict()
        assert d["name"] == "ctr"

    def test_performance_metric_excellent(self):
        m = PerformanceMetric("revenue", "affiliate", 1000, 800)
        assert m.status == "excellent"

    def test_performance_metric_good(self):
        m = PerformanceMetric("traffic", "seo", 85, 100)
        assert m.status == "good"

    def test_performance_metric_poor(self):
        m = PerformanceMetric("clicks", "pins", 10, 100)
        assert m.status == "poor"

    def test_mistake_record(self):
        m = MistakeRecord("pins", "publish_failed", "high", "Pin publish failed")
        assert m.mistake_id.startswith("mist_")
        assert m.resolved is False
        d = m.to_dict()
        assert d["severity"] == "high"

    def test_strategy_version(self):
        sv = StrategyVersion("1.1.0", "Improved pin strategy", 85.5, {"pins": True})
        assert sv.version_id.startswith("sv_")
        assert sv.version == "1.1.0"
        assert sv.rollback_available is True
        d = sv.to_dict()
        assert d["version"] == "1.1.0"

    def test_learned_pattern(self):
        lp = LearnedPattern("high_traffic", "Pages with high traffic", 0.85, "analyzer", 10)
        assert lp.pattern_id.startswith("lp_")
        assert lp.confidence == 0.85
        assert lp.support_count == 10
        d = lp.to_dict()
        assert d["pattern_name"] == "high_traffic"

    def test_learned_pattern_confidence_clamp(self):
        lp = LearnedPattern("test", "", 1.5)
        assert lp.confidence == 1.0
        lp2 = LearnedPattern("test2", "", -0.5)
        assert lp2.confidence == 0.0

    def test_recommendation(self):
        r = Recommendation("Optimize Pins", "Add better descriptions",
                          "seo", "high", "high")
        assert r.recommendation_id.startswith("rec_")
        assert r.status == "pending"
        d = r.to_dict()
        assert d["priority"] == "high"

    def test_improvement_action(self):
        act = ImprovementAction("optimize", "pins", "Optimize pin descriptions")
        assert act.action_id.startswith("imp_")
        assert act.status == "pending"
        d = act.to_dict()
        assert d["action_type"] == "optimize"

    def test_knowledge_entry(self):
        ke = KnowledgeEntry("best_pins", "Vertical images work best",
                           "research", 0.9, ["pins", "images"])
        assert ke.entry_id.startswith("ke_")
        assert ke.topic == "best_pins"
        d = ke.to_dict()
        assert d["confidence"] == 0.9

    def test_decision_result(self):
        dr = DecisionResult("Should we publish more?", "yes", 0.8,
                           "High traffic detected", {"traffic": 1000})
        assert dr.decision_id.startswith("dec_")
        assert dr.decision == "yes"
        d = dr.to_dict()
        assert d["confidence"] == 0.8

    def test_prompt_template(self):
        pt = PromptTemplate("pin_desc", "pinterest", "Write about {{topic}}")
        assert pt.prompt_id.startswith("pt_")
        assert pt.version == "1.0"
        d = pt.to_dict()
        assert d["category"] == "pinterest"

    def test_memory_record(self):
        mr = MemoryRecord("user_pref", {"theme": "dark"}, "ui", 3600, 0.8)
        assert mr.memory_id.startswith("mem_")
        assert mr.ttl == 3600
        d = mr.to_dict()
        assert d["importance"] == 0.8

    def test_learning_summary(self):
        ls = LearningSummary()
        assert ls.total_events == 0
        assert ls.current_version == "1.0.0"


# ══════════════════════════════════════════════════════════════════════
# LearningCollector Tests
# ══════════════════════════════════════════════════════════════════════

class TestLearningCollector:
    def setup_method(self):
        self.col = LearningCollector()

    def test_collect(self):
        e = self.col.collect("pins", "publish", 0.9)
        assert e.module == "pins"
        assert self.col.get_stats()["total_events"] == 1

    def test_collect_from_all_modules(self):
        data = {
            "pins": [{"event_type": "publish", "score": 0.9, "success": True}],
            "seo": [{"event_type": "optimize", "score": 0.8, "success": True}],
        }
        count = self.col.collect_from_all_modules(data)
        assert count == 2
        assert self.col.get_stats()["total_events"] == 2

    def test_collect_max_events(self):
        for i in range(10005):
            self.col.collect("test", "event", 1.0)
        assert self.col.get_stats()["total_events"] <= 10000

    def test_get_events_filter_module(self):
        self.col.collect("pins", "pub")
        self.col.collect("seo", "opt")
        events = self.col.get_events(module="pins")
        assert len(events) == 1

    def test_get_events_filter_type(self):
        self.col.collect("m1", "type_a")
        self.col.collect("m2", "type_b")
        events = self.col.get_events(event_type="type_a")
        assert len(events) == 1

    def test_clear_events(self):
        self.col.collect("m", "e")
        assert self.col.clear_events() == 1
        assert self.col.get_stats()["total_events"] == 0

    def test_get_stats(self):
        self.col.collect("pins", "pub", 0.9, success=True)
        self.col.collect("pins", "pub", 0.2, success=False)
        stats = self.col.get_stats()
        assert stats["successful_events"] == 1
        assert stats["failed_events"] == 1
        assert stats["success_rate"] == 50.0
        assert "pins" in stats["events_by_module"]


# ══════════════════════════════════════════════════════════════════════
# PerformanceAnalyzer Tests
# ══════════════════════════════════════════════════════════════════════

class TestPerformanceAnalyzer:
    def setup_method(self):
        self.an = PerformanceAnalyzer()

    def test_record_metric(self):
        m = self.an.record_metric("ctr", "pins", 3.5, 5.0)
        assert m.name == "ctr"
        assert len(self.an.get_metrics()) == 1

    def test_get_metrics_filter_module(self):
        self.an.record_metric("ctr", "pins", 3.5, 5.0)
        self.an.record_metric("ctr", "seo", 2.0, 5.0)
        assert len(self.an.get_metrics(module="pins")) == 1

    def test_get_metrics_filter_name(self):
        self.an.record_metric("ctr", "pins", 3.5, 5.0)
        self.an.record_metric("impressions", "pins", 100, 200)
        assert len(self.an.get_metrics(name="ctr")) == 1

    def test_get_best_performers(self):
        self.an.record_metric("a", "m", 90, 100)
        self.an.record_metric("b", "m", 50, 100)
        best = self.an.get_best_performers("m")
        assert len(best) >= 1
        assert best[0]["name"] == "a"

    def test_get_worst_performers(self):
        self.an.record_metric("a", "m", 90, 100)
        self.an.record_metric("b", "m", 30, 100)
        worst = self.an.get_worst_performers("m")
        assert len(worst) >= 1
        assert worst[0]["name"] == "b"

    def test_analyze_events_empty(self):
        result = self.an.analyze_events([])
        assert result["total"] == 0

    def test_analyze_events(self):
        events = [
            LearningEvent("pins", "pub", 0.9, success=True),
            LearningEvent("pins", "pub", 0.5, success=True),
            LearningEvent("seo", "opt", 0.0, success=False),
        ]
        result = self.an.analyze_events(events)
        assert result["total"] == 3
        assert result["success_rate"] == 66.7
        assert result["avg_score"] == 0.7

    def test_get_stats(self):
        self.an.record_metric("a", "m1", 1, 1)
        self.an.record_metric("b", "m2", 2, 2)
        stats = self.an.get_stats()
        assert stats["total_metrics"] == 2
        assert stats["modules_tracked"] == 2


# ══════════════════════════════════════════════════════════════════════
# MistakeDetector Tests
# ══════════════════════════════════════════════════════════════════════

class TestMistakeDetector:
    def setup_method(self):
        self.md = MistakeDetector()

    def test_record_mistake(self):
        m = self.md.record_mistake("pins", "publish_failed", "high",
                                    "Failed to publish pin")
        assert m.module == "pins"
        assert m.resolved is False

    def test_get_mistakes_filter_module(self):
        self.md.record_mistake("pins", "fail")
        self.md.record_mistake("seo", "fail")
        assert len(self.md.get_mistakes(module="pins")) == 1

    def test_get_mistakes_filter_severity(self):
        self.md.record_mistake("pins", "type_a", "high")
        self.md.record_mistake("pins", "type_b", "low")
        assert len(self.md.get_mistakes(severity="high")) == 1

    def test_mark_resolved(self):
        m = self.md.record_mistake("m", "t")
        assert self.md.mark_resolved(m.mistake_id) is True
        assert m.resolved is True
        assert self.md.mark_resolved("bad") is False

    def test_detect_from_events_failed(self):
        events = [LearningEvent("m", "t", 0.0, success=False)]
        detected = self.md.detect_from_events(events)
        assert len(detected) == 1
        assert detected[0].mistake_type == "failed_event"

    def test_detect_from_events_low_score(self):
        events = [LearningEvent("m", "t", 0.2, success=True)]
        detected = self.md.detect_from_events(events)
        assert len(detected) == 1
        assert detected[0].mistake_type == "low_score"

    def test_detect_from_events_good(self):
        events = [LearningEvent("m", "t", 0.9, success=True)]
        detected = self.md.detect_from_events(events)
        assert len(detected) == 0

    def test_get_unresolved_count(self):
        m = self.md.record_mistake("m", "t")
        assert self.md.get_unresolved_count() == 1
        self.md.mark_resolved(m.mistake_id)
        assert self.md.get_unresolved_count() == 0

    def test_get_stats(self):
        self.md.record_mistake("m", "t", "high")
        self.md.record_mistake("m", "t", "low")
        stats = self.md.get_stats()
        assert stats["total_mistakes"] == 2
        assert stats["by_severity"]["high"] == 1


# ══════════════════════════════════════════════════════════════════════
# StrategyLearner Tests
# ══════════════════════════════════════════════════════════════════════

class TestStrategyLearner:
    def setup_method(self):
        self.sl = StrategyLearner()

    def test_learn(self):
        result = self.sl.learn("best_time", "14:00", "analyzer", 0.7)
        assert result["value"] == "14:00"
        assert result["support_count"] == 1

    def test_learn_existing(self):
        self.sl.learn("key", "val1", "", 0.5)
        self.sl.learn("key", "val2", "", 0.9)
        entry = self.sl.get_learning("key")
        assert entry["support_count"] == 2

    def test_get_learning(self):
        self.sl.learn("k", "v")
        assert self.sl.get_learning("k") is not None
        assert self.sl.get_learning("nonexistent") is None

    def test_get_all_learnings(self):
        self.sl.learn("k1", "v1")
        self.sl.learn("k2", "v2")
        assert len(self.sl.get_all_learnings()) == 2

    def test_learn_from_metrics(self):
        metrics = [PerformanceMetric("ctr", "pins", 100, 50)]  # ratio 2.0
        keys = self.sl.learn_from_metrics(metrics)
        assert len(keys) == 1

    def test_get_stats(self):
        self.sl.learn("k", "v", "", 0.8)
        stats = self.sl.get_stats()
        assert stats["total_learnings"] == 1
        assert stats["avg_confidence"] == 0.8


# ══════════════════════════════════════════════════════════════════════
# PromptOptimizer Tests
# ══════════════════════════════════════════════════════════════════════

class TestPromptOptimizer:
    def setup_method(self):
        self.po = PromptOptimizer()

    def test_register_prompt(self):
        p = self.po.register_prompt("pin_desc", "pinterest", "Write about {{topic}}")
        assert p.prompt_id.startswith("pt_")
        assert p.name == "pin_desc"

    def test_get_prompt(self):
        p = self.po.register_prompt("test", "cat", "template")
        assert self.po.get_prompt(p.prompt_id) is p
        assert self.po.get_prompt("bad") is None

    def test_get_by_category(self):
        self.po.register_prompt("p1", "cat_a", "t1")
        self.po.register_prompt("p2", "cat_b", "t2")
        self.po.register_prompt("p3", "cat_a", "t3")
        assert len(self.po.get_prompts_by_category("cat_a")) == 2

    def test_get_all_prompts(self):
        self.po.register_prompt("p1", "c", "t")
        assert len(self.po.get_all_prompts()) == 1

    def test_record_use(self):
        p = self.po.register_prompt("test", "c", "t")
        assert self.po.record_use(p.prompt_id, 0.8) is True
        assert p.use_count == 1
        assert p.performance_score == 0.8
        assert self.po.record_use("bad", 0.5) is False

    def test_optimize(self):
        p = self.po.register_prompt("test", "c", "old")
        assert self.po.optimize(p.prompt_id, "new") is True
        assert p.template == "new"
        assert p.version == "1.1"
        assert self.po.optimize("bad", "x") is False

    def test_get_best_prompts(self):
        p1 = self.po.register_prompt("a", "cat", "t1")
        p2 = self.po.register_prompt("b", "cat", "t2")
        self.po.record_use(p1.prompt_id, 0.9)
        self.po.record_use(p2.prompt_id, 0.5)
        best = self.po.get_best_prompts("cat", 1)
        assert len(best) == 1
        assert best[0].name == "a"

    def test_get_stats(self):
        self.po.register_prompt("a", "c1", "t")
        self.po.register_prompt("b", "c2", "t")
        stats = self.po.get_stats()
        assert stats["total_prompts"] == 2
        assert stats["categories"] == 2


# ══════════════════════════════════════════════════════════════════════
# DecisionEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestDecisionEngine:
    def setup_method(self):
        self.de = DecisionEngine()

    def test_add_decision_rule(self):
        self.de.add_decision_rule("scale", "scale_content", 0.7, "Scale winning")
        # No direct getter, but should not raise

    def test_decide_no_rule(self):
        result = self.de.decide("unknown question")
        assert result.decision == "no_action"
        assert "No matching" in result.reasoning

    def test_decide_with_rule(self):
        self.de.add_decision_rule("more pins", "increase_production", 0.6, "Low pins")
        result = self.de.decide("should we generate more pins?")
        assert result.decision == "increase_production"

    def test_decide_with_context(self):
        self.de.add_decision_rule("fix", "run_recovery", 0.8, "Fix issues")
        result = self.de.decide("fix mistakes", {"success_rate": 0.3})
        assert result.confidence < 0.8  # reduced by context

    def test_get_decisions(self):
        self.de.decide("test")
        assert len(self.de.get_decisions()) == 1

    def test_get_stats(self):
        self.de.add_decision_rule("a", "b", 0.5, "c")
        self.de.decide("test")
        stats = self.de.get_stats()
        assert stats["total_decisions"] == 1
        assert stats["rules_available"] == 1


# ══════════════════════════════════════════════════════════════════════
# PatternRecognizer Tests
# ══════════════════════════════════════════════════════════════════════

class TestPatternRecognizer:
    def setup_method(self):
        self.pr = PatternRecognizer()

    def test_recognize(self):
        p = self.pr.recognize("high_traffic", "High traffic pattern", 0.8, "analyzer")
        assert p.pattern_name == "high_traffic"

    def test_recognize_existing(self):
        p1 = self.pr.recognize("pattern_x", "desc", 0.5)
        p2 = self.pr.recognize("pattern_x", "desc", 0.5)
        assert p1 is p2  # same object
        assert p2.support_count == 2

    def test_get_pattern(self):
        p = self.pr.recognize("test", "desc")
        assert self.pr.get_pattern(p.pattern_id) is p
        assert self.pr.get_pattern("bad") is None

    def test_get_by_source(self):
        self.pr.recognize("p1", source="src_a")
        self.pr.recognize("p2", source="src_b")
        assert len(self.pr.get_patterns_by_source("src_a")) == 1

    def test_get_all_patterns(self):
        self.pr.recognize("p1")
        self.pr.recognize("p2")
        assert len(self.pr.get_all_patterns()) == 2

    def test_analyze_events_empty(self):
        assert len(self.pr.analyze_events([])) == 0

    def test_analyze_events_high_success(self):
        events = [LearningEvent("m", "t", 0.9, success=True) for _ in range(20)]
        patterns = self.pr.analyze_events(events)
        assert any(p.pattern_name == "high_success_rate" for p in patterns)

    def test_analyze_events_low_success(self):
        events = [LearningEvent("m", "t", 0.1, success=False) for _ in range(20)]
        patterns = self.pr.analyze_events(events)
        assert any(p.pattern_name == "low_success_rate" for p in patterns)

    def test_analyze_events_high_performance(self):
        events = [LearningEvent("m", "t", 0.9, success=True) for _ in range(5)]
        patterns = self.pr.analyze_events(events)
        assert any(p.pattern_name == "high_performance" for p in patterns)

    def test_get_stats(self):
        self.pr.recognize("p1", confidence=0.8)
        self.pr.recognize("p2", confidence=0.6)
        stats = self.pr.get_stats()
        assert stats["total_patterns"] == 2
        assert stats["avg_confidence"] == 0.7


# ══════════════════════════════════════════════════════════════════════
# KnowledgeBaseManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestKnowledgeBaseManager:
    def setup_method(self):
        self.kb = KnowledgeBaseManager()

    def test_add_entry(self):
        e = self.kb.add_entry("topic", "content", "source", 0.8, ["tag"])
        assert e.entry_id.startswith("ke_")
        assert e.topic == "topic"

    def test_get_entry(self):
        e = self.kb.add_entry("t", "c")
        assert self.kb.get_entry(e.entry_id) is e
        assert self.kb.get_entry("bad") is None

    def test_search(self):
        self.kb.add_entry("best_pins", "Vertical images are best", tags=["pins"])
        self.kb.add_entry("seo_tips", "Use keywords", tags=["seo"])
        results = self.kb.search("vertical")
        assert len(results) == 1
        results2 = self.kb.search("pins")
        assert len(results2) == 1  # matches tag

    def test_search_by_tag(self):
        self.kb.add_entry("a", "content a", tags=["tag1"])
        self.kb.add_entry("b", "content b", tags=["tag2"])
        assert len(self.kb.search_by_tag("tag1")) == 1

    def test_update_entry(self):
        e = self.kb.add_entry("t", "old")
        assert self.kb.update_entry(e.entry_id, content="new", confidence=0.9) is True
        assert e.content == "new"
        assert e.confidence == 0.9
        assert self.kb.update_entry("bad") is False

    def test_remove_entry(self):
        e = self.kb.add_entry("t", "c")
        assert self.kb.remove_entry(e.entry_id) is True
        assert self.kb.remove_entry("bad") is False

    def test_get_all_entries(self):
        self.kb.add_entry("a", "c")
        self.kb.add_entry("b", "c")
        assert len(self.kb.get_all_entries()) == 2

    def test_get_stats(self):
        self.kb.add_entry("a", "c", confidence=0.9)
        self.kb.add_entry("b", "c", confidence=0.7)
        stats = self.kb.get_stats()
        assert stats["total_entries"] == 2
        assert stats["avg_confidence"] == 0.8


# ══════════════════════════════════════════════════════════════════════
# RecommendationEngine Tests
# ══════════════════════════════════════════════════════════════════════

class TestRecommendationEngine:
    def setup_method(self):
        self.re = RecommendationEngine()

    def test_add_recommendation(self):
        r = self.re.add_recommendation("Optimize", "Do it", "seo", "high")
        assert r.recommendation_id.startswith("rec_")

    def test_get_recommendation(self):
        r = self.re.add_recommendation("T", "D")
        assert self.re.get_recommendation(r.recommendation_id) is r

    def test_get_pending(self):
        self.re.add_recommendation("T1", "D1")
        self.re.add_recommendation("T2", "D2")
        assert len(self.re.get_pending()) == 2

    def test_get_by_category(self):
        self.re.add_recommendation("A", "D", "seo")
        self.re.add_recommendation("B", "D", "pins")
        assert len(self.re.get_by_category("seo")) == 1

    def test_mark_implemented(self):
        r = self.re.add_recommendation("T", "D")
        assert self.re.mark_implemented(r.recommendation_id) is True
        assert r.status == "implemented"
        assert r.implemented_at is not None
        assert self.re.mark_implemented("bad") is False

    def test_dismiss(self):
        r = self.re.add_recommendation("T", "D")
        assert self.re.dismiss(r.recommendation_id) is True
        assert r.status == "dismissed"
        assert self.re.dismiss("bad") is False

    def test_generate_from_mistakes(self):
        mistakes = [MistakeRecord("pins", "fail", "high", "Failed")]
        recs = self.re.generate_from_mistakes(mistakes)
        assert len(recs) == 1
        assert "Fix" in recs[0].title

    def test_generate_from_mistakes_resolved(self):
        m = MistakeRecord("pins", "fail")
        m.resolved = True
        recs = self.re.generate_from_mistakes([m])
        assert len(recs) == 0

    def test_generate_from_patterns(self):
        patterns = [LearnedPattern("low_success_rate", "Low rate", 0.8)]
        recs = self.re.generate_from_patterns(patterns)
        assert len(recs) >= 1

    def test_get_all_recommendations(self):
        self.re.add_recommendation("A", "D")
        self.re.add_recommendation("B", "D")
        assert len(self.re.get_all_recommendations()) == 2

    def test_get_stats(self):
        self.re.add_recommendation("A", "D", priority="high")
        self.re.add_recommendation("B", "D", priority="low")
        stats = self.re.get_stats()
        assert stats["total"] == 2
        assert stats["by_priority"]["high"] == 1


# ══════════════════════════════════════════════════════════════════════
# SelfImprovementManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestSelfImprovementManager:
    def setup_method(self):
        self.si = SelfImprovementManager()

    def test_apply_improvement_no_handler(self):
        act = self.si.apply_improvement("optimize", "pins", "Test")
        assert act.status == "simulated"
        assert "No handler" in act.result["note"]

    def test_apply_improvement_with_handler(self):
        def handler(params):
            return {"optimized": True}
        self.si.register_handler("optimize", handler)
        act = self.si.apply_improvement("optimize", "pins", "Test", {"key": "val"})
        assert act.status == "completed"
        assert act.result["optimized"] is True

    def test_apply_improvement_handler_error(self):
        def handler(params):
            raise ValueError("error!")
        self.si.register_handler("fail", handler)
        act = self.si.apply_improvement("fail")
        assert act.status == "failed"

    def test_apply_recommendations(self):
        rec1 = Recommendation("A", "D")
        rec2 = Recommendation("B", "D")
        rec1.status = "pending"
        rec2.status = "pending"
        count = self.si.apply_recommendations([rec1, rec2])
        assert count == 2
        assert rec1.status == "implemented"

    def test_get_actions(self):
        self.si.apply_improvement("test", "m", "desc")
        assert len(self.si.get_actions()) == 1

    def test_get_actions_by_status(self):
        self.si.apply_improvement("t1")
        actions = self.si.get_actions(status="simulated")
        assert len(actions) == 1

    def test_get_stats(self):
        self.si.apply_improvement("t1")
        self.si.apply_improvement("t2")
        stats = self.si.get_stats()
        assert stats["total_actions"] == 2


# ══════════════════════════════════════════════════════════════════════
# VersionManager Tests
# ══════════════════════════════════════════════════════════════════════

class TestVersionManager:
    def setup_method(self):
        self.vm = VersionManager()

    def test_create_version(self):
        sv = self.vm.create_version("Initial release", 100.0, {"key": "val"})
        assert sv.version.startswith("1.")

    def test_get_current_version(self):
        v1 = self.vm.create_version("v1")
        assert self.vm.get_current_version() == v1.version

    def test_get_version(self):
        sv = self.vm.create_version("test")
        assert self.vm.get_version(sv.version) is sv
        assert self.vm.get_version("99.99.99") is None

    def test_get_all_versions(self):
        self.vm.create_version("v1")
        self.vm.create_version("v2")
        assert len(self.vm.get_all_versions()) == 2

    def test_rollback(self):
        sv = self.vm.create_version("v1", config_snapshot={"setting": 1})
        config = self.vm.rollback(sv.version)
        assert config is not None
        assert config["setting"] == 1

    def test_rollback_nonexistent(self):
        assert self.vm.rollback("99.99") is None

    def test_get_stats(self):
        self.vm.create_version("v1")
        stats = self.vm.get_stats()
        assert stats["total_versions"] == 1


# ══════════════════════════════════════════════════════════════════════
# UniversalMemoryConnector Tests
# ══════════════════════════════════════════════════════════════════════

class TestUniversalMemoryConnector:
    def setup_method(self):
        self.mem = UniversalMemoryConnector()

    def test_store(self):
        mr = self.mem.store("key1", "value1", "namespace1")
        assert mr.memory_id.startswith("mem_")
        assert mr.key == "key1"

    def test_retrieve(self):
        self.mem.store("k", "v", "ns")
        assert self.mem.retrieve("k", "ns") == "v"
        assert self.mem.retrieve("k", "other") is None

    def test_retrieve_expired(self):
        self.mem.store("k", "v", "ns", ttl=0.001)
        time.sleep(0.01)
        assert self.mem.retrieve("k", "ns") is None

    def test_remember(self):
        self.mem.store("k", "v", "ns")
        rec = self.mem.remember("k", "ns")
        assert rec is not None
        assert rec.value == "v"

    def test_remember_expired(self):
        self.mem.store("k", "v", "ns", ttl=0.001)
        time.sleep(0.01)
        assert self.mem.remember("k", "ns") is None

    def test_forget(self):
        self.mem.store("k", "v", "ns")
        assert self.mem.forget("k", "ns") is True
        assert self.mem.forget("k", "ns") is False

    def test_clear_namespace(self):
        self.mem.store("k1", "v1", "ns1")
        self.mem.store("k2", "v2", "ns2")
        self.mem.store("k3", "v3", "ns1")
        assert self.mem.clear_namespace("ns1") == 2
        assert self.mem.clear_namespace("ns1") == 0

    def test_get_all_keys(self):
        self.mem.store("a", "1", "ns")
        self.mem.store("b", "2", "ns")
        keys = self.mem.get_all_keys("ns")
        assert len(keys) == 2
        assert "a" in keys

    def test_get_stats(self):
        self.mem.store("a", "1", "ns1")
        self.mem.store("b", "2", "ns2")
        stats = self.mem.get_stats()
        assert stats["total_records"] == 2
        assert stats["namespaces"] == 2


# ══════════════════════════════════════════════════════════════════════
# LearningAPI Tests
# ══════════════════════════════════════════════════════════════════════

class TestLearningAPI:
    def setup_method(self):
        self.engine = LearningConnector()
        self.api = self.engine.api

    def test_get_status(self):
        status = self.api.get_status()
        assert "collector" in status
        assert "analyzer" in status
        assert "mistakes" in status
        assert "strategy" in status
        assert "prompts" in status
        assert "decisions" in status
        assert "patterns" in status
        assert "knowledge" in status
        assert "recommendations" in status
        assert "improvements" in status
        assert "versions" in status
        assert "memory" in status

    def test_get_learning_summary(self):
        summary = self.api.get_learning_summary()
        assert "total_events" in summary
        assert "success_rate" in summary
        assert "current_version" in summary
        assert summary["current_version"] == "1.0.0"

    def test_run_learning_cycle(self):
        result = self.api.run_learning_cycle()
        assert "cycle" in result
        assert "success_rate" in result


# ══════════════════════════════════════════════════════════════════════
# LearningConnector Tests
# ══════════════════════════════════════════════════════════════════════

class TestLearningConnector:
    def setup_method(self):
        self.engine = LearningConnector()

    def test_initialization(self):
        assert self.engine.collector is not None
        assert self.engine.analyzer is not None
        assert self.engine.mistakes is not None
        assert self.engine.strategy is not None
        assert self.engine.prompts is not None
        assert self.engine.decisions is not None
        assert self.engine.patterns is not None
        assert self.engine.knowledge is not None
        assert self.engine.recommendations is not None
        assert self.engine.improvements is not None
        assert self.engine.versions is not None
        assert self.engine.memory is not None
        assert self.engine.api is not None

    def test_initial_knowledge(self):
        entries = self.engine.knowledge.get_all_entries()
        assert len(entries) >= 5

    def test_initial_decision_rules(self):
        self.engine.decisions.decide("generate more pins")
        self.engine.decisions.decide("scale winning content")
        decisions = self.engine.decisions.get_decisions()
        assert len(decisions) >= 2

    def test_collect_event(self):
        self.engine.collect_event("pins", "publish", 0.95, {"id": "123"}, True)
        stats = self.engine.collector.get_stats()
        assert stats["total_events"] == 1

    def test_record_metric(self):
        self.engine.record_metric("ctr", "pins", 3.5, 5.0)
        assert len(self.engine.analyzer.get_metrics()) == 1

    def test_run_learning_cycle(self):
        self.engine.collect_event("pins", "publish", 0.9, success=True)
        self.engine.collect_event("pins", "publish", 0.2, success=False)
        self.engine.collect_event("seo", "optimize", 0.8, success=True)
        result = self.engine.run_learning_cycle()
        assert result["cycle"] == 1
        assert result["events_analyzed"] >= 3
        assert result["mistakes_detected"] >= 1  # low score event

    def test_run_learning_cycle_multiple(self):
        for i in range(3):
            self.engine.collect_event("m", "t", 0.9, success=True)
        r1 = self.engine.run_learning_cycle()
        assert r1["cycle"] == 1
        r2 = self.engine.run_learning_cycle()
        assert r2["cycle"] == 2

    def test_get_summary(self):
        self.engine.collect_event("m", "t", 0.9)
        summary = self.engine.get_summary()
        assert isinstance(summary, LearningSummary)
        assert summary.total_events >= 1

    def test_get_status(self):
        status = self.engine.get_status()
        assert "module" in status
        assert "Learning Connector" in status["module"]
        assert "summary" in status
        assert status["summary"]["total_events"] == 0  # initially

    def test_start_stop_learning_cycle(self):
        r = self.engine.start_learning_cycle()
        assert r["status"] == "started"
        r = self.engine.stop_learning_cycle()
        assert r["status"] == "stopped"


# ══════════════════════════════════════════════════════════════════════
# Exception Classes
# ══════════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_base(self):
        with pytest.raises(LearningError):
            raise LearningError()

    def test_knowledge(self):
        with pytest.raises(KnowledgeError):
            raise KnowledgeError()

    def test_pattern(self):
        with pytest.raises(PatternRecognitionError):
            raise PatternRecognitionError()

    def test_memory(self):
        with pytest.raises(MemoryError):
            raise MemoryError()

    def test_version(self):
        with pytest.raises(VersionError):
            raise VersionError()

    def test_recommendation(self):
        with pytest.raises(RecommendationError):
            raise RecommendationError()

    def test_improvement(self):
        with pytest.raises(ImprovementError):
            raise ImprovementError()

    def test_collection(self):
        with pytest.raises(CollectionError):
            raise CollectionError()

    def test_analysis(self):
        with pytest.raises(AnalysisError):
            raise AnalysisError()

    def test_decision(self):
        with pytest.raises(DecisionError):
            raise DecisionError()

    def test_strategy(self):
        with pytest.raises(StrategyError):
            raise StrategyError()


# ══════════════════════════════════════════════════════════════════════
# Singleton Tests
# ══════════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_connector(self):
        c1 = get_learning_connector()
        c2 = get_learning_connector()
        assert c1 is c2
