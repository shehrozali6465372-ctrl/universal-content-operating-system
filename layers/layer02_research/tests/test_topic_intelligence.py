"""
Tests for Topic Intelligence Module
Layer 2: Research Engine — Module 2

Run: python -m pytest layers/layer02_research/tests/test_topic_intelligence.py -v
"""

import json
import pytest
from datetime import datetime, timezone, timedelta

from layers.layer02_research.modules.topic_intelligence.topic_entry import TopicEntry
from layers.layer02_research.modules.topic_intelligence.topic_scorer import TopicScorer
from layers.layer02_research.modules.topic_intelligence.topic_categorizer import TopicCategorizer
from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager
from layers.layer02_research.modules.topic_intelligence.exceptions import (
    TopicNotFoundError, DuplicateTopicError, InvalidScoringError,
)


# ═══════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════

@pytest.fixture
def manager(tmp_path):
    return TopicIntelManager(storage_path=str(tmp_path / "topics.json"))


@pytest.fixture
def manager_with_topics(manager):
    """Manager pre-populated with diverse topics."""
    topics_data = [
        ("AI in Finance", "ai", "finance", 8.5, 7.0, 6.0, ["ai", "finance", "trading"]),
        ("Crypto Trading Tips", "crypto", "finance", 9.0, 6.0, 8.0, ["bitcoin", "trading", "crypto"]),
        ("Healthy Recipes", "cooking", "health", 7.0, 8.0, 4.0, ["recipe", "cooking", "healthy"]),
        ("Python Tutorial", "technology", "education", 6.5, 7.5, 5.0, ["python", "coding", "tutorial"]),
        ("Workout Routine", "fitness", "health", 8.0, 7.0, 5.0, ["workout", "gym", "fitness"]),
        ("Travel Europe", "travel", "lifestyle", 7.5, 6.5, 6.0, ["travel", "europe", "adventure"]),
        ("Parenting Tips", "parenting", "lifestyle", 8.0, 8.5, 3.0, ["parenting", "baby", "family"]),
        ("Marketing Strategy", "business", "marketing", 6.0, 6.0, 7.0, ["marketing", "brand", "sales"]),
    ]
    for name, niche, cat, eng, aud, comp, kws in topics_data:
        manager.add_topic(
            name=name, niche=niche, category=cat,
            engagement_score=eng, audience_fit_score=aud, competition_score=comp,
            keywords=kws, confidence=0.8,
        )
    return manager


# ═══════════════════════════════════════════
# Test 1: Topic Entry Model
# ═══════════════════════════════════════════

class TestTopicEntry:
    def test_create_topic(self):
        t = TopicEntry("AI Trends", niche="ai", engagement_score=8.0)
        assert t.name == "AI Trends"
        assert t.niche == "ai"
        assert t.engagement_score == 8.0
        assert t.status == "active"

    def test_composite_score_calculation(self):
        t = TopicEntry("Test", engagement_score=10.0, audience_fit_score=10.0, competition_score=0.0, confidence=1.0)
        assert t.composite_score > 8.0

    def test_opportunity_score_high_engagement_low_competition(self):
        t = TopicEntry("Easy Win", engagement_score=9.0, audience_fit_score=8.0, competition_score=2.0)
        assert t.opportunity_score >= 7.0

    def test_score_clamping(self):
        t = TopicEntry("Clamped", engagement_score=15.0, audience_fit_score=-5.0, competition_score=12.0)
        assert t.engagement_score == 10.0
        assert t.audience_fit_score == 0.0
        assert t.competition_score == 10.0

    def test_niche_validation(self):
        t = TopicEntry("Test", niche="invalid_niche")
        assert t.niche == "general"

    def test_to_dict(self):
        t = TopicEntry("Test", niche="ai", category="tech")
        d = t.to_dict()
        assert d["name"] == "Test"
        assert d["niche"] == "ai"
        assert "composite_score" in d
        assert "created_at" in d
        assert "expires_at" in d

    def test_from_dict(self):
        d = {
            "name": "Restored", "niche": "finance", "category": "cat",
            "engagement_score": 7.0, "audience_fit_score": 6.0, "competition_score": 5.0,
        }
        t = TopicEntry.from_dict(d)
        assert t.name == "Restored"
        assert t.niche == "finance"
        assert t.engagement_score == 7.0

    def test_from_dict_preserves_id(self):
        d = {
            "name": "X", "topic_id": "custom_id_123",
            "engagement_score": 5.0, "audience_fit_score": 5.0, "competition_score": 5.0,
        }
        t = TopicEntry.from_dict(d)
        assert t.topic_id == "custom_id_123"

    def test_is_expired(self):
        t = TopicEntry("Expired", expires_in_hours=0)
        assert t.is_expired() is True

    def test_not_expired(self):
        t = TopicEntry("Fresh", expires_in_hours=100)
        assert t.is_expired() is False

    def test_is_promotable(self):
        t = TopicEntry("Great", engagement_score=9.0, audience_fit_score=8.0,
                       competition_score=3.0, confidence=0.8, expires_in_hours=100)
        assert t.is_promotable() is True

    def test_not_promotable_low_score(self):
        t = TopicEntry("Bad", engagement_score=2.0, audience_fit_score=1.0,
                       competition_score=9.0, confidence=0.3, expires_in_hours=100)
        assert t.is_promotable() is False

    def test_update_scores(self):
        t = TopicEntry("Update", engagement_score=5.0, audience_fit_score=5.0, competition_score=5.0)
        old_score = t.composite_score
        t.update_scores(engagement_score=9.0, competition_score=2.0)
        assert t.composite_score != old_score
        assert t.engagement_score == 9.0
        assert t.competition_score == 2.0

    def test_update_scores_clamps(self):
        t = TopicEntry("Clamp", engagement_score=5.0, audience_fit_score=5.0, competition_score=5.0)
        t.update_scores(engagement_score=20.0)
        assert t.engagement_score == 10.0

    def test_difficulty_level_invalid(self):
        t = TopicEntry("Test", difficulty_level="crazy")
        assert t.difficulty_level == "medium"

    def test_keywords_and_hashtags(self):
        t = TopicEntry("Tags", keywords=["ai", "ml"], hashtags=["#ai", "#ml"], tags=["hot"])
        assert len(t.keywords) == 2
        assert len(t.hashtags) == 2
        assert "hot" in t.tags

    def test_metadata(self):
        t = TopicEntry("Meta", metadata={"source": "manual"})
        assert t.metadata["source"] == "manual"

    def test_confidence_clamped(self):
        t = TopicEntry("Test", confidence=2.0)
        assert t.confidence == 1.0
        t2 = TopicEntry("Test2", confidence=-1.0)
        assert t2.confidence == 0.0

    def test_estimated_reach_negative(self):
        t = TopicEntry("Test", estimated_reach=-100)
        assert t.estimated_reach == 0


# ═══════════════════════════════════════════
# Test 2: Topic Scorer
# ═══════════════════════════════════════════

class TestTopicScorer:
    def test_get_weights(self):
        scorer = TopicScorer()
        w = scorer.get_weights("finance")
        assert "engagement" in w
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_get_default_weights(self):
        scorer = TopicScorer()
        w = scorer.get_weights("unknown_niche")
        assert w == scorer.get_weights("general")

    def test_set_weights(self):
        scorer = TopicScorer()
        scorer.set_weights("custom", {"engagement": 0.5, "audience_fit": 0.3, "competition": 0.2})
        w = scorer.get_weights("custom")
        assert w["engagement"] == 0.5

    def test_set_weights_invalid_sum(self):
        scorer = TopicScorer()
        with pytest.raises(ValueError):
            scorer.set_weights("bad", {"engagement": 0.5, "audience_fit": 0.5, "competition": 0.5})

    def test_score_topic(self):
        scorer = TopicScorer()
        t = TopicEntry("Scored", niche="finance", engagement_score=8.0, audience_fit_score=7.0, competition_score=4.0)
        scorer.score_topic(t)
        assert t.opportunity_score > 0
        assert t.composite_score > 0

    def test_batch_score(self):
        scorer = TopicScorer()
        topics = [
            TopicEntry("A", engagement_score=7.0, audience_fit_score=6.0, competition_score=5.0),
            TopicEntry("B", engagement_score=8.0, audience_fit_score=7.0, competition_score=3.0),
        ]
        scorer.batch_score(topics)
        assert all(t.composite_score > 0 for t in topics)

    def test_rank_topics(self):
        scorer = TopicScorer()
        t1 = TopicEntry("Low", engagement_score=3.0, audience_fit_score=3.0, competition_score=8.0)
        t2 = TopicEntry("High", engagement_score=9.0, audience_fit_score=9.0, competition_score=2.0)
        ranked = scorer.rank_topics([t1, t2])
        assert ranked[0].name == "High"

    def test_filter_by_threshold(self):
        scorer = TopicScorer()
        t1 = TopicEntry("Good", engagement_score=8.0, audience_fit_score=7.0, competition_score=3.0, confidence=0.8)
        t2 = TopicEntry("Bad", engagement_score=2.0, audience_fit_score=1.0, competition_score=9.0, confidence=0.2)
        filtered = scorer.filter_by_threshold([t1, t2], min_composite=5.0, min_engagement=3.0, min_confidence=0.3)
        assert len(filtered) == 1
        assert filtered[0].name == "Good"

    def test_record_performance(self):
        scorer = TopicScorer()
        scorer.record_performance("t1", 8.0)
        scorer.record_performance("t1", 6.0)
        avg = scorer.get_average_performance("t1")
        assert avg == 7.0

    def test_get_average_performance_empty(self):
        scorer = TopicScorer()
        assert scorer.get_average_performance("nonexistent") is None

    def test_set_adjustment_factor(self):
        scorer = TopicScorer()
        scorer.set_adjustment_factor("finance", 1.5)
        t = TopicEntry("Adj", niche="finance", engagement_score=8.0, audience_fit_score=7.0, competition_score=3.0)
        scorer.score_topic(t)
        assert t.opportunity_score > 0

    def test_adjustment_factor_clamped(self):
        scorer = TopicScorer()
        scorer.set_adjustment_factor("x", 10.0)
        scorer.set_adjustment_factor("y", 0.01)
        # Should not raise

    def test_get_difficulty_label(self):
        scorer = TopicScorer()
        t1 = TopicEntry("Easy", competition_score=1.0)
        t2 = TopicEntry("Medium", competition_score=4.0)
        t3 = TopicEntry("Hard", competition_score=7.0)
        t4 = TopicEntry("VeryHard", competition_score=9.0)
        assert scorer.get_difficulty_label(t1) == "easy"
        assert scorer.get_difficulty_label(t2) == "medium"
        assert scorer.get_difficulty_label(t3) == "hard"
        assert scorer.get_difficulty_label(t4) == "very_hard"

    def test_suggest_hashtags(self):
        scorer = TopicScorer()
        t = TopicEntry("Tags", niche="ai", hashtags=["#ai", "#tech"], keywords=["python", "ml"])
        tags = scorer.suggest_hashtags(t, max_count=5)
        assert "#ai" in tags
        assert "#python" in tags
        assert "#ai" in tags  # niche tag
        assert len(tags) <= 5


# ═══════════════════════════════════════════
# Test 3: Topic Categorizer
# ═══════════════════════════════════════════

class TestTopicCategorizer:
    def test_detect_niche_finance(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["investment", "stock", "trading"])
        assert niche == "finance"

    def test_detect_niche_tech(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["python", "coding", "software"])
        assert niche == "technology"

    def test_detect_niche_health(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["diet", "nutrition", "yoga"])
        assert niche == "health"

    def test_detect_niche_ai(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["chatgpt", "llm", "deep learning"])
        assert niche == "ai"

    def test_detect_niche_crypto(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["bitcoin", "ethereum", "defi"])
        assert niche == "crypto"

    def test_detect_niche_general(self):
        cat = TopicCategorizer()
        niche = cat.detect_niche(["xyz", "random"])
        assert niche == "general"

    def test_detect_niche_empty(self):
        cat = TopicCategorizer()
        assert cat.detect_niche([]) == "general"

    def test_suggest_content_type(self):
        cat = TopicCategorizer()
        types = cat.suggest_content_type("finance")
        assert "carousel" in types
        assert len(types) > 0

    def test_suggest_content_type_unknown(self):
        cat = TopicCategorizer()
        types = cat.suggest_content_type("unknown")
        assert "text_post" in types

    def test_auto_categorize(self):
        cat = TopicCategorizer()
        t = TopicEntry("Test", niche="general", keywords=["bitcoin", "trading", "crypto"])
        cat.auto_categorize(t)
        assert t.niche in ("crypto", "finance")

    def test_auto_categorize_preserves_existing(self):
        cat = TopicCategorizer()
        t = TopicEntry("Test", niche="ai", keywords=["bitcoin"])
        cat.auto_categorize(t)
        assert t.niche == "ai"

    def test_auto_categorize_no_keywords(self):
        cat = TopicCategorizer()
        t = TopicEntry("Test", niche="general")
        cat.auto_categorize(t)
        assert t.niche == "general"

    def test_batch_categorize(self):
        cat = TopicCategorizer()
        t1 = TopicEntry("A", niche="general", keywords=["workout", "gym"])
        t2 = TopicEntry("B", niche="general", keywords=["recipe", "cooking"])
        cat.batch_categorize([t1, t2])
        assert t1.niche == "fitness"
        assert t2.niche == "cooking"

    def test_cluster_topics(self):
        cat = TopicCategorizer()
        topics = [
            TopicEntry("A", niche="ai", keywords=["ai"]),
            TopicEntry("B", niche="ai", keywords=["ml"]),
            TopicEntry("C", niche="cooking", keywords=["recipe"]),
        ]
        clusters = cat.cluster_topics(topics)
        # ai has 2 topics → should cluster
        assert any("ai" in k for k in clusters)

    def test_cluster_topics_no_cluster(self):
        cat = TopicCategorizer()
        topics = [
            TopicEntry("A", niche="ai", keywords=["ai"]),
            TopicEntry("B", niche="cooking", keywords=["recipe"]),
        ]
        clusters = cat.cluster_topics(topics)
        assert len(clusters) == 0

    def test_find_related(self):
        cat = TopicCategorizer()
        t1 = TopicEntry("Main", keywords=["ai", "python", "ml"])
        t2 = TopicEntry("Related", keywords=["ai", "deep learning"])
        t3 = TopicEntry("Unrelated", keywords=["recipe", "cooking"])
        related = cat.find_related(t1, [t2, t3], max_results=5)
        assert t2.topic_id in related
        assert t3.topic_id not in related

    def test_find_related_no_keywords(self):
        cat = TopicCategorizer()
        t1 = TopicEntry("A", niche="ai")
        t2 = TopicEntry("B", niche="ai")
        related = cat.find_related(t1, [t2])
        assert t2.topic_id in related

    def test_find_related_empty(self):
        cat = TopicCategorizer()
        t1 = TopicEntry("A", keywords=["unique123"])
        related = cat.find_related(t1, [])
        assert len(related) == 0

    def test_get_niche_stats(self):
        cat = TopicCategorizer()
        topics = [
            TopicEntry("A", niche="ai", engagement_score=8.0, audience_fit_score=7.0, competition_score=3.0),
            TopicEntry("B", niche="ai", engagement_score=6.0, audience_fit_score=5.0, competition_score=5.0),
        ]
        stats = cat.get_niche_stats(topics)
        assert "ai" in stats
        assert stats["ai"]["count"] == 2
        assert "avg_composite" in stats["ai"]
        assert "top_topic" in stats["ai"]

    def test_get_niche_stats_empty(self):
        cat = TopicCategorizer()
        stats = cat.get_niche_stats([])
        assert len(stats) == 0


# ═══════════════════════════════════════════
# Test 4: Topic Intel Manager — CRUD
# ═══════════════════════════════════════════

class TestManagerCRUD:
    def test_add_topic(self, manager):
        t = manager.add_topic("AI News", niche="ai", engagement_score=7.0)
        assert t.name == "AI News"
        assert manager.exists("AI News")

    def test_add_topic_auto_categorize(self, manager):
        t = manager.add_topic("Bitcoin Tips", keywords=["bitcoin", "trading", "crypto"])
        assert t.niche in ("crypto", "finance")

    def test_add_topic_duplicate_raises(self, manager):
        manager.add_topic("Unique")
        with pytest.raises(DuplicateTopicError):
            manager.add_topic("Unique")

    def test_add_topic_case_insensitive_dup(self, manager):
        manager.add_topic("CaseTest")
        with pytest.raises(DuplicateTopicError):
            manager.add_topic("casetest")

    def test_get_topic(self, manager):
        t = manager.add_topic("GetMe")
        found = manager.get_topic(t.topic_id)
        assert found.name == "GetMe"

    def test_get_topic_not_found(self, manager):
        with pytest.raises(TopicNotFoundError):
            manager.get_topic("nope")

    def test_get_topic_by_name(self, manager):
        manager.add_topic("ByName")
        found = manager.get_topic_by_name("byname")
        assert found is not None
        assert found.name == "ByName"

    def test_get_topic_by_name_not_found(self, manager):
        assert manager.get_topic_by_name("ghost") is None

    def test_update_topic(self, manager):
        t = manager.add_topic("Updatable", engagement_score=5.0)
        updated = manager.update_topic(t.topic_id, engagement_score=9.0, name="Updated")
        assert updated.engagement_score == 9.0
        assert updated.name == "Updated"

    def test_update_topic_not_found(self, manager):
        with pytest.raises(TopicNotFoundError):
            manager.update_topic("nope", name="X")

    def test_update_topic_scores_recalculate(self, manager):
        t = manager.add_topic("Recalc", engagement_score=3.0, audience_fit_score=3.0, competition_score=7.0)
        old_composite = t.composite_score
        manager.update_topic(t.topic_id, engagement_score=9.0, competition_score=1.0)
        updated = manager.get_topic(t.topic_id)
        assert updated.composite_score > old_composite

    def test_delete_topic(self, manager):
        t = manager.add_topic("DeleteMe")
        assert manager.delete_topic(t.topic_id) is True
        assert not manager.exists("DeleteMe")

    def test_delete_topic_not_found(self, manager):
        with pytest.raises(TopicNotFoundError):
            manager.delete_topic("ghost")

    def test_exists(self, manager):
        manager.add_topic("Exists")
        assert manager.exists("Exists") is True
        assert manager.exists("Nope") is False

    def test_list_topics(self, manager):
        manager.add_topic("A", niche="ai")
        manager.add_topic("B", niche="cooking")
        all_topics = manager.list_topics()
        assert len(all_topics) == 2

    def test_list_topics_by_niche(self, manager):
        manager.add_topic("A", niche="ai")
        manager.add_topic("B", niche="ai")
        manager.add_topic("C", niche="cooking")
        ai_topics = manager.list_topics(niche="ai")
        assert len(ai_topics) == 2

    def test_list_topics_by_status(self, manager):
        t = manager.add_topic("Active")
        manager.update_topic(t.topic_id, status="archived")
        active = manager.list_topics(status="active")
        assert len(active) == 0


# ═══════════════════════════════════════════
# Test 5: Topic Intel Manager — Intelligence
# ═══════════════════════════════════════════

class TestManagerIntelligence:
    def test_rank_topics(self, manager_with_topics):
        ranked = manager_with_topics.rank_topics()
        assert len(ranked) > 0
        assert ranked[0].composite_score >= ranked[-1].composite_score

    def test_rank_topics_by_niche(self, manager_with_topics):
        ranked = manager_with_topics.rank_topics(niche="ai")
        assert all(t.niche == "ai" for t in ranked)

    def test_get_top_topics(self, manager_with_topics):
        top = manager_with_topics.get_top_topics(count=3)
        assert len(top) == 3

    def test_get_promotable_topics(self, manager_with_topics):
        promos = manager_with_topics.get_promotable_topics()
        assert isinstance(promos, list)

    def test_find_opportunities(self, manager_with_topics):
        opps = manager_with_topics.find_opportunities(min_score=6.0)
        assert isinstance(opps, list)
        assert all(t.opportunity_score >= 6.0 for t in opps)

    def test_suggest_for_niche(self, manager_with_topics):
        suggestions = manager_with_topics.suggest_for_niche("ai", count=2)
        assert len(suggestions) <= 2

    def test_suggest_for_niche_empty(self, manager):
        suggestions = manager.suggest_for_niche("nonexistent")
        assert len(suggestions) == 0

    def test_cluster_topics(self, manager_with_topics):
        clusters = manager_with_topics.cluster_topics()
        assert isinstance(clusters, dict)

    def test_get_niche_stats(self, manager_with_topics):
        stats = manager_with_topics.get_niche_stats()
        assert len(stats) > 0
        for niche, data in stats.items():
            assert "count" in data
            assert "avg_composite" in data

    def test_cleanup_expired(self, manager):
        t = manager.add_topic("Expire", engagement_score=5.0)
        # Force expiry by setting expires_at to the past
        t.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        removed = manager.cleanup_expired()
        assert removed >= 1


# ═══════════════════════════════════════════
# Test 6: Persistence
# ═══════════════════════════════════════════

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "persist.json"
        m1 = TopicIntelManager(storage_path=str(path))
        m1.add_topic("Persist", niche="ai", engagement_score=8.0)
        count = len(m1.list_topics())
        assert count == 1

        m2 = TopicIntelManager(storage_path=str(path))
        assert len(m2.list_topics()) == 1
        t = m2.list_topics()[0]
        assert t.name == "Persist"
        assert t.engagement_score == 8.0

    def test_no_storage(self):
        m = TopicIntelManager()
        m.add_topic("NoStorage")
        assert m.exists("NoStorage")

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("not valid json {{{")
        m = TopicIntelManager(storage_path=str(path))
        assert len(m.list_topics()) == 0

    def test_history_recorded(self, tmp_path):
        path = tmp_path / "hist.json"
        m = TopicIntelManager(storage_path=str(path))
        m.add_topic("Hist")
        m.add_topic("Hist2")
        assert len(m._history) >= 2


# ═══════════════════════════════════════════
# Test 7: Health Check
# ═══════════════════════════════════════════

class TestHealthCheck:
    def test_health_empty(self, manager):
        h = manager.health_check()
        assert h["total_topics"] == 0
        assert h["active"] == 0
        assert h["scorer_ready"] is True
        assert h["categorizer_ready"] is True

    def test_health_with_data(self, manager_with_topics):
        h = manager_with_topics.health_check()
        assert h["total_topics"] > 0
        assert h["active"] > 0
        assert h["niches_covered"] > 1
        assert h["avg_composite_score"] > 0


# ═══════════════════════════════════════════
# Test 8: Edge Cases
# ═══════════════════════════════════════════

class TestEdgeCases:
    def test_all_niches_add(self, manager):
        for niche in TopicEntry.NICHES:
            t = manager.add_topic(f"Test_{niche}", niche=niche)
            assert t.niche == niche

    def test_special_characters_name(self, manager):
        t = manager.add_topic("Topic @#$%^&*()")
        assert t.name == "Topic @#$%^&*()"

    def test_very_long_name(self, manager):
        long_name = "A" * 500
        t = manager.add_topic(long_name)
        assert t.name == long_name

    def test_empty_keywords(self, manager):
        t = manager.add_topic("NoKeywords", keywords=[])
        assert t.keywords == []

    def test_many_topics_performance(self, manager):
        for i in range(100):
            manager.add_topic(f"Topic_{i}", niche="general", engagement_score=float(i % 10))
        assert len(manager.list_topics()) == 100
        ranked = manager.rank_topics()
        assert len(ranked) == 100

    def test_concurrent_access(self, manager):
        """Basic thread safety test."""
        import threading
        errors = []

        def add_topic(i):
            try:
                manager.add_topic(f"Thread_{i}", niche="general")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_topic, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(manager.list_topics()) == 20
