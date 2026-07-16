"""Tests for Layer 5 — Image & Visual Intelligence."""
from layers.layer05_image.modules.image_planner.image_planner import ImagePlanner
from layers.layer05_image.modules.image_prompt.image_prompt import ImagePromptBuilder
from layers.layer05_image.modules.image_provider.image_provider import MockImageProvider
from layers.layer05_image.modules.layout_engine.layout_engine import LayoutEngine
from layers.layer05_image.modules.thumbnail_engine.thumbnail_engine import ThumbnailEngine
from layers.layer05_image.modules.carousel_planner.carousel_planner import CarouselPlanner
from layers.layer05_image.modules.infographic_engine.infographic_engine import InfographicEngine
from layers.layer05_image.modules.image_optimizer.image_optimizer import ImageOptimizer
from layers.layer05_image.modules.image_memory.image_memory import ImageMemory
from layers.layer05_image.modules.image_orchestrator.image_orchestrator import ImageOrchestrator


class TestImagePlanner:
    def setup_method(self):
        self.ip = ImagePlanner()

    def test_plan_basic(self):
        plans = self.ip.plan("AI Jobs", "facebook")
        assert len(plans) == 1
        assert plans[0].platform == "facebook"

    def test_plan_multi(self):
        plans = self.ip.plan("AI", count=3)
        assert len(plans) == 3

    def test_plan_multi_platform(self):
        result = self.ip.plan_multi_platform("AI", ["facebook", "instagram"])
        assert "facebook" in result
        assert "instagram" in result

    def test_suggest_type(self):
        assert self.ip.suggest_type("educate", "pinterest") == "infographic"
        assert self.ip.suggest_type("entertain", "facebook") == "meme"
        assert self.ip.suggest_type("promote", "instagram") == "product"

    def test_to_dict(self):
        plans = self.ip.plan("AI", "facebook")
        d = plans[0].to_dict()
        assert "plan_id" in d
        assert "dimensions" in d


class TestImagePromptBuilder:
    def setup_method(self):
        self.pb = ImagePromptBuilder()

    def test_build(self):
        p = self.pb.build("A futuristic city", style="modern", platform="instagram")
        assert p.text != ""
        assert p.aspect_ratio == "1080:1080"

    def test_build_negative_prompt(self):
        p = self.pb.build("test", platform="facebook")
        assert "blurry" in p.negative_prompt

    def test_build_batch(self):
        ps = self.pb.build_batch(["A", "B", "C"], platform="twitter")
        assert len(ps) == 3

    def test_styles(self):
        for s in ("modern", "minimalist", "vibrant", "professional", "artistic"):
            p = self.pb.build("test", style=s)
            assert p.style == s

    def test_to_dict(self):
        p = self.pb.build("test")
        d = p.to_dict()
        assert "text" in d


class TestImageProvider:
    def test_mock_generate(self):
        p = MockImageProvider()
        r = p.generate("test prompt")
        assert r.image_url != ""
        assert r.provider == "mock"

    def test_mock_configured(self):
        assert MockImageProvider().is_configured() is True

    def test_mock_stats(self):
        p = MockImageProvider()
        p.generate("test")
        assert p.stats["calls"] == 1


class TestLayoutEngine:
    def test_get_layout(self):
        le = LayoutEngine()
        layout = le.get_layout("instagram", "photo")
        assert layout.width == 1080
        assert layout.height == 1080

    def test_infographic_layout(self):
        le = LayoutEngine()
        layout = le.get_layout("pinterest", "infographic")
        assert layout.layout_type == "multi_panel"

    def test_available_layouts(self):
        le = LayoutEngine()
        assert len(le.get_available_layouts()) >= 5


class TestThumbnailEngine:
    def test_plan_youtube(self):
        te = ThumbnailEngine()
        t = te.plan("AI Tutorial", "youtube")
        assert t.dimensions == (1280, 720)

    def test_plan_count(self):
        te = ThumbnailEngine()
        te.plan("A", "youtube")
        te.plan("B", "youtube")
        assert te.plan_count == 2


class TestCarouselPlanner:
    def test_plan(self):
        cp = CarouselPlanner()
        plan = cp.plan("AI Tips", "instagram", key_points=["Tip 1", "Tip 2", "Tip 3"])
        assert plan.total_slides == 5  # cover + 3 content + CTA
        assert plan.slides[0].is_cover is True
        assert plan.slides[-1].is_cta is True

    def test_to_dict(self):
        cp = CarouselPlanner()
        plan = cp.plan("AI", "instagram", slide_count=3)
        d = plan.to_dict()
        assert "slides" in d


class TestInfographicEngine:
    def test_plan(self):
        ie = InfographicEngine()
        plan = ie.plan("AI Growth", chart_type="bar", platform="pinterest")
        assert plan.chart_type == "bar"
        assert plan.dimensions == (1000, 1500)

    def test_suggest_chart(self):
        ie = InfographicEngine()
        assert ie.suggest_chart("trend") == "line"
        assert ie.suggest_chart("proportion") == "pie"


class TestImageOptimizer:
    def test_optimize(self):
        io = ImageOptimizer()
        r = io.optimize(1080, 1080, "instagram")
        assert r.is_optimal is True

    def test_optimize_small(self):
        io = ImageOptimizer()
        r = io.optimize(200, 200, "facebook")
        assert r.is_optimal is False
        assert len(r.recommendations) > 0

    def test_to_dict(self):
        io = ImageOptimizer()
        r = io.optimize(1080, 1080, "facebook")
        d = r.to_dict()
        assert "platform" in d


class TestImageMemory:
    def test_profile(self):
        im = ImageMemory()
        p = im.set_profile("brand", colors=["#FF0000"], style="modern")
        assert p.name == "brand"
        assert im.profile_count == 1

    def test_store_image(self):
        im = ImageMemory()
        rec = im.store_image("facebook", "AI", "https://img.com/a.png")
        assert rec["platform"] == "facebook"
        assert im.history_count == 1

    def test_get_history(self):
        im = ImageMemory()
        im.store_image("facebook", "A", "url1")
        im.store_image("twitter", "B", "url2")
        assert len(im.get_history("facebook")) == 1


class TestImageOrchestrator:
    def setup_method(self):
        self.orch = ImageOrchestrator()

    def test_run(self):
        r = self.orch.run("AI Jobs", "facebook")
        assert r.topic == "AI Jobs"
        assert r.image_plan is not None
        assert r.prompt is not None
        assert r.layout is not None
        assert r.image_response is not None

    def test_run_multi_platform(self):
        results = self.orch.run_multi_platform("AI", ["facebook", "instagram"])
        assert len(results) == 2

    def test_run_different_platforms(self):
        for p in ("facebook", "instagram", "twitter", "linkedin", "youtube"):
            r = self.orch.run("AI", p)
            assert r.platform == p

    def test_run_count(self):
        self.orch.run("A", "facebook")
        self.orch.run("B", "twitter")
        assert self.orch.run_count == 2

    def test_to_dict(self):
        r = self.orch.run("AI", "facebook")
        d = r.to_dict()
        assert "topic" in d
        assert "prompt" in d

    def test_memory_stored(self):
        self.orch.run("AI", "facebook")
        assert self.orch.memory.history_count >= 1
