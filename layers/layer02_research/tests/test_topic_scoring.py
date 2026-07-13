"""
Tests for Topic Scoring Engine
Layer 2: Research Engine — Module 8

Run: python -m pytest layers/layer02_research/tests/test_topic_scoring.py -v
"""

import pytest

from layers.layer02_research.modules.topic_scoring.scoring_rules import ScoringRulesEngine, ScoringRule, DEFAULT_RULES
from layers.layer02_research.modules.topic_scoring.weight_manager import WeightManager, DEFAULT_WEIGHTS
from layers.layer02_research.modules.topic_scoring.score_normalizer import ScoreNormalizer
from layers.layer02_research.modules.topic_scoring.opportunity_scorer import OpportunityScorer
from layers.layer02_research.modules.topic_scoring.risk_scorer import RiskScorer
from layers.layer02_research.modules.topic_scoring.confidence_fusion import ConfidenceFusion
from layers.layer02_research.modules.topic_scoring.scoring_engine import ScoringEngine, ScoringResult
from layers.layer02_research.modules.topic_scoring.scoring_manager import ScoringManager


@pytest.fixture
def manager(tmp_path):
    return ScoringManager(storage_path=str(tmp_path / "scoring.json"))


# ═══════════════════════════════════════════
# Test 1: Scoring Rules
# ═══════════════════════════════════════════

class TestScoringRules:
    def test_default_rules_exist(self):
        assert len(DEFAULT_RULES) > 0

    def test_add_rule(self):
        engine = ScoringRulesEngine()
        rule = ScoringRule("test1", "Test Rule", "bonus", "trend >= 5", 1.0, "Test")
        engine.add_rule(rule)
        assert engine.get_rule("test1") is not None

    def test_remove_rule(self):
        engine = ScoringRulesEngine()
        engine.add_rule(ScoringRule("temp", "Temp"))
        assert engine.remove_rule("temp") is True
        assert engine.get_rule("temp") is None

    def test_evaluate_rules(self):
        engine = ScoringRulesEngine()
        scores = {"trend_score": 9.0, "competition_score": 2.0, "verification_score": 8.5, "confidence": 0.9}
        applied = engine.evaluate(scores)
        assert len(applied) > 0

    def test_compute_bonus(self):
        engine = ScoringRulesEngine()
        scores = {"trend_score": 9.0, "competition_score": 2.0, "verification_score": 8.5, "confidence": 0.9}
        bonus = engine.compute_bonus(scores)
        assert bonus > 0

    def test_penalty_rules(self):
        engine = ScoringRulesEngine()
        scores = {"trend_score": 1.0, "competition_score": 9.5, "knowledge_score": 0.5}
        bonus = engine.compute_bonus(scores)
        assert bonus < 0

    def test_list_rules(self):
        engine = ScoringRulesEngine()
        rules = engine.list_rules()
        assert len(rules) > 0

    def test_reset_to_defaults(self):
        engine = ScoringRulesEngine()
        engine.add_rule(ScoringRule("temp", "Temp"))
        engine.reset_to_defaults()
        assert engine.get_rule("temp") is None

    def test_rule_to_dict(self):
        r = ScoringRule("r1", "Test", "bonus", "trend >= 5", 1.0)
        d = r.to_dict()
        assert d["rule_id"] == "r1"


# ═══════════════════════════════════════════
# Test 2: Weight Manager
# ═══════════════════════════════════════════

class TestWeightManager:
    def test_get_default_weights(self):
        wm = WeightManager()
        w = wm.get_weights("general")
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_get_niche_weights(self):
        wm = WeightManager()
        w = wm.get_weights("finance")
        assert "verification" in w
        assert w["verification"] >= 0.2  # Finance should weight verification heavily

    def test_set_weights(self):
        wm = WeightManager()
        wm.set_weights("custom", {"trend": 0.5, "audience": 0.2, "competition": 0.1,
                                   "knowledge": 0.1, "verification": 0.05, "engagement": 0.03, "freshness": 0.02})
        w = wm.get_weights("custom")
        assert w["trend"] == 0.5

    def test_set_weights_invalid_sum(self):
        wm = WeightManager()
        with pytest.raises(ValueError):
            wm.set_weights("bad", {"trend": 0.5, "audience": 0.5, "competition": 0.5,
                                    "knowledge": 0.5, "verification": 0.5, "engagement": 0.5, "freshness": 0.5})

    def test_set_weights_unknown_dim(self):
        wm = WeightManager()
        with pytest.raises(ValueError):
            wm.set_weights("bad", {"unknown_dim": 1.0})

    def test_get_all_niches(self):
        wm = WeightManager()
        niches = wm.get_all_niches()
        assert "finance" in niches
        assert "technology" in niches

    def test_interpolate(self):
        wm = WeightManager()
        w = wm.interpolate("finance", "technology", 0.5)
        assert abs(sum(w.values()) - 1.0) < 0.01

    def test_remove_niche(self):
        wm = WeightManager()
        wm.register_niche("temp", DEFAULT_WEIGHTS)
        assert wm.remove_niche("temp") is True

    def test_normalize_weights(self):
        wm = WeightManager()
        normalized = wm.normalize_weights({"a": 2, "b": 3, "c": 5})
        assert abs(sum(normalized.values()) - 1.0) < 0.01


# ═══════════════════════════════════════════
# Test 3: Score Normalizer
# ═══════════════════════════════════════════

class TestScoreNormalizer:
    def test_normalize_minmax(self):
        assert ScoreNormalizer.normalize_minmax(5, 0, 10) == 5.0
        assert ScoreNormalizer.normalize_minmax(0, 0, 10) == 0.0
        assert ScoreNormalizer.normalize_minmax(10, 0, 10) == 10.0

    def test_normalize_minmax_custom_range(self):
        assert ScoreNormalizer.normalize_minmax(50, 0, 100) == 5.0

    def test_clip(self):
        assert ScoreNormalizer.clip(15) == 10.0
        assert ScoreNormalizer.clip(-5) == 0.0
        assert ScoreNormalizer.clip(5) == 5.0

    def test_normalize_distribution(self):
        result = ScoreNormalizer.normalize_distribution({"a": 1, "b": 5, "c": 10})
        assert result["a"] == 0.0
        assert result["c"] == 10.0

    def test_weighted_average(self):
        scores = {"a": 8.0, "b": 6.0}
        weights = {"a": 0.6, "b": 0.4}
        avg = ScoreNormalizer.weighted_average(scores, weights)
        assert avg == 7.2

    def test_geometric_mean(self):
        gm = ScoreNormalizer.geometric_mean([4, 9])
        assert gm == 6.0

    def test_harmonic_mean(self):
        hm = ScoreNormalizer.harmonic_mean([2, 4])
        assert hm > 0

    def test_empty_values(self):
        assert ScoreNormalizer.geometric_mean([]) == 0.0
        assert ScoreNormalizer.harmonic_mean([]) == 0.0
        assert ScoreNormalizer.weighted_average({}, {}) == 0.0


# ═══════════════════════════════════════════
# Test 4: Opportunity Scorer
# ═══════════════════════════════════════════

class TestOpportunityScorer:
    def test_high_opportunity(self):
        os = OpportunityScorer()
        result = os.calculate(trend_score=9.0, competition_score=2.0, audience_score=8.0, knowledge_score=8.0)
        assert result.overall_opportunity >= 7.0

    def test_low_opportunity(self):
        os = OpportunityScorer()
        result = os.calculate(trend_score=2.0, competition_score=9.0, audience_score=3.0, knowledge_score=2.0)
        assert result.overall_opportunity <= 4.0

    def test_result_to_dict(self):
        os = OpportunityScorer()
        result = os.calculate()
        d = result.to_dict()
        assert "overall_opportunity" in d
        assert "market_opportunity" in d

    def test_factors_recorded(self):
        os = OpportunityScorer()
        result = os.calculate(trend_score=7.0)
        assert "trend_input" in result.factors


# ═══════════════════════════════════════════
# Test 5: Risk Scorer
# ═══════════════════════════════════════════

class TestRiskScorer:
    def test_low_risk(self):
        rs = RiskScorer()
        result = rs.calculate(trend_score=8.0, competition_score=2.0, knowledge_score=9.0, audience_score=8.0)
        assert result.risk_level in ("VERY_LOW", "LOW")

    def test_high_risk(self):
        rs = RiskScorer()
        result = rs.calculate(trend_score=1.0, competition_score=9.5, knowledge_score=1.0, audience_score=1.0)
        assert result.risk_level in ("HIGH", "CRITICAL")

    def test_risk_factors(self):
        rs = RiskScorer()
        result = rs.calculate(competition_score=9.5)
        assert len(result.risk_factors) > 0

    def test_mitigations(self):
        rs = RiskScorer()
        result = rs.calculate(competition_score=9.5, knowledge_score=1.0)
        assert len(result.mitigations) > 0

    def test_result_to_dict(self):
        rs = RiskScorer()
        result = rs.calculate()
        d = result.to_dict()
        assert "risk_level" in d
        assert "risk_factors" in d


# ═══════════════════════════════════════════
# Test 6: Confidence Fusion
# ═══════════════════════════════════════════

class TestConfidenceFusion:
    def test_fuse_high(self):
        cf = ConfidenceFusion()
        result = cf.fuse({"trend": 0.9, "audience": 0.85, "knowledge": 0.9})
        assert result.confidence >= 0.8

    def test_fuse_low(self):
        cf = ConfidenceFusion()
        result = cf.fuse({"trend": 0.2, "audience": 0.3})
        assert result.confidence < 0.5

    def test_fuse_empty(self):
        cf = ConfidenceFusion()
        result = cf.fuse({})
        assert result.confidence == 0.0

    def test_fuse_with_evidence(self):
        cf = ConfidenceFusion()
        result = cf.fuse({"trend": 0.8}, evidence=["ev1", "ev2", "ev3", "ev4", "ev5"])
        assert result.confidence > 0.8

    def test_from_scores(self):
        cf = ConfidenceFusion()
        result = cf.from_scores({"trend": 8.0, "audience": 7.0})
        assert result.confidence > 0


# ═══════════════════════════════════════════
# Test 7: Scoring Engine
# ═══════════════════════════════════════════

class TestScoringEngine:
    def test_score_basic(self):
        se = ScoringEngine()
        result = se.score("AI Jobs", "ai", {
            "trend": 8.0, "audience": 7.0, "competition": 4.0,
            "knowledge": 8.0, "verification": 9.0,
        })
        assert result.overall_score > 5.0
        assert result.recommendation in ScoringResult.RECOMMENDATIONS

    def test_score_strong_publish(self):
        se = ScoringEngine()
        result = se.score("Hot Topic", "ai", {
            "trend": 9.0, "audience": 8.5, "competition": 2.0,
            "knowledge": 9.0, "verification": 9.5, "engagement": 8.0,
        }, evidence=["ev1", "ev2", "ev3", "ev4"])
        assert result.recommendation in ("strong_publish", "publish")

    def test_score_skip(self):
        se = ScoringEngine()
        result = se.score("Dead Topic", "general", {
            "trend": 1.0, "audience": 1.0, "competition": 9.5,
            "knowledge": 1.0, "verification": 1.0,
        })
        assert result.recommendation in ("skip", "revise")

    def test_score_includes_opportunity(self):
        se = ScoringEngine()
        result = se.score("Test", "ai", {"trend": 7.0, "audience": 6.0})
        assert result.opportunity is not None
        assert result.opportunity.overall_opportunity > 0

    def test_score_includes_risk(self):
        se = ScoringEngine()
        result = se.score("Test", "ai", {"trend": 7.0, "competition": 3.0})
        assert result.risk is not None
        assert result.risk.risk_level in ("VERY_LOW", "LOW", "MEDIUM", "HIGH", "CRITICAL")

    def test_niche_specific_weights(self):
        se = ScoringEngine()
        result_ai = se.score("Test", "ai", {"trend": 8.0, "verification": 5.0})
        result_fin = se.score("Test", "finance", {"trend": 8.0, "verification": 5.0})
        # Finance weights verification higher, so different overall
        assert result_ai.overall_score != result_fin.overall_score

    def test_result_to_dict(self):
        se = ScoringEngine()
        result = se.score("Test", "ai", {"trend": 7.0})
        d = result.to_dict()
        assert "topic" in d
        assert "overall_score" in d
        assert "recommendation" in d
        assert "confidence" in d

    def test_weighted_scores(self):
        se = ScoringEngine()
        result = se.score("Test", "ai", {"trend": 8.0, "audience": 6.0})
        assert len(result.weighted_scores) > 0

    def test_raw_scores_clipped(self):
        se = ScoringEngine()
        result = se.score("Test", "ai", {"trend": 15.0, "audience": -5.0})
        assert result.raw_scores["trend"] == 10.0
        assert result.raw_scores["audience"] == 0.0


# ═══════════════════════════════════════════
# Test 8: Scoring Manager
# ═══════════════════════════════════════════

class TestScoringManager:
    def test_score_topic(self, manager):
        result = manager.score_topic("AI Jobs", "ai", {
            "trend": 8.0, "audience": 7.0, "competition": 4.0,
        })
        assert result.overall_score > 0
        assert result.recommendation in ScoringResult.RECOMMENDATIONS

    def test_get_result(self, manager):
        manager.score_topic("Test", "ai", {"trend": 7.0})
        result = manager.get_result("Test")
        assert result is not None

    def test_get_ranked(self, manager):
        manager.score_topic("A", "ai", {"trend": 9.0})
        manager.score_topic("B", "ai", {"trend": 5.0})
        ranked = manager.get_ranked(10)
        assert len(ranked) == 2
        assert ranked[0].overall_score >= ranked[1].overall_score

    def test_get_recommendations(self, manager):
        manager.score_topic("Good", "ai", {
            "trend": 9.0, "audience": 9.0, "competition": 1.0,
            "knowledge": 9.0, "verification": 9.5, "engagement": 9.0,
        }, evidence=["ev1", "ev2", "ev3", "ev4"])
        results = manager.get_recommendations("strong_publish")
        assert isinstance(results, list)

    def test_compare_topics(self, manager):
        manager.score_topic("A", "ai", {"trend": 9.0})
        manager.score_topic("B", "ai", {"trend": 4.0})
        cmp = manager.compare_topics("A", "B")
        assert cmp["winner"] == "A"

    def test_compare_missing(self, manager):
        cmp = manager.compare_topics("X", "Y")
        assert "error" in cmp

    def test_statistics(self, manager):
        manager.score_topic("A", "ai", {"trend": 7.0})
        stats = manager.get_statistics()
        assert stats["total"] == 1
        assert "avg_score" in stats

    def test_health_check(self, manager):
        h = manager.health_check()
        assert h["engine_ready"] is True
        assert h["available_niches"] > 0

    def test_persistence(self, tmp_path):
        path = tmp_path / "score.json"
        m1 = ScoringManager(storage_path=str(path))
        m1.score_topic("Test", "ai", {"trend": 7.0})
        assert path.exists()

    def test_no_storage(self):
        m = ScoringManager()
        m.score_topic("Test", "ai", {"trend": 7.0})
        assert m.get_result("Test") is not None

    def test_batch_scoring(self, manager):
        topics = [
            {"topic": "A", "scores": {"trend": 8.0}},
            {"topic": "B", "scores": {"trend": 5.0}},
        ]
        results = manager.score_batch(topics)
        assert len(results) == 2

    def test_custom_niche_weights(self, manager):
        manager.weight_manager.register_niche("custom_niche", {
            "trend": 0.5, "audience": 0.1, "competition": 0.1,
            "knowledge": 0.1, "verification": 0.1, "engagement": 0.05, "freshness": 0.05,
        })
        result = manager.score_topic("Test", "custom_niche", {"trend": 9.0})
        assert result.overall_score > 0

    def test_concurrent_scoring(self, manager):
        import threading
        errors = []

        def score(i):
            try:
                manager.score_topic(f"Topic_{i}", "ai", {"trend": float(i)})
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=score, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert manager.get_statistics()["total"] == 15
