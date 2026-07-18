"""Tests for Layer 10 Module 7 — Knowledge & Research Intelligence Engine."""
from layers.layer10_monetization.modules.knowledge_research.research_manager import (
    ResearchManager,
)
from layers.layer10_monetization.modules.knowledge_research.trend_discovery import (
    TrendDiscovery, TREND_CATEGORIES,
)
from layers.layer10_monetization.modules.knowledge_research.competitor_intelligence import (
    CompetitorIntelligence,
)
from layers.layer10_monetization.modules.knowledge_research.audience_intelligence import (
    AudienceIntelligence,
)
from layers.layer10_monetization.modules.knowledge_research.market_intelligence import (
    MarketIntelligence,
)
from layers.layer10_monetization.modules.knowledge_research.knowledge_graph import (
    KnowledgeGraph,
)
from layers.layer10_monetization.modules.knowledge_research.fact_verifier import (
    FactVerifier,
)
from layers.layer10_monetization.modules.knowledge_research.research_memory import (
    ResearchMemory,
)
from layers.layer10_monetization.modules.knowledge_research.research_metrics import ResearchMetrics
from layers.layer10_monetization.modules.knowledge_research.research_report import (
    ResearchReportGenerator,
)
from layers.layer10_monetization.modules.knowledge_research.source_manager import (
    SourceManager,
)
from layers.layer10_monetization.modules.knowledge_research.research_scheduler import (
    ResearchScheduler,
)
from layers.layer10_monetization.modules.knowledge_research.research_validator import (
    ResearchValidator,
)
from layers.layer10_monetization.modules.knowledge_research.research_orchestrator import (
    ResearchOrchestrator,
)
from layers.layer10_monetization.modules.knowledge_research.exceptions import (
    ResearchError,
    SourceUnavailableError,
    TrendDetectionError,
    VerificationError,
    KnowledgeError,
    MemoryError,
    ValidationError,
    ResearchTimeoutError,
)


# ─── ResearchManager Tests ──────────────────────────────────────
class TestResearchManager:
    def setup_method(self):
        self.manager = ResearchManager()

    def test_start_stop(self):
        assert self.manager.start() is True
        assert self.manager._is_running is True
        assert self.manager.stop() is True
        assert self.manager._is_running is False

    def test_create_task(self):
        task = self.manager.create_task("AI trends", ["facebook", "linkedin"])
        assert task.task_id.startswith("rtask_")
        assert task.topic == "AI trends"
        assert task.platforms == ["facebook", "linkedin"]
        assert task.status == "pending"

    def test_execute_task(self):
        task = self.manager.create_task("ML trends")
        result = self.manager.execute_task(task.task_id)
        assert result is not None
        assert result.status == "completed"
        assert result.completed_at is not None
        assert "findings" in result.results

    def test_execute_task_not_found(self):
        result = self.manager.execute_task("rtask_99999")
        assert result is None

    def test_get_pending_tasks(self):
        self.manager.create_task("Task A")
        self.manager.create_task("Task B")
        pending = self.manager.get_pending_tasks()
        assert len(pending) == 2

    def test_get_completed_tasks(self):
        task = self.manager.create_task("Task A")
        self.manager.execute_task(task.task_id)
        completed = self.manager.get_completed_tasks()
        assert len(completed) == 1

    def test_research_shorthand(self):
        results = self.manager.research("quantum computing", ["x"])
        assert "topic" in results
        assert results["topic"] == "quantum computing"

    def test_priority(self):
        task = self.manager.create_task("High priority", priority=5)
        assert task.priority == 5

    def test_stats(self):
        self.manager.create_task("A")
        stats = self.manager.get_stats()
        assert stats["total_tasks"] == 1
        assert stats["completed"] == 0
        assert stats["pending"] == 1
        assert stats["running"] is False

    def test_events_tracked(self):
        self.manager.start()
        self.manager.stop()
        assert len(self.manager._events) == 2
        assert self.manager._events[0]["event"] == "research_started"
        assert self.manager._events[1]["event"] == "research_stopped"

    def test_default_platforms(self):
        task = self.manager.create_task("General topic")
        assert task.platforms == ["universal"]

    def test_task_to_dict(self):
        task = self.manager.create_task("Test")
        assert task.task_id.startswith("rtask_")
        assert task.topic == "Test"
        assert task.status == "pending"


# ─── TrendDiscovery Tests ──────────────────────────────────────
class TestTrendDiscovery:
    def setup_method(self):
        self.td = TrendDiscovery()

    def test_discover(self):
        trends = self.td.discover("AI", "facebook")
        assert len(trends) == 1
        assert trends[0].topic == "AI"
        assert trends[0].platform == "facebook"
        assert trends[0].trend_score > 0

    def test_discover_default_topic(self):
        trends = self.td.discover(platform="linkedin")
        assert len(trends) == 1
        assert "linkedin" in trends[0].topic

    def test_discover_batch(self):
        trends = self.td.discover_batch(["AI", "ML", "DL"], "x")
        assert len(trends) == 3
        assert all(t.platform == "x" for t in trends)

    def test_get_top_trends(self):
        self.td.discover("Alpha", "facebook")
        self.td.discover("Beta", "facebook")
        top = self.td.get_top_trends(1)
        assert len(top) == 1

    def test_get_top_trends_filtered(self):
        self.td.discover("Topic A", "facebook")
        self.td.discover("Topic B", "linkedin")
        fb_trends = self.td.get_top_trends(platform="facebook")
        assert all(t.platform == "facebook" for t in fb_trends)

    def test_get_by_category(self):
        self.td.discover("AI", category="hashtag")
        self.td.discover("ML", category="topic")
        hashtags = self.td.get_by_category("hashtag")
        assert len(hashtags) == 1

    def test_category_validation(self):
        trends = self.td.discover("Test", category="invalid_cat")
        assert trends[0].category == "topic"

    def test_trend_score_range(self):
        trends = self.td.discover("Anything")
        assert 0 < trends[0].trend_score <= 1.0

    def test_growth_rate(self):
        trends = self.td.discover("Viral topic")
        assert trends[0].growth_rate >= 0

    def test_stats(self):
        self.td.discover("A", "facebook")
        self.td.discover("B", "linkedin")
        stats = self.td.get_stats()
        assert stats["total"] == 2
        assert "facebook" in stats["by_platform"]

    def test_trend_categories_constant(self):
        assert "topic" in TREND_CATEGORIES
        assert "hashtag" in TREND_CATEGORIES
        assert "seasonal" in TREND_CATEGORIES

    def test_trend_to_dict(self):
        trends = self.td.discover("AI", "x")
        d = trends[0].to_dict()
        assert "trend_id" in d
        assert "score" in d
        assert "growth" in d


# ─── CompetitorIntelligence Tests ──────────────────────────────
class TestCompetitorIntelligence:
    def setup_method(self):
        self.ci = CompetitorIntelligence()

    def test_add_competitor(self):
        comp = self.ci.add_competitor("RivalCorp", "facebook")
        assert comp.profile_id.startswith("comp_")
        assert comp.name == "RivalCorp"
        assert comp.platform == "facebook"

    def test_analyze(self):
        comp = self.ci.add_competitor("Rival", "linkedin")
        analyzed = self.ci.analyze(comp.profile_id, {
            "posting_frequency": 5.0,
            "engagement_rate": 3.2,
            "content_types": ["article", "post"],
        })
        assert analyzed is not None
        assert analyzed.posting_frequency == 5.0
        assert analyzed.engagement_rate == 3.2
        assert "article" in analyzed.content_types

    def test_analyze_not_found(self):
        result = self.ci.analyze("comp_99999")
        assert result is None

    def test_analyze_no_data(self):
        comp = self.ci.add_competitor("Empty", "x")
        analyzed = self.ci.analyze(comp.profile_id)
        assert analyzed is not None

    def test_compare(self):
        self.ci.add_competitor("A", "facebook")
        self.ci.add_competitor("B", "facebook")
        comparisons = self.ci.compare()
        assert len(comparisons) >= 1

    def test_get_stats(self):
        self.ci.add_competitor("A", "facebook")
        stats = self.ci.get_stats()
        assert stats["total_competitors"] == 1

    def test_competitor_to_dict(self):
        comp = self.ci.add_competitor("TestCo", "x")
        d = comp.to_dict()
        assert "profile_id" in d
        assert "engagement_rate" in d

    def test_analyses_tracked(self):
        comp = self.ci.add_competitor("Tracked", "linkedin")
        self.ci.analyze(comp.profile_id, {"engagement_rate": 1.0})
        assert len(self.ci._analyses) == 1


# ─── AudienceIntelligence Tests ─────────────────────────────────
class TestAudienceIntelligence:
    def setup_method(self):
        self.ai = AudienceIntelligence()

    def test_create_profile(self):
        profile = self.ai.create_profile("facebook")
        assert profile.profile_id.startswith("aud_")
        assert profile.platform == "facebook"

    def test_update_profile(self):
        profile = self.ai.create_profile("linkedin")
        updated = self.ai.update_profile(profile.profile_id, {
            "interests": ["AI", "ML"],
            "languages": ["en", "ur"],
        })
        assert updated is not None
        assert "AI" in updated.interests
        assert "ur" in updated.languages

    def test_update_profile_not_found(self):
        result = self.ai.update_profile("aud_99999", {"interests": ["test"]})
        assert result is None

    def test_get_profile(self):
        self.ai.create_profile("x")
        profile = self.ai.get_profile("x")
        assert profile is not None
        assert profile.platform == "x"

    def test_get_profile_not_found(self):
        profile = self.ai.get_profile("unknown")
        assert profile is None

    def test_get_all_profiles(self):
        self.ai.create_profile("facebook")
        self.ai.create_profile("linkedin")
        all_profiles = self.ai.get_all_profiles()
        assert len(all_profiles) == 2

    def test_get_insights(self):
        self.ai._insights.append({"platform": "facebook", "data": "test"})
        insights = self.ai.get_insights("facebook")
        assert len(insights) == 1

    def test_get_insights_all(self):
        self.ai._insights.append({"platform": "facebook"})
        self.ai._insights.append({"platform": "linkedin"})
        all_insights = self.ai.get_insights()
        assert len(all_insights) == 2

    def test_stats(self):
        self.ai.create_profile("facebook")
        stats = self.ai.get_stats()
        assert stats["total_profiles"] == 1

    def test_profile_to_dict(self):
        profile = self.ai.create_profile("tiktok")
        d = profile.to_dict()
        assert "profile_id" in d
        assert "platform" in d

    def test_update_sets_timestamp(self):
        profile = self.ai.create_profile("reddit")
        old_time = profile.updated_at
        import time
        time.sleep(0.01)
        self.ai.update_profile(profile.profile_id, {"interests": ["gaming"]})
        assert profile.updated_at >= old_time


# ─── MarketIntelligence Tests ───────────────────────────────────
class TestMarketIntelligence:
    def setup_method(self):
        self.mi = MarketIntelligence()

    def test_analyze(self):
        insight = self.mi.analyze("industry", "facebook")
        assert insight.insight_id.startswith("mins_")
        assert insight.category == "industry"
        assert insight.platform == "facebook"
        assert insight.impact > 0

    def test_analyze_defaults(self):
        insight = self.mi.analyze()
        assert insight.platform == "universal"
        assert insight.category == "industry"

    def test_get_by_category(self):
        self.mi.analyze("niche", "facebook")
        self.mi.analyze("industry", "linkedin")
        niche = self.mi.get_by_category("niche")
        assert len(niche) == 1

    def test_get_by_platform(self):
        self.mi.analyze("industry", "facebook")
        self.mi.analyze("industry", "linkedin")
        fb = self.mi.get_by_platform("facebook")
        assert len(fb) == 1

    def test_get_top_insights(self):
        for _ in range(5):
            self.mi.analyze("industry")
        top = self.mi.get_top_insights(3)
        assert len(top) == 3
        assert top[0].impact >= top[-1].impact

    def test_stats(self):
        self.mi.analyze("niche")
        self.mi.analyze("industry")
        stats = self.mi.get_stats()
        assert stats["total"] == 2
        assert "niche" in stats["by_category"]

    def test_insight_to_dict(self):
        insight = self.mi.analyze("trend", "x")
        d = insight.to_dict()
        assert "insight_id" in d
        assert "impact" in d
        assert "confidence" in d

    def test_multiple_platforms(self):
        platforms = ["facebook", "linkedin", "x", "instagram"]
        for p in platforms:
            self.mi.analyze("industry", p)
        stats = self.mi.get_stats()
        assert stats["total"] == 4


# ─── KnowledgeGraph Tests ──────────────────────────────────────
class TestKnowledgeGraph:
    def setup_method(self):
        self.kg = KnowledgeGraph()

    def test_add_entity(self):
        entity = self.kg.add_entity("Artificial Intelligence", "topic")
        assert entity.entity_id.startswith("ke_")
        assert entity.name == "Artificial Intelligence"
        assert entity.entity_type == "topic"

    def test_get_entity(self):
        self.kg.add_entity("Python", "language")
        entity = self.kg.get_entity("Python")
        assert entity is not None
        assert entity.name == "Python"

    def test_get_entity_case_insensitive(self):
        self.kg.add_entity("Machine Learning", "topic")
        entity = self.kg.get_entity("machine learning")
        assert entity is not None

    def test_add_relationship(self):
        self.kg.add_entity("AI", "topic")
        self.kg.add_entity("ML", "topic")
        result = self.kg.add_relationship("AI", "ML", "contains")
        assert result is True

    def test_add_relationship_missing_entity(self):
        result = self.kg.add_relationship("Missing1", "Missing2", "rel")
        assert result is False

    def test_relationship_on_entity(self):
        self.kg.add_entity("A", "topic")
        self.kg.add_entity("B", "topic")
        self.kg.add_relationship("A", "B", "related_to")
        entity = self.kg.get_entity("A")
        assert len(entity.relationships) == 1

    def test_search(self):
        self.kg.add_entity("Python", "language")
        self.kg.add_entity("Python3", "version")
        results = self.kg.search(query="Python")
        assert len(results) == 2

    def test_search_by_type(self):
        self.kg.add_entity("Python", "language")
        self.kg.add_entity("Java", "language")
        self.kg.add_entity("React", "framework")
        results = self.kg.search(entity_type="language")
        assert len(results) == 2

    def test_search_min_confidence(self):
        entity = self.kg.add_entity("HighConf", "topic")
        entity.confidence = 0.9
        entity2 = self.kg.add_entity("LowConf", "topic")
        entity2.confidence = 0.1
        results = self.kg.search(min_confidence=0.5)
        assert len(results) == 1
        assert results[0].name == "HighConf"

    def test_exists(self):
        self.kg.add_entity("React", "framework")
        assert self.kg.exists("React") is True
        assert self.kg.exists("Vue") is False

    def test_stats(self):
        self.kg.add_entity("A", "topic")
        self.kg.add_entity("B", "topic")
        self.kg.add_entity("C", "trend")
        stats = self.kg.get_stats()
        assert stats["total_entities"] == 3
        assert stats["by_type"]["topic"] == 2

    def test_entity_to_dict(self):
        entity = self.kg.add_entity("Test", "concept")
        d = entity.to_dict()
        assert "entity_id" in d
        assert "relationships" in d


# ─── FactVerifier Tests ─────────────────────────────────────────
class TestFactVerifier:
    def setup_method(self):
        self.fv = FactVerifier()

    def test_verify(self):
        result = self.fv.verify("Python is a programming language")
        assert result.result_id.startswith("fvr_")
        assert result.claim == "Python is a programming language"
        assert result.confidence > 0
        assert result.status in ("verified", "uncertain")

    def test_verify_with_context(self):
        result = self.fv.verify("Test claim", {"source": "wiki"})
        assert result is not None

    def test_verify_batch(self):
        claims = ["Claim A", "Claim B", "Claim C"]
        results = self.fv.verify_batch(claims)
        assert len(results) == 3
        assert all(r.claim == c for r, c in zip(results, claims))

    def test_get_verified(self):
        for i in range(5):
            self.fv.verify(f"Claim {i}")
        verified = self.fv.get_verified(min_confidence=0.0)
        assert len(verified) > 0

    def test_get_unverified(self):
        self.fv.verify("Some uncertain claim")
        unverified = self.fv.get_unverified()
        assert isinstance(unverified, list)

    def test_stats(self):
        self.fv.verify("A")
        self.fv.verify("B")
        stats = self.fv.get_stats()
        assert stats["total"] == 2

    def test_result_to_dict(self):
        result = self.fv.verify("Test")
        d = result.to_dict()
        assert "result_id" in d
        assert "status" in d
        assert "confidence" in d

    def test_multiple_verifications(self):
        for _ in range(10):
            self.fv.verify("Repeated claim")
        assert len(self.fv._results) == 10


# ─── ResearchMemory Tests ──────────────────────────────────────
class TestResearchMemory:
    def setup_method(self):
        self.mem = ResearchMemory()

    def test_store(self):
        entry = self.mem.store("AI trends", {"count": 5}, source="api", confidence=0.8)
        assert entry.entry_id.startswith("rmem_")
        assert entry.query == "AI trends"
        assert entry.confidence == 0.8
        assert entry.source == "api"

    def test_store_with_tags(self):
        entry = self.mem.store("Query", {"data": 1}, tags=["ai", "trending"])
        assert "ai" in entry.tags
        assert "trending" in entry.tags

    def test_get_cached(self):
        self.mem.store("AI topic", {"data": 1})
        cached = self.mem.get_cached("AI topic")
        assert cached is not None
        assert cached.query == "AI topic"
        assert cached.access_count == 1

    def test_get_cached_case_insensitive(self):
        self.mem.store("Machine Learning", {"data": 1})
        cached = self.mem.get_cached("machine learning")
        assert cached is not None

    def test_get_cached_not_found(self):
        cached = self.mem.get_cached("Nonexistent")
        assert cached is None

    def test_get_cached_increments_access(self):
        self.mem.store("Test", {"data": 1})
        self.mem.get_cached("Test")
        self.mem.get_cached("Test")
        entry = self.mem.get_cached("Test")
        assert entry.access_count == 3

    def test_search_by_query(self):
        self.mem.store("AI trends", {"a": 1})
        self.mem.store("ML news", {"b": 2})
        results = self.mem.search(query="AI")
        assert len(results) == 1

    def test_search_by_tag(self):
        self.mem.store("Q1", {"a": 1}, tags=["ai"])
        self.mem.store("Q2", {"b": 2}, tags=["ml"])
        results = self.mem.search(tag="ai")
        assert len(results) == 1

    def test_search_min_confidence(self):
        self.mem.store("High conf", {"a": 1}, confidence=0.9)
        self.mem.store("Low conf", {"b": 2}, confidence=0.1)
        results = self.mem.search(min_confidence=0.5)
        assert len(results) == 1

    def test_search_limit(self):
        for i in range(20):
            self.mem.store(f"Query {i}", {"i": i})
        results = self.mem.search(limit=5)
        assert len(results) == 5

    def test_max_entries(self):
        mem = ResearchMemory(max_entries=3)
        for i in range(5):
            mem.store(f"Query {i}", {"i": i})
        assert len(mem._entries) == 3

    def test_stats(self):
        self.mem.store("A", {"a": 1}, confidence=0.8)
        self.mem.store("B", {"b": 2}, confidence=0.6)
        stats = self.mem.get_stats()
        assert stats["total"] == 2
        assert stats["avg_confidence"] > 0


# ─── ResearchMetrics Tests ─────────────────────────────────────
class TestResearchMetrics:
    def setup_method(self):
        self.metrics = ResearchMetrics()

    def test_record_research_success(self):
        self.metrics.record_research(success=True, duration_ms=150.0, accuracy=0.9, api_calls=3)
        assert self.metrics.get_success_rate() == 1.0
        assert self.metrics.get_avg_duration() == 150.0

    def test_record_research_failure(self):
        self.metrics.record_research(success=False, duration_ms=50.0)
        assert self.metrics.get_success_rate() == 0.0

    def test_success_rate_mixed(self):
        self.metrics.record_research(success=True)
        self.metrics.record_research(success=True)
        self.metrics.record_research(success=False)
        assert self.metrics.get_success_rate() == round(2 / 3, 3)

    def test_avg_duration(self):
        self.metrics.record_research(success=True, duration_ms=100.0)
        self.metrics.record_research(success=True, duration_ms=200.0)
        assert self.metrics.get_avg_duration() == 150.0

    def test_avg_duration_empty(self):
        assert self.metrics.get_avg_duration() == 0.0

    def test_accuracy(self):
        self.metrics.record_research(success=True, accuracy=0.8)
        self.metrics.record_research(success=True, accuracy=0.6)
        assert self.metrics.get_accuracy() == 0.7

    def test_accuracy_empty(self):
        assert self.metrics.get_accuracy() == 0.0

    def test_cache_hit_rate(self):
        self.metrics.record_research(success=True, cache_hit=True)
        self.metrics.record_research(success=True, cache_hit=False)
        assert self.metrics.get_cache_hit_rate() == 0.5

    def test_summary(self):
        self.metrics.record_research(success=True, duration_ms=100, accuracy=0.9, api_calls=2)
        summary = self.metrics.get_summary()
        assert summary["total_research"] == 1
        assert summary["successful"] == 1
        assert summary["api_calls"] == 2

    def test_reset(self):
        self.metrics.record_research(success=True)
        self.metrics.reset()
        assert self.metrics.get_success_rate() == 0.0
        assert self.metrics._total_research == 0


# ─── ResearchReportGenerator Tests ─────────────────────────────
class TestResearchReportGenerator:
    def setup_method(self):
        self.rg = ResearchReportGenerator()

    def test_generate(self):
        report = self.rg.generate("daily", {"key": "value"})
        assert report.report_id.startswith("rrpt_")
        assert report.report_type == "daily"
        assert report.data["key"] == "value"

    def test_generate_no_data(self):
        report = self.rg.generate("weekly")
        assert report.data == {}

    def test_add_recommendation(self):
        report = self.rg.generate("monthly")
        report.add_recommendation("Increase posting frequency")
        report.add_recommendation("Use more hashtags")
        assert len(report.recommendations) == 2

    def test_get_summary(self):
        report = self.rg.generate("daily")
        report.add_recommendation("Rec 1")
        summary = report.get_summary()
        assert summary["recommendation_count"] == 1
        assert summary["report_type"] == "daily"

    def test_export_dict(self):
        report = self.rg.generate("daily", {"topic": "AI"})
        report.add_recommendation("Rec 1")
        exported = report.export_dict()
        assert "data" in exported
        assert "recommendations" in exported
        assert exported["recommendations"] == ["Rec 1"]

    def test_get_recent(self):
        for i in range(5):
            self.rg.generate(f"report_{i}")
        recent = self.rg.get_recent(3)
        assert len(recent) == 3

    def test_get_recent_fewer_than_available(self):
        self.rg.generate("daily")
        recent = self.rg.get_recent(10)
        assert len(recent) == 1

    def test_stats(self):
        self.rg.generate("daily")
        self.rg.generate("weekly")
        stats = self.rg.get_stats()
        assert stats["total"] == 2


# ─── SourceManager Tests ────────────────────────────────────────
class TestSourceManager:
    def setup_method(self):
        self.sm = SourceManager()

    def test_add_source(self):
        source = self.sm.add_source("NewsAPI", "api", trust_score=0.9)
        assert source.source_id.startswith("src_")
        assert source.name == "NewsAPI"
        assert source.trust_score == 0.9

    def test_get_source(self):
        source = self.sm.add_source("RSS Feed", "rss")
        retrieved = self.sm.get_source(source.source_id)
        assert retrieved is not None
        assert retrieved.name == "RSS Feed"

    def test_get_source_not_found(self):
        retrieved = self.sm.get_source("src_99999")
        assert retrieved is None

    def test_get_by_type(self):
        self.sm.add_source("API 1", "api")
        self.sm.add_source("API 2", "api")
        self.sm.add_source("RSS 1", "rss")
        apis = self.sm.get_by_type("api")
        assert len(apis) == 2

    def test_get_trusted(self):
        self.sm.add_source("Trusted", "api", trust_score=0.9)
        self.sm.add_source("Untrusted", "api", trust_score=0.2)
        trusted = self.sm.get_trusted(min_trust=0.5)
        assert len(trusted) == 1
        assert trusted[0].name == "Trusted"

    def test_disabled_source_excluded(self):
        source = self.sm.add_source("Disabled", "api", trust_score=0.9)
        source.enabled = False
        trusted = self.sm.get_trusted(min_trust=0.0)
        assert len(trusted) == 0

    def test_get_all(self):
        self.sm.add_source("A", "api")
        self.sm.add_source("B", "rss")
        all_sources = self.sm.get_all()
        assert len(all_sources) == 2

    def test_stats(self):
        self.sm.add_source("A", "api")
        self.sm.add_source("B", "api")
        self.sm.add_source("C", "rss")
        stats = self.sm.get_stats()
        assert stats["total"] == 3
        assert stats["by_type"]["api"] == 2

    def test_source_to_dict(self):
        source = self.sm.add_source("Test", "web", trust_score=0.75)
        d = source.to_dict()
        assert "source_id" in d
        assert "trust" in d


# ─── ResearchScheduler Tests ────────────────────────────────────
class TestResearchScheduler:
    def setup_method(self):
        self.rs = ResearchScheduler()

    def test_schedule(self):
        job = self.rs.schedule("Daily AI scan", "daily", query="AI trends")
        assert job.job_id.startswith("srjob_")
        assert job.name == "Daily AI scan"
        assert job.schedule_type == "daily"
        assert job.query == "AI trends"

    def test_schedule_invalid_type(self):
        job = self.rs.schedule("Bad", "invalid_type")
        assert job.schedule_type == "daily"

    def test_get_job(self):
        job = self.rs.schedule("Test", "weekly")
        retrieved = self.rs.get_job(job.job_id)
        assert retrieved is not None
        assert retrieved.name == "Test"

    def test_get_job_not_found(self):
        retrieved = self.rs.get_job("srjob_99999")
        assert retrieved is None

    def test_get_by_type(self):
        self.rs.schedule("Daily 1", "daily")
        self.rs.schedule("Daily 2", "daily")
        self.rs.schedule("Weekly 1", "weekly")
        dailies = self.rs.get_by_type("daily")
        assert len(dailies) == 2

    def test_get_enabled(self):
        job = self.rs.schedule("Enabled Job", "daily")
        self.rs.schedule("Disabled Job", "weekly")
        job.enabled = False
        enabled = self.rs.get_enabled()
        assert len(enabled) == 1

    def test_get_all(self):
        self.rs.schedule("A", "daily")
        self.rs.schedule("B", "weekly")
        all_jobs = self.rs.get_all()
        assert len(all_jobs) == 2

    def test_stats(self):
        self.rs.schedule("A", "daily")
        self.rs.schedule("B", "weekly")
        self.rs.schedule("C", "daily")
        stats = self.rs.get_stats()
        assert stats["total"] == 3
        assert stats["by_type"]["daily"] == 2

    def test_job_to_dict(self):
        job = self.rs.schedule("Test", "monthly")
        d = job.to_dict()
        assert "job_id" in d
        assert "schedule_type" in d
        assert "enabled" in d

    def test_platforms(self):
        job = self.rs.schedule("Test", "daily", platforms=["facebook", "x"])
        assert job.platforms == ["facebook", "x"]


# ─── ResearchValidator Tests ────────────────────────────────────
class TestResearchValidator:
    def setup_method(self):
        self.v = ResearchValidator()

    def test_valid_research(self):
        result = self.v.validate({"confidence": 0.8, "source_count": 3})
        assert result.is_valid is True
        assert result.score > 0

    def test_low_confidence(self):
        result = self.v.validate({"confidence": 0.1, "source_count": 1})
        assert result.is_valid is False
        assert result.score < 1.0
        assert len(result.issues) > 0

    def test_no_sources(self):
        result = self.v.validate({"confidence": 0.8, "source_count": 0})
        assert len(result.warnings) > 0

    def test_stale_data(self):
        result = self.v.validate({"confidence": 0.8, "source_count": 1, "freshness_hours": 200})
        assert any("Stale" in w for w in result.warnings)

    def test_fresh_data(self):
        result = self.v.validate({"confidence": 0.8, "source_count": 1, "freshness_hours": 12})
        assert not any("Stale" in w for w in result.warnings)

    def test_custom_min_confidence(self):
        v = ResearchValidator(min_confidence=0.7)
        result = v.validate({"confidence": 0.5, "source_count": 1})
        assert result.is_valid is False

    def test_stats(self):
        self.v.validate({"confidence": 0.8, "source_count": 1})
        self.v.validate({"confidence": 0.1, "source_count": 0})
        stats = self.v.get_stats()
        assert stats["total"] == 2
        assert stats["valid"] == 1

    def test_result_to_dict(self):
        result = self.v.validate({"confidence": 0.9, "source_count": 2})
        d = result.to_dict()
        assert "is_valid" in d
        assert "score" in d
        assert "issues" in d
        assert "warnings" in d

    def test_empty_data(self):
        result = self.v.validate({})
        assert result.is_valid is True
        assert len(result.warnings) > 0


# ─── ResearchOrchestrator Tests ─────────────────────────────────
class TestResearchOrchestrator:
    def setup_method(self):
        self.orch = ResearchOrchestrator()

    def test_research_basic(self):
        results = self.orch.research("AI Technology")
        assert results["topic"] == "AI Technology"
        assert "stages" in results
        assert results["from_cache"] is not True

    def test_research_stages(self):
        results = self.orch.research("Machine Learning", ["facebook"])
        stages = results["stages"]
        assert "trends" in stages
        assert "competitors" in stages
        assert "audience" in stages
        assert "market" in stages
        assert "knowledge" in stages
        assert "verification" in stages
        assert "validation" in stages

    def test_research_multi_platform(self):
        results = self.orch.research("Cloud Computing", ["facebook", "linkedin", "x"])
        stages = results["stages"]
        assert stages["competitors"]["count"] == 3
        assert stages["audience"]["profiles"] == 3

    def test_research_cache_hit(self):
        self.orch.research("AI Trends")
        results = self.orch.research("AI Trends")
        assert results.get("from_cache") is True
        assert "cache" in results["stages"]

    def test_health_check(self):
        health = self.orch.get_health()
        assert "trends" in health
        assert "competitors" in health
        assert "knowledge" in health
        assert "metrics" in health
        assert health["pipeline_runs"] >= 0

    def test_research_populates_knowledge_graph(self):
        self.orch.research("Python Language")
        assert self.orch.knowledge_graph.exists("Python Language")

    def test_research_populates_memory(self):
        self.orch.research("Test Topic")
        cached = self.orch.memory.get_cached("Test Topic")
        assert cached is not None

    def test_research_records_metrics(self):
        self.orch.research("Metrics Test")
        summary = self.orch.metrics.get_summary()
        assert summary["total_research"] >= 1

    def test_research_creates_validation(self):
        self.orch.research("Validation Test")
        stats = self.orch.validator.get_stats()
        assert stats["total"] >= 1

    def test_research_creates_report(self):
        self.orch.research("Report Test")
        recent = self.orch.report_generator.get_recent(1)
        assert len(recent) >= 1

    def test_research_default_platforms(self):
        results = self.orch.research("Default Platform Test")
        assert results["topic"] == "Default Platform Test"

    def test_research_with_context(self):
        results = self.orch.research("Context Test", context={"source": "manual"})
        assert "stages" in results


# ─── Exceptions Tests ──────────────────────────────────────────
class TestExceptions:
    def test_research_error_hierarchy(self):
        assert issubclass(SourceUnavailableError, ResearchError)
        assert issubclass(TrendDetectionError, ResearchError)
        assert issubclass(VerificationError, ResearchError)
        assert issubclass(KnowledgeError, ResearchError)
        assert issubclass(MemoryError, ResearchError)
        assert issubclass(ValidationError, ResearchError)
        assert issubclass(ResearchTimeoutError, ResearchError)

    def test_research_error_is_exception(self):
        assert issubclass(ResearchError, Exception)

    def test_exceptions_can_be_raised(self):
        try:
            raise SourceUnavailableError("Source down")
        except ResearchError as e:
            assert "Source down" in str(e)

    def test_exceptions_independent(self):
        exceptions = [
            SourceUnavailableError, TrendDetectionError, VerificationError,
            KnowledgeError, MemoryError, ValidationError, ResearchTimeoutError,
        ]
        for exc in exceptions:
            try:
                raise exc("test")
            except ResearchError:
                pass
