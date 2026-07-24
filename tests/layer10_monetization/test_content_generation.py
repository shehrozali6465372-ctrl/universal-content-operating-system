"""Tests for Layer 10 Module 6 — Content Generation Engine."""
from layers.layer10_monetization.modules.content_generation.content_generator import ContentGenerator
from layers.layer10_monetization.modules.content_generation.content_template import ContentTemplate, TemplateLibrary
from layers.layer10_monetization.modules.content_generation.platform_adapter import PlatformAdapter
from layers.layer10_monetization.modules.content_generation.tone_engine import ToneEngine, ToneProfile
from layers.layer10_monetization.modules.content_generation.hook_generator import HookGenerator
from layers.layer10_monetization.modules.content_generation.cta_engine import CTAEngine
from layers.layer10_monetization.modules.content_generation.seo_optimizer import SEOOptimizer
from layers.layer10_monetization.modules.content_generation.content_memory import ContentMemory
from layers.layer10_monetization.modules.content_generation.generation_metrics import GenerationMetrics
from layers.layer10_monetization.modules.content_generation.generation_report import GenerationReport
from layers.layer10_monetization.modules.content_generation.content_generation_manager import ContentGenerationManager


# ─── ContentGenerator Tests ──────────────────────────────────────
class TestContentGenerator:
    def setup_method(self):
        self.gen = ContentGenerator()

    def test_generate(self):
        content = self.gen.generate("AI Technology", "facebook")
        assert content.content_id.startswith("gc_")
        assert content.platform == "facebook"
        assert len(content.text) > 0

    def test_generate_different_platforms(self):
        for platform in ("facebook", "instagram", "x", "linkedin", "tiktok"):
            content = self.gen.generate("Test", platform)
            assert content.platform == platform

    def test_generate_batch(self):
        contents = self.gen.generate_batch(["AI", "ML", "DL"], "linkedin")
        assert len(contents) == 3

    def test_get_limits(self):
        limits = self.gen.get_limits("x")
        assert limits["max_text"] == 280

    def test_get_limits_unknown(self):
        limits = self.gen.get_limits("unknown")
        assert "max_text" in limits

    def test_stats(self):
        self.gen.generate("Test", "facebook")
        stats = self.gen.get_stats()
        assert stats["total_generated"] == 1

    def test_to_dict(self):
        content = self.gen.generate("Test", "instagram")
        d = content.to_dict()
        assert "content_id" in d
        assert "platform" in d


# ─── ContentTemplate Tests ───────────────────────────────────────
class TestContentTemplate:
    def setup_method(self):
        self.lib = TemplateLibrary()

    def test_create_template(self):
        tpl = ContentTemplate("social_post", "facebook")
        tpl.add_section("hook", "Did you know {{topic}}?")
        tpl.add_section("body", "Here's what you need to know.")
        assert len(tpl.structure) == 2

    def test_render(self):
        tpl = ContentTemplate("post", "facebook")
        tpl.add_section("hook", "About {{topic}}")
        result = tpl.render({"topic": "AI"})
        assert result == "About AI"

    def test_library_add(self):
        tpl = ContentTemplate("post", "facebook")
        self.lib.add(tpl)
        assert len(self.lib.get_all()) == 1

    def test_library_get_by_platform(self):
        self.lib.add(ContentTemplate("p1", "facebook"))
        self.lib.add(ContentTemplate("p2", "instagram"))
        fb = self.lib.get_by_platform("facebook")
        assert len(fb) == 1

    def test_library_stats(self):
        self.lib.add(ContentTemplate("p1", "facebook"))
        stats = self.lib.get_stats()
        assert stats["total"] == 1
        assert stats["by_platform"]["facebook"] == 1


# ─── PlatformAdapter Tests ───────────────────────────────────────
class TestPlatformAdapter:
    def setup_method(self):
        self.adapter = PlatformAdapter()

    def test_adapt_facebook(self):
        result = self.adapter.adapt("Great post!", "facebook")
        assert len(result) > 0

    def test_adapt_x_concise(self):
        long_text = "word " * 100
        result = self.adapter.adapt(long_text, "x")
        assert len(result) <= 280

    def test_adapt_linkedin(self):
        result = self.adapter.adapt("Professional content", "linkedin")
        assert result == "Professional content"

    def test_get_rules(self):
        rules = self.adapter.get_rules("linkedin")
        assert rules["tone"] == "professional"

    def test_set_rules(self):
        self.adapter.set_rules("custom", {"tone": "custom"})
        rules = self.adapter.get_rules("custom")
        assert rules["tone"] == "custom"

    def test_supported_platforms(self):
        platforms = self.adapter.get_supported_platforms()
        assert "facebook" in platforms
        assert "linkedin" in platforms


# ─── ToneEngine Tests ────────────────────────────────────────────
class TestToneEngine:
    def setup_method(self):
        self.engine = ToneEngine()

    def test_set_tone(self):
        tone = self.engine.set_tone("casual")
        assert tone.name == "casual"
        assert tone.formality < 0.5

    def test_get_tone(self):
        tone = self.engine.get_tone()
        assert tone.name == "professional"

    def test_blend_tones(self):
        blended = self.engine.blend_tones("professional", "casual", 0.5)
        assert blended.formality > 0.3
        assert blended.formality < 0.9

    def test_available_tones(self):
        tones = self.engine.get_available_tones()
        assert "professional" in tones
        assert "casual" in tones
        assert len(tones) >= 5

    def test_history(self):
        self.engine.set_tone("casual")
        history = self.engine.get_history()
        assert len(history) == 1

    def test_tone_to_dict(self):
        tone = ToneProfile("educational")
        d = tone.to_dict()
        assert "formality" in d
        assert "humor" in d


# ─── HookGenerator Tests ─────────────────────────────────────────
class TestHookGenerator:
    def setup_method(self):
        self.hg = HookGenerator()

    def test_generate(self):
        hooks = self.hg.generate("AI Technology", "question", "linkedin")
        assert len(hooks) > 0
        assert hooks[0].platform == "linkedin"

    def test_generate_batch(self):
        hooks = self.hg.generate_batch("AI", "facebook")
        assert len(hooks) >= 3

    def test_best_hooks(self):
        self.hg.generate_batch("AI")
        best = self.hg.get_best_hooks(3)
        assert len(best) <= 3

    def test_stats(self):
        self.hg.generate_batch("AI")
        stats = self.hg.get_stats()
        assert stats["total"] > 0


# ─── CTAEngine Tests ─────────────────────────────────────────────
class TestCTAEngine:
    def setup_method(self):
        self.cta = CTAEngine()

    def test_generate(self):
        ctas = self.cta.generate("facebook", count=2)
        assert len(ctas) == 2
        assert ctas[0].platform == "facebook"

    def test_generate_different_platforms(self):
        for platform in ("facebook", "instagram", "x", "linkedin"):
            ctas = self.cta.generate(platform, count=1)
            assert len(ctas) == 1

    def test_add_custom_cta(self):
        self.cta.add_custom_cta("custom", "Custom CTA!")
        ctas = self.cta.generate("custom")
        assert any("Custom" in c.text for c in ctas)

    def test_stats(self):
        self.cta._ctas.clear()
        self.cta.generate("facebook")
        self.cta.generate("instagram")
        stats = self.cta.get_stats()
        assert stats["total"] == 6


# ─── SEOOptimizer Tests ──────────────────────────────────────────
class TestSEOOptimizer:
    def setup_method(self):
        self.seo = SEOOptimizer()

    def test_optimize_title(self):
        result = self.seo.optimize_title("AI Trends", "artificial intelligence")
        assert "artificial intelligence" in result["optimized"].lower()

    def test_optimize_title_no_keyword(self):
        result = self.seo.optimize_title("AI Trends")
        assert result["optimized"] == "AI Trends"

    def test_optimize_title_too_long(self):
        result = self.seo.optimize_title("A" * 100)
        assert len(result["optimized"]) <= 60

    def test_optimize_description(self):
        result = self.seo.optimize_description("About AI", "machine learning")
        assert "machine learning" in result["optimized"].lower()

    def test_generate_meta(self):
        meta = self.seo.generate_meta("Title", "Description", ["ai", "tech"])
        assert meta["keywords"] == ["ai", "tech"]

    def test_keyword_density(self):
        result = self.seo.check_keyword_density("AI is great and AI is future", "AI")
        assert result["count"] == 2


# ─── ContentMemory Tests ─────────────────────────────────────────
class TestContentMemory:
    def setup_method(self):
        self.mem = ContentMemory()

    def test_store(self):
        entry = self.mem.store("social_post", "facebook", "AI", quality_score=0.8)
        assert entry.entry_id.startswith("cmem_")
        assert entry.quality_score == 0.8

    def test_search(self):
        self.mem.store("social_post", "facebook", "AI")
        self.mem.store("article", "linkedin", "ML")
        results = self.mem.search(platform="facebook")
        assert len(results) == 1

    def test_search_min_quality(self):
        self.mem.store("post", "fb", "AI", quality_score=0.9)
        self.mem.store("post", "fb", "ML", quality_score=0.3)
        results = self.mem.search(min_quality=0.5)
        assert len(results) == 1

    def test_top_performers(self):
        self.mem.store("post", "fb", "AI", quality_score=0.9)
        self.mem.store("post", "fb", "ML", quality_score=0.5)
        top = self.mem.get_top_performers(1)
        assert top[0].quality_score == 0.9

    def test_stats(self):
        self.mem.store("post", "fb")
        stats = self.mem.get_stats()
        assert stats["total"] == 1


# ─── GenerationMetrics Tests ─────────────────────────────────────
class TestGenerationMetrics:
    def setup_method(self):
        self.metrics = GenerationMetrics()

    def test_record(self):
        self.metrics.record_generation("facebook", "social_post", 100, 0.8)
        assert self.metrics._total_generated == 1

    def test_avg_generation_time(self):
        self.metrics.record_generation(generation_time_ms=100)
        self.metrics.record_generation(generation_time_ms=200)
        assert self.metrics.get_avg_generation_time() == 150.0

    def test_avg_quality(self):
        self.metrics.record_generation(quality_score=0.8)
        self.metrics.record_generation(quality_score=0.6)
        assert self.metrics.get_avg_quality() == 0.7

    def test_summary(self):
        self.metrics.record_generation("facebook", "post", 100, 0.8)
        summary = self.metrics.get_summary()
        assert summary["total_generated"] == 1
        assert "facebook" in summary["by_platform"]


# ─── GenerationReport Tests ──────────────────────────────────────
class TestGenerationReport:
    def test_create(self):
        report = GenerationReport()
        assert report.report_id.startswith("grep_")

    def test_set_summary(self):
        report = GenerationReport()
        report.set_summary({"total_generated": 10, "avg_quality": 0.85})
        assert report.total_content == 10
        assert report.avg_quality == 0.85

    def test_export_dict(self):
        report = GenerationReport()
        report.set_summary({"total_generated": 5})
        report.add_recommendation("Improve quality")
        d = report.export_dict()
        assert "recommendations" in d
        assert d["total_content"] == 5


# ─── ContentGenerationManager Tests ──────────────────────────────
class TestContentGenerationManager:
    def setup_method(self):
        self.mgr = ContentGenerationManager()

    def test_generate(self):
        result = self.mgr.generate("AI Technology", "facebook")
        assert "content" in result
        assert "hooks" in result
        assert "ctas" in result
        assert "seo" in result
        assert "tone" in result
        assert result["duration_ms"] >= 0

    def test_generate_multi_platform(self):
        results = self.mgr.generate_multi_platform("AI", ["facebook", "linkedin"])
        assert "facebook" in results
        assert "linkedin" in results

    def test_generate_batch(self):
        results = self.mgr.generate_batch(["AI", "ML"])
        assert len(results) == 2

    def test_generate_report(self):
        self.mgr.generate("Test")
        report = self.mgr.generate_report()
        assert report.report_id.startswith("grep_")

    def test_health(self):
        self.mgr.generate("Test")
        health = self.mgr.get_health()
        assert "metrics" in health
        assert "memory" in health

    def test_different_tones(self):
        for tone in ("professional", "casual", "educational"):
            result = self.mgr.generate("AI", "linkedin", tone=tone)
            assert result["tone"]["formality"] >= 0

    def test_different_content_types(self):
        for ct in ("social_post", "article", "thread"):
            result = self.mgr.generate("AI", "linkedin", content_type=ct)
            assert "content" in result


# ─── Integration Tests ───────────────────────────────────────────
class TestContentGenerationIntegration:
    def setup_method(self):
        self.mgr = ContentGenerationManager()

    def test_full_pipeline(self):
        result = self.mgr.generate(
            "How AI is transforming healthcare",
            platform="linkedin",
            content_type="article",
            tone="educational",
        )
        assert "content" in result
        assert result["content"]["platform"] == "linkedin"
        assert len(result["hooks"]) > 0
        assert len(result["ctas"]) > 0

    def test_cross_platform_generation(self):
        platforms = ["facebook", "instagram", "x", "linkedin", "tiktok"]
        results = self.mgr.generate_multi_platform("AI in 2024", platforms)
        assert len(results) == 5
        for platform, result in results.items():
            assert result["content"]["platform"] == platform

    def test_content_adaptation(self):
        result = self.mgr.generate("Long article about technology", "x")
        assert result["content"]["text_length"] <= 280

    def test_memory_and_metrics(self):
        for i in range(3):
            self.mgr.generate(f"Topic {i}", "facebook")
        health = self.mgr.get_health()
        assert health["memory"]["total"] == 3
        assert health["metrics"]["total_generated"] == 3

    def test_report_generation(self):
        for i in range(5):
            self.mgr.generate(f"Topic {i}", "linkedin")
        report = self.mgr.generate_report()
        d = report.export_dict()
        assert d["total_content"] == 5
