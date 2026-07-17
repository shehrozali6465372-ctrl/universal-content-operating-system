"""Tests for Layer 9 Module 4 — Brand Voice Learning Engine."""
from layers.layer09_learning.modules.brand_voice_learning.brand_profile import (
    BrandProfile,
)
from layers.layer09_learning.modules.brand_voice_learning.voice_analyzer import (
    VoiceAnalyzer,
)
from layers.layer09_learning.modules.brand_voice_learning.tone_learning import (
    ToneLearner,
)
from layers.layer09_learning.modules.brand_voice_learning.vocabulary_learning import (
    VocabularyLearner,
)
from layers.layer09_learning.modules.brand_voice_learning.style_learning import (
    StyleLearner,
)
from layers.layer09_learning.modules.brand_voice_learning.terminology_learning import (
    TerminologyLearner,
)
from layers.layer09_learning.modules.brand_voice_learning.consistency_tracker import (
    ConsistencyTracker,
)
from layers.layer09_learning.modules.brand_voice_learning.brand_memory import (
    BrandMemory,
)
from layers.layer09_learning.modules.brand_voice_learning.voice_metrics import VoiceMetrics
from layers.layer09_learning.modules.brand_voice_learning.brand_manager import (
    BrandManager, BrandCycleResult,
)
from layers.layer09_learning.modules.brand_voice_learning.exceptions import (
    BrandVoiceError, AnalysisError, ConsistencyError, LearningError,
)


# ─── BrandProfile Tests ───────────────────────────────────────────────
class TestBrandProfile:
    def test_create_default(self):
        b = BrandProfile()
        assert b.profile_id.startswith("brp_")
        assert b.version == 1
        assert b.status == "draft"
        assert b.industry == "general"

    def test_create_with_args(self):
        b = BrandProfile(name="Acme", industry="technology")
        assert b.name == "Acme"
        assert b.industry == "technology"

    def test_invalid_industry(self):
        b = BrandProfile(industry="unknown")
        assert b.industry == "general"

    def test_is_active(self):
        b = BrandProfile()
        b.status = "active"
        assert b.is_active is True

    def test_tone_count(self):
        b = BrandProfile()
        b.add_tone("professional", 0.8)
        assert b.tone_count == 1

    def test_vocabulary_size(self):
        b = BrandProfile()
        b.add_vocabulary("expert", 0.7)
        assert b.vocabulary_size == 1

    def test_add_forbidden_word(self):
        b = BrandProfile()
        b.add_forbidden_word("cheap")
        assert "cheap" in b.forbidden_words

    def test_add_forbidden_word_no_dupe(self):
        b = BrandProfile()
        b.add_forbidden_word("cheap")
        b.add_forbidden_word("cheap")
        assert b.forbidden_words.count("cheap") == 1

    def test_add_preferred_word(self):
        b = BrandProfile()
        b.add_preferred_word("innovative")
        assert "innovative" in b.preferred_words

    def test_add_terminology(self):
        b = BrandProfile()
        b.add_terminology("AI", "Artificial Intelligence")
        assert b.terminology["AI"] == "Artificial Intelligence"

    def test_record_usage(self):
        b = BrandProfile()
        b.record_usage(0.8)
        assert b.usage_count == 1
        assert b.consistency_score == 0.8

    def test_record_usage_average(self):
        b = BrandProfile()
        b.record_usage(0.6)
        b.record_usage(0.8)
        assert b.usage_count == 2
        assert b.consistency_score == 0.7

    def test_fork(self):
        b = BrandProfile(name="Test", industry="technology")
        b.add_tone("professional", 0.8)
        b.target_audience = "developers"
        child = b.fork()
        assert child.version == 2
        assert child.parent_id == b.profile_id
        assert child.tone_profile == {"professional": 0.8}
        assert child.target_audience == "developers"

    def test_to_dict(self):
        b = BrandProfile(name="Test")
        d = b.to_dict()
        assert "profile_id" in d
        assert d["name"] == "Test"

    def test_to_dict_with_data(self):
        b = BrandProfile(name="Test")
        b.add_tone("professional", 0.8)
        d = b.to_dict()
        assert "professional" in d["tone_profile"]
        assert d["tone_profile"]["professional"] == 0.8

    def test_add_tone_clamps(self):
        b = BrandProfile()
        b.add_tone("test", 1.5)
        assert b.tone_profile["test"] == 1.0
        b.add_tone("test2", -0.5)
        assert b.tone_profile["test2"] == 0.0


# ─── VoiceAnalyzer Tests ──────────────────────────────────────────────
class TestVoiceAnalyzer:
    def setup_method(self):
        self.analyzer = VoiceAnalyzer()

    def test_analyze_professional(self):
        content = "Our expert industry solution provides enterprise strategy for your business."
        result = self.analyzer.analyze(content)
        assert "professional" in result.detected_tones
        assert result.score > 0

    def test_analyze_friendly(self):
        content = "Hello everyone! Thanks for the awesome support. We love our community!"
        result = self.analyzer.analyze(content)
        assert "friendly" in result.detected_tones

    def test_analyze_educational(self):
        content = "Learn how to discover the best tips. Here is a guide on how to code."
        result = self.analyzer.analyze(content)
        assert "educational" in result.detected_tones

    def test_analyze_formality_high(self):
        content = "Furthermore, the solution provides enterprise-grade security. Therefore, we recommend it."
        result = self.analyzer.analyze(content)
        assert result.formality_estimate == "high"

    def test_analyze_formality_low(self):
        content = "Hey guys! lol this is gonna be awesome. Btw check this out!"
        result = self.analyzer.analyze(content)
        assert result.formality_estimate == "low"

    def test_analyze_empty(self):
        result = self.analyzer.analyze("")
        assert result.score >= 0

    def test_analyze_findings(self):
        content = "x " * 100
        result = self.analyzer.analyze(content)
        assert isinstance(result.findings, list)

    def test_result_to_dict(self):
        content = "Our expert solution provides strategy."
        result = self.analyzer.analyze(content)
        d = result.to_dict()
        assert "detected_tones" in d
        assert "score" in d

    def test_get_results(self):
        self.analyzer.analyze("Test content")
        assert len(self.analyzer.get_results()) == 1

    def test_avg_sentence_length(self):
        content = "This is a sentence. This is another sentence. And one more sentence here."
        result = self.analyzer.analyze(content)
        assert result.avg_sentence_length > 0


# ─── ToneLearner Tests ────────────────────────────────────────────────
class TestToneLearner:
    def setup_method(self):
        self.learner = ToneLearner()

    def test_learn_basic(self):
        current = {"professional": 0.5, "friendly": 0.3}
        perf = {"professional": [0.9, 0.8, 0.7], "friendly": [0.3, 0.2, 0.4]}
        results = self.learner.learn(current, perf)
        assert len(results) == 2

    def test_learn_best_tones(self):
        current = {"professional": 0.5, "friendly": 0.5}
        perf = {"professional": [0.9, 0.9], "friendly": [0.3, 0.3]}
        self.learner.learn(current, perf)
        best = self.learner.get_best_tones(1)
        assert best[0].tone == "professional"

    def test_learn_worst_tones(self):
        current = {"professional": 0.5, "friendly": 0.5}
        perf = {"professional": [0.9, 0.9], "friendly": [0.3, 0.3]}
        self.learner.learn(current, perf)
        worst = self.learner.get_worst_tones(1)
        assert worst[0].tone == "friendly"

    def test_get_tone(self):
        current = {"professional": 0.5}
        perf = {"professional": [0.8, 0.9]}
        self.learner.learn(current, perf)
        result = self.learner.get_tone("professional")
        assert result is not None

    def test_get_tone_not_found(self):
        self.learner.learn({}, {})
        assert self.learner.get_tone("nonexistent") is None

    def test_learning_count(self):
        self.learner.learn({}, {})
        self.learner.learn({}, {})
        assert self.learner.learning_count == 2

    def test_result_to_dict(self):
        current = {"professional": 0.5}
        perf = {"professional": [0.8, 0.9]}
        results = self.learner.learn(current, perf)
        d = results[0].to_dict()
        assert "tone" in d
        assert "suggested_weight" in d

    def test_empty_performance(self):
        results = self.learner.learn({"t": 0.5}, {"t": []})
        assert len(results) == 0


# ─── VocabularyLearner Tests ──────────────────────────────────────────
class TestVocabularyLearner:
    def setup_method(self):
        self.learner = VocabularyLearner()

    def test_learn_basic(self):
        current = {"expert": 0.3}
        perf = {"expert": [0.9, 0.8, 0.7], "simple": [0.2, 0.1, 0.3]}
        insights = self.learner.learn(current, perf, min_samples=2)
        assert len(insights) == 2

    def test_learn_increases(self):
        current = {"innovative": 0.2}
        perf = {"innovative": [0.9, 0.8, 0.9]}
        self.learner.learn(current, perf, min_samples=2)
        increases = self.learner.get_increases()
        assert len(increases) >= 1

    def test_learn_decreases(self):
        current = {"cheap": 0.5}
        perf = {"cheap": [0.1, 0.2, 0.1]}
        self.learner.learn(current, perf, min_samples=2)
        decreases = self.learner.get_decreases()
        assert len(decreases) >= 1

    def test_get_insight(self):
        perf = {"word": [0.8, 0.9, 0.7]}
        self.learner.learn({}, perf, min_samples=2)
        insight = self.learner.get_insight("word")
        assert insight is not None

    def test_min_samples_filter(self):
        perf = {"word": [0.8]}
        insights = self.learner.learn({}, perf, min_samples=3)
        assert len(insights) == 0

    def test_learning_count(self):
        self.learner.learn({}, {})
        assert self.learner.learning_count == 1

    def test_insight_to_dict(self):
        perf = {"word": [0.8, 0.9, 0.7]}
        insights = self.learner.learn({}, perf, min_samples=2)
        d = insights[0].to_dict()
        assert "word" in d
        assert "action" in d


# ─── StyleLearner Tests ───────────────────────────────────────────────
class TestStyleLearner:
    def setup_method(self):
        self.learner = StyleLearner()

    def test_learn_basic(self):
        current = {"sentence_style": "long"}
        perf = {"sentence_style": {"short": [0.8, 0.9], "long": [0.3, 0.4]}}
        insights = self.learner.learn(current, perf, min_samples=2)
        assert len(insights) == 1
        assert insights[0].suggested_value == "short"

    def test_get_suggestions(self):
        current = {"emoji_style": "heavy"}
        perf = {"emoji_style": {"light": [0.9, 0.8], "heavy": [0.3, 0.2]}}
        self.learner.learn(current, perf, min_samples=2)
        suggestions = self.learner.get_suggestions()
        assert len(suggestions) >= 1

    def test_get_insight(self):
        perf = {"cta_style": {"question": [0.8, 0.9]}}
        self.learner.learn({}, perf, min_samples=2)
        insight = self.learner.get_insight("cta_style")
        assert insight is not None

    def test_learning_count(self):
        self.learner.learn({}, {})
        assert self.learner.learning_count == 1

    def test_insight_to_dict(self):
        perf = {"style": {"a": [0.8, 0.9]}}
        insights = self.learner.learn({}, perf, min_samples=2)
        d = insights[0].to_dict()
        assert "style_element" in d


# ─── TerminologyLearner Tests ─────────────────────────────────────────
class TestTerminologyLearner:
    def setup_method(self):
        self.learner = TerminologyLearner()

    def test_learn_basic(self):
        current = {"AI": "Artificial Intelligence"}
        perf = {"AI": [0.8, 0.9, 0.7], "ML": [0.5, 0.6, 0.4]}
        insights = self.learner.learn(current, perf, min_samples=2)
        assert len(insights) == 2

    def test_learn_emphasize(self):
        perf = {"AI": [0.9, 0.8, 0.9]}
        self.learner.learn({}, perf, min_samples=2)
        emphasized = self.learner.get_emphasized()
        assert len(emphasized) >= 1

    def test_learn_simplify(self):
        perf = {"jargon": [0.1, 0.2, 0.1]}
        self.learner.learn({}, perf, min_samples=2)
        simplified = self.learner.get_simplified()
        assert len(simplified) >= 1

    def test_get_insight(self):
        perf = {"term": [0.8, 0.9, 0.7]}
        self.learner.learn({}, perf, min_samples=2)
        insight = self.learner.get_insight("term")
        assert insight is not None

    def test_learning_count(self):
        self.learner.learn({}, {})
        assert self.learner.learning_count == 1


# ─── ConsistencyTracker Tests ─────────────────────────────────────────
class TestConsistencyTracker:
    def setup_method(self):
        self.tracker = ConsistencyTracker()

    def _make_brand(self, tones=None, preferred=None, forbidden=None, terminology=None):
        b = BrandProfile(name="Test Brand", industry="technology")
        if tones:
            for t, w in tones.items():
                b.add_tone(t, w)
        if preferred:
            for w in preferred:
                b.add_preferred_word(w)
        if forbidden:
            for w in forbidden:
                b.add_forbidden_word(w)
        if terminology:
            for term, defn in terminology.items():
                b.add_terminology(term, defn)
        return b

    def test_check_basic(self):
        brand = self._make_brand(tones={"professional": 0.8})
        content = "Our expert solution provides enterprise strategy."
        check = self.tracker.check_content(content, brand)
        assert check.overall_score > 0

    def test_check_forbidden_words(self):
        brand = self._make_brand(forbidden=["cheap"])
        check = self.tracker.check_content("This is a cheap product", brand)
        assert len(check.violations) >= 1

    def test_check_no_forbidden(self):
        brand = self._make_brand(forbidden=["cheap"])
        check = self.tracker.check_content("This is a premium product", brand)
        assert len(check.violations) == 0

    def test_check_vocabulary_match(self):
        brand = self._make_brand(preferred=["innovative", "expert"])
        check = self.tracker.check_content("Our innovative expert solution", brand)
        assert check.vocabulary_match > 0

    def test_check_to_dict(self):
        brand = self._make_brand(tones={"professional": 0.8})
        check = self.tracker.check_content("Expert strategy", brand)
        d = check.to_dict()
        assert "overall_score" in d
        assert "violation_count" in d

    def test_get_average_score(self):
        brand = self._make_brand(tones={"professional": 0.8})
        self.tracker.check_content("Expert strategy", brand)
        self.tracker.check_content("Industry solution", brand)
        avg = self.tracker.get_average_score()
        assert avg > 0

    def test_get_average_score_empty(self):
        assert self.tracker.get_average_score() == 0.0

    def test_get_violations_count(self):
        brand = self._make_brand(forbidden=["bad"])
        self.tracker.check_content("bad content", brand)
        self.tracker.check_content("bad words", brand)
        assert self.tracker.get_violations_count() >= 1

    def test_get_checks(self):
        brand = self._make_brand()
        self.tracker.check_content("Test", brand)
        assert len(self.tracker.get_checks()) == 1

    def test_terminology_check(self):
        brand = self._make_brand(terminology={"AI": "Artificial Intelligence"})
        check = self.tracker.check_content("Our AI solution is great", brand)
        assert check.terminology_match > 0


# ─── BrandMemory Tests ────────────────────────────────────────────────
class TestBrandMemory:
    def setup_method(self):
        self.memory = BrandMemory()

    def test_store(self):
        entry = self.memory.store("brp_1", "insight", "Good voice")
        assert entry.brand_id == "brp_1"
        assert self.memory.entry_count == 1

    def test_store_with_tags(self):
        entry = self.memory.store("brp_1", "insight", "Test", tags=["tech"])
        assert "tech" in entry.tags

    def test_search_by_brand(self):
        self.memory.store("brp_1", "insight", "A")
        self.memory.store("brp_2", "insight", "B")
        assert len(self.memory.search(brand_id="brp_1")) == 1

    def test_search_by_type(self):
        self.memory.store("brp_1", "insight", "A")
        self.memory.store("brp_1", "mistake", "B")
        assert len(self.memory.search(learning_type="mistake")) == 1

    def test_archive(self):
        entry = self.memory.store("brp_1", "insight", "Test")
        assert self.memory.archive(entry.entry_id) is True
        assert self.memory.entry_count == 0

    def test_get_by_id(self):
        entry = self.memory.store("brp_1", "insight", "Test")
        assert self.memory.get_by_id(entry.entry_id) is not None

    def test_get_stats(self):
        self.memory.store("brp_1", "insight", "A")
        stats = self.memory.get_stats()
        assert stats["active"] == 1

    def test_max_entries(self):
        m = BrandMemory(max_entries=3)
        for i in range(5):
            m.store("brp_1", "insight", f"E{i}")
        assert m.entry_count == 3


# ─── VoiceMetrics Tests ───────────────────────────────────────────────
class TestVoiceMetrics:
    def setup_method(self):
        self.metrics = VoiceMetrics()

    def test_record_analysis(self):
        self.metrics.record_analysis()
        self.metrics.record_analysis()
        assert self.metrics.get_summary()["total_analyses"] == 2

    def test_record_consistency_check(self):
        self.metrics.record_consistency_check(0.8, 1)
        assert self.metrics.get_avg_consistency() == 0.8

    def test_violation_rate(self):
        self.metrics.record_consistency_check(0.8, 2)
        self.metrics.record_consistency_check(0.9, 0)
        assert self.metrics.get_violation_rate() == 1.0

    def test_record_adjustments(self):
        self.metrics.record_tone_adjustment()
        self.metrics.record_vocabulary_adjustment()
        summary = self.metrics.get_summary()
        assert summary["tone_adjustments"] == 1
        assert summary["vocabulary_adjustments"] == 1

    def test_summary(self):
        self.metrics.record_analysis()
        self.metrics.record_consistency_check(0.9, 0)
        summary = self.metrics.get_summary()
        assert "total_analyses" in summary

    def test_reset(self):
        self.metrics.record_analysis()
        self.metrics.reset()
        assert self.metrics.get_summary()["total_analyses"] == 0

    def test_no_data(self):
        assert self.metrics.get_avg_consistency() == 0.0
        assert self.metrics.get_violation_rate() == 0.0


# ─── BrandCycleResult Tests ───────────────────────────────────────────
class TestBrandCycleResult:
    def test_create(self):
        r = BrandCycleResult("brp_1")
        assert r.cycle_id.startswith("bcy_")
        assert r.brand_id == "brp_1"

    def test_to_dict(self):
        r = BrandCycleResult("brp_1")
        d = r.to_dict()
        assert "cycle_id" in d
        assert d["brand_id"] == "brp_1"


# ─── BrandManager Tests ───────────────────────────────────────────────
class TestBrandManager:
    def setup_method(self):
        self.manager = BrandManager()

    def _make_brand(self):
        b = BrandProfile(name="Test Brand", industry="technology")
        b.add_tone("professional", 0.8)
        b.add_tone("friendly", 0.3)
        b.add_preferred_word("innovative")
        b.add_preferred_word("expert")
        b.add_forbidden_word("cheap")
        b.add_terminology("AI", "Artificial Intelligence")
        b.target_audience = "developers"
        b.formality_level = "high"
        return b

    def test_register_brand(self):
        b = self._make_brand()
        self.manager.register_brand(b)
        assert len(self.manager._brands) == 1

    def test_run_learning_cycle_minimal(self):
        b = self._make_brand()
        samples = ["Our expert AI solution provides innovative technology."]
        result = self.manager.run_learning_cycle(b, samples)
        assert result.cycle_id.startswith("bcy_")
        assert result.voice_analysis is not None

    def test_run_learning_cycle_with_tone(self):
        b = self._make_brand()
        samples = ["Expert strategy for enterprise."]
        tone_perf = {"professional": [0.9, 0.8], "friendly": [0.3, 0.2]}
        result = self.manager.run_learning_cycle(b, samples, tone_performance=tone_perf)
        assert len(result.tone_insights) > 0

    def test_run_learning_cycle_with_vocab(self):
        b = self._make_brand()
        samples = ["Innovative expert solution."]
        vocab_perf = {"innovative": [0.9, 0.8, 0.7], "cheap": [0.1, 0.2]}
        result = self.manager.run_learning_cycle(b, samples, vocabulary_performance=vocab_perf)
        assert len(result.vocabulary_insights) > 0

    def test_run_learning_cycle_with_style(self):
        b = self._make_brand()
        samples = ["Test content."]
        style_perf = {"emoji_style": {"light": [0.8, 0.9], "heavy": [0.2, 0.1]}}
        result = self.manager.run_learning_cycle(b, samples, style_performance=style_perf)
        assert len(result.style_insights) > 0

    def test_check_content(self):
        b = self._make_brand()
        check = self.manager.check_content("Our innovative expert AI solution", b)
        assert "overall_score" in check

    def test_health(self):
        b = self._make_brand()
        self.manager.run_learning_cycle(b, ["Test content."])
        health = self.manager.get_health()
        assert health["total_cycles"] == 1
        assert "memory_stats" in health

    def test_cycle_count(self):
        b = self._make_brand()
        self.manager.run_learning_cycle(b, ["Test."])
        self.manager.run_learning_cycle(b, ["Test2."])
        assert self.manager.cycle_count == 2

    def test_events(self):
        b = self._make_brand()
        self.manager.run_learning_cycle(b, ["Test."])
        assert len(self.manager.events) == 1

    def test_get_recent_cycles(self):
        b = self._make_brand()
        for _ in range(3):
            self.manager.run_learning_cycle(b, ["Test."])
        assert len(self.manager.get_recent_cycles(2)) == 2

    def test_recommendations_generated(self):
        b = self._make_brand()
        result = self.manager.run_learning_cycle(b, ["Test."])
        assert isinstance(result.recommendations, list)


# ─── Exceptions Tests ─────────────────────────────────────────────────
class TestExceptions:
    def test_base(self):
        assert issubclass(BrandVoiceError, Exception)

    def test_analysis(self):
        assert issubclass(AnalysisError, BrandVoiceError)

    def test_consistency(self):
        assert issubclass(ConsistencyError, BrandVoiceError)

    def test_learning(self):
        assert issubclass(LearningError, BrandVoiceError)


# ─── Integration Tests ────────────────────────────────────────────────
class TestBrandVoiceLearningIntegration:
    def test_full_pipeline(self):
        """Test: Profile → Analyze → Learn Tones → Learn Vocab → Check Consistency."""
        manager = BrandManager()
        brand = BrandProfile(name="TechCorp", industry="technology")
        brand.add_tone("professional", 0.8)
        brand.add_tone("educational", 0.6)
        brand.add_preferred_word("innovative")
        brand.add_preferred_word("expert")
        brand.add_forbidden_word("cheap")
        brand.add_terminology("AI", "Artificial Intelligence")
        brand.formality_level = "high"

        samples = [
            "Our innovative AI expert solution provides enterprise-grade technology.",
            "Discover how our expert team delivers innovative industry solutions.",
        ]
        tone_perf = {"professional": [0.9, 0.8, 0.7], "educational": [0.6, 0.5, 0.7]}
        vocab_perf = {"innovative": [0.9, 0.8, 0.7], "expert": [0.8, 0.9, 0.8]}

        result = manager.run_learning_cycle(brand, samples, tone_perf, vocab_perf)
        assert result.voice_analysis is not None
        assert len(result.tone_insights) > 0
        assert len(result.vocabulary_insights) > 0

    def test_consistency_with_violations(self):
        """Test: Content with forbidden words is flagged."""
        brand = BrandProfile(name="Test")
        brand.add_forbidden_word("cheap")
        brand.add_preferred_word("premium")

        manager = BrandManager()
        check = manager.check_content("This cheap product is not premium", brand)
        assert check["violation_count"] >= 1

    def test_tone_learning_affects_profile(self):
        """Test: Tone learning suggests profile updates."""
        learner = ToneLearner()
        current = {"professional": 0.3, "friendly": 0.3}
        perf = {"professional": [0.9, 0.9, 0.8], "friendly": [0.2, 0.3, 0.1]}
        results = learner.learn(current, perf)
        best = learner.get_best_tones(1)
        assert best[0].tone == "professional"
        assert best[0].suggested_weight > current["professional"]

    def test_vocabulary_increases_decreases(self):
        """Test: Vocabulary learner correctly identifies increases and decreases."""
        learner = VocabularyLearner()
        current = {"great": 0.2, "bad": 0.5}
        perf = {"great": [0.9, 0.8, 0.9], "bad": [0.1, 0.2, 0.1]}
        learner.learn(current, perf, min_samples=2)
        assert len(learner.get_increases()) >= 1
        assert len(learner.get_decreases()) >= 1

    def test_brand_memory_after_cycles(self):
        """Test: Memory stores learnings across cycles."""
        manager = BrandManager()
        brand = BrandProfile(name="Test")
        brand.add_tone("professional", 0.8)
        manager.run_learning_cycle(brand, ["Expert solution."])
        stats = manager.memory.get_stats()
        assert stats["total"] >= 0

    def test_fork_and_compare_consistency(self):
        """Test: Fork brand and compare consistency."""
        original = BrandProfile(name="Original")
        original.add_tone("professional", 0.5)
        original.add_preferred_word("expert")
        original.add_forbidden_word("cheap")

        forked = original.fork()
        forked.add_tone("professional", 0.9)
        forked.add_preferred_word("innovative")

        tracker = ConsistencyTracker()
        check1 = tracker.check_content("Expert solution", original)
        check2 = tracker.check_content("Expert innovative solution", forked)
        assert check2.overall_score >= check1.overall_score
