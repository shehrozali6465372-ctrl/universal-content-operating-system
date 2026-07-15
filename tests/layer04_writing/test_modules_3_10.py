"""Tests for Layer 4 Modules 3-10 (production-grade, platform-agnostic)."""
from layers.layer04_writing.modules.caption_engine.caption_engine import CaptionEngine
from layers.layer04_writing.modules.hashtag_engine.hashtag_engine import HashtagEngine
from layers.layer04_writing.modules.tone_adapter.tone_adapter import ToneAdapter
from layers.layer04_writing.modules.hook_engine.hook_engine import HookEngine, HookResult
from layers.layer04_writing.modules.cta_engine.cta_engine import CTAGenerator
from layers.layer04_writing.modules.content_optimizer.content_optimizer import ContentOptimizer
from layers.layer04_writing.modules.writing_memory.writing_memory import WritingMemory
from layers.layer04_writing.modules.writing_orchestrator.writing_orchestrator import WritingOrchestrator, OrchestratorResult


# ── CaptionEngine ──
class TestCaptionEngine:
    def setup_method(self):
        self.ce = CaptionEngine()

    def test_generate_facebook(self):
        r = self.ce.generate("Great content that goes on and on about very interesting topics", "facebook")
        assert r.platform == "facebook"
        assert r.word_count > 0

    def test_generate_twitter_truncation(self):
        long_text = "word " * 200
        r = self.ce.generate(long_text, "twitter")
        assert r.char_count <= 280

    def test_multi_platform(self):
        r = self.ce.generate_multi_platform("Test content", ["facebook", "twitter", "linkedin"])
        assert len(r) == 3

    def test_to_dict(self):
        r = self.ce.generate("Test", "facebook")
        d = r.to_dict()
        assert "caption" in d
        assert "platform" in d

    def test_generation_count(self):
        self.ce.generate("A", "facebook")
        self.ce.generate("B", "twitter")
        assert self.ce.generation_count == 2


# ── HashtagEngine ──
class TestHashtagEngine:
    def setup_method(self):
        self.he = HashtagEngine()

    def test_generate_basic(self):
        r = self.he.generate("Technology is transforming our world with AI and innovation")
        assert r.count > 0

    def test_max_limit_instagram(self):
        for _ in range(100):
            r = self.he.generate("test topic about technology", "instagram")
            if r.count > 0:
                break
        assert r.count <= 30

    def test_categories(self):
        r = self.he.generate("AI in finance", categories=["technology", "finance"])
        assert r.count > 0

    def test_generate_seo(self):
        r = self.he.generate_seo("Learn how to code in Python for data science", "Python tutorial")
        assert len(r.keywords) > 0

    def test_to_dict(self):
        r = self.he.generate("test", categories=["technology"])
        d = r.to_dict()
        assert "hashtags" in d

    def test_generation_count(self):
        self.he.generate("A")
        self.he.generate("B")
        assert self.he.generation_count == 2


# ── ToneAdapter ──
class TestToneAdapter:
    def setup_method(self):
        self.ta = ToneAdapter()

    def test_adapt_to_linkedin(self):
        r = self.ta.adapt("Hey guys, check out this amazing stuff! It's gonna blow your mind!", target_platform="linkedin")
        assert r.target_tone == "professional"
        assert len(r.changes) > 0

    def test_adapt_multi_platform(self):
        r = self.ta.adapt_to_multi_platform("Test content")
        assert len(r) >= 4

    def test_get_platform_default(self):
        tone = self.ta.get_platform_default("instagram")
        assert tone == "enthusiastic"

    def test_get_tone_profile(self):
        p = self.ta.get_tone_profile("playful")
        assert "humor" in p

    def test_to_dict(self):
        r = self.ta.adapt("test", target_platform="twitter")
        d = r.to_dict()
        assert "adapted_text" in d

    def test_adaptation_count(self):
        self.ta.adapt("test", target_platform="twitter")
        self.ta.adapt("test", target_platform="linkedin")
        assert self.ta.adaptation_count == 2


# ── HookEngine ──
class TestHookEngine:
    def setup_method(self):
        self.he = HookEngine()

    def test_generate(self):
        r = self.he.generate("AI Jobs", goal="educate")
        assert isinstance(r, HookResult)
        assert r.hook_type != ""
        assert r.hook != ""

    def test_generate_batch(self):
        r = self.he.generate_batch("AI", count=3)
        assert len(r) == 3

    def test_hook_contains_topic(self):
        r = self.he.generate("Crypto Mining", hook_type="question")
        assert "Crypto" in r.hook or "mining" in r.hook.lower()

    def test_alternatives(self):
        r = self.he.generate("AI", goal="educate")
        assert len(r.alternatives) > 0

    def test_to_dict(self):
        r = self.he.generate("AI")
        d = r.to_dict()
        assert "hook" in d

    def test_generation_count(self):
        self.he.generate("A")
        self.he.generate("B")
        assert self.he.generation_count == 2


# ── CTAGenerator ──
class TestCTAGenerator:
    def setup_method(self):
        self.cg = CTAGenerator()

    def test_generate_facebook(self):
        r = self.cg.generate("facebook", "engage")
        assert r.platform == "facebook"
        assert r.cta_text != ""
        assert len(r.alternatives) > 0

    def test_custom_cta(self):
        r = self.cg.generate(custom_cta="Follow for more!")
        assert r.cta_text == "Follow for more!"

    def test_generate_batch(self):
        r = self.cg.generate_batch("facebook", count=2)
        assert len(r) == 2

    def test_append_to_content(self):
        r = self.cg.generate("facebook", "engage")
        result = self.cg.append_to_content("Great content", r)
        assert "Great content" in result
        assert r.cta_text in result

    def test_to_dict(self):
        r = self.cg.generate("facebook")
        d = r.to_dict()
        assert "cta_text" in d

    def test_generation_count(self):
        self.cg.generate("facebook")
        self.cg.generate("twitter")
        assert self.cg.generation_count == 2


# ── ContentOptimizer ──
class TestContentOptimizer:
    def setup_method(self):
        self.co = ContentOptimizer()

    def test_optimize_facebook(self):
        r = self.co.optimize("This is test content with lots of words that makes sense.", "facebook")
        assert r.platform == "facebook"
        assert r.readability_score > 0

    def test_optimize_twitter_truncation(self):
        long = "word " * 1000
        r = self.co.optimize(long, "twitter")
        assert len(r.optimized_text) <= 280

    def test_seo_optimization(self):
        r = self.co.optimize_seo("AI is transforming technology jobs for developers.", focus_keyword="technology")
        assert r.seo_score > 0

    def test_readability(self):
        text = "It is. Very simple. Short sentences."
        r = self.co.optimize(text, "facebook")
        assert r.readability_score >= 0.5

    def test_to_dict(self):
        r = self.co.optimize("test", "facebook")
        d = r.to_dict()
        assert "score" in d

    def test_optimization_count(self):
        self.co.optimize("A", "facebook")
        self.co.optimize("B", "instagram")
        assert self.co.optimization_count == 2


# ── WritingMemory ──
class TestWritingMemory:
    def setup_method(self):
        self.wm = WritingMemory(max_size=10)

    def test_set_and_get_voice(self):
        voice = self.wm.set_voice("my_brand", tone="professional",
                                   personality=["expert", "helpful"],
                                   dos=["Be clear"], donts=["Use slang"])
        assert voice.name == "my_brand"
        assert "Be clear" in voice.dos

    def test_get_voice_nonexistent(self):
        assert self.wm.get_voice("nonexistent") is None

    def test_store_draft(self):
        rec = self.wm.store_draft("facebook", "AI", "Great content", "friendly")
        assert rec.platform == "facebook"
        assert self.wm.count == 1

    def test_get_by_platform(self):
        self.wm.store_draft("facebook", "A", "text1")
        self.wm.store_draft("twitter", "B", "text2")
        self.wm.store_draft("facebook", "C", "text3")
        assert len(self.wm.get_by_platform("facebook")) == 2

    def test_consistency_check(self):
        self.wm.set_voice("brand", donts=["salesy", "clickbait"])
        result = self.wm.check_consistency("Great content about AI", "brand")
        assert result["consistent"] is True
        result = self.wm.check_consistency("This salesy post will blow your mind", "brand")
        assert result["consistent"] is False

    def test_max_size(self):
        for i in range(15):
            self.wm.store_draft("p", "topic", f"text{i}")
        assert self.wm.count <= 10

    def test_voice_count(self):
        self.wm.set_voice("a", "friendly")
        self.wm.set_voice("b", "professional")
        assert self.wm.voice_count == 2

    def test_get_recent(self):
        self.wm.store_draft("f", "t1", "t")
        self.wm.store_draft("f", "t2", "t")
        self.wm.store_draft("f", "t3", "t")
        assert len(self.wm.get_recent(2)) == 2

    def test_to_dict(self):
        self.wm.set_voice("brand", tone="friendly")
        v = self.wm.get_voice("brand")
        d = v.to_dict()
        assert "tone" in d

    def test_draft_to_dict(self):
        rec = self.wm.store_draft("f", "t", "text")
        d = rec.to_dict()
        assert "platform" in d


# ── WritingOrchestrator (integration) ──
class TestWritingOrchestrator:
    def setup_method(self):
        self.wo = WritingOrchestrator()

    def test_run_basic(self):
        result = self.wo.run("AI Jobs", platforms=["facebook", "twitter"])
        assert isinstance(result, OrchestratorResult)
        assert result.topic == "AI Jobs"
        assert len(result.outputs) == 2

    def test_run_all_platforms(self):
        result = self.wo.run("AI Jobs")
        assert len(result.outputs) >= 4  # default four platforms

    def test_run_different_goals(self):
        for goal in ("educate", "entertain", "promote"):
            result = self.wo.run("Tech", goal=goal)
            assert result.plan.goal == goal

    def test_run_with_audience(self):
        result = self.wo.run("AI Jobs", audience="students")
        assert result.plan.audience == "students"

    def test_orchestrator_outputs_have_hashtags(self):
        r = self.wo.run("AI Technology", platforms=["facebook", "instagram"])
        for o in r.outputs:
            assert o.hashtags is not None

    def test_orchestrator_outputs_have_cta(self):
        r = self.wo.run("AI", platforms=["facebook"])
        assert r.outputs[0].cta != ""

    def test_orchestrator_stores_in_memory(self):
        r = self.wo.run("AI Jobs", platforms=["facebook"])
        history = self.wo.get_history(platform="facebook")
        assert len(history) >= 1

    def test_orchestrator_has_pipeline_time(self):
        r = self.wo.run("AI Jobs")
        assert r.pipeline_time_ms >= 0

    def test_to_dict(self):
        r = self.wo.run("AI")
        d = r.to_dict()
        assert "topic" in d
        assert "outputs" in d

    def test_orchestrator_count(self):
        self.wo.run("A", platforms=["facebook"])
        self.wo.run("B", platforms=["facebook"])
        assert self.wo.run_count == 2
