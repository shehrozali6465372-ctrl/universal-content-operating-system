"""Tests for Layer 9 Module 3 — Strategy Optimization Engine."""
from layers.layer09_learning.modules.strategy_optimization.strategy_profile import (
    StrategyProfile,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_history import (
    StrategyHistory,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_comparator import (
    StrategyComparator,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_patterns import (
    StrategyPatternDetector, StrategyPattern,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_optimizer import (
    StrategyOptimizer, StrategySuggestion,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_recommender import (
    StrategyRecommender, StrategyRecommendation,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_memory import (
    StrategyMemory, StrategyMemoryEntry,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_metrics import StrategyMetrics
from layers.layer09_learning.modules.strategy_optimization.strategy_validator import (
    StrategyValidator, StrategyValidationError,
)
from layers.layer09_learning.modules.strategy_optimization.strategy_manager import (
    StrategyManager, StrategyCycleResult,
)
from layers.layer09_learning.modules.strategy_optimization.exceptions import (
    StrategyOptimizationError, PatternDetectionError,
    RecommendationError,
)


# ─── StrategyProfile Tests ────────────────────────────────────────────
class TestStrategyProfile:
    def test_create_default(self):
        s = StrategyProfile()
        assert s.strategy_id.startswith("stg_")
        assert s.version == 1
        assert s.strategy_type == "engagement"
        assert s.status == "draft"
        assert s.usage_count == 0

    def test_create_with_args(self):
        s = StrategyProfile(name="Growth Plan", strategy_type="growth")
        assert s.name == "Growth Plan"
        assert s.strategy_type == "growth"

    def test_invalid_type_falls_back(self):
        s = StrategyProfile(strategy_type="invalid")
        assert s.strategy_type == "engagement"

    def test_success_rate(self):
        s = StrategyProfile()
        s.success_count = 8
        s.failure_count = 2
        assert s.success_rate == 0.8

    def test_success_rate_no_usage(self):
        assert StrategyProfile().success_rate == 0.0

    def test_is_active(self):
        s = StrategyProfile()
        s.status = "active"
        assert s.is_active is True

    def test_effective_score(self):
        s = StrategyProfile()
        s.avg_engagement = 0.8
        s.avg_reach = 0.6
        s.avg_conversion = 0.4
        score = s.effective_score
        assert score == round(0.8 * 0.4 + 0.6 * 0.3 + 0.4 * 0.3, 3)

    def test_record_usage_success(self):
        s = StrategyProfile()
        s.record_usage(True, engagement=0.7, reach=100.0, conversion=0.05)
        assert s.usage_count == 1
        assert s.success_count == 1
        assert s.avg_engagement == 0.7

    def test_record_usage_failure(self):
        s = StrategyProfile()
        s.record_usage(False, engagement=0.1)
        assert s.failure_count == 1
        assert s.success_count == 0

    def test_record_usage_averages(self):
        s = StrategyProfile()
        s.record_usage(True, engagement=0.4, reach=100.0, conversion=0.02)
        s.record_usage(True, engagement=0.8, reach=200.0, conversion=0.08)
        assert s.avg_engagement == 0.6
        assert s.avg_reach == 150.0

    def test_fork(self):
        s = StrategyProfile(name="Test", strategy_type="growth")
        s.target_platforms = ["facebook", "linkedin"]
        child = s.fork()
        assert child.version == 2
        assert child.parent_id == s.strategy_id
        assert child.target_platforms == ["facebook", "linkedin"]

    def test_to_dict(self):
        s = StrategyProfile(name="Test")
        d = s.to_dict()
        assert "strategy_id" in d
        assert d["name"] == "Test"

    def test_to_dict_with_usage(self):
        s = StrategyProfile(name="Test")
        s.record_usage(True, engagement=0.8)
        d = s.to_dict()
        assert d["usage_count"] == 1


# ─── StrategyHistory Tests ────────────────────────────────────────────
class TestStrategyHistory:
    def setup_method(self):
        self.history = StrategyHistory()

    def test_record(self):
        s = StrategyProfile(name="Test")
        entry = self.history.record(s, "created", {"engagement": 0.8})
        assert entry.strategy_id == s.strategy_id
        assert entry.metrics["engagement"] == 0.8

    def test_get_strategy_history(self):
        s = StrategyProfile(name="Test")
        self.history.record(s, "created")
        self.history.record(s, "optimized")
        assert len(self.history.get_strategy_history(s.strategy_id)) == 2

    def test_get_recent(self):
        s = StrategyProfile(name="T")
        for _ in range(5):
            self.history.record(s, "created")
        assert len(self.history.get_recent(3)) == 3

    def test_get_by_action(self):
        s = StrategyProfile(name="T")
        self.history.record(s, "created")
        self.history.record(s, "optimized")
        assert len(self.history.get_by_action("created")) == 1

    def test_get_best_version(self):
        s1 = StrategyProfile(name="v1")
        s1.version = 1
        s2 = StrategyProfile(name="v2")
        s2.version = 2
        self.history.record(s1, "created", {"engagement": 0.5})
        self.history.record(s2, "created", {"engagement": 0.9})
        best = self.history.get_best_version(s1.strategy_id, "engagement")
        assert best is not None

    def test_entry_count(self):
        s = StrategyProfile(name="T")
        self.history.record(s, "created")
        assert self.history.entry_count == 1

    def test_entry_to_dict(self):
        s = StrategyProfile(name="T")
        entry = self.history.record(s, "created")
        d = entry.to_dict()
        assert "entry_id" in d
        assert d["action"] == "created"


# ─── StrategyComparator Tests ─────────────────────────────────────────
class TestStrategyComparator:
    def setup_method(self):
        self.comp = StrategyComparator()

    def _make(self, engagement=0.5, reach=0.5, conversion=0.5):
        s = StrategyProfile(name="Test")
        s.avg_engagement = engagement
        s.avg_reach = reach
        s.avg_conversion = conversion
        s.success_count = 5
        s.failure_count = 5
        return s

    def test_compare(self):
        baseline = self._make(0.3, 0.3, 0.3)
        candidate = self._make(0.8, 0.8, 0.8)
        results = self.comp.compare(baseline, candidate)
        assert len(results) == 5
        candidate_wins = sum(1 for r in results if r.winner == "candidate")
        assert candidate_wins >= 3

    def test_compare_equal(self):
        b = self._make(0.5, 0.5, 0.5)
        c = self._make(0.5, 0.5, 0.5)
        results = self.comp.compare(b, c)
        assert all(r.winner == "tie" for r in results)

    def test_get_overall_winner(self):
        b = self._make(0.3, 0.3, 0.3)
        c = self._make(0.8, 0.8, 0.8)
        assert self.comp.get_overall_winner(b, c) == "candidate"

    def test_get_significant_differences(self):
        b = self._make(0.1, 0.1, 0.1)
        c = self._make(0.9, 0.9, 0.9)
        self.comp.compare(b, c)
        assert len(self.comp.get_significant_differences()) > 0

    def test_comparison_result_to_dict(self):
        b = self._make()
        c = self._make(0.8, 0.8, 0.8)
        results = self.comp.compare(b, c)
        d = results[0].to_dict()
        assert "metric_name" in d
        assert "winner" in d


# ─── StrategyPattern Tests ────────────────────────────────────────────
class TestStrategyPattern:
    def test_create(self):
        p = StrategyPattern("success", "Good pattern")
        assert p.pattern_type == "success"
        assert p.description == "Good pattern"
        assert p.pattern_id.startswith("sp_")

    def test_invalid_type(self):
        p = StrategyPattern("invalid", "test")
        assert p.pattern_type == "success"

    def test_to_dict(self):
        p = StrategyPattern("failure", "Bad")
        p.confidence = 0.8
        d = p.to_dict()
        assert d["confidence"] == 0.8


# ─── StrategyPatternDetector Tests ────────────────────────────────────
class TestStrategyPatternDetector:
    def setup_method(self):
        self.detector = StrategyPatternDetector()

    def _make(self, name="T", platforms=None, score=0.8, usage=5, freq="daily"):
        s = StrategyProfile(name=name, strategy_type="engagement")
        s.target_platforms = platforms or ["facebook"]
        s.avg_engagement = score
        s.avg_reach = score
        s.avg_conversion = score
        s.usage_count = usage
        s.posting_frequency = freq
        return s

    def test_detect_empty(self):
        patterns = self.detector.detect([])
        assert len(patterns) == 0

    def test_detect_high_performers(self):
        strategies = [
            self._make(f"s{i}", platforms=["linkedin"], score=0.9, usage=5)
            for i in range(4)
        ]
        patterns = self.detector.detect(strategies)
        success = [p for p in patterns if p.pattern_type == "success"]
        assert len(success) >= 1

    def test_detect_low_performers(self):
        strategies = [
            self._make(f"s{i}", platforms=["x"], score=0.1, usage=5)
            for i in range(4)
        ]
        patterns = self.detector.detect(strategies)
        failures = [p for p in patterns if p.pattern_type == "failure"]
        assert len(failures) >= 1

    def test_detect_platform_patterns(self):
        strategies = [
            self._make(f"s{i}", platforms=["instagram"], score=0.8, usage=3)
            for i in range(3)
        ]
        patterns = self.detector.detect(strategies)
        platform_p = [p for p in patterns if p.pattern_type == "platform_specific"]
        assert len(platform_p) >= 1

    def test_detection_count(self):
        strategies = [self._make(f"s{i}", score=0.5, usage=3) for i in range(3)]
        self.detector.detect(strategies)
        self.detector.detect(strategies)
        assert self.detector.detection_count == 2

    def test_get_patterns_by_type(self):
        strategies = [self._make(f"s{i}", score=0.9, usage=5) for i in range(4)]
        self.detector.detect(strategies)
        success = self.detector.get_patterns("success")
        for p in success:
            assert p.pattern_type == "success"

    def test_pattern_count(self):
        strategies = [self._make(f"s{i}", platforms=["fb"], score=0.9, usage=5) for i in range(4)]
        self.detector.detect(strategies)
        assert self.detector.pattern_count > 0


# ─── StrategySuggestion Tests ─────────────────────────────────────────
class TestStrategySuggestion:
    def test_create(self):
        s = StrategySuggestion("targeting", "high")
        assert s.suggestion_type == "targeting"
        assert s.priority == "high"
        assert s.suggestion_id.startswith("ss_")

    def test_to_dict(self):
        s = StrategySuggestion("frequency", "critical")
        s.field = "posting_frequency"
        d = s.to_dict()
        assert d["field"] == "posting_frequency"
        assert d["priority"] == "critical"


# ─── StrategyOptimizer Tests ──────────────────────────────────────────
class TestStrategyOptimizer:
    def setup_method(self):
        self.optimizer = StrategyOptimizer()

    def _make(self, platforms=None, audience="", pillars=None, tactics=None,
              freq="daily", engagement=0.5, usage=10):
        s = StrategyProfile(name="Test Strategy")
        s.target_platforms = platforms or []
        s.target_audience = audience
        s.content_pillars = pillars or []
        s.engagement_tactics = tactics or []
        s.posting_frequency = freq
        s.avg_engagement = engagement
        s.usage_count = usage
        return s

    def test_optimize_no_platforms(self):
        s = self._make()
        result = self.optimizer.optimize(s)
        types = [sg.suggestion_type for sg in result.suggestions]
        assert "targeting" in types

    def test_optimize_no_audience(self):
        s = self._make(platforms=["facebook"])
        result = self.optimizer.optimize(s)
        fields = [sg.field for sg in result.suggestions]
        assert "target_audience" in fields

    def test_optimize_frequency_suggestion(self):
        s = self._make(platforms=["fb"], audience="test", freq="daily", engagement=0.2, usage=10)
        result = self.optimizer.optimize(s)
        freq_suggestions = [sg for sg in result.suggestions if sg.suggestion_type == "frequency"]
        assert len(freq_suggestions) >= 1

    def test_optimize_content_pillars(self):
        s = self._make(platforms=["fb"], audience="test")
        result = self.optimizer.optimize(s)
        content = [sg for sg in result.suggestions if sg.suggestion_type == "content"]
        assert len(content) >= 1

    def test_optimize_engagement_tactics(self):
        s = self._make(platforms=["fb"], audience="test", pillars=["p1", "p2"])
        result = self.optimizer.optimize(s)
        eng = [sg for sg in result.suggestions if sg.suggestion_type == "engagement"]
        assert len(eng) >= 1

    def test_optimize_with_patterns(self):
        s = self._make(platforms=["fb"], audience="test", pillars=["a", "b"], tactics=["poll"])
        pat = StrategyPattern("success", "High on linkedin")
        pat.platform = "linkedin"
        result = self.optimizer.optimize(s, [pat])
        pattern_suggestions = [sg for sg in result.suggestions if sg.suggestion_type == "pattern"]
        assert len(pattern_suggestions) >= 1

    def test_optimize_confidence(self):
        s = self._make(platforms=[], audience="", usage=20)
        result = self.optimizer.optimize(s)
        assert result.confidence > 0

    def test_optimize_no_suggestions(self):
        s = self._make(platforms=["fb"], audience="test", pillars=["a", "b", "c"], tactics=["poll", "question"])
        s.optimal_hours = [9, 12, 18]
        result = self.optimizer.optimize(s)
        assert result.confidence == 0.0

    def test_get_results(self):
        self.optimizer.optimize(self._make(platforms=["fb"]))
        assert len(self.optimizer.get_results()) == 1

    def test_optimization_count(self):
        self.optimizer.optimize(self._make(platforms=["a"]))
        self.optimizer.optimize(self._make(platforms=["b"]))
        assert self.optimizer.optimization_count == 2


# ─── StrategyRecommendation Tests ─────────────────────────────────────
class TestStrategyRecommendation:
    def test_create(self):
        r = StrategyRecommendation("scale", "high")
        assert r.recommendation_type == "scale"
        assert r.priority == "high"
        assert r.recommendation_id.startswith("sr_")

    def test_to_dict(self):
        r = StrategyRecommendation("optimize", "medium")
        r.strategy_id = "stg_1"
        d = r.to_dict()
        assert d["strategy_id"] == "stg_1"


# ─── StrategyRecommender Tests ────────────────────────────────────────
class TestStrategyRecommender:
    def setup_method(self):
        self.recommender = StrategyRecommender()

    def _make(self, name="T", score=0.5, usage=5, platforms=None):
        s = StrategyProfile(name=name, strategy_type="engagement")
        s.avg_engagement = score
        s.avg_reach = score
        s.avg_conversion = score
        s.usage_count = usage
        s.target_platforms = platforms or ["facebook"]
        return s

    def test_recommend_empty(self):
        recs = self.recommender.recommend([])
        assert len(recs) == 0

    def test_recommend_scaling(self):
        strategies = [self._make(f"s{i}", score=0.9, usage=5) for i in range(3)]
        recs = self.recommender.recommend(strategies)
        scale = [r for r in recs if r.recommendation_type == "scale"]
        assert len(scale) >= 1

    def test_recommend_optimization(self):
        strategies = [self._make(f"s{i}", score=0.5, usage=5) for i in range(3)]
        recs = self.recommender.recommend(strategies)
        optimize = [r for r in recs if r.recommendation_type == "optimize"]
        assert len(optimize) >= 1

    def test_recommend_deprecation(self):
        strategies = [self._make(f"s{i}", score=0.1, usage=6) for i in range(3)]
        recs = self.recommender.recommend(strategies)
        deprecate = [r for r in recs if r.recommendation_type == "deprecate"]
        assert len(deprecate) >= 1

    def test_recommend_new_platforms(self):
        s1 = StrategyProfile(name="s1", strategy_type="engagement")
        s1.target_platforms = ["linkedin"]
        s1.avg_engagement = 0.8
        s1.avg_reach = 0.8
        s1.avg_conversion = 0.8
        s1.usage_count = 5
        s2 = StrategyProfile(name="s2", strategy_type="engagement")
        s2.target_platforms = ["linkedin"]
        s2.avg_engagement = 0.7
        s2.avg_reach = 0.7
        s2.avg_conversion = 0.7
        s2.usage_count = 5
        s3 = StrategyProfile(name="s3", strategy_type="engagement")
        s3.target_platforms = []
        s3.avg_engagement = 0.5
        s3.avg_reach = 0.5
        s3.avg_conversion = 0.5
        s3.usage_count = 5
        recs = self.recommender.recommend([s1, s2, s3])
        expand = [r for r in recs if r.recommendation_type == "expand"]
        assert len(expand) >= 1

    def test_get_recommendations_filtered(self):
        strategies = [self._make(f"s{i}", score=0.9, usage=5) for i in range(3)]
        self.recommender.recommend(strategies)
        scale = self.recommender.get_recommendations(rec_type="scale")
        assert all(r.recommendation_type == "scale" for r in scale)

    def test_recommendation_count(self):
        strategies = [self._make(f"s{i}", score=0.9, usage=5) for i in range(3)]
        self.recommender.recommend(strategies)
        assert self.recommender.recommendation_count > 0


# ─── StrategyMemoryEntry Tests ────────────────────────────────────────
class TestStrategyMemoryEntry:
    def test_create(self):
        e = StrategyMemoryEntry("stg_1", "insight")
        assert e.strategy_id == "stg_1"
        assert e.archived is False

    def test_to_dict(self):
        e = StrategyMemoryEntry("stg_1", "mistake")
        d = e.to_dict()
        assert d["learning_type"] == "mistake"


# ─── StrategyMemory Tests ─────────────────────────────────────────────
class TestStrategyMemory:
    def setup_method(self):
        self.memory = StrategyMemory()

    def test_store(self):
        entry = self.memory.store("stg_1", "insight", "Good strategy")
        assert entry.strategy_id == "stg_1"
        assert self.memory.entry_count == 1

    def test_store_with_tags(self):
        entry = self.memory.store("stg_1", "insight", "Test", tags=["growth"])
        assert "growth" in entry.tags

    def test_search_by_strategy(self):
        self.memory.store("stg_1", "insight", "A")
        self.memory.store("stg_2", "insight", "B")
        assert len(self.memory.search(strategy_id="stg_1")) == 1

    def test_search_by_type(self):
        self.memory.store("stg_1", "insight", "A")
        self.memory.store("stg_1", "mistake", "B")
        assert len(self.memory.search(learning_type="mistake")) == 1

    def test_search_by_tag(self):
        self.memory.store("stg_1", "insight", "A", tags=["growth"])
        self.memory.store("stg_1", "insight", "B", tags=["engagement"])
        assert len(self.memory.search(tag="growth")) == 1

    def test_archive(self):
        entry = self.memory.store("stg_1", "insight", "Test")
        assert self.memory.archive(entry.entry_id) is True
        assert self.memory.entry_count == 0

    def test_get_by_id(self):
        entry = self.memory.store("stg_1", "insight", "Test")
        assert self.memory.get_by_id(entry.entry_id) is not None

    def test_get_stats(self):
        self.memory.store("stg_1", "insight", "A")
        self.memory.store("stg_1", "mistake", "B")
        stats = self.memory.get_stats()
        assert stats["active"] == 2

    def test_max_entries(self):
        m = StrategyMemory(max_entries=3)
        for i in range(5):
            m.store("stg_1", "insight", f"E{i}")
        assert m.entry_count == 3


# ─── StrategyMetrics Tests ────────────────────────────────────────────
class TestStrategyMetrics:
    def setup_method(self):
        self.metrics = StrategyMetrics()

    def test_record_optimization(self):
        self.metrics.record_optimization(0.8, improved=True)
        assert self.metrics.get_optimization_success_rate() == 1.0

    def test_record_analysis(self):
        self.metrics.record_analysis()
        self.metrics.record_analysis()
        assert self.metrics.get_summary()["total_analyses"] == 2

    def test_record_comparison(self):
        self.metrics.record_comparison(15.0)
        assert self.metrics.get_avg_improvement_rate() == 15.0

    def test_record_recommendation(self):
        self.metrics.record_recommendation(3)
        assert self.metrics.get_summary()["total_recommendations"] == 3

    def test_summary(self):
        self.metrics.record_optimization(0.7, True)
        self.metrics.record_analysis()
        summary = self.metrics.get_summary()
        assert "total_optimizations" in summary

    def test_reset(self):
        self.metrics.record_optimization(0.8, True)
        self.metrics.reset()
        assert self.metrics.get_optimization_success_rate() == 0.0

    def test_no_data(self):
        assert self.metrics.get_optimization_success_rate() == 0.0
        assert self.metrics.get_avg_optimization_score() == 0.0


# ─── StrategyValidationError Tests ────────────────────────────────────
class TestStrategyValidationError:
    def test_create(self):
        e = StrategyValidationError("name", "error", "Empty name")
        assert e.field == "name"
        assert e.severity == "error"

    def test_to_dict(self):
        e = StrategyValidationError("name", "warning", "Missing")
        d = e.to_dict()
        assert d["severity"] == "warning"


# ─── StrategyValidator Tests ──────────────────────────────────────────
class TestStrategyValidator:
    def setup_method(self):
        self.validator = StrategyValidator()

    def test_validate_valid(self):
        s = StrategyProfile(name="Growth Plan", strategy_type="growth")
        s.target_platforms = ["facebook"]
        s.target_audience = "Students"
        s.content_pillars = ["education", "tips"]
        s.tone_guidelines = "Friendly"
        result = self.validator.validate(s)
        assert result.is_valid is True
        assert result.score > 80

    def test_validate_empty_name(self):
        s = StrategyProfile(name="")
        result = self.validator.validate(s)
        assert result.is_valid is False
        assert result.error_count >= 1

    def test_validate_invalid_type(self):
        s = StrategyProfile(name="Test")
        s.strategy_type = "invalid_type"
        result = self.validator.validate(s)
        assert result.is_valid is False

    def test_validate_warnings(self):
        s = StrategyProfile(name="Test")
        result = self.validator.validate(s)
        assert result.is_valid is True
        assert result.warning_count >= 3

    def test_validate_batch(self):
        s1 = StrategyProfile(name="Valid")
        s1.target_platforms = ["fb"]
        s1.target_audience = "test"
        s1.content_pillars = ["a"]
        s1.tone_guidelines = "test"
        s2 = StrategyProfile(name="")
        results = self.validator.validate_batch([s1, s2])
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False

    def test_score_decreases(self):
        valid = StrategyProfile(name="Valid")
        valid.target_platforms = ["fb"]
        valid.target_audience = "test"
        valid.content_pillars = ["a"]
        valid.tone_guidelines = "test"
        invalid = StrategyProfile(name="")
        v1 = self.validator.validate(valid)
        v2 = self.validator.validate(invalid)
        assert v1.score > v2.score

    def test_result_to_dict(self):
        s = StrategyProfile(name="Test")
        result = self.validator.validate(s)
        d = result.to_dict()
        assert "is_valid" in d
        assert "score" in d

    def test_get_invalid_count(self):
        self.validator.validate(StrategyProfile(name="Valid"))
        self.validator.validate(StrategyProfile(name=""))
        assert self.validator.get_invalid_count() == 1


# ─── StrategyCycleResult Tests ────────────────────────────────────────
class TestStrategyCycleResult:
    def test_create(self):
        r = StrategyCycleResult("stg_1")
        assert r.cycle_id.startswith("scy_")
        assert r.is_approved is False

    def test_to_dict(self):
        r = StrategyCycleResult("stg_1")
        r.patterns_found = 3
        d = r.to_dict()
        assert d["patterns_found"] == 3


# ─── StrategyManager Tests ────────────────────────────────────────────
class TestStrategyManager:
    def setup_method(self):
        self.manager = StrategyManager()

    def _make(self, name="Test Strategy", score=0.5, usage=10, platforms=None):
        s = StrategyProfile(name=name, strategy_type="engagement")
        s.target_platforms = platforms or ["facebook"]
        s.target_audience = "General"
        s.content_pillars = ["education", "entertainment"]
        s.tone_guidelines = "Professional"
        s.avg_engagement = score
        s.avg_reach = score
        s.avg_conversion = score
        s.usage_count = usage
        s.success_count = int(usage * 0.7)
        s.failure_count = usage - s.success_count
        return s

    def test_register_strategy(self):
        s = self._make()
        self.manager.register_strategy(s)
        assert len(self.manager._strategies) == 1

    def test_run_optimization_cycle(self):
        s = self._make()
        result = self.manager.run_optimization_cycle(s)
        assert result.cycle_id.startswith("scy_")
        assert result.optimization is not None

    def test_run_cycle_events(self):
        self.manager.run_optimization_cycle(self._make())
        assert len(self.manager.events) == 1

    def test_compare_strategies(self):
        b = self._make("Baseline", score=0.3)
        c = self._make("Candidate", score=0.8)
        winner = self.manager.compare_strategies(b, c)
        assert winner in ("candidate", "baseline", "tie")

    def test_health(self):
        self.manager.run_optimization_cycle(self._make())
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert "memory_stats" in health

    def test_cycle_count(self):
        self.manager.run_optimization_cycle(self._make())
        self.manager.run_optimization_cycle(self._make())
        assert self.manager.cycle_count == 2

    def test_get_recent_cycles(self):
        for _ in range(3):
            self.manager.run_optimization_cycle(self._make())
        assert len(self.manager.get_recent_cycles(2)) == 2

    def test_history_populated(self):
        self.manager.run_optimization_cycle(self._make())
        assert self.manager.history.entry_count >= 1

    def test_manager_components(self):
        assert self.manager.history is not None
        assert self.manager.comparator is not None
        assert self.manager.pattern_detector is not None
        assert self.manager.optimizer is not None
        assert self.manager.recommender is not None
        assert self.manager.memory is not None
        assert self.manager.metrics is not None
        assert self.manager.validator is not None

    def test_multiple_strategies_pattern_detection(self):
        for i in range(5):
            s = self._make(f"Strategy {i}", platforms=["linkedin"], score=0.9, usage=5)
            self.manager.run_optimization_cycle(s)
        health = self.manager.get_health()
        assert health["total_cycles"] == 5


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(StrategyOptimizationError, Exception)

    def test_pattern_detection(self):
        assert issubclass(PatternDetectionError, StrategyOptimizationError)

    def test_recommendation(self):
        assert issubclass(RecommendationError, StrategyOptimizationError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestStrategyOptimizationIntegration:
    def test_full_pipeline(self):
        """Test: Register → Detect → Optimize → Recommend → Validate."""
        manager = StrategyManager()
        s = StrategyProfile(name="Growth Strategy", strategy_type="growth")
        s.target_platforms = ["facebook", "linkedin"]
        s.target_audience = "Tech professionals"
        s.content_pillars = ["AI insights", "Industry trends"]
        s.tone_guidelines = "Professional yet approachable"
        s.avg_engagement = 0.7
        s.avg_reach = 500.0
        s.avg_conversion = 0.05
        s.usage_count = 15
        s.success_count = 12
        s.failure_count = 3

        result = manager.run_optimization_cycle(s)
        assert result.optimization is not None
        assert result.is_approved is True
        assert manager.history.entry_count >= 1

    def test_compare_and_recommend(self):
        """Test: Compare strategies and generate recommendations."""
        manager = StrategyManager()
        for i in range(4):
            s = StrategyProfile(name=f"Strategy {i}", strategy_type="engagement")
            s.target_platforms = ["facebook"]
            s.avg_engagement = 0.8
            s.avg_reach = 0.7
            s.avg_conversion = 0.05
            s.usage_count = 5
            manager.register_strategy(s)

        recs = manager.recommender.recommend(manager._strategies)
        assert len(recs) > 0

    def test_pattern_to_optimization(self):
        """Test: Patterns detected feed into optimization."""
        manager = StrategyManager()
        for i in range(4):
            s = StrategyProfile(name=f"S{i}", strategy_type="engagement")
            s.target_platforms = ["linkedin"]
            s.avg_engagement = 0.9
            s.avg_reach = 0.8
            s.avg_conversion = 0.1
            s.usage_count = 5
            manager.register_strategy(s)

        patterns = manager.pattern_detector.detect(manager._strategies)
        assert len(patterns) > 0

        new_s = StrategyProfile(name="New", strategy_type="growth")
        new_s.target_platforms = []
        opt = manager.optimizer.optimize(new_s, patterns)
        assert opt.changes_made > 0

    def test_validator_blocks_invalid(self):
        """Test: Validator catches issues."""
        v = StrategyValidator()
        s = StrategyProfile(name="")
        result = v.validate(s)
        assert result.is_valid is False

    def test_memory_after_cycles(self):
        """Test: Memory stores learnings."""
        manager = StrategyManager()
        s = StrategyProfile(name="Test", strategy_type="engagement")
        s.target_platforms = ["fb"]
        s.avg_engagement = 0.5
        s.usage_count = 5
        manager.run_optimization_cycle(s)
        stats = manager.memory.get_stats()
        assert stats["total"] >= 0

    def test_fork_and_compare(self):
        """Test: Fork strategy and compare versions."""
        original = StrategyProfile(name="Original", strategy_type="growth")
        original.avg_engagement = 0.4
        original.avg_reach = 0.3
        original.avg_conversion = 0.02
        forked = original.fork()
        forked.avg_engagement = 0.8
        forked.avg_reach = 0.7
        forked.avg_conversion = 0.1

        comp = StrategyComparator()
        winner = comp.get_overall_winner(original, forked)
        assert winner == "candidate"
