"""
Tests for Audience Research Module
Layer 2: Research Engine — Module 4

Run: python -m pytest layers/layer02_research/tests/test_audience_research.py -v
"""

import pytest

from layers.layer02_research.modules.audience_research.audience_profile import AudienceProfile
from layers.layer02_research.modules.audience_research.interest_mapper import InterestMapper, InterestNode
from layers.layer02_research.modules.audience_research.behavior_analyzer import BehaviorAnalyzer, BehaviorAnalysis
from layers.layer02_research.modules.audience_research.demographic_analyzer import DemographicAnalyzer, DemographicProfile
from layers.layer02_research.modules.audience_research.engagement_predictor import EngagementPredictor, Prediction
from layers.layer02_research.modules.audience_research.audience_intel_manager import AudienceIntelManager
from layers.layer02_research.modules.audience_research.exceptions import (
    AudienceNotFoundError, DuplicateAudienceError,
)


# ═══════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════

@pytest.fixture
def manager(tmp_path):
    return AudienceIntelManager(storage_path=str(tmp_path / "audiences.json"))


@pytest.fixture
def manager_with_audiences(manager):
    """Manager with pre-populated audience segments."""
    audiences = [
        ("Tech Enthusiasts", "ai", "technology", [25, 40], 50000, 6.5),
        ("Finance Pros", "finance", "business", [30, 55], 30000, 5.0),
        ("Fitness Fanatics", "fitness", "health", [18, 35], 80000, 8.0),
        ("Travel Lovers", "travel", "lifestyle", [22, 45], 45000, 7.0),
        ("Marketing Gurus", "marketing", "business", [28, 50], 25000, 4.5),
    ]
    for name, niche, cat, ages, size, eng in audiences:
        manager.add_audience(
            segment_name=name, niche=niche, category=cat,
            age_range=ages, size_estimate=size, engagement_rate=eng,
            interests=[niche, cat], confidence=0.8,
        )
    return manager


# ═══════════════════════════════════════════
# Test 1: Audience Profile
# ═══════════════════════════════════════════

class TestAudienceProfile:
    def test_create_profile(self):
        p = AudienceProfile("Test Segment", niche="ai", size_estimate=5000)
        assert p.segment_name == "Test Segment"
        assert p.niche == "ai"
        assert p.status == "active"

    def test_age_midpoint(self):
        p = AudienceProfile("A", age_range=[20, 40])
        assert p.get_age_midpoint() == 30.0

    def test_age_midpoint_default(self):
        p = AudienceProfile("A")
        assert p.get_age_midpoint() == 41.5

    def test_mobile_percentage(self):
        p = AudienceProfile("A", device_split={"mobile": 80.0, "desktop": 20.0})
        assert p.get_mobile_percentage() == 80.0

    def test_is_high_value(self):
        p = AudienceProfile("A", engagement_rate=6.0, confidence=0.7, size_estimate=5000)
        assert p.is_high_value() is True

    def test_not_high_value(self):
        p = AudienceProfile("A", engagement_rate=2.0, confidence=0.3, size_estimate=500)
        assert p.is_high_value() is False

    def test_is_growing(self):
        p = AudienceProfile("A", growth_trend="growing")
        assert p.is_growing() is True
        p2 = AudienceProfile("B", growth_rate=10.0)
        assert p2.is_growing() is True

    def test_size_tier(self):
        assert AudienceProfile("A", size_estimate=5_000_000).get_size_tier() == "massive"
        assert AudienceProfile("B", size_estimate=500_000).get_size_tier() == "large"
        assert AudienceProfile("C", size_estimate=50_000).get_size_tier() == "medium"
        assert AudienceProfile("D", size_estimate=5_000).get_size_tier() == "small"
        assert AudienceProfile("E", size_estimate=500).get_size_tier() == "niche"

    def test_to_dict(self):
        p = AudienceProfile("X", niche="ai", size_estimate=1000)
        d = p.to_dict()
        assert d["segment_name"] == "X"
        assert d["niche"] == "ai"
        assert "profile_id" in d

    def test_from_dict(self):
        d = {"segment_name": "Restore", "niche": "finance", "size_estimate": 5000}
        p = AudienceProfile.from_dict(d)
        assert p.segment_name == "Restore"
        assert p.size_estimate == 5000

    def test_from_dict_preserves_id(self):
        d = {"segment_name": "X", "profile_id": "custom_id"}
        p = AudienceProfile.from_dict(d)
        assert p.profile_id == "custom_id"

    def test_engagement_clamped(self):
        p = AudienceProfile("A", engagement_rate=150)
        assert p.engagement_rate == 100.0

    def test_size_estimate_negative(self):
        p = AudienceProfile("A", size_estimate=-100)
        assert p.size_estimate == 0

    def test_growth_trend_invalid(self):
        p = AudienceProfile("A", growth_trend="invalid")
        assert p.growth_trend == "unknown"

    def test_buying_stage_invalid(self):
        p = AudienceProfile("A", buying_stage="invalid")
        assert p.buying_stage == "unknown"

    def test_interests_and_behaviors(self):
        p = AudienceProfile("A", interests=["ai", "ml"], behaviors=["active", "buyer"])
        assert len(p.interests) == 2
        assert "buyer" in p.behaviors

    def test_personas_and_pain_points(self):
        p = AudienceProfile("A", personas=[{"name": "Student"}], pain_points=["lack of time"])
        assert len(p.personas) == 1
        assert "lack of time" in p.pain_points


# ═══════════════════════════════════════════
# Test 2: Interest Mapper
# ═══════════════════════════════════════════

class TestInterestMapper:
    def test_add_interest(self):
        im = InterestMapper()
        node = im.add_interest("python", category="technology", relevance_score=8.0)
        assert node.name == "python"
        assert node.composite_score > 0

    def test_auto_detect_category(self):
        im = InterestMapper()
        node = im.add_interest("ai")
        assert node.category == "technology"  # ai is child of technology

    def test_get_interest(self):
        im = InterestMapper()
        im.add_interest("crypto")
        node = im.get_interest("crypto")
        assert node is not None

    def test_remove_interest(self):
        im = InterestMapper()
        im.add_interest("temp")
        assert im.remove_interest("temp") is True
        assert im.get_interest("temp") is None

    def test_remove_nonexistent(self):
        im = InterestMapper()
        assert im.remove_interest("ghost") is False

    def test_list_interests(self):
        im = InterestMapper()
        im.add_interest("a")
        im.add_interest("b")
        assert len(im.list_interests()) == 2

    def test_get_top_interests(self):
        im = InterestMapper()
        im.add_interest("low", relevance_score=2.0, popularity_score=2.0)
        im.add_interest("high", relevance_score=9.0, popularity_score=9.0)
        top = im.get_top_interests(1)
        assert top[0].name == "high"

    def test_get_by_category(self):
        im = InterestMapper()
        im.add_interest("python", category="technology")
        im.add_interest("recipe", category="cooking")
        tech = im.get_by_category("technology")
        assert len(tech) == 1

    def test_cluster_interests(self):
        im = InterestMapper()
        im.add_interest("python", category="technology")
        im.add_interest("recipe", category="cooking")
        clusters = im.cluster_interests()
        assert "technology" in clusters
        assert "cooking" in clusters

    def test_find_related(self):
        im = InterestMapper()
        im.add_interest("python")
        related = im.find_related("python")
        assert isinstance(related, list)

    def test_find_related_nonexistent(self):
        im = InterestMapper()
        assert im.find_related("ghost") == []

    def test_compute_overlap(self):
        im = InterestMapper()
        assert im.compute_overlap(["a", "b", "c"], ["b", "c", "d"]) > 0
        assert im.compute_overlap(["a"], ["b"]) == 0.0
        assert im.compute_overlap([], ["a"]) == 0.0

    def test_score_content_fit(self):
        im = InterestMapper()
        score = im.score_content_fit(["ai", "python"], ["ai", "ml", "python"])
        assert score > 0

    def test_score_content_fit_empty(self):
        im = InterestMapper()
        assert im.score_content_fit([], ["a"]) == 0.0
        assert im.score_content_fit(["a"], []) == 0.0

    def test_suggest_content_topics(self):
        im = InterestMapper()
        im.add_interest("python")
        suggestions = im.suggest_content_topics(["python"], count=5)
        assert isinstance(suggestions, list)

    def test_interest_node_to_dict(self):
        node = InterestNode("test", category="tech", relevance_score=7.0)
        d = node.to_dict()
        assert d["name"] == "test"
        assert d["relevance_score"] == 7.0


# ═══════════════════════════════════════════
# Test 3: Behavior Analyzer
# ═══════════════════════════════════════════

class TestBehaviorAnalyzer:
    def test_analyze_empty(self):
        ba = BehaviorAnalyzer()
        result = ba.analyze("p1", interaction_hours=[], interaction_days=[])
        assert result.confidence == 0.0

    def test_analyze_with_data(self):
        ba = BehaviorAnalyzer()
        hours = [9, 10, 10, 11, 14, 15, 20, 21]
        days = ["Monday", "Monday", "Tuesday", "Wednesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        result = ba.analyze("p1", interaction_hours=hours, interaction_days=days)
        assert len(result.online_peak_hours) > 0
        assert result.most_active_day != ""

    def test_peak_hours(self):
        ba = BehaviorAnalyzer()
        hours = [9, 9, 9, 10, 10, 14, 14, 14, 14]
        result = ba.analyze("p1", interaction_hours=hours, interaction_days=[])
        assert 14 in result.best_posting_hours or 9 in result.best_posting_hours

    def test_consistency(self):
        ba = BehaviorAnalyzer()
        hours = [10, 10, 10, 10, 10, 10, 10]
        result = ba.analyze("p1", interaction_hours=hours, interaction_days=[])
        assert result.behavior_consistency > 0

    def test_sharing_rate(self):
        ba = BehaviorAnalyzer()
        hours = [10] * 10
        days = ["Monday"] * 10
        types = ["click", "click", "share", "share", "share", "click", "click", "click", "click", "click"]
        result = ba.analyze("p1", hours, days, interaction_types=types)
        assert result.sharing_rate == 30.0

    def test_click_rate(self):
        ba = BehaviorAnalyzer()
        hours = [10] * 10
        days = ["Monday"] * 10
        types = ["click", "click", "click", "click", "click", "like", "like", "like", "like", "like"]
        result = ba.analyze("p1", hours, days, interaction_types=types)
        assert result.click_rate == 50.0

    def test_predict_optimal_time(self):
        ba = BehaviorAnalyzer()
        hours = [9, 9, 9, 14, 14, 14, 20, 20]
        ba.analyze("p1", hours, ["Monday"] * 8)
        hour = ba.predict_optimal_posting_time("p1")
        assert hour in (9, 14, 20)

    def test_predict_best_day(self):
        ba = BehaviorAnalyzer()
        ba.analyze("p1", [10] * 7, ["Monday", "Monday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        day = ba.predict_best_day("p1")
        assert day == "Monday"

    def test_compare_segments(self):
        ba = BehaviorAnalyzer()
        ba.analyze("a", [9, 10, 11], ["Monday", "Tuesday"])
        ba.analyze("b", [14, 15, 16], ["Wednesday", "Thursday"])
        cmp = ba.compare_segments("a", "b")
        assert "peak_hours_overlap" in cmp

    def test_compare_segments_missing(self):
        ba = BehaviorAnalyzer()
        cmp = ba.compare_segments("x", "y")
        assert "error" in cmp

    def test_analysis_to_dict(self):
        a = BehaviorAnalysis("x")
        d = a.to_dict()
        assert d["profile_id"] == "x"


# ═══════════════════════════════════════════
# Test 4: Demographic Analyzer
# ═══════════════════════════════════════════

class TestDemographicAnalyzer:
    def test_analyze_empty(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1")
        assert dp.data_completeness == 0.0

    def test_analyze_full(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", ages=[25, 30, 35], genders=["m", "m", "f"],
                        locations=["US", "US", "UK"], languages=["en", "en"],
                        devices=["mobile", "mobile", "desktop"])
        assert dp.data_completeness > 0
        assert dp.age_group_primary != ""
        assert dp.gender_primary != ""
        assert dp.top_locations != []

    def test_age_groups(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", ages=[20, 22, 23])
        assert dp.age_group_primary == "young_adult"

    def test_gender_split(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", genders=["m", "m", "m", "f"])
        assert dp.gender_primary == "m"
        assert dp.gender_distribution["m"] == 75.0

    def test_top_locations(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", locations=["US", "US", "US", "UK", "UK", "DE"])
        assert dp.top_locations[0] == "US"

    def test_mobile_first(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", devices=["mobile", "mobile", "mobile", "desktop"])
        assert dp.mobile_first is True

    def test_diversity_score(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", genders=["m", "m", "f", "f"])
        assert dp.diversity_score > 0

    def test_concentration_score(self):
        da = DemographicAnalyzer()
        dp = da.analyze("p1", locations=["US", "US", "US", "UK"])
        assert dp.concentration_score > 0

    def test_find_segments(self):
        da = DemographicAnalyzer()
        da.analyze("p1", ages=[30], genders=["m"], locations=["US"])
        segs = da.find_segments("p1")
        assert len(segs) > 0
        assert any(s["type"] == "age" for s in segs)

    def test_find_segments_empty(self):
        da = DemographicAnalyzer()
        assert da.find_segments("missing") == []

    def test_get_profile(self):
        da = DemographicAnalyzer()
        da.analyze("p1", ages=[25])
        assert da.get_profile("p1") is not None

    def test_get_profile_missing(self):
        da = DemographicAnalyzer()
        assert da.get_profile("ghost") is None

    def test_to_dict(self):
        dp = DemographicProfile("x")
        d = dp.to_dict()
        assert d["profile_id"] == "x"


# ═══════════════════════════════════════════
# Test 5: Engagement Predictor
# ═══════════════════════════════════════════

class TestEngagementPredictor:
    def test_predict_basic(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=6.0, interests=["ai"])
        pred = ep.predict(aud, content_type="video", topic="ai")
        assert pred.predicted_engagement > 0
        assert pred.confidence > 0

    def test_predict_interest_match(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=6.0, interests=["ai", "python"])
        pred_match = ep.predict(aud, topic="ai")
        pred_no_match = ep.predict(aud, topic="cooking")
        assert pred_match.predicted_engagement >= pred_no_match.predicted_engagement

    def test_predict_peak_hour(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=5.0, peak_engagement_hours=[10, 14])
        pred = ep.predict(aud, posting_hour=10)
        assert pred.factors["time_factor"] > 1.0

    def test_predict_buying_stage(self):
        ep = EngagementPredictor()
        aud_adv = AudienceProfile("A", buying_stage="advocacy", engagement_rate=5.0)
        aud_aware = AudienceProfile("B", buying_stage="awareness", engagement_rate=5.0)
        p1 = ep.predict(aud_adv)
        p2 = ep.predict(aud_aware)
        assert p1.predicted_engagement >= p2.predicted_engagement

    def test_predict_batch(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=5.0, interests=["ai"])
        variants = [
            {"content_type": "video", "topic": "ai"},
            {"content_type": "text", "topic": "ai"},
        ]
        results = ep.predict_batch(aud, variants)
        assert len(results) == 2
        assert results[0].predicted_engagement >= results[1].predicted_engagement

    def test_recommend_ab_test(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=5.0, interests=["ai"])
        result = ep.recommend_ab_test(aud, topic="ai")
        assert "best_variant" in result
        assert "recommendation" in result

    def test_get_predictions(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=5.0)
        ep.predict(aud)
        ep.predict(aud)
        preds = ep.get_predictions(aud.profile_id)
        assert len(preds) == 2

    def test_get_top_predictions(self):
        ep = EngagementPredictor()
        aud = AudienceProfile("A", engagement_rate=5.0)
        for _ in range(5):
            ep.predict(aud)
        top = ep.get_top_predictions(aud.profile_id, 2)
        assert len(top) == 2

    def test_prediction_to_dict(self):
        pred = Prediction(content_type="video", topic="ai", predicted_engagement=7.0)
        d = pred.to_dict()
        assert d["content_type"] == "video"
        assert d["predicted_engagement"] == 7.0

    def test_prediction_clamped(self):
        pred = Prediction(predicted_engagement=15.0)
        assert pred.predicted_engagement == 10.0


# ═══════════════════════════════════════════
# Test 6: Manager CRUD
# ═══════════════════════════════════════════

class TestManagerCRUD:
    def test_add_audience(self, manager):
        a = manager.add_audience("Test", niche="ai", size_estimate=5000)
        assert a.segment_name == "Test"
        assert manager.exists("Test")

    def test_add_duplicate_raises(self, manager):
        manager.add_audience("Unique")
        with pytest.raises(DuplicateAudienceError):
            manager.add_audience("Unique")

    def test_case_insensitive_dup(self, manager):
        manager.add_audience("CaseTest")
        with pytest.raises(DuplicateAudienceError):
            manager.add_audience("casetest")

    def test_get_audience(self, manager):
        a = manager.add_audience("GetMe")
        found = manager.get_audience(a.profile_id)
        assert found.segment_name == "GetMe"

    def test_get_not_found(self, manager):
        with pytest.raises(AudienceNotFoundError):
            manager.get_audience("ghost")

    def test_get_by_name(self, manager):
        manager.add_audience("ByName")
        found = manager.get_by_name("byname")
        assert found is not None

    def test_get_by_name_not_found(self, manager):
        assert manager.get_by_name("ghost") is None

    def test_update_audience(self, manager):
        a = manager.add_audience("Update", size_estimate=1000)
        manager.update_audience(a.profile_id, size_estimate=99999)
        updated = manager.get_audience(a.profile_id)
        assert updated.size_estimate == 99999

    def test_update_not_found(self, manager):
        with pytest.raises(AudienceNotFoundError):
            manager.update_audience("nope", size_estimate=1)

    def test_delete_audience(self, manager):
        a = manager.add_audience("DeleteMe")
        assert manager.delete_audience(a.profile_id) is True
        assert not manager.exists("DeleteMe")

    def test_delete_not_found(self, manager):
        with pytest.raises(AudienceNotFoundError):
            manager.delete_audience("ghost")

    def test_list_audiences(self, manager):
        manager.add_audience("A", niche="ai")
        manager.add_audience("B", niche="cooking")
        assert len(manager.list_audiences()) == 2

    def test_list_by_niche(self, manager):
        manager.add_audience("A", niche="ai")
        manager.add_audience("B", niche="ai")
        manager.add_audience("C", niche="cooking")
        assert len(manager.list_audiences(niche="ai")) == 2


# ═══════════════════════════════════════════
# Test 7: Manager Intelligence
# ═══════════════════════════════════════════

class TestManagerIntelligence:
    def test_run_full_analysis(self, manager_with_audiences):
        auds = manager_with_audiences.list_audiences()
        result = manager_with_audiences.run_full_analysis(
            auds[0].profile_id,
            interaction_hours=[9, 10, 10, 14, 14, 20],
            interaction_days=["Monday", "Monday", "Tuesday", "Wednesday", "Wednesday", "Friday"],
            interaction_types=["click", "click", "share", "like", "click", "share"],
            ages=[25, 30, 35, 28, 32],
            genders=["m", "m", "f", "m", "f"],
            locations=["US", "US", "UK", "US", "DE"],
            languages=["en", "en", "en", "en", "de"],
            devices=["mobile", "mobile", "mobile", "desktop", "mobile"],
        )
        assert result.last_analyzed != result.created_at

    def test_run_full_analysis_minimal(self, manager_with_audiences):
        auds = manager_with_audiences.list_audiences()
        result = manager_with_audiences.run_full_analysis(auds[0].profile_id)
        assert result.segment_name == auds[0].segment_name

    def test_predict_engagement(self, manager_with_audiences):
        auds = manager_with_audiences.list_audiences()
        pred = manager_with_audiences.predict_engagement(
            auds[0].profile_id, content_type="video", topic=auds[0].niche,
        )
        assert pred.predicted_engagement > 0

    def test_get_content_recommendations(self, manager_with_audiences):
        auds = manager_with_audiences.list_audiences()
        recs = manager_with_audiences.get_content_recommendations(auds[0].profile_id)
        assert "audience" in recs
        assert "suggested_topics" in recs
        assert "size_tier" in recs

    def test_interest_mapper_populated(self, manager_with_audiences):
        interests = manager_with_audiences.interest_mapper.list_interests()
        assert len(interests) > 0


# ═══════════════════════════════════════════
# Test 8: Persistence
# ═══════════════════════════════════════════

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "persist.json"
        m1 = AudienceIntelManager(storage_path=str(path))
        m1.add_audience("Persist", size_estimate=5000)
        m2 = AudienceIntelManager(storage_path=str(path))
        assert len(m2.list_audiences()) == 1
        assert m2.list_audiences()[0].segment_name == "Persist"

    def test_no_storage(self):
        m = AudienceIntelManager()
        m.add_audience("NoStorage")
        assert m.exists("NoStorage")

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")
        m = AudienceIntelManager(storage_path=str(path))
        assert len(m.list_audiences()) == 0

    def test_health_check_empty(self, manager):
        h = manager.health_check()
        assert h["total_audiences"] == 0
        assert h["interest_mapper_ready"] is True

    def test_health_check_with_data(self, manager_with_audiences):
        h = manager_with_audiences.health_check()
        assert h["total_audiences"] == 5
        assert h["active"] == 5
        assert h["interests_mapped"] > 0


# ═══════════════════════════════════════════
# Test 9: Edge Cases
# ═══════════════════════════════════════════

class TestEdgeCases:
    def test_special_characters_name(self, manager):
        a = manager.add_audience("Audience @#$%^&*()")
        assert a.segment_name == "Audience @#$%^&*()"

    def test_many_audiences_performance(self, manager):
        for i in range(50):
            manager.add_audience(f"Aud_{i}", niche="general", size_estimate=i * 100)
        assert len(manager.list_audiences()) == 50

    def test_concurrent_access(self, manager):
        import threading
        errors = []

        def add_aud(i):
            try:
                manager.add_audience(f"Thread_{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=add_aud, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(manager.list_audiences()) == 20

    def test_profile_from_dict_all_fields(self):
        d = {
            "segment_name": "Full", "niche": "ai", "category": "tech",
            "age_range": [20, 40], "gender_split": {"m": 60, "f": 40},
            "locations": ["US", "UK"], "languages": ["en"],
            "interests": ["ai", "ml"], "behaviors": ["active"],
            "online_hours": [10, 14], "peak_engagement_hours": [10],
            "device_split": {"mobile": 80, "desktop": 20},
            "content_preferences": ["video"], "format_preferences": ["reel"],
            "avg_session_duration": 15.0, "avg_posts_interacted": 3.0,
            "engagement_rate": 7.0, "growth_rate": 5.0,
            "size_estimate": 10000, "growth_trend": "growing",
            "personas": [{"name": "Student"}],
            "pain_points": ["time"], "desires": ["knowledge"],
            "buying_stage": "consideration", "confidence": 0.9,
            "tags": ["hot"], "metadata": {"k": "v"},
            "profile_id": "custom_id", "status": "growing",
            "created_at": "2026-01-01", "updated_at": "2026-06-01",
            "last_analyzed": "2026-07-01",
        }
        p = AudienceProfile.from_dict(d)
        assert p.profile_id == "custom_id"
        assert p.interests == ["ai", "ml"]
        assert p.buying_stage == "consideration"
        assert p.status == "growing"
