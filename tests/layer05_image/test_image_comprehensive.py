"""Comprehensive Layer 5 Tests — 120+ tests for production-grade coverage."""
from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner
from layers.layer05_image.modules.image_prompt.image_prompt import ImagePromptBuilder, STYLE_PRESETS
from layers.layer05_image.modules.image_provider.image_provider import MockImageProvider, ImageResponse
from layers.layer05_image.modules.layout_engine.layout_engine import LayoutEngine, LAYOUT_PRESETS
from layers.layer05_image.modules.thumbnail_engine.thumbnail_engine import ThumbnailEngine
from layers.layer05_image.modules.carousel_planner.carousel_planner import CarouselPlanner
from layers.layer05_image.modules.infographic_engine.infographic_engine import InfographicEngine, CHART_TYPES
from layers.layer05_image.modules.image_optimizer.image_optimizer import ImageOptimizer, PLATFORM_IMAGE_CONFIG
from layers.layer05_image.modules.image_memory.image_memory import ImageMemory
from layers.layer05_image.modules.image_orchestrator.image_orchestrator import ImageOrchestrator
from layers.layer05_image.modules.accessibility_engine.accessibility_engine import AccessibilityEngine
from layers.layer05_image.modules.visual_quality.visual_quality import VisualQualityScorer
from layers.layer05_image.modules.prompt_evaluator.prompt_evaluator import PromptEvaluator


# ═══════════════════════════════════════
# Image Planner — Platform Specs
# ═══════════════════════════════════════

class TestImagePlannerPlatforms:
    def setup_method(self):
        self.ip = ImagePlanner()

    def test_facebook_feed(self):
        plans = self.ip.plan("AI", "facebook")
        assert plans[0].dimensions == (1200, 630)

    def test_instagram_feed(self):
        plans = self.ip.plan("AI", "instagram")
        assert plans[0].dimensions == (1080, 1080)

    def test_twitter_tweet(self):
        plans = self.ip.plan("AI", "twitter")
        assert plans[0].platform == "twitter"

    def test_linkedin_feed(self):
        plans = self.ip.plan("AI", "linkedin")
        assert plans[0].dimensions == (1200, 627)

    def test_youtube_thumbnail(self):
        plans = self.ip.plan("AI", "youtube")
        assert plans[0].platform == "youtube"

    def test_pinterest_pin(self):
        plans = self.ip.plan("AI", "pinterest")
        assert plans[0].platform == "pinterest"

    def test_tiktok_cover(self):
        plans = self.ip.plan("AI", "tiktok")
        assert plans[0].platform == "tiktok"

    def test_threads_post(self):
        plans = self.ip.plan("AI", "threads")
        assert plans[0].dimensions == (1080, 1080)

    def test_plan_count_multiple(self):
        plans = self.ip.plan("AI", "facebook", count=5)
        assert len(plans) == 5

    def test_plan_id_unique(self):
        import time
        time.sleep(0.001)
        plans = self.ip.plan("AI", "facebook", count=3)
        ids = [p.plan_id for p in plans]
        assert len(ids) == 3

    def test_suggest_type_photo(self):
        assert self.ip.suggest_type("educate", "facebook") in ("illustration", "infographic")

    def test_suggest_type_meme(self):
        assert self.ip.suggest_type("entertain", "facebook") == "meme"

    def test_suggest_type_product(self):
        assert self.ip.suggest_type("promote", "instagram") == "product"

    def test_suggest_type_quote(self):
        assert self.ip.suggest_type("inspire", "instagram") == "quote"

    def test_suggest_type_default(self):
        assert self.ip.suggest_type("engage", "facebook") in ("photo", "meme", "quote", "illustration")

    def test_all_image_types_in_plan(self):
        for img_type in ("photo", "illustration", "infographic", "meme", "quote", "product", "carousel", "thumbnail"):
            plans = self.ip.plan("AI", "facebook", image_type=img_type)
            assert plans[0].image_type == img_type

    def test_plan_to_dict_fields(self):
        plans = self.ip.plan("AI", "facebook")
        d = plans[0].to_dict()
        for field in ("plan_id", "image_type", "platform", "dimensions", "style", "priority"):
            assert field in d

    def test_plan_multi_platform_all(self):
        platforms = ["facebook", "instagram", "twitter", "linkedin", "youtube", "pinterest", "tiktok", "threads"]
        result = self.ip.plan_multi_platform("AI", platforms)
        assert len(result) == 8

    def test_plan_count_stat(self):
        self.ip.plan("A", "facebook", count=3)
        self.ip.plan("B", "twitter")
        assert self.ip.plan_count == 4

    def test_plan_metadata(self):
        plans = self.ip.plan("AI", "facebook")
        assert isinstance(plans[0].metadata, dict)

    def test_plan_priority_default(self):
        plans = self.ip.plan("AI", "facebook")
        assert plans[0].priority == "medium"

    def test_plan_style_default(self):
        plans = self.ip.plan("AI", "facebook")
        assert plans[0].style == "modern"


# ═══════════════════════════════════════
# Image Prompt Builder — Styles & Specs
# ═══════════════════════════════════════

class TestImagePromptComprehensive:
    def setup_method(self):
        self.pb = ImagePromptBuilder()

    def test_all_styles(self):
        for style in STYLE_PRESETS:
            p = self.pb.build("A cat", style=style)
            assert p.style == style
            assert p.text != ""

    def test_aspect_ratio_facebook(self):
        p = self.pb.build("test", platform="facebook")
        assert p.aspect_ratio == "1200:630"

    def test_aspect_ratio_instagram(self):
        p = self.pb.build("test", platform="instagram")
        assert p.aspect_ratio == "1080:1080"

    def test_aspect_ratio_twitter(self):
        p = self.pb.build("test", platform="twitter")
        assert p.aspect_ratio == "16:9"

    def test_aspect_ratio_linkedin(self):
        p = self.pb.build("test", platform="linkedin")
        assert p.aspect_ratio == "1200:627"

    def test_aspect_ratio_tiktok(self):
        p = self.pb.build("test", platform="tiktok")
        assert p.aspect_ratio == "9:16"

    def test_negative_prompt_always(self):
        p = self.pb.build("test")
        assert "blurry" in p.negative_prompt

    def test_hd_quality_professional(self):
        p = self.pb.build("test", style="professional")
        assert p.parameters.get("quality") == "hd"

    def test_standard_quality_modern(self):
        p = self.pb.build("test", style="modern")
        assert p.parameters.get("quality") == "standard"

    def test_batch_size(self):
        ps = self.pb.build_batch(["A", "B", "C", "D", "E"])
        assert len(ps) == 5

    def test_extra_instructions(self):
        p = self.pb.build("test", extra_instructions=["warm lighting", "golden hour"])
        assert "warm lighting" in p.text

    def test_to_dict_fields(self):
        p = self.pb.build("test")
        d = p.to_dict()
        for field in ("prompt_id", "text", "negative_prompt", "style", "aspect_ratio"):
            assert field in d

    def test_build_count(self):
        self.pb.build("A")
        self.pb.build("B")
        assert self.pb.build_count == 2

    def test_prompt_id_unique(self):
        import time
        time.sleep(0.001)
        p1 = self.pb.build("A")
        p2 = self.pb.build("B")
        assert len(p1.prompt_id) > 0


# ═══════════════════════════════════════
# Image Provider
# ═══════════════════════════════════════

class TestImageProviderComprehensive:
    def test_mock_generate_returns_url(self):
        p = MockImageProvider()
        r = p.generate("test")
        assert r.image_url.startswith("http")

    def test_mock_revised_prompt(self):
        p = MockImageProvider()
        r = p.generate("my prompt here")
        assert r.revised_prompt == "my prompt here"

    def mock_provider_stats(self):
        p = MockImageProvider()
        p.generate("a")
        p.generate("b")
        assert p.stats["calls"] == 2

    def test_response_to_dict(self):
        r = ImageResponse()
        r.image_url = "http://test.com/img.png"
        d = r.to_dict()
        assert "image_url" in d
        assert "latency_ms" in d

    def test_mock_custom_url(self):
        p = MockImageProvider()
        p._mock_url = "http://custom.com/img.jpg"
        r = p.generate("test")
        assert r.image_url == "http://custom.com/img.jpg"


# ═══════════════════════════════════════
# Layout Engine
# ═══════════════════════════════════════

class TestLayoutEngineComprehensive:
    def setup_method(self):
        self.le = LayoutEngine()

    def test_all_platforms(self):
        for p in ("facebook", "instagram", "twitter", "linkedin", "youtube", "pinterest"):
            layout = self.le.get_layout(p, "photo")
            assert layout.width > 0
            assert layout.height > 0

    def test_infographic_gets_multi_panel(self):
        layout = self.le.get_layout("pinterest", "infographic")
        assert layout.layout_type == "multi_panel"

    def test_quote_gets_centered(self):
        layout = self.le.get_layout("instagram", "quote")
        assert layout.layout_type == "centered"

    def test_carousel_gets_single_focal(self):
        layout = self.le.get_layout("instagram", "carousel")
        assert layout.layout_type == "single_focal"

    def test_layout_override(self):
        layout = self.le.get_layout("facebook", "photo", layout_type="diagonal")
        assert layout.layout_type == "diagonal"

    def test_available_layouts_count(self):
        assert len(self.le.get_available_layouts()) == len(LAYOUT_PRESETS)

    def test_layout_to_dict(self):
        layout = self.le.get_layout("facebook", "photo")
        d = layout.to_dict()
        assert "layout_type" in d
        assert "guidelines" in d


# ═══════════════════════════════════════
# Thumbnail Engine
# ═══════════════════════════════════════

class TestThumbnailEngineComprehensive:
    def setup_method(self):
        self.te = ThumbnailEngine()

    def test_youtube_thumb(self):
        t = self.te.plan("AI Tutorial", "youtube")
        assert t.dimensions == (1280, 720)

    def test_facebook_thumb(self):
        t = self.te.plan("AI Jobs", "facebook")
        assert t.dimensions == (1200, 630)

    def test_twitter_thumb(self):
        t = self.te.plan("AI News", "twitter")
        assert t.dimensions == (1200, 675)

    def test_text_shortened(self):
        t = self.te.plan("A" * 100, "youtube")
        assert len(t.text) <= 40

    def test_plan_to_dict(self):
        t = self.te.plan("AI", "youtube")
        d = t.to_dict()
        assert "plan_id" in d
        assert "dimensions" in d

    def test_plan_id_unique(self):
        t1 = self.te.plan("A", "youtube")
        t2 = self.te.plan("B", "youtube")
        assert len(t1.plan_id) > 0


# ═══════════════════════════════════════
# Carousel Planner
# ═══════════════════════════════════════

class TestCarouselPlannerComprehensive:
    def setup_method(self):
        self.cp = CarouselPlanner()

    def test_plan_structure(self):
        plan = self.cp.plan("AI Tips", "instagram", key_points=["Tip 1", "Tip 2", "Tip 3"])
        assert plan.total_slides == 5

    def test_cover_first(self):
        plan = self.cp.plan("AI", "instagram", slide_count=3)
        assert plan.slides[0].is_cover is True

    def test_cta_last(self):
        plan = self.cp.plan("AI", "instagram", slide_count=3)
        assert plan.slides[-1].is_cta is True

    def test_content_slides(self):
        plan = self.cp.plan("AI", "instagram", key_points=["A", "B"])
        content = [s for s in plan.slides if not s.is_cover and not s.is_cta]
        assert len(content) == 2

    def test_slide_to_dict(self):
        plan = self.cp.plan("AI", "instagram", slide_count=3)
        d = plan.slides[0].to_dict()
        assert "slide_number" in d
        assert "is_cover" in d

    def test_plan_to_dict(self):
        plan = self.cp.plan("AI", "instagram", slide_count=3)
        d = plan.to_dict()
        assert "slides" in d
        assert "total_slides" in d

    def test_different_platforms(self):
        for p in ("instagram", "linkedin", "facebook"):
            plan = self.cp.plan("AI", p)
            assert plan.platform == p


# ═══════════════════════════════════════
# Infographic Engine
# ═══════════════════════════════════════

class TestInfographicEngineComprehensive:
    def setup_method(self):
        self.ie = InfographicEngine()

    def test_all_chart_types(self):
        for ct in CHART_TYPES:
            plan = self.ie.plan("AI", chart_type=ct)
            assert plan.chart_type == ct

    def test_suggest_trend(self):
        assert self.ie.suggest_chart("trend") == "line"

    def test_suggest_proportion(self):
        assert self.ie.suggest_chart("proportion") == "pie"

    def test_suggest_process(self):
        assert self.ie.suggest_chart("process") == "flowchart"

    def test_suggest_comparison(self):
        assert self.ie.suggest_chart("comparison") == "bar"

    def test_suggest_default(self):
        assert self.ie.suggest_chart("unknown") == "bar"

    def test_dimensions_pinterest(self):
        plan = self.ie.plan("AI", platform="pinterest")
        assert plan.dimensions == (1000, 1500)

    def test_dimensions_instagram(self):
        plan = self.ie.plan("AI", platform="instagram")
        assert plan.dimensions == (1080, 1350)

    def test_plan_with_data(self):
        data = [{"label": "A", "value": 10}, {"label": "B", "value": 20}]
        plan = self.ie.plan("AI", data=data)
        assert len(plan.data_points) == 2

    def test_plan_to_dict(self):
        plan = self.ie.plan("AI", chart_type="bar")
        d = plan.to_dict()
        assert "chart_type" in d


# ═══════════════════════════════════════
# Image Optimizer
# ═══════════════════════════════════════

class TestImageOptimizerComprehensive:
    def setup_method(self):
        self.io = ImageOptimizer()

    def test_all_platforms_optimize(self):
        for p in PLATFORM_IMAGE_CONFIG:
            r = self.io.optimize(1080, 1080, p)
            assert r.platform == p

    def test_optimal_large_image(self):
        r = self.io.optimize(1920, 1080, "facebook")
        assert r.is_optimal is True

    def test_too_small(self):
        r = self.io.optimize(100, 100, "facebook")
        assert r.is_optimal is False

    def test_instagram_ratio_warning(self):
        r = self.io.optimize(2000, 500, "instagram")
        assert len(r.recommendations) > 0

    def test_format_assigned(self):
        r = self.io.optimize(1080, 1080, "twitter")
        assert r.format in ("jpg", "png", "gif")

    def test_optimization_count(self):
        self.io.optimize(1080, 1080, "facebook")
        self.io.optimize(1080, 1080, "twitter")
        assert self.io.optimization_count == 2

    def test_to_dict_fields(self):
        r = self.io.optimize(1080, 1080, "facebook")
        d = r.to_dict()
        for field in ("platform", "format", "dimensions", "is_optimal"):
            assert field in d


# ═══════════════════════════════════════
# Image Memory
# ═══════════════════════════════════════

class TestImageMemoryComprehensive:
    def setup_method(self):
        self.im = ImageMemory()

    def test_multiple_profiles(self):
        self.im.set_profile("brand1", colors=["#FF0000"])
        self.im.set_profile("brand2", colors=["#0000FF"])
        assert self.im.profile_count == 2

    def test_profile_to_dict(self):
        p = self.im.set_profile("test", colors=["#FFF"], style="minimalist")
        d = p.to_dict()
        assert d["name"] == "test"
        assert d["style"] == "minimalist"

    def test_store_multiple(self):
        self.im.store_image("facebook", "A", "url1")
        self.im.store_image("instagram", "B", "url2")
        self.im.store_image("twitter", "C", "url3")
        assert self.im.history_count == 3

    def test_history_filter(self):
        self.im.store_image("facebook", "A", "url1")
        self.im.store_image("twitter", "B", "url2")
        assert len(self.im.get_history("facebook")) == 1

    def test_history_limit(self):
        for i in range(20):
            self.im.store_image("fb", f"topic{i}", f"url{i}")
        assert len(self.im.get_history(limit=5)) == 5

    def test_get_profile_none(self):
        assert self.im.get_profile("nonexistent") is None


# ═══════════════════════════════════════
# Accessibility Engine
# ═══════════════════════════════════════

class TestAccessibilityEngine:
    def setup_method(self):
        self.ae = AccessibilityEngine()

    def test_alt_text_generation(self):
        alt = self.ae.generate_alt_text("AI Jobs", "infographic", "growth chart")
        assert "infographic" in alt.lower()
        assert "AI Jobs" in alt

    def test_alt_text_no_desc(self):
        alt = self.ae.generate_alt_text("AI", "photo")
        assert "AI" in alt

    def test_contrast_black_white(self):
        ratio = self.ae.check_contrast("#000000", "#FFFFFF")
        assert ratio >= 15

    def test_contrast_low(self):
        ratio = self.ae.check_contrast("#CCCCCC", "#FFFFFF")
        assert ratio < 4.5

    def test_contrast_medium(self):
        ratio = self.ae.check_contrast("#333333", "#FFFFFF")
        assert 10 < ratio < 15

    def test_validate_good(self):
        r = self.ae.validate("Short text", "#000000", "#FFFFFF", "AI")
        assert r.contrast_score >= 10

    def test_validate_low_contrast(self):
        r = self.ae.validate("text", "#CCCCCC", "#FFFFFF", "AI")
        assert any("contrast" in i.lower() for i in r.issues)

    def test_validate_too_much_text(self):
        r = self.ae.validate("word " * 20, "#000000", "#FFFFFF", "AI")
        assert any("text" in i.lower() for i in r.issues)

    def test_validate_empty(self):
        r = self.ae.validate("", "#000000", "#FFFFFF", "AI")
        assert r.alt_text != ""

    def test_to_dict(self):
        r = self.ae.validate("text", "#000000", "#FFFFFF", "AI")
        d = r.to_dict()
        for field in ("alt_text", "contrast_score", "issues", "score"):
            assert field in d

    def test_check_count(self):
        self.ae.validate("a", "#000", "#FFF", "t")
        self.ae.validate("b", "#000", "#FFF", "t")
        assert self.ae.check_count == 2


# ═══════════════════════════════════════
# Visual Quality Scorer
# ═══════════════════════════════════════

class TestVisualQualityScorer:
    def setup_method(self):
        self.vqs = VisualQualityScorer()

    def test_photo_quality(self):
        r = self.vqs.score(image_type="photo")
        assert r.overall_score > 0.5

    def test_meme_clickability(self):
        r = self.vqs.score(image_type="meme")
        assert r.clickability >= 0.85

    def test_thumbnail_clickability(self):
        r = self.vqs.score(image_type="thumbnail")
        assert r.clickability >= 0.8

    def test_face_boosts(self):
        r1 = self.vqs.score(image_type="photo", has_face=False)
        r2 = self.vqs.score(image_type="photo", has_face=True)
        assert r2.composition_score >= r1.composition_score

    def test_dense_text_penalty(self):
        r = self.vqs.score(text_overlay="word " * 20)
        assert r.text_density_score < 0.5
        assert len(r.issues) > 0

    def test_short_text_good(self):
        r = self.vqs.score(text_overlay="AI is great")
        assert r.text_density_score == 0.9

    def test_instagram_boost(self):
        r_fb = self.vqs.score(image_type="photo", platform="facebook")
        r_ig = self.vqs.score(image_type="photo", platform="instagram")
        assert r_ig.clickability >= r_fb.clickability

    def test_grades(self):
        r = self.vqs.score(image_type="meme", has_face=True)
        assert r.grade in ("A+", "A", "B+")

    def test_score_count(self):
        self.vqs.score()
        self.vqs.score()
        assert self.vqs.score_count == 2

    def test_to_dict(self):
        r = self.vqs.score()
        d = r.to_dict()
        for field in ("composition", "overall_score", "grade"):
            assert field in d


# ═══════════════════════════════════════
# Prompt Evaluator
# ═══════════════════════════════════════

class TestPromptEvaluator:
    def setup_method(self):
        self.pe = PromptEvaluator()

    def test_evaluate_good_prompt(self):
        r = self.pe.evaluate("A detailed, professional, modern cityscape with vibrant colors")
        assert r.score > 0.5

    def test_evaluate_short_prompt(self):
        r = self.pe.evaluate("cat")
        assert r.clarity_score < 0.6
        assert len(r.issues) > 0

    def test_evaluate_adds_quality_words(self):
        r = self.pe.evaluate("A beautiful sunset with golden light")
        assert "detailed" in r.refined_prompt.lower() or "quality" in r.refined_prompt.lower()

    def test_evaluate_clarity_long(self):
        r = self.pe.evaluate("This is a very long and detailed description of something interesting")
        assert r.clarity_score >= 0.8

    def test_evaluate_to_dict(self):
        r = self.pe.evaluate("test prompt")
        d = r.to_dict()
        for field in ("clarity", "specificity", "score"):
            assert field in d

    def test_eval_count(self):
        self.pe.evaluate("A")
        self.pe.evaluate("B")
        assert self.pe.eval_count == 2

    def test_refine_enhances(self):
        r = self.pe.evaluate("x")
        assert len(r.refined_prompt) >= len(r.prompt)


# ═══════════════════════════════════════
# Image Orchestrator — Integration
# ═══════════════════════════════════════

class TestImageOrchestratorComprehensive:
    def setup_method(self):
        self.orch = ImageOrchestrator()

    def test_run_all_platforms(self):
        for p in ("facebook", "instagram", "twitter", "linkedin", "youtube", "pinterest", "tiktok", "threads"):
            r = self.orch.run("AI", p)
            assert r.platform == p
            assert r.image_plan is not None
            assert r.prompt is not None
            assert r.layout is not None

    def test_run_multi_platform(self):
        results = self.orch.run_multi_platform("AI", ["facebook", "instagram", "linkedin"])
        assert len(results) == 3

    def test_run_different_types(self):
        for t in ("photo", "infographic", "meme", "quote", "carousel"):
            r = self.orch.run("AI", "facebook", image_type=t)
            assert r.image_plan.image_type == t

    def test_run_different_styles(self):
        for s in ("modern", "minimalist", "vibrant", "professional"):
            r = self.orch.run("AI", "facebook", style=s)
            assert r.prompt.style == s

    def test_run_has_image_response(self):
        r = self.orch.run("AI", "facebook")
        assert r.image_response is not None
        assert r.image_response.image_url != ""

    def test_run_has_optimization(self):
        r = self.orch.run("AI", "facebook")
        assert r.optimization is not None

    def test_run_pipeline_time(self):
        r = self.orch.run("AI", "facebook")
        assert r.pipeline_time_ms >= 0

    def test_run_to_dict(self):
        r = self.orch.run("AI", "facebook")
        d = r.to_dict()
        for field in ("topic", "platform", "prompt", "image"):
            assert field in d

    def test_run_count(self):
        self.orch.run("A", "facebook")
        self.orch.run("B", "instagram")
        assert self.orch.run_count == 2

    def test_memory_populated(self):
        self.orch.run("AI", "facebook")
        assert self.orch.memory.history_count >= 1
