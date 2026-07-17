"""Tests for Layer 9 Module 8 — Content Optimization Engine."""
from layers.layer09_learning.modules.content_optimization.optimization_profile import (
    OptimizationProfile,
)
from layers.layer09_learning.modules.content_optimization.content_analyzer import (
    ContentAnalyzer,
)
from layers.layer09_learning.modules.content_optimization.optimization_rules import (
    RuleLibrary,
)
from layers.layer09_learning.modules.content_optimization.suggestion_generator import (
    SuggestionGenerator,
)
from layers.layer09_learning.modules.content_optimization.rewrite_engine import (
    RewriteEngine,
)
from layers.layer09_learning.modules.content_optimization.variant_evaluator import (
    VariantEvaluator,
)
from layers.layer09_learning.modules.content_optimization.optimization_memory import (
    OptimizationMemory,
)
from layers.layer09_learning.modules.content_optimization.optimization_metrics import OptimizationMetrics
from layers.layer09_learning.modules.content_optimization.optimization_validator import (
    OptimizationValidator,
)
from layers.layer09_learning.modules.content_optimization.optimization_manager import (
    OptimizationManager, OptimizationResult,
)
from layers.layer09_learning.modules.content_optimization.exceptions import (
    ContentOptimizationError, AnalysisError, RewriteError, ValidationError,
)


# ─── OptimizationProfile Tests ───────────────────────────────────────
class TestOptimizationProfile:
    def test_create(self):
        p = OptimizationProfile("engagement", "moderate")
        assert p.profile_id.startswith("op_")
        assert p.goal == "engagement"
        assert p.level == "moderate"

    def test_invalid_goal(self):
        p = OptimizationProfile("invalid")
        assert p.goal == "engagement"

    def test_invalid_level(self):
        p = OptimizationProfile("engagement", "extreme")
        assert p.level == "moderate"

    def test_is_aggressive(self):
        p = OptimizationProfile("engagement", "aggressive")
        assert p.is_aggressive is True

    def test_add_constraint(self):
        p = OptimizationProfile()
        p.add_constraint("max 200 words")
        assert "max 200 words" in p.constraints

    def test_add_constraint_no_dupe(self):
        p = OptimizationProfile()
        p.add_constraint("test")
        p.add_constraint("test")
        assert p.constraints.count("test") == 1

    def test_to_dict(self):
        p = OptimizationProfile("seo", "light")
        d = p.to_dict()
        assert d["goal"] == "seo"
        assert d["level"] == "light"


# ─── ContentAnalyzer Tests ────────────────────────────────────────────
class TestContentAnalyzer:
    def setup_method(self):
        self.analyzer = ContentAnalyzer()

    def test_analyze_basic(self):
        content = "This is a test post about AI. It has multiple sentences to test readability."
        result = self.analyzer.analyze(content, "c1")
        assert result.content_id == "c1"
        assert result.word_count > 0
        assert result.overall_score > 0

    def test_analyze_empty(self):
        result = self.analyzer.analyze("")
        assert result.word_count == 0
        assert result.overall_score == 0.0

    def test_analyze_with_hook(self):
        content = "Did you know? AI is transforming everything. Here's the thing about technology."
        result = self.analyzer.analyze(content)
        assert result.hook_strength > 0.3

    def test_analyze_with_cta(self):
        content = "Great post about technology. Comment below and share your thoughts! Follow for more."
        result = self.analyzer.analyze(content)
        assert result.cta_strength > 0.3

    def test_strengths_found(self):
        content = "Did you know? AI is amazing. Follow us for more tips and share this post!"
        result = self.analyzer.analyze(content)
        assert len(result.strengths) > 0

    def test_weaknesses_found(self):
        content = "Hi"
        result = self.analyzer.analyze(content)
        assert len(result.weaknesses) > 0

    def test_readability_score(self):
        content = "Simple words. Short sentences. Easy to read."
        result = self.analyzer.analyze(content)
        assert result.readability_score > 0.5

    def test_seo_score(self):
        content = "AI tips #AI #Tech #Digital Marketing tips for everyone!"
        result = self.analyzer.analyze(content)
        assert result.seo_score > 0

    def test_get_analyses(self):
        self.analyzer.analyze("Test content")
        assert len(self.analyzer.get_analyses()) == 1

    def test_result_to_dict(self):
        result = self.analyzer.analyze("Test content here")
        d = result.to_dict()
        assert "word_count" in d
        assert "overall_score" in d


# ─── RuleLibrary Tests ────────────────────────────────────────────────
class TestRuleLibrary:
    def setup_method(self):
        self.library = RuleLibrary()

    def test_default_rules_loaded(self):
        assert self.library.rule_count > 0

    def test_get_rules_all(self):
        rules = self.library.get_rules()
        assert len(rules) > 0

    def test_get_rules_by_type(self):
        rules = self.library.get_rules("title")
        assert all(r.rule_type == "title" for r in rules)

    def test_get_by_field(self):
        rules = self.library.get_by_field("cta")
        assert all(r.target_field == "cta" for r in rules)

    def test_get_by_priority(self):
        rules = self.library.get_by_priority("high")
        assert all(r.priority == "high" for r in rules)

    def test_add_rule(self):
        rule = self.library.add_rule("custom", "Custom rule", "body", "low")
        assert rule.description == "Custom rule"
        assert self.library.rule_count > 14

    def test_rule_to_dict(self):
        rules = self.library.get_rules()
        d = rules[0].to_dict()
        assert "rule_id" in d
        assert "description" in d


# ─── SuggestionGenerator Tests ────────────────────────────────────────
class TestSuggestionGenerator:
    def setup_method(self):
        self.generator = SuggestionGenerator()

    def test_generate_from_weaknesses(self):
        analysis = {"weaknesses": ["Low readability", "Missing CTA"], "cta_strength": 0.2, "seo_score": 0.3}
        suggestions = self.generator.generate("Test content", analysis, max_suggestions=5)
        assert len(suggestions) > 0

    def test_generate_no_weaknesses(self):
        analysis = {"weaknesses": [], "cta_strength": 0.8, "seo_score": 0.8}
        suggestions = self.generator.generate("Test content", analysis)
        assert len(suggestions) == 0

    def test_generate_max_limit(self):
        analysis = {"weaknesses": ["A", "B", "C", "D", "E", "F"], "cta_strength": 0.1, "seo_score": 0.1}
        suggestions = self.generator.generate("Test", analysis, max_suggestions=3)
        assert len(suggestions) <= 3

    def test_suggestion_to_dict(self):
        analysis = {"weaknesses": ["Missing CTA"], "cta_strength": 0.2}
        suggestions = self.generator.generate("Test", analysis)
        if suggestions:
            d = suggestions[0].to_dict()
            assert "suggestion_id" in d


# ─── RewriteEngine Tests ──────────────────────────────────────────────
class TestRewriteEngine:
    def setup_method(self):
        self.engine = RewriteEngine()

    def test_rewrite_with_cta(self):
        content = "Great post about AI technology."
        suggestions = [{"field": "cta", "description": "Add CTA", "suggested_value": "Share your thoughts!"}]
        variant = self.engine.rewrite(content, suggestions)
        assert variant.changes_made >= 1
        assert "Share" in variant.content

    def test_rewrite_with_title(self):
        content = "This is a very long title that should be shortened for better engagement."
        suggestions = [{"field": "title", "description": "Shorten title", "suggested_value": "Short title"}]
        variant = self.engine.rewrite(content, suggestions)
        assert "Short title" in variant.content

    def test_rewrite_no_changes(self):
        content = "No suggestions to apply."
        variant = self.engine.rewrite(content, [])
        assert variant.changes_made == 0
        assert variant.content == content

    def test_generate_variants(self):
        content = "Test content for variants."
        suggestions = [
            {"field": "cta", "description": "Add CTA", "suggested_value": "Comment!"},
            {"field": "seo", "description": "Add hashtags"},
        ]
        variants = self.engine.generate_variants(content, suggestions, count=2)
        assert len(variants) == 2

    def test_variant_to_dict(self):
        variant = self.engine.rewrite("Test", [])
        d = variant.to_dict()
        assert "variant_id" in d
        assert "content" in d

    def test_variant_word_count(self):
        variant = self.engine.rewrite("Hello world test content", [])
        assert variant.word_count == 4


# ─── VariantEvaluator Tests ──────────────────────────────────────────
class TestVariantEvaluator:
    def setup_method(self):
        self.evaluator = VariantEvaluator()

    def test_evaluate_improvement(self):
        original = "Short."
        variant = "This is a much longer and more detailed post about an important topic with good engagement hooks?"
        comp = self.evaluator.evaluate(original, variant, "v1")
        assert comp.variant_score > comp.original_score
        assert comp.winner == "variant"

    def test_evaluate_no_improvement(self):
        original = "A well-written post with good content."
        comp = self.evaluator.evaluate(original, original, "v1")
        assert comp.winner == "tie"

    def test_evaluate_batch(self):
        original = "Test content."
        variants = [{"variant_id": "v1", "content": "Better test content with more words."}]
        results = self.evaluator.evaluate_batch(original, variants)
        assert len(results) == 1

    def test_get_best_variant(self):
        original = "Test."
        self.evaluator.evaluate(original, "Better version.", "v1")
        self.evaluator.evaluate(original, "Even better version with more detail.", "v2")
        best = self.evaluator.get_best_variant()
        assert best is not None

    def test_comparison_to_dict(self):
        comp = self.evaluator.evaluate("Test", "Better test content.", "v1")
        d = comp.to_dict()
        assert "improvement_pct" in d
        assert "winner" in d

    def test_evaluation_count(self):
        self.evaluator.evaluate("A", "B")
        assert self.evaluator.evaluation_count == 1


# ─── OptimizationMemory Tests ─────────────────────────────────────────
class TestOptimizationMemory:
    def setup_method(self):
        self.memory = OptimizationMemory()

    def test_store(self):
        entry = self.memory.store("engagement", "Good hook pattern", success_rate=0.8)
        assert entry.pattern_type == "engagement"
        assert self.memory.entry_count == 1

    def test_store_with_tags(self):
        entry = self.memory.store("seo", "Hashtag pattern", tags=["facebook", "linkedin"])
        assert "facebook" in entry.tags

    def test_search_by_type(self):
        self.memory.store("engagement", "A")
        self.memory.store("seo", "B")
        results = self.memory.search(pattern_type="engagement")
        assert len(results) == 1

    def test_search_by_tag(self):
        self.memory.store("engagement", "A", tags=["fb"])
        self.memory.store("engagement", "B", tags=["li"])
        results = self.memory.search(tag="fb")
        assert len(results) == 1

    def test_get_top_patterns(self):
        self.memory.store("a", "A", success_rate=0.9)
        self.memory.store("b", "B", success_rate=0.5)
        top = self.memory.get_top_patterns(1)
        assert top[0].success_rate == 0.9

    def test_get_stats(self):
        self.memory.store("a", "A")
        self.memory.store("b", "B")
        stats = self.memory.get_stats()
        assert stats["total"] == 2

    def test_max_entries(self):
        m = OptimizationMemory(max_entries=3)
        for i in range(5):
            m.store("t", f"E{i}")
        assert m.entry_count == 3

    def test_entry_to_dict(self):
        entry = self.memory.store("t", "D")
        d = entry.to_dict()
        assert "entry_id" in d


# ─── OptimizationMetrics Tests ────────────────────────────────────────
class TestOptimizationMetrics:
    def setup_method(self):
        self.metrics = OptimizationMetrics()

    def test_record_optimization(self):
        self.metrics.record_optimization(0.1, accepted=True)
        assert self.metrics.get_acceptance_rate() == 1.0
        assert self.metrics.get_avg_improvement() == 0.1

    def test_record_suggestions(self):
        self.metrics.record_suggestions(5)
        assert self.metrics.get_summary()["total_suggestions"] == 5

    def test_record_variant(self):
        self.metrics.record_variant()
        assert self.metrics.get_summary()["total_variants"] == 1

    def test_summary(self):
        self.metrics.record_optimization(0.1, True)
        summary = self.metrics.get_summary()
        assert "total_optimizations" in summary

    def test_reset(self):
        self.metrics.record_optimization(0.1)
        self.metrics.reset()
        assert self.metrics.get_avg_improvement() == 0.0

    def test_no_data(self):
        assert self.metrics.get_acceptance_rate() == 0.0
        assert self.metrics.get_avg_improvement() == 0.0


# ─── OptimizationValidator Tests ──────────────────────────────────────
class TestOptimizationValidator:
    def setup_method(self):
        self.validator = OptimizationValidator()

    def test_validate_good(self):
        result = self.validator.validate("Great content about AI technology with good engagement!")
        assert result.is_valid is True
        assert result.safety_pass is True

    def test_validate_empty(self):
        result = self.validator.validate("")
        assert result.is_valid is False

    def test_validate_unsafe(self):
        result = self.validator.validate("This contains hate speech.")
        assert result.safety_pass is False
        assert result.is_valid is False

    def test_validate_forbidden_terms(self):
        result = self.validator.validate("Cheap product for sale", forbidden_terms=["cheap"])
        assert result.brand_pass is False

    def test_validate_brand_terms(self):
        result = self.validator.validate("Premium AI solution", brand_terms=["AI", "premium"])
        assert result.brand_pass is True

    def test_validate_short(self):
        result = self.validator.validate("Hi")
        assert len(result.warnings) > 0

    def test_result_to_dict(self):
        result = self.validator.validate("Good content")
        d = result.to_dict()
        assert "is_valid" in d
        assert "overall_score" in d


# ─── OptimizationResult Tests ─────────────────────────────────────────
class TestOptimizationResult:
    def test_create(self):
        r = OptimizationResult("Test content")
        assert r.result_id.startswith("ocr_")
        assert r.original == "Test content"

    def test_to_dict(self):
        r = OptimizationResult("Test")
        r.suggestions_applied = 3
        d = r.to_dict()
        assert d["suggestions_applied"] == 3


# ─── OptimizationManager Tests ────────────────────────────────────────
class TestOptimizationManager:
    def setup_method(self):
        self.manager = OptimizationManager()

    def test_optimize_basic(self):
        content = "Great post about AI. It has some good content."
        result = self.manager.optimize(content)
        assert result.result_id.startswith("ocr_")
        assert result.optimized is not None
        assert result.analysis is not None

    def test_optimize_with_profile(self):
        profile = OptimizationProfile("engagement", "moderate")
        profile.platform = "facebook"
        result = self.manager.optimize("Test content for optimization.", profile)
        assert result.result_id.startswith("ocr_")

    def test_optimize_validates(self):
        result = self.manager.optimize("Good content about AI technology.")
        assert result.validation_passed is True

    def test_optimize_stores_memory(self):
        content = "Good post with potential. It has decent content."
        result = self.manager.optimize(content)
        if result.improvement_pct > 0:
            assert result.memory_stored is True

    def test_health(self):
        self.manager.optimize("Test content for health check.")
        health = self.manager.get_health()
        assert health["total_optimizations"] == 1
        assert "metrics" in health

    def test_optimization_count(self):
        self.manager.optimize("Test 1")
        self.manager.optimize("Test 2")
        assert self.manager.optimization_count == 2

    def test_events(self):
        self.manager.optimize("Test content")
        assert len(self.manager.events) == 1

    def test_get_recent_results(self):
        for _ in range(3):
            self.manager.optimize("Test content for results")
        assert len(self.manager.get_recent_results(2)) == 2

    def test_manager_components(self):
        assert self.manager.analyzer is not None
        assert self.manager.rules is not None
        assert self.manager.suggestion_generator is not None
        assert self.manager.rewrite_engine is not None
        assert self.manager.evaluator is not None
        assert self.manager.memory is not None
        assert self.manager.metrics is not None
        assert self.manager.validator is not None


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(ContentOptimizationError, Exception)

    def test_analysis(self):
        assert issubclass(AnalysisError, ContentOptimizationError)

    def test_rewrite(self):
        assert issubclass(RewriteError, ContentOptimizationError)

    def test_validation(self):
        assert issubclass(ValidationError, ContentOptimizationError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestContentOptimizationIntegration:
    def test_full_pipeline(self):
        """Test: Analyze → Suggest → Rewrite → Evaluate → Validate → Store."""
        manager = OptimizationManager()
        content = "AI is great. Follow us for more!"
        result = manager.optimize(content)
        assert result.analysis is not None
        assert result.optimized is not None
        assert result.validation_passed is True

    def test_analyzer_drives_suggestions(self):
        """Test: Weak content generates more suggestions."""
        analyzer = ContentAnalyzer()
        generator = SuggestionGenerator()
        weak = "Hi"
        strong = "Did you know? AI is transforming everything. Follow us for more tips and insights!"
        weak_analysis = analyzer.analyze(weak)
        strong_analysis = analyzer.analyze(strong)
        weak_suggestions = generator.generate(weak, weak_analysis.to_dict())
        strong_suggestions = generator.generate(strong, strong_analysis.to_dict())
        assert len(weak_suggestions) >= len(strong_suggestions)

    def test_rewrite_applies_suggestions(self):
        """Test: Rewrite engine applies CTA suggestion."""
        engine = RewriteEngine()
        content = "Good post about technology."
        suggestions = [{"field": "cta", "description": "Add CTA", "suggested_value": "Comment below!"}]
        variant = engine.rewrite(content, suggestions)
        assert "Comment" in variant.content

    def test_evaluator_compares_variants(self):
        """Test: Evaluator correctly identifies better variant."""
        evaluator = VariantEvaluator()
        original = "Short."
        improved = "This is a much longer and more engaging post with questions? Share your thoughts!"
        comp = evaluator.evaluate(original, improved)
        assert comp.winner == "variant"

    def test_memory_stores_successful_patterns(self):
        """Test: Successful optimizations are stored in memory."""
        memory = OptimizationMemory()
        memory.store("engagement", "Hook pattern", success_rate=0.9, tags=["facebook"])
        results = memory.search(tag="facebook")
        assert len(results) == 1
        assert results[0].success_rate == 0.9

    def test_validator_blocks_unsafe(self):
        """Test: Validator catches unsafe content."""
        validator = OptimizationValidator()
        result = validator.validate("This is hate content.")
        assert result.safety_pass is False
        assert result.is_valid is False

    def test_multiple_optimizations(self):
        """Test: Multiple optimizations track metrics correctly."""
        manager = OptimizationManager()
        for i in range(3):
            manager.optimize(f"Test content number {i} for metrics tracking.")
        assert manager.optimization_count == 3
        assert manager.metrics.get_summary()["total_optimizations"] == 3
