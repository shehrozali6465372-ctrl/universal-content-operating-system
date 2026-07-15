"""Tests for Layer 4 Module 2 — Draft Generator (production-grade)."""
from layers.layer04_writing.modules.content_planner.writing_plan import WritingPlan
from layers.layer04_writing.modules.draft_generator.llm_provider import MockLLMProvider, LLMResponse
from layers.layer04_writing.modules.draft_generator.prompt_builder import PromptBuilder, PromptSet
from layers.layer04_writing.modules.draft_generator.draft_validator import DraftValidator
from layers.layer04_writing.modules.draft_generator.variant_generator import VariantGenerator, DraftVariant
from layers.layer04_writing.modules.draft_generator.draft_memory import DraftMemory
from layers.layer04_writing.modules.draft_generator.draft_manager import DraftManager, DraftManagerResult


def make_plan(topic="AI Jobs", goal="educate", platform="facebook"):
    p = WritingPlan(topic=topic)
    p.goal = goal
    p.platform = platform
    p.length = "medium"
    p.tone = "friendly"
    p.cta = "engage"
    p.strategy = "educational"
    return p


# ── MockLLMProvider ──

class TestMockLLMProvider:
    def test_generate(self):
        provider = MockLLMProvider(response="Test draft content here.")
        resp = provider.generate("Write about AI")
        assert isinstance(resp, LLMResponse)
        assert resp.text == "Test draft content here."
        assert resp.model == "mock-model"

    def test_is_configured(self):
        assert MockLLMProvider().is_configured() is True

    def test_stats(self):
        p = MockLLMProvider()
        p.generate("test")
        stats = p.stats
        assert stats["calls"] == 1
        assert stats["total_tokens"] > 0

    def test_set_responses(self):
        p = MockLLMProvider()
        p.set_responses(["First", "Second"])
        r1 = p.generate("test")
        r2 = p.generate("test")
        assert r1.text == "First"
        assert r2.text == "Second"

    def test_generate_batch(self):
        p = MockLLMProvider()
        responses = p.generate_batch(["p1", "p2"])
        assert len(responses) == 2


# ── PromptBuilder ──

class TestPromptBuilder:
    def setup_method(self):
        self.pb = PromptBuilder()

    def test_build_basic(self):
        plan = make_plan()
        ps = self.pb.build(plan)
        assert isinstance(ps, PromptSet)
        assert len(ps.system_prompt) > 0
        assert len(ps.user_prompt) > 0

    def test_build_system_includes_tone(self):
        plan = make_plan()
        plan.tone = "professional"
        ps = self.pb.build(plan)
        assert "professional" in ps.system_prompt.lower()

    def test_build_system_includes_goal(self):
        plan = make_plan(goal="entertain")
        ps = self.pb.build(plan)
        assert "entertain" in ps.system_prompt.lower()

    def test_build_user_includes_length(self):
        plan = make_plan()
        plan.length = "short"
        ps = self.pb.build(plan)
        assert "100 words" in ps.user_prompt

    def test_build_user_includes_cta(self):
        plan = make_plan()
        plan.cta = "comment"
        ps = self.pb.build(plan)
        assert "comment" in ps.user_prompt.lower()

    def test_build_variant(self):
        plan = make_plan()
        ps = self.pb.build_variant(plan, "bold")
        assert "bold" in ps.user_prompt.lower() or "provoke" in ps.user_prompt.lower()

    def test_build_with_context(self):
        plan = make_plan()
        context = {"evidence": ["Fact 1", "Fact 2"], "key_points": ["Point A"]}
        ps = self.pb.build(plan, context)
        assert "Fact 1" in ps.user_prompt

    def test_parameters(self):
        plan = make_plan()
        ps = self.pb.build(plan)
        assert "temperature" in ps.parameters
        assert "max_tokens" in ps.parameters

    def test_to_dict(self):
        plan = make_plan()
        ps = self.pb.build(plan)
        d = ps.to_dict()
        assert "plan_id" in d

    def test_prompt_count(self):
        plan = make_plan()
        self.pb.build(plan)
        assert self.pb.prompt_count == 1


# ── DraftValidator ──

class TestDraftValidator:
    def setup_method(self):
        self.dv = DraftValidator()

    def test_valid_draft(self):
        text = "AI jobs are increasing rapidly. Companies need skilled developers. The demand for AI talent has grown significantly in recent years. This trend will continue."
        r = self.dv.validate(text, length="medium")
        assert r.is_valid is True
        assert r.word_count > 20

    def test_too_short(self):
        text = "Short."
        r = self.dv.validate(text, length="medium")
        assert r.word_count == 1
        assert any("short" in i.lower() for i in r.issues)

    def test_empty(self):
        r = self.dv.validate("", length="medium")
        assert r.word_count == 0
        assert len(r.issues) >= 2

    def test_repeated_words(self):
        text = "amazing " * 10 + "AI is growing fast and companies are hiring more developers."
        r = self.dv.validate(text, length="medium")
        assert len(r.issues) > 0

    def test_url_detected(self):
        text = "Check https://example.com for more info. " * 5
        r = self.dv.validate(text, length="medium")
        assert any("URL" in i for i in r.issues)

    def test_to_dict(self):
        r = self.dv.validate("Test draft with enough words to pass minimum checks easily.")
        d = r.to_dict()
        assert "valid" in d
        assert "word_count" in d


# ── VariantGenerator ──

class TestVariantGenerator:
    def setup_method(self):
        self.vg = VariantGenerator()

    def test_generate_variants(self):
        plan = make_plan()
        variants = self.vg.generate_variants(plan)
        assert len(variants) == 3  # default: original, alternative, bold
        assert all(isinstance(v, DraftVariant) for v in variants)

    def test_generate_custom_variants(self):
        plan = make_plan()
        variants = self.vg.generate_variants(plan, variant_types=["original", "minimal"])
        assert len(variants) == 2

    def test_variants_have_prompts(self):
        plan = make_plan()
        variants = self.vg.generate_variants(plan)
        for v in variants:
            assert v.prompt_set is not None

    def test_to_dict(self):
        plan = make_plan()
        variants = self.vg.generate_variants(plan, variant_types=["original"])
        d = variants[0].to_dict()
        assert "variant_type" in d


# ── DraftMemory ──

class TestDraftMemory:
    def setup_method(self):
        self.dm = DraftMemory(max_size=5)

    def test_store_and_retrieve(self):
        rec = self.dm.store("p1", "AI", "Draft text here")
        assert rec.topic == "AI"
        assert self.dm.count == 1

    def test_get_by_topic(self):
        self.dm.store("p1", "AI", "text1")
        self.dm.store("p1", "Crypto", "text2")
        assert len(self.dm.get_by_topic("AI")) == 1

    def test_get_by_plan(self):
        self.dm.store("p1", "AI", "text1")
        self.dm.store("p2", "AI", "text2")
        assert len(self.dm.get_by_plan("p1")) == 1

    def test_max_size(self):
        for i in range(7):
            self.dm.store(f"p{i}", "topic", f"text{i}")
        assert self.dm.count <= 5

    def test_total_tokens(self):
        self.dm.store("p1", "AI", "text", tokens=100)
        self.dm.store("p2", "AI", "text", tokens=200)
        assert self.dm.total_tokens == 300


# ── DraftManager ──

class TestDraftManager:
    def setup_method(self):
        self.provider = MockLLMProvider(response="AI jobs are booming in 2026. Companies need developers with AI skills. The demand is growing rapidly.")
        self.dm = DraftManager(provider=self.provider)

    def test_generate_basic(self):
        plan = make_plan()
        result = self.dm.generate(plan)
        assert isinstance(result, DraftManagerResult)
        assert result.draft is not None
        assert result.draft.text == self.provider._mock_response

    def test_generate_with_validation(self):
        plan = make_plan()
        result = self.dm.generate(plan, validate=True)
        assert result.draft.validation is not None

    def test_generate_without_validation(self):
        plan = make_plan()
        result = self.dm.generate(plan, validate=False)
        assert result.draft.validation is None

    def test_generate_with_context(self):
        plan = make_plan()
        context = {"evidence": ["AI demand up 30%"], "key_points": ["Growth", "Salaries"]}
        result = self.dm.generate(plan, context=context)
        assert result.draft is not None

    def test_generate_variants(self):
        plan = make_plan()
        result = self.dm.generate_variants(plan, variant_types=["original", "bold"])
        assert len(result.variants) == 2

    def test_draft_has_prompt(self):
        plan = make_plan()
        result = self.dm.generate(plan)
        assert result.draft.prompt is not None

    def test_draft_has_metadata(self):
        plan = make_plan()
        result = self.dm.generate(plan)
        d = result.draft.to_dict()
        assert "tokens_used" in d
        assert "latency_ms" in d

    def test_draft_count(self):
        plan = make_plan()
        self.dm.generate(plan)
        self.dm.generate(plan)
        assert self.dm.draft_count == 2

    def test_memory_stored(self):
        plan = make_plan()
        self.dm.generate(plan)
        assert self.dm.memory.count >= 1

    def test_history(self):
        plan = make_plan()
        self.dm.generate(plan)
        history = self.dm.get_history(topic="AI Jobs")
        assert len(history) >= 1

    def test_to_dict(self):
        plan = make_plan()
        result = self.dm.generate(plan)
        d = result.to_dict()
        assert "plan_id" in d
        assert "total_tokens" in d

    def test_generate_all_platforms(self):
        for platform in ("facebook", "twitter", "linkedin"):
            plan = make_plan(platform=platform)
            result = self.dm.generate(plan)
            assert result.draft is not None

    def test_generate_all_goals(self):
        for goal in ("educate", "entertain", "inspire", "promote", "engage"):
            plan = make_plan(goal=goal)
            result = self.dm.generate(plan)
            assert result.draft is not None
