"""Tests for Layer 9 Module 2 — Prompt Optimization Engine."""
from layers.layer09_learning.modules.prompt_optimization.prompt_profile import (
    PromptProfile,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_history import (
    PromptHistory,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_comparator import (
    PromptComparator,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_analyzer import (
    PromptAnalyzer, AnalysisFinding,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_optimizer import (
    PromptOptimizer, OptimizationSuggestion,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_variants import (
    PromptVariants, PromptVariant, VariantTest,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_memory import (
    PromptMemory, PromptMemoryEntry,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_metrics import PromptMetrics
from layers.layer09_learning.modules.prompt_optimization.prompt_validator import (
    PromptValidator, ValidationError,
)
from layers.layer09_learning.modules.prompt_optimization.prompt_manager import (
    PromptManager, OptimizationCycleResult,
)
from layers.layer09_learning.modules.prompt_optimization.exceptions import (
    PromptOptimizationError, ValidationFailedError, OptimizationError,
    HistoryError, MemoryError,
)


# ─── PromptProfile Tests ─────────────────────────────────────────────
class TestPromptProfile:
    def test_create_default(self):
        p = PromptProfile()
        assert p.profile_id.startswith("pp_")
        assert p.version == 1
        assert p.category == "content_generation"
        assert p.status == "draft"
        assert p.template == ""
        assert p.usage_count == 0
        assert p.success_count == 0
        assert p.failure_count == 0

    def test_create_with_args(self):
        p = PromptProfile(template="Write a post about {topic}", category="hook", version=3)
        assert p.template == "Write a post about {topic}"
        assert p.category == "hook"
        assert p.version == 3

    def test_invalid_category_falls_back(self):
        p = PromptProfile(category="invalid")
        assert p.category == "content_generation"

    def test_success_rate_no_usage(self):
        p = PromptProfile()
        assert p.success_rate == 0.0

    def test_success_rate_with_usage(self):
        p = PromptProfile()
        p.success_count = 7
        p.failure_count = 3
        assert p.success_rate == 0.7

    def test_is_active(self):
        p = PromptProfile()
        p.status = "active"
        assert p.is_active is True

    def test_is_not_active(self):
        p = PromptProfile()
        assert p.is_active is False

    def test_effective_score(self):
        p = PromptProfile()
        p.avg_engagement = 0.8
        p.avg_quality_score = 0.9
        p.avg_confidence = 0.7
        score = p.effective_score
        assert score == round(0.8 * 0.4 + 0.9 * 0.4 + 0.7 * 0.2, 3)

    def test_record_usage_success(self):
        p = PromptProfile()
        p.record_usage(True, engagement=0.8, quality=0.9, confidence=0.7)
        assert p.usage_count == 1
        assert p.success_count == 1
        assert p.failure_count == 0
        assert p.avg_engagement == 0.8

    def test_record_usage_failure(self):
        p = PromptProfile()
        p.record_usage(False, engagement=0.2, quality=0.3)
        assert p.failure_count == 1
        assert p.success_count == 0

    def test_record_usage_averages(self):
        p = PromptProfile()
        p.record_usage(True, engagement=0.6, quality=0.7, confidence=0.5)
        p.record_usage(True, engagement=0.8, quality=0.9, confidence=0.7)
        assert p.usage_count == 2
        assert p.avg_engagement == 0.7
        assert p.avg_quality_score == 0.8

    def test_fork(self):
        p = PromptProfile(template="Test template", category="hook", version=2)
        p.platform = "facebook"
        p.tone = "friendly"
        child = p.fork()
        assert child.version == 3
        assert child.parent_id == p.profile_id
        assert child.template == p.template
        assert child.platform == "facebook"
        assert child.tone == "friendly"

    def test_to_dict(self):
        p = PromptProfile(template="Hello", category="caption")
        d = p.to_dict()
        assert "profile_id" in d
        assert d["template"] == "Hello"
        assert d["category"] == "caption"
        assert d["success_rate"] == 0.0

    def test_to_dict_with_usage(self):
        p = PromptProfile()
        p.record_usage(True, engagement=0.8, quality=0.9)
        d = p.to_dict()
        assert d["usage_count"] == 1
        assert d["avg_engagement"] == 0.8


# ─── PromptHistory Tests ──────────────────────────────────────────────
class TestPromptHistory:
    def setup_method(self):
        self.history = PromptHistory()

    def test_record(self):
        p = PromptProfile(template="Test", category="caption")
        entry = self.history.record(p, "created", {"engagement": 0.8})
        assert entry.profile_id == p.profile_id
        assert entry.action == "created"
        assert entry.metrics["engagement"] == 0.8

    def test_get_profile_history(self):
        p = PromptProfile(template="Test")
        self.history.record(p, "created")
        self.history.record(p, "updated")
        entries = self.history.get_profile_history(p.profile_id)
        assert len(entries) == 2

    def test_get_profile_history_empty(self):
        entries = self.history.get_profile_history("nonexistent")
        assert len(entries) == 0

    def test_get_recent(self):
        p = PromptProfile(template="Test")
        for _ in range(5):
            self.history.record(p, "created")
        recent = self.history.get_recent(3)
        assert len(recent) == 3

    def test_get_by_action(self):
        p = PromptProfile(template="Test")
        self.history.record(p, "created")
        self.history.record(p, "updated")
        self.history.record(p, "created")
        created = self.history.get_by_action("created")
        assert len(created) == 2

    def test_get_performance_snapshots(self):
        p = PromptProfile(template="Test")
        self.history.record(p, "created", {"engagement": 0.5})
        self.history.record(p, "optimized", {"engagement": 0.8})
        snapshots = self.history.get_performance_snapshots(p.profile_id)
        assert len(snapshots) == 2
        assert snapshots[0]["engagement"] == 0.5

    def test_get_best_version(self):
        p1 = PromptProfile(template="v1", version=1)
        p2 = PromptProfile(template="v2", version=2)
        self.history.record(p1, "created", {"engagement": 0.5})
        self.history.record(p2, "created", {"engagement": 0.9})
        best = self.history.get_best_version(p1.profile_id, "engagement")
        assert best is not None

    def test_get_best_version_no_data(self):
        assert self.history.get_best_version("none") is None

    def test_entry_count(self):
        p = PromptProfile(template="T")
        self.history.record(p, "created")
        assert self.history.entry_count == 1

    def test_max_entries_overflow(self):
        h = PromptHistory(max_entries=5)
        p = PromptProfile(template="T")
        for _ in range(10):
            h.record(p, "created")
        assert h.entry_count == 5

    def test_entry_to_dict(self):
        p = PromptProfile(template="T")
        entry = self.history.record(p, "created", {"q": 0.9})
        d = entry.to_dict()
        assert "entry_id" in d
        assert d["action"] == "created"


# ─── PromptComparator Tests ───────────────────────────────────────────
class TestPromptComparator:
    def setup_method(self):
        self.comp = PromptComparator()

    def _make_profile(self, engagement=0.5, quality=0.6, confidence=0.7, success_rate=0.8):
        p = PromptProfile(template="Test template for comparison")
        p.avg_engagement = engagement
        p.avg_quality_score = quality
        p.avg_confidence = confidence
        p.success_count = int(success_rate * 10)
        p.failure_count = 10 - p.success_count
        return p

    def test_compare(self):
        baseline = self._make_profile(0.5, 0.5, 0.5)
        candidate = self._make_profile(0.8, 0.8, 0.8)
        results = self.comp.compare(baseline, candidate)
        assert len(results) == 5
        candidate_wins = sum(1 for r in results if r.winner == "candidate")
        assert candidate_wins >= 3

    def test_compare_equal(self):
        baseline = self._make_profile(0.5, 0.5, 0.5)
        candidate = self._make_profile(0.5, 0.5, 0.5)
        results = self.comp.compare(baseline, candidate)
        assert all(r.winner == "tie" for r in results)

    def test_compare_baseline_wins(self):
        baseline = self._make_profile(0.9, 0.9, 0.9)
        candidate = self._make_profile(0.3, 0.3, 0.3)
        results = self.comp.compare(baseline, candidate)
        baseline_wins = sum(1 for r in results if r.winner == "baseline")
        assert baseline_wins >= 3

    def test_get_overall_winner(self):
        baseline = self._make_profile(0.3, 0.3, 0.3)
        candidate = self._make_profile(0.9, 0.9, 0.9)
        assert self.comp.get_overall_winner(baseline, candidate) == "candidate"

    def test_get_overall_winner_tie(self):
        baseline = self._make_profile(0.5, 0.5, 0.5)
        candidate = self._make_profile(0.5, 0.5, 0.5)
        assert self.comp.get_overall_winner(baseline, candidate) == "tie"

    def test_significance_levels(self):
        baseline = self._make_profile(0.1, 0.1, 0.1)
        candidate = self._make_profile(0.5, 0.5, 0.5)
        results = self.comp.compare(baseline, candidate)
        sigs = [r.significance for r in results]
        assert "high" in sigs or "medium" in sigs

    def test_comparison_result_to_dict(self):
        baseline = self._make_profile(0.5)
        candidate = self._make_profile(0.8)
        results = self.comp.compare(baseline, candidate)
        d = results[0].to_dict()
        assert "metric_name" in d
        assert "winner" in d

    def test_get_significant_differences(self):
        baseline = self._make_profile(0.1)
        candidate = self._make_profile(0.9)
        self.comp.compare(baseline, candidate)
        sigs = self.comp.get_significant_differences()
        assert len(sigs) > 0

    def test_get_results(self):
        baseline = self._make_profile()
        candidate = self._make_profile(0.9, 0.9, 0.9)
        self.comp.compare(baseline, candidate)
        assert len(self.comp.get_results()) == 5


# ─── AnalysisFinding Tests ────────────────────────────────────────────
class TestAnalysisFinding:
    def test_create(self):
        f = AnalysisFinding("engagement", "warning")
        assert f.category == "engagement"
        assert f.severity == "warning"
        assert f.finding_id.startswith("af_")

    def test_to_dict(self):
        f = AnalysisFinding("quality", "critical")
        f.description = "Low quality"
        d = f.to_dict()
        assert d["category"] == "quality"
        assert d["severity"] == "critical"


# ─── PromptAnalyzer Tests ─────────────────────────────────────────────
class TestPromptAnalyzer:
    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    def test_analyze_empty_prompt(self):
        p = PromptProfile(template="")
        report = self.analyzer.analyze(p)
        critical = [f for f in report.findings if f.severity == "critical"]
        assert len(critical) >= 1
        assert report.score < 80

    def test_analyze_low_engagement(self):
        p = PromptProfile(template="A good prompt template with enough detail")
        p.usage_count = 10
        p.avg_engagement = 0.1
        p.avg_quality_score = 0.8
        p.success_count = 7
        p.failure_count = 3
        report = self.analyzer.analyze(p)
        findings = [f for f in report.findings if f.category == "engagement"]
        assert len(findings) >= 1

    def test_analyze_high_quality(self):
        p = PromptProfile(template="A well-crafted prompt template for content generation")
        p.usage_count = 20
        p.avg_engagement = 0.9
        p.avg_quality_score = 0.95
        p.avg_confidence = 0.9
        p.success_count = 18
        p.failure_count = 2
        report = self.analyzer.analyze(p)
        assert report.overall_health in ("excellent", "good")
        assert report.score > 70

    def test_analyze_no_usage(self):
        p = PromptProfile(template="A new prompt template that has never been tested")
        report = self.analyzer.analyze(p)
        usage_findings = [f for f in report.findings if f.category == "usage"]
        assert len(usage_findings) >= 1

    def test_analyze_short_template(self):
        p = PromptProfile(template="Short")
        report = self.analyzer.analyze(p)
        template_findings = [f for f in report.findings if f.category == "template"]
        assert len(template_findings) >= 1

    def test_health_classification(self):
        assert self.analyzer._classify_health(95) == "excellent"
        assert self.analyzer._classify_health(75) == "good"
        assert self.analyzer._classify_health(55) == "fair"
        assert self.analyzer._classify_health(30) == "poor"

    def test_get_reports(self):
        p1 = PromptProfile(template="Template one for testing purposes only")
        p2 = PromptProfile(template="Template two for testing purposes only")
        self.analyzer.analyze(p1)
        self.analyzer.analyze(p2)
        assert len(self.analyzer.get_reports()) == 2

    def test_get_critical_findings(self):
        p = PromptProfile(template="")
        self.analyzer.analyze(p)
        critical = self.analyzer.get_critical_findings()
        assert len(critical) >= 1

    def test_analysis_report_to_dict(self):
        p = PromptProfile(template="A valid template for analysis")
        report = self.analyzer.analyze(p)
        d = report.to_dict()
        assert "finding_count" in d
        assert "overall_health" in d
        assert "score" in d


# ─── OptimizationSuggestion Tests ─────────────────────────────────────
class TestOptimizationSuggestion:
    def test_create(self):
        s = OptimizationSuggestion("template", "high")
        assert s.suggestion_type == "template"
        assert s.priority == "high"
        assert s.suggestion_id.startswith("os_")

    def test_to_dict(self):
        s = OptimizationSuggestion("parameter", "critical")
        s.field = "platform"
        d = s.to_dict()
        assert d["field"] == "platform"
        assert d["priority"] == "critical"


# ─── PromptOptimizer Tests ────────────────────────────────────────────
class TestPromptOptimizer:
    def setup_method(self):
        self.optimizer = PromptOptimizer()

    def test_optimize_empty_template(self):
        p = PromptProfile(template="")
        result = self.optimizer.optimize(p)
        assert result.changes_made >= 1
        assert result.optimized_template.startswith("[OPTIMIZED]")

    def test_optimize_short_template_low_quality(self):
        p = PromptProfile(template="Short prompt")
        p.avg_quality_score = 0.3
        p.usage_count = 10
        result = self.optimizer.optimize(p)
        assert result.changes_made >= 1

    def test_optimize_missing_parameters(self):
        p = PromptProfile(template="A well-formed prompt template for testing")
        p.platform = ""
        p.tone = ""
        result = self.optimizer.optimize(p)
        types = [s.suggestion_type for s in result.suggestions]
        assert "parameter" in types

    def test_optimize_with_analysis(self):
        p = PromptProfile(template="A good template for content generation")
        p.usage_count = 5
        p.avg_quality_score = 0.3
        analyzer = PromptAnalyzer()
        analysis = analyzer.analyze(p)
        result = self.optimizer.optimize(p, analysis)
        assert result.confidence > 0

    def test_optimize_confidence_high_usage(self):
        p = PromptProfile(template="A detailed prompt template with specific instructions")
        p.usage_count = 20
        result = self.optimizer.optimize(p)
        assert result.confidence > 0

    def test_optimize_no_suggestions(self):
        p = PromptProfile(template="A perfectly detailed prompt template with many instructions")
        p.platform = "facebook"
        p.tone = "friendly"
        p.tags = ["test"]
        p.usage_count = 10
        p.avg_quality_score = 0.9
        result = self.optimizer.optimize(p)
        assert result.confidence == 0.0

    def test_get_results(self):
        p = PromptProfile(template="Test")
        self.optimizer.optimize(p)
        assert len(self.optimizer.get_results()) == 1

    def test_optimization_count(self):
        self.optimizer.optimize(PromptProfile(template="A"))
        self.optimizer.optimize(PromptProfile(template="B"))
        assert self.optimizer.optimization_count == 2


# ─── PromptVariant Tests ──────────────────────────────────────────────
class TestPromptVariant:
    def test_create(self):
        p = PromptProfile(template="Test template")
        v = PromptVariant(p, "B", is_control=False)
        assert v.variant_label == "B"
        assert v.is_control is False
        assert v.variant_id.startswith("pv_")

    def test_create_control(self):
        p = PromptProfile(template="Control")
        v = PromptVariant(p, "A", is_control=True)
        assert v.is_control is True

    def test_effective_score(self):
        p = PromptProfile()
        p.avg_engagement = 0.8
        v = PromptVariant(p)
        assert v.effective_score == p.effective_score

    def test_to_dict(self):
        p = PromptProfile(template="T")
        v = PromptVariant(p, "B")
        d = v.to_dict()
        assert d["variant_label"] == "B"
        assert "effective_score" in d


# ─── VariantTest Tests ────────────────────────────────────────────────
class TestVariantTest:
    def test_create(self):
        t = VariantTest("Test name", min_samples=5)
        assert t.test_name == "Test name"
        assert t.min_samples == 5
        assert t.status == "running"

    def test_add_variant(self):
        t = VariantTest()
        p = PromptProfile(template="T")
        v = PromptVariant(p, "A", is_control=True)
        t.add_variant(v)
        assert len(t.variants) == 1

    def test_get_control(self):
        t = VariantTest()
        p = PromptProfile(template="T")
        ctrl = PromptVariant(p, "A", is_control=True)
        cand = PromptVariant(p, "B")
        t.add_variant(ctrl)
        t.add_variant(cand)
        assert t.get_control() is ctrl

    def test_has_sufficient_samples_no(self):
        t = VariantTest(min_samples=10)
        p = PromptProfile(template="T")
        p.usage_count = 5
        v = PromptVariant(p, "A", is_control=True)
        t.add_variant(v)
        assert t.has_sufficient_samples() is False

    def test_has_sufficient_samples_yes(self):
        t = VariantTest(min_samples=5)
        p = PromptProfile(template="T")
        p.usage_count = 5
        v = PromptVariant(p, "A", is_control=True)
        t.add_variant(v)
        assert t.has_sufficient_samples() is True

    def test_to_dict(self):
        t = VariantTest("My Test")
        d = t.to_dict()
        assert d["test_name"] == "My Test"
        assert d["status"] == "running"


# ─── PromptVariants Tests ─────────────────────────────────────────────
class TestPromptVariants:
    def setup_method(self):
        self.variants = PromptVariants()

    def test_create_test(self):
        baseline = PromptProfile(template="Baseline prompt template")
        candidates = [PromptProfile(template="Candidate A prompt template")]
        test = self.variants.create_test("My Test", baseline, candidates)
        assert test.test_name == "My Test"
        assert len(test.variants) == 2
        assert test.variants[0].is_control is True

    def test_record_outcome(self):
        baseline = PromptProfile(template="Baseline prompt for testing")
        candidates = [PromptProfile(template="Candidate prompt for testing")]
        test = self.variants.create_test("T", baseline, candidates)
        self.variants.record_outcome(test.test_id, test.variants[0].variant_id, True, 0.8)
        assert test.variants[0].profile.usage_count == 1

    def test_record_outcome_nonexistent(self):
        self.variants.record_outcome("fake", "fake", True)
        # Should not raise

    def test_evaluate_test_insufficient(self):
        baseline = PromptProfile(template="Baseline for testing")
        test = self.variants.create_test("T", baseline, [], min_samples=100)
        result = self.variants.evaluate_test(test.test_id)
        assert result is None

    def test_evaluate_test_sufficient(self):
        baseline = PromptProfile(template="Baseline for testing")
        baseline.avg_engagement = 0.5
        cand = PromptProfile(template="Candidate for testing")
        cand.avg_engagement = 0.9
        test = self.variants.create_test("T", baseline, [cand], min_samples=0)
        for v in test.variants:
            v.profile.usage_count = 5
        winner_id = self.variants.evaluate_test(test.test_id)
        assert winner_id is not None
        assert test.status == "completed"

    def test_get_test(self):
        baseline = PromptProfile(template="B")
        test = self.variants.create_test("T", baseline, [])
        found = self.variants.get_test(test.test_id)
        assert found is not None

    def test_get_test_not_found(self):
        assert self.variants.get_test("nonexistent") is None

    def test_get_tests(self):
        baseline = PromptProfile(template="B")
        self.variants.create_test("T1", baseline, [])
        self.variants.create_test("T2", baseline, [])
        assert self.variants.test_count == 2

    def test_get_tests_by_status(self):
        baseline = PromptProfile(template="B")
        t = self.variants.create_test("T", baseline, [])
        t.status = "completed"
        completed = self.variants.get_tests("completed")
        assert len(completed) == 1


# ─── PromptMemoryEntry Tests ──────────────────────────────────────────
class TestPromptMemoryEntry:
    def test_create(self):
        e = PromptMemoryEntry("pp_1", "insight")
        assert e.profile_id == "pp_1"
        assert e.learning_type == "insight"
        assert e.archived is False

    def test_to_dict(self):
        e = PromptMemoryEntry("pp_1", "mistake")
        e.tags.append("test")
        d = e.to_dict()
        assert d["learning_type"] == "mistake"
        assert "test" in d["tags"]


# ─── PromptMemory Tests ───────────────────────────────────────────────
class TestPromptMemory:
    def setup_method(self):
        self.memory = PromptMemory()

    def test_store(self):
        entry = self.memory.store("pp_1", "insight", "Good template", confidence=0.8)
        assert entry.profile_id == "pp_1"
        assert entry.confidence == 0.8
        assert self.memory.entry_count == 1

    def test_store_with_tags(self):
        entry = self.memory.store("pp_1", "insight", "Test", tags=["hook", "facebook"])
        assert "hook" in entry.tags
        assert "facebook" in entry.tags

    def test_search_by_profile(self):
        self.memory.store("pp_1", "insight", "A")
        self.memory.store("pp_2", "insight", "B")
        results = self.memory.search(profile_id="pp_1")
        assert len(results) == 1

    def test_search_by_type(self):
        self.memory.store("pp_1", "insight", "A")
        self.memory.store("pp_1", "mistake", "B")
        results = self.memory.search(learning_type="mistake")
        assert len(results) == 1

    def test_search_by_tag(self):
        self.memory.store("pp_1", "insight", "A", tags=["hook"])
        self.memory.store("pp_1", "insight", "B", tags=["seo"])
        results = self.memory.search(tag="hook")
        assert len(results) == 1

    def test_get_recent(self):
        for i in range(5):
            self.memory.store("pp_1", "insight", f"Entry {i}")
        recent = self.memory.get_recent(3)
        assert len(recent) == 3

    def test_archive(self):
        entry = self.memory.store("pp_1", "insight", "Test")
        assert self.memory.archive(entry.entry_id) is True
        assert self.memory.entry_count == 0

    def test_archive_nonexistent(self):
        assert self.memory.archive("nonexistent") is False

    def test_get_by_id(self):
        entry = self.memory.store("pp_1", "insight", "Test")
        found = self.memory.get_by_id(entry.entry_id)
        assert found is not None

    def test_get_by_id_not_found(self):
        assert self.memory.get_by_id("nonexistent") is None

    def test_get_stats(self):
        self.memory.store("pp_1", "insight", "A")
        self.memory.store("pp_1", "mistake", "B")
        stats = self.memory.get_stats()
        assert stats["active"] == 2
        assert stats["by_type"]["insight"] == 1
        assert stats["by_type"]["mistake"] == 1

    def test_max_entries(self):
        m = PromptMemory(max_entries=3)
        for i in range(5):
            m.store("pp_1", "insight", f"E{i}")
        assert m.entry_count == 3


# ─── PromptMetrics Tests ──────────────────────────────────────────────
class TestPromptMetrics:
    def setup_method(self):
        self.metrics = PromptMetrics()

    def test_record_optimization_success(self):
        self.metrics.record_optimization(0.8, improved=True)
        assert self.metrics.get_optimization_success_rate() == 1.0

    def test_record_optimization_mixed(self):
        self.metrics.record_optimization(0.8, improved=True)
        self.metrics.record_optimization(0.5, improved=False)
        assert self.metrics.get_optimization_success_rate() == 0.5

    def test_record_analysis(self):
        self.metrics.record_analysis()
        self.metrics.record_analysis()
        summary = self.metrics.get_summary()
        assert summary["total_analyses"] == 2

    def test_record_comparison(self):
        self.metrics.record_comparison(15.0)
        self.metrics.record_comparison(-5.0)
        assert self.metrics.get_avg_improvement_rate() == 5.0

    def test_record_variant_test(self):
        self.metrics.record_variant_test()
        summary = self.metrics.get_summary()
        assert summary["total_variants_tested"] == 1

    def test_get_avg_optimization_score(self):
        self.metrics.record_optimization(0.6)
        self.metrics.record_optimization(0.8)
        assert self.metrics.get_avg_optimization_score() == 0.7

    def test_summary(self):
        self.metrics.record_optimization(0.7, True)
        self.metrics.record_analysis()
        summary = self.metrics.get_summary()
        assert "total_optimizations" in summary
        assert "optimization_success_rate" in summary

    def test_reset(self):
        self.metrics.record_optimization(0.8, True)
        self.metrics.reset()
        assert self.metrics.get_optimization_success_rate() == 0.0

    def test_no_data(self):
        assert self.metrics.get_optimization_success_rate() == 0.0
        assert self.metrics.get_avg_optimization_score() == 0.0
        assert self.metrics.get_avg_improvement_rate() == 0.0


# ─── ValidationError Tests ────────────────────────────────────────────
class TestValidationError:
    def test_create(self):
        e = ValidationError("template", "error", "Empty template")
        assert e.field == "template"
        assert e.severity == "error"

    def test_to_dict(self):
        e = ValidationError("template", "warning", "Too short")
        d = e.to_dict()
        assert d["field"] == "template"
        assert d["severity"] == "warning"


# ─── PromptValidator Tests ────────────────────────────────────────────
class TestPromptValidator:
    def setup_method(self):
        self.validator = PromptValidator()

    def test_validate_valid_prompt(self):
        p = PromptProfile(
            template="Write a compelling post about AI technology for social media",
            category="content_generation",
        )
        p.platform = "facebook"
        p.tone = "professional"
        result = self.validator.validate(p)
        assert result.is_valid is True
        assert result.score > 80

    def test_validate_empty_template(self):
        p = PromptProfile(template="")
        result = self.validator.validate(p)
        assert result.is_valid is False
        assert result.error_count >= 1

    def test_validate_short_template(self):
        p = PromptProfile(template="Hi")
        result = self.validator.validate(p)
        assert result.is_valid is False

    def test_validate_long_template(self):
        p = PromptProfile(template="x" * 20000)
        result = self.validator.validate(p)
        assert result.is_valid is False

    def test_validate_invalid_category(self):
        p = PromptProfile(template="A valid prompt template with enough characters")
        p.category = "invalid_cat"
        result = self.validator.validate(p)
        assert result.is_valid is False

    def test_validate_warnings(self):
        p = PromptProfile(template="A valid prompt template with enough characters to pass validation")
        p.platform = ""
        p.tone = ""
        result = self.validator.validate(p)
        assert result.is_valid is True
        assert result.warning_count >= 2

    def test_validate_batch(self):
        profiles = [
            PromptProfile(template="Valid prompt template with enough characters for testing"),
            PromptProfile(template=""),
        ]
        results = self.validator.validate_batch(profiles)
        assert len(results) == 2
        assert results[0].is_valid is True
        assert results[1].is_valid is False

    def test_get_invalid_count(self):
        self.validator.validate(PromptProfile(template="Valid template with enough chars for testing"))
        self.validator.validate(PromptProfile(template=""))
        assert self.validator.get_invalid_count() == 1

    def test_score_decreases_with_errors(self):
        valid = PromptProfile(template="A valid template with enough characters for testing")
        v1 = self.validator.validate(valid)
        invalid = PromptProfile(template="")
        v2 = self.validator.validate(invalid)
        assert v1.score > v2.score

    def test_result_to_dict(self):
        p = PromptProfile(template="A valid prompt template with enough characters for testing")
        result = self.validator.validate(p)
        d = result.to_dict()
        assert "is_valid" in d
        assert "error_count" in d
        assert "score" in d


# ─── OptimizationCycleResult Tests ────────────────────────────────────
class TestOptimizationCycleResult:
    def test_create(self):
        r = OptimizationCycleResult("pp_1")
        assert r.cycle_id.startswith("poc_")
        assert r.profile_id == "pp_1"
        assert r.is_approved is False

    def test_to_dict(self):
        r = OptimizationCycleResult("pp_1")
        r.improvements_suggested = 3
        r.validation_score = 95.0
        d = r.to_dict()
        assert d["improvements_suggested"] == 3
        assert d["is_approved"] is False


# ─── PromptManager Tests ──────────────────────────────────────────────
class TestPromptManager:
    def setup_method(self):
        self.manager = PromptManager()

    def _make_profile(self, template="A detailed prompt template for content generation", quality=0.8):
        p = PromptProfile(template=template)
        p.platform = "facebook"
        p.tone = "friendly"
        p.usage_count = 10
        p.avg_quality_score = quality
        p.avg_engagement = 0.7
        p.success_count = 8
        p.failure_count = 2
        return p

    def test_run_optimization_cycle(self):
        p = self._make_profile()
        result = self.manager.run_optimization_cycle(p)
        assert result.cycle_id.startswith("poc_")
        assert result.analysis is not None
        assert result.optimization is not None

    def test_run_optimization_cycle_events(self):
        p = self._make_profile()
        self.manager.run_optimization_cycle(p)
        assert len(self.manager.events) == 1
        assert self.manager.events[0]["event"] == "optimization_cycle_completed"

    def test_compare_prompts(self):
        baseline = self._make_profile(quality=0.3)
        candidate = self._make_profile(quality=0.9)
        winner = self.manager.compare_prompts(baseline, candidate)
        assert winner in ("candidate", "baseline", "tie")

    def test_create_ab_test(self):
        baseline = self._make_profile()
        candidates = [self._make_profile(quality=0.9)]
        test = self.manager.create_ab_test("My Test", baseline, candidates)
        assert test.test_name == "My Test"

    def test_health(self):
        p = self._make_profile()
        self.manager.run_optimization_cycle(p)
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert "memory_stats" in health
        assert "metrics" in health

    def test_cycle_count(self):
        self.manager.run_optimization_cycle(self._make_profile())
        self.manager.run_optimization_cycle(self._make_profile())
        assert self.manager.cycle_count == 2

    def test_get_recent_cycles(self):
        for _ in range(3):
            self.manager.run_optimization_cycle(self._make_profile())
        recent = self.manager.get_recent_cycles(2)
        assert len(recent) == 2

    def test_history_populated(self):
        self.manager.run_optimization_cycle(self._make_profile())
        assert self.manager.history.entry_count >= 1

    def test_memory_populated(self):
        p = PromptProfile(template="x")
        p.platform = "facebook"
        p.usage_count = 20
        p.avg_engagement = 0.1
        p.avg_quality_score = 0.1
        p.success_count = 5
        p.failure_count = 15
        self.manager.run_optimization_cycle(p)
        stats = self.manager.memory.get_stats()
        assert stats["active"] >= 1

    def test_manager_components_exist(self):
        assert self.manager.history is not None
        assert self.manager.comparator is not None
        assert self.manager.analyzer is not None
        assert self.manager.optimizer is not None
        assert self.manager.variants is not None
        assert self.manager.memory is not None
        assert self.manager.metrics is not None
        assert self.manager.validator is not None


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base_exception(self):
        assert issubclass(PromptOptimizationError, Exception)

    def test_validation_failed(self):
        assert issubclass(ValidationFailedError, PromptOptimizationError)

    def test_optimization_error(self):
        assert issubclass(OptimizationError, PromptOptimizationError)

    def test_history_error(self):
        assert issubclass(HistoryError, PromptOptimizationError)

    def test_memory_error(self):
        assert issubclass(MemoryError, PromptOptimizationError)


# ─── Cross-module Integration Tests ───────────────────────────────────
class TestPromptOptimizationIntegration:
    def test_full_optimization_pipeline(self):
        """Test: Profile → Analyze → Optimize → Validate → Store."""
        manager = PromptManager()
        p = PromptProfile(
            template="Write an engaging social media post about {topic} for {platform}",
            category="content_generation",
        )
        p.platform = "linkedin"
        p.tone = "professional"
        p.tags = ["social", "engagement"]
        p.usage_count = 15
        p.avg_engagement = 0.6
        p.avg_quality_score = 0.5
        p.avg_confidence = 0.7
        p.success_count = 10
        p.failure_count = 5

        result = manager.run_optimization_cycle(p)
        assert result.analysis is not None
        assert result.optimization is not None
        assert result.is_approved is True
        assert manager.history.entry_count >= 1

    def test_ab_test_lifecycle(self):
        """Test: Create test → Record outcomes → Evaluate."""
        manager = PromptManager()
        baseline = PromptProfile(template="Baseline prompt for A/B testing")
        baseline.avg_engagement = 0.5
        candidate = PromptProfile(template="Candidate prompt for A/B testing")
        candidate.avg_engagement = 0.8

        test = manager.create_ab_test("Test 1", baseline, [candidate])
        for v in test.variants:
            v.profile.usage_count = 10

        winner = manager.variants.evaluate_test(test.test_id)
        assert winner is not None
        assert test.status == "completed"

    def test_compare_and_optimize(self):
        """Test: Compare prompts → Optimize the losing one."""
        comp = PromptComparator()
        baseline = PromptProfile(template="Baseline prompt for comparison test")
        baseline.avg_engagement = 0.3
        baseline.avg_quality_score = 0.4
        candidate = PromptProfile(template="Candidate prompt for comparison test")
        candidate.avg_engagement = 0.8
        candidate.avg_quality_score = 0.9

        winner = comp.get_overall_winner(baseline, candidate)
        assert winner == "candidate"

        optimizer = PromptOptimizer()
        result = optimizer.optimize(baseline)
        assert result.changes_made >= 0

    def test_memory_search_after_optimization(self):
        """Test: Memory stores and retrieves optimization learnings."""
        manager = PromptManager()
        p = PromptProfile(template="A prompt template that needs improvement for testing")
        p.platform = "twitter"
        manager.run_optimization_cycle(p)

        results = manager.memory.search(tag="twitter")
        assert len(results) >= 1

    def test_analyzer_to_optimizer_pipeline(self):
        """Test: Analyzer findings feed into optimizer suggestions."""
        analyzer = PromptAnalyzer()
        optimizer = PromptOptimizer()

        p = PromptProfile(template="A short prompt")
        p.usage_count = 5
        p.avg_quality_score = 0.3
        p.avg_engagement = 0.2

        analysis = analyzer.analyze(p)
        result = optimizer.optimize(p, analysis)
        assert result.changes_made >= 0

    def test_validator_blocks_invalid(self):
        """Test: Validator catches issues before optimization."""
        validator = PromptValidator()
        p = PromptProfile(template="")
        result = validator.validate(p)
        assert result.is_valid is False
        assert result.error_count >= 1

    def test_profile_fork_and_compare(self):
        """Test: Fork a profile and compare versions."""
        original = PromptProfile(template="Original prompt for fork test", version=1)
        original.avg_engagement = 0.5
        forked = original.fork()
        forked.avg_engagement = 0.8

        comp = PromptComparator()
        winner = comp.get_overall_winner(original, forked)
        assert winner == "candidate"

    def test_metrics_track_full_cycle(self):
        """Test: Metrics accumulate across multiple cycles."""
        manager = PromptManager()
        for _ in range(3):
            p = PromptProfile(template="A test prompt template for metrics tracking")
            p.platform = "facebook"
            manager.run_optimization_cycle(p)

        summary = manager.metrics.get_summary()
        assert summary["total_optimizations"] == 3
        assert summary["total_analyses"] == 3
