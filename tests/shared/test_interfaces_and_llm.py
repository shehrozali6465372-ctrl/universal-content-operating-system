"""Tests for interfaces and LLM abstraction."""

from layers.shared.interfaces import IResearchModule, IWritingModule, IPublisher, IAnalyticsProvider, ILearningModule
from layers.shared.llm_provider import BaseLLMProvider, LLMResponse, LLMFactory


# Concrete test implementations

class FakeResearchModule(IResearchModule):
    def get_module_name(self): return "fake_research"
    def execute(self, ctx): return {"result": "ok"}
    def get_confidence(self): return 0.9
    def get_evidence(self): return ["evidence1"]


class FakeWritingModule(IWritingModule):
    def generate(self, topic, ctx): return {"content": f"About {topic}"}
    def get_module_name(self): return "fake_writer"
    def get_supported_styles(self): return ["informative", "humorous"]


class FakePublisher(IPublisher):
    def publish(self, content): return {"post_id": "123", "status": "published"}
    def get_platform(self): return "facebook"
    def is_healthy(self): return True


class FakeAnalytics(IAnalyticsProvider):
    def collect(self, post_id): return {"likes": 10}
    def get_metrics(self, post_id): return {"reach": 100}
    def get_provider_name(self): return "fake_analytics"


class FakeLLM(BaseLLMProvider):
    def get_provider_name(self): return "fake_llm"
    def generate(self, prompt, system_prompt=None, temperature=0.7, max_tokens=1024, **kw):
        return LLMResponse(content=f"Response to: {prompt}", model="fake-v1", usage={"tokens": 50})
    def is_available(self): return True
    def get_models(self): return ["fake-v1"]


class TestInterfaces:
    def test_research_module(self):
        m = FakeResearchModule()
        assert m.get_module_name() == "fake_research"
        assert m.get_confidence() == 0.9

    def test_writing_module(self):
        m = FakeWritingModule()
        r = m.generate("AI Jobs", {})
        assert "AI Jobs" in r["content"]

    def test_publisher(self):
        p = FakePublisher()
        assert p.get_platform() == "facebook"
        assert p.is_healthy() is True

    def test_analytics(self):
        a = FakeAnalytics()
        assert a.get_provider_name() == "fake_analytics"

    def test_cannot_instantiate_abc(self):
        try:
            IResearchModule()
            assert False, "Should raise"
        except TypeError:
            pass


class TestLLMResponse:
    def test_create(self):
        r = LLMResponse(content="hello", model="gpt-4", usage={"tokens": 10})
        assert r.content == "hello"

    def test_to_dict(self):
        r = LLMResponse(content="hi", model="gpt-4")
        d = r.to_dict()
        assert d["content"] == "hi"


class TestLLMFactory:
    def setup_method(self):
        LLMFactory.reset()

    def test_register_and_create(self):
        LLMFactory.register("fake", FakeLLM)
        llm = LLMFactory.create("fake")
        assert llm.get_provider_name() == "fake_llm"

    def test_create_unknown(self):
        try:
            LLMFactory.create("nonexistent")
            assert False
        except ValueError:
            pass

    def test_generate(self):
        LLMFactory.register("fake", FakeLLM)
        llm = LLMFactory.create("fake")
        resp = llm.generate("Tell me about AI")
        assert "Tell me about AI" in resp.content
        assert resp.model == "fake-v1"

    def test_is_available(self):
        LLMFactory.register("fake", FakeLLM)
        llm = LLMFactory.create("fake")
        assert llm.is_available() is True

    def test_get_available_providers(self):
        LLMFactory.register("a", FakeLLM)
        LLMFactory.register("b", FakeLLM)
        assert set(LLMFactory.get_available_providers()) == {"a", "b"}

    def test_reset(self):
        LLMFactory.register("a", FakeLLM)
        LLMFactory.reset()
        assert LLMFactory.get_available_providers() == []
