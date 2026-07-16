"""Tests for Layer 6 Module 9 — Quality Scoring & Confidence Engine."""
from layers.layer06_quality.modules.quality_scoring_engine.score_aggregator import ScoreAggregator
from layers.layer06_quality.modules.quality_scoring_engine.confidence_fusion import ConfidenceFusion
from layers.layer06_quality.modules.quality_scoring_engine.quality_grader import QualityGrader
from layers.layer06_quality.modules.quality_scoring_engine.decision_engine import DecisionEngine
from layers.layer06_quality.modules.quality_scoring_engine.explainability_engine import ExplainabilityEngine
from layers.layer06_quality.modules.quality_scoring_engine.risk_analyzer import RiskAnalyzer
from layers.layer06_quality.modules.quality_scoring_engine.quality_engine import QualityEngine
from layers.layer06_quality.modules.quality_scoring_engine.quality_result import ModuleScore, QualityResult


def _make_scores(**kwargs):
    """Helper to create module scores for testing."""
    defaults = {
        "content_quality": (94, 0.95),
        "fact_validation": (98, 0.98),
        "safety": (100, 1.0),
        "originality": (91, 0.90),
        "seo": (89, 0.88),
        "platform_compliance": (97, 0.95),
        "brand_voice": (92, 0.85),
    }
    scores = []
    for name, (score, conf) in defaults.items():
        if name in kwargs:
            score, conf = kwargs[name]
        scores.append(ModuleScore(name, score, conf))
    return scores


# ── ScoreAggregator Tests ──

class TestScoreAggregator:
    def setup_method(self):
        self.agg = ScoreAggregator()

    def test_basic_aggregation(self):
        scores = _make_scores()
        result = self.agg.aggregate(scores)
        assert 70 <= result <= 100

    def test_empty_scores(self):
        assert self.agg.aggregate([]) == 0.0

    def test_single_module(self):
        scores = [ModuleScore("safety", 95, 1.0)]
        result = self.agg.aggregate(scores)
        assert result == 95.0

    def test_low_score_pulls_down(self):
        scores = _make_scores(safety=(20, 1.0))
        result = self.agg.aggregate(scores)
        assert result < 90

    def test_confidence_weights(self):
        high_conf = [ModuleScore("safety", 90, 1.0)]
        low_conf = [ModuleScore("safety", 90, 0.3)]
        r1 = self.agg.aggregate(high_conf)
        r2 = self.agg.aggregate(low_conf)
        assert r1 == r2  # Same score, but confidence affects fusion

    def test_get_missing_modules(self):
        scores = [ModuleScore("safety", 90, 1.0)]
        missing = self.agg.get_missing_modules(scores)
        assert "safety" not in missing
        assert "content_quality" in missing

    def test_set_weight(self):
        self.agg.set_weight("safety", 0.5)
        weights = self.agg.get_weights()
        assert weights["safety"] > 0.3  # normalized weight should be highest

    def test_aggregate_confidence(self):
        scores = _make_scores()
        conf = self.agg.aggregate_confidence(scores)
        assert 0.0 <= conf <= 1.0


# ── ConfidenceFusion Tests ──

class TestConfidenceFusion:
    def setup_method(self):
        self.fusion = ConfidenceFusion()

    def test_basic_fusion(self):
        scores = _make_scores()
        result = self.fusion.fuse(scores)
        assert 0.0 <= result <= 1.0

    def test_empty_scores(self):
        assert self.fusion.fuse([]) == 0.0

    def test_high_confidence_fusion(self):
        scores = [ModuleScore("safety", 100, 1.0)]
        result = self.fusion.fuse(scores)
        assert result >= 0.8

    def test_critical_issues_reduce_confidence(self):
        ms = ModuleScore("safety", 50, 0.5)
        ms.critical_issues.append("Critical failure")
        result = self.fusion.fuse([ms])
        assert result < 0.5

    def test_fuse_with_context(self):
        scores = _make_scores()
        result = self.fusion.fuse_with_context(scores, 0.9, 0.9)
        assert result >= 0.5

    def test_fuse_count(self):
        scores = _make_scores()
        self.fusion.fuse(scores)
        assert self.fusion.fuse_count == 1


# ── QualityGrader Tests ──

class TestQualityGrader:
    def setup_method(self):
        self.grader = QualityGrader()

    def test_grade_a_plus(self):
        assert self.grader.grade(98) == "A+"

    def test_grade_a(self):
        assert self.grader.grade(94) == "A"

    def test_grade_b(self):
        assert self.grader.grade(84) == "B"

    def test_grade_c(self):
        assert self.grader.grade(74) == "C"

    def test_grade_d(self):
        assert self.grader.grade(65) == "D"

    def test_grade_f(self):
        assert self.grader.grade(30) == "F"

    def test_grade_description(self):
        desc = self.grader.grade_description("A+")
        assert "Exceptional" in desc

    def test_is_passing(self):
        assert self.grader.is_passing("B")
        assert not self.grader.is_passing("D")

    def test_is_publish_ready(self):
        assert self.grader.is_publish_ready("A")
        assert self.grader.is_publish_ready("B-")
        assert not self.grader.is_publish_ready("C")


# ── DecisionEngine Tests ──

class TestDecisionEngine:
    def setup_method(self):
        self.engine = DecisionEngine()

    def test_approve_high_score(self):
        scores = _make_scores()
        result = self.engine.decide(95, scores, confidence=0.95)
        assert result.decision == "approve"

    def test_approve_with_warnings(self):
        scores = _make_scores()
        result = self.engine.decide(75, scores, confidence=0.8)
        assert result.decision == "approve_with_warnings"

    def test_human_review(self):
        scores = _make_scores()
        result = self.engine.decide(55, scores, confidence=0.6)
        assert result.decision == "human_review"

    def test_revise(self):
        scores = _make_scores()
        result = self.engine.decide(40, scores, confidence=0.5)
        assert result.decision == "revise"

    def test_reject(self):
        scores = _make_scores()
        result = self.engine.decide(20, scores, confidence=0.3)
        assert result.decision == "reject"

    def test_hard_stop_safety(self):
        scores = [ModuleScore("safety", 15, 1.0)]
        result = self.engine.decide(90, scores, confidence=0.9)
        assert result.decision == "reject"
        assert "safety_critical" in result.hard_stops_triggered

    def test_hard_stop_facts(self):
        scores = [ModuleScore("fact_validation", 10, 1.0)]
        result = self.engine.decide(90, scores, confidence=0.9)
        assert result.decision == "reject"

    def test_module_contributions(self):
        scores = _make_scores()
        result = self.engine.decide(90, scores, confidence=0.9)
        assert "safety" in result.module_contributions
        assert result.module_contributions["safety"] == "positive"

    def test_to_dict(self):
        scores = _make_scores()
        result = self.engine.decide(90, scores, confidence=0.9)
        d = result.to_dict()
        assert "decision" in d
        assert "hard_stops" in d

    def test_decision_count(self):
        self.engine.decide(90, [], 0.9)
        assert self.engine.decision_count == 1


# ── RiskAnalyzer Tests ──

class TestRiskAnalyzer:
    def setup_method(self):
        self.analyzer = RiskAnalyzer()

    def test_low_risk(self):
        scores = _make_scores()
        result = self.analyzer.analyze(scores, 95)
        assert result.level == "low"

    def test_high_risk_safety(self):
        scores = _make_scores(safety=(20, 1.0))
        result = self.analyzer.analyze(scores, 80)
        assert result.level in ("medium", "high", "critical")

    def test_medium_risk(self):
        scores = _make_scores(safety=(60, 0.8))
        result = self.analyzer.analyze(scores, 50)
        assert result.level in ("medium", "high", "critical")

    def test_critical_issues_increase_risk(self):
        ms = ModuleScore("safety", 50, 0.5)
        ms.critical_issues.append("Major issue")
        result = self.analyzer.analyze([ms], 30)
        assert result.level in ("medium", "high", "critical")

    def test_to_dict(self):
        result = self.analyzer.analyze([], 90)
        d = result.to_dict()
        assert "level" in d
        assert "factors" in d


# ── ExplainabilityEngine Tests ──

class TestExplainabilityEngine:
    def setup_method(self):
        self.engine = ExplainabilityEngine()

    def test_explain(self):
        scores = _make_scores()
        explanations = self.engine.explain(95, scores, "approve", "low")
        assert len(explanations) >= len(scores)

    def test_explain_empty(self):
        explanations = self.engine.explain(0, [], "reject", "critical")
        assert len(explanations) >= 2  # decision + risk

    def test_format_summary(self):
        scores = _make_scores()
        explanations = self.engine.explain(95, scores, "approve", "low")
        summary = self.engine.format_summary(95, "A+", "approve", explanations)
        assert "95" in summary
        assert "A+" in summary

    def test_explain_count(self):
        self.engine.explain(90, [], "approve", "low")
        assert self.engine.explain_count == 1


# ── QualityEngine Tests ──

class TestQualityEngine:
    def setup_method(self):
        self.engine = QualityEngine()

    def test_full_pipeline(self):
        scores = _make_scores()
        result = self.engine.score(scores)
        assert isinstance(result, QualityResult)
        assert result.overall_score > 0
        assert result.grade in ("A+", "A", "A-", "B+", "B", "B-")
        assert result.decision in ("approve", "approve_with_warnings")

    def test_score_quick(self):
        scores = _make_scores()
        result = self.engine.score_quick(scores)
        assert "overall_score" in result
        assert "grade" in result
        assert "decision" in result

    def test_format_summary(self):
        scores = _make_scores()
        result = self.engine.score(scores)
        summary = self.engine.format_summary(result)
        assert "Overall Quality" in summary

    def test_with_critical_issues(self):
        ms = ModuleScore("safety", 80, 0.8)
        ms.critical_issues.append("Safety violation")
        scores = [ms]
        result = self.engine.score(scores)
        assert len(result.explanations) > 0  # explanations should mention issues

    def test_statistics_populated(self):
        scores = _make_scores()
        result = self.engine.score(scores)
        assert "scoring_time_ms" in result.statistics
        assert "modules_scored" in result.statistics

    def test_check_count(self):
        self.engine.score(_make_scores())
        assert self.engine.check_count == 1

    def test_to_dict(self):
        scores = _make_scores()
        result = self.engine.score(scores)
        d = result.to_dict()
        assert "overall_score" in d
        assert "module_scores" in d
        assert "explanations" in d

    def test_quality_result_get_module_score(self):
        scores = _make_scores()
        result = self.engine.score(scores)
        safety = result.get_module_score("safety")
        assert safety is not None
        assert result.get_module_score("nonexistent") is None
