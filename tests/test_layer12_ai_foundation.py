"""Tests for Layer 12 — Enterprise AI Foundation."""
from __future__ import annotations

# ─── Module 1: Universal LLM Manager ────────────────────────────────
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import LLMManager
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_config import LLMConfig
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_registry import LLMRegistry
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_factory import LLMFactory
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_builder import LLMBuilder
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_metrics import LLMMetrics
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cache import LLMCache
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cost_tracker import LLMCostTracker
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_health import LLMHealth
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_memory import LLMMemory
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_fallback import LLMFallback
from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_pool import LLMPool

# ─── Module 2: Model Provider Framework ──────────────────────────────
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_registry import ProviderRegistry
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_factory import ProviderFactory
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_loader import ProviderLoader
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.claude_provider import ClaudeProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.deepseek_provider import DeepSeekProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.grok_provider import GrokProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.mistral_provider import MistralProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.cohere_provider import CohereProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.ollama_provider import OllamaProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.llama_provider import LlamaProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.qwen_provider import QwenProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.openrouter_provider import OpenRouterProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_context import ProviderContext
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_metrics import ProviderMetrics
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_health import ProviderHealth
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_validator import ProviderValidator
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_events import ProviderEvents
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_cache import ProviderCache
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_cost import ProviderCost
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_limits import ProviderLimits
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_retry import ProviderRetry
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_timeout import ProviderTimeout
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_report import ProviderReport
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_config import ProviderConfig
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_stream import ProviderStream
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_batch import ProviderBatch
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_embed import ProviderEmbed
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_fine_tune import ProviderFineTune
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_security import ProviderSecurity
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_ab_test import ProviderABTest
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_fallback import ProviderFallback
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_logger import ProviderLogger
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_analytics import ProviderAnalytics


# ═══════════════════════════════════════════════════════════════════════
# MODULE 1: Universal LLM Manager
# ═══════════════════════════════════════════════════════════════════════

class TestLLMManager:
    def setup_method(self):
        self.manager = LLMManager()

    def test_start_stop(self):
        assert self.manager.start() is True
        assert self.manager.stop() is True

    def test_generate(self):
        self.manager.start()
        resp = self.manager.generate("Hello world")
        assert resp.content
        assert resp.model
        assert resp.provider

    def test_generate_with_model(self):
        resp = self.manager.generate("Test prompt", model="gpt-4o")
        assert resp.model == "gpt-4o"

    def test_generate_with_provider(self):
        resp = self.manager.generate("Test", provider="claude")
        assert resp.provider == "claude"

    def test_chat(self):
        msgs = [{"role": "user", "content": "Hi there"}]
        resp = self.manager.chat(msgs)
        assert resp.content

    def test_batch_generate(self):
        results = self.manager.batch_generate(["a", "b", "c"])
        assert len(results) == 3

    def test_get_usage_report(self):
        report = self.manager.get_usage_report()
        assert isinstance(report, dict)

    def test_get_cost_report(self):
        report = self.manager.get_cost_report()
        assert isinstance(report, dict)

    def test_get_health(self):
        health = self.manager.get_health()
        assert isinstance(health, dict)
        assert "healthy" in health

    def test_status(self):
        status = self.manager.status()
        assert isinstance(status, dict)
        assert "running" in status


class TestLLMConfig:
    def test_defaults(self):
        cfg = LLMConfig()
        assert cfg.default_provider == "openai"
        assert cfg.default_model == "gpt-4o-mini"
        assert cfg.budget_limit == 100.0

    def test_to_dict(self):
        d = LLMConfig().to_dict()
        assert "default_provider" in d

    def test_from_dict(self):
        cfg = LLMConfig.from_dict({"default_provider": "claude"})
        assert cfg.default_provider == "claude"


class TestLLMRegistry:
    def test_register(self):
        r = LLMRegistry()
        info = r.register("openai", "gpt-4o")
        assert info.provider == "openai"

    def test_get(self):
        r = LLMRegistry()
        r.register("openai", "gpt-4o")
        info = r.get("openai", "gpt-4o")
        assert info is not None

    def test_get_all(self):
        r = LLMRegistry()
        r.register("openai", "gpt-4o")
        r.register("claude", "claude-3")
        assert len(r.get_all()) >= 2

    def test_get_by_provider(self):
        r = LLMRegistry()
        r.register("openai", "gpt-4o")
        r.register("openai", "gpt-3.5")
        assert len(r.get_by_provider("openai")) == 2

    def test_stats(self):
        r = LLMRegistry()
        r.register("openai", "gpt-4o")
        s = r.get_stats()
        assert s["total"] == 1


class TestLLMFactory:
    def test_create_production(self):
        mgr = LLMFactory.create("production")
        assert mgr is not None

    def test_create_development(self):
        mgr = LLMFactory.create("development")
        assert mgr is not None

    def test_get_presets(self):
        presets = LLMFactory.get_presets()
        assert len(presets) > 0
        assert "production" in presets


class TestLLMCache:
    def test_set_get(self):
        c = LLMCache()
        c.set("test prompt", "gpt-4o", "cached response")
        val = c.get("test prompt", "gpt-4o")
        assert val == "cached response"

    def test_miss(self):
        c = LLMCache()
        val = c.get("noexist", "gpt-4o")
        assert val is None

    def test_stats(self):
        c = LLMCache()
        c.set("a", "m", "r")
        s = c.get_stats()
        assert s["entries"] == 1

    def test_clear(self):
        c = LLMCache()
        c.set("a", "m", "r")
        count = c.clear()
        assert count == 1


class TestLLMCostTracker:
    def test_record(self):
        ct = LLMCostTracker()
        ct.record("openai", "gpt-4o", 100, 50, 0.001)
        s = ct.get_stats()
        assert s["total_entries"] == 1

    def test_daily_budget(self):
        ct = LLMCostTracker(daily_budget=0.0001)
        ct.record("openai", "gpt-4o", 1000000, 1000000, 999.0)
        assert ct.is_over_daily_budget() is True

    def test_get_by_provider(self):
        ct = LLMCostTracker()
        ct.record("openai", "gpt-4o", 100, 50, 0.5)
        bp = ct.get_by_provider()
        assert "openai" in bp

    def test_get_by_model(self):
        ct = LLMCostTracker()
        ct.record("openai", "gpt-4o", 100, 50, 0.5)
        bm = ct.get_by_model()
        assert "gpt-4o" in bm


class TestLLMMetrics:
    def test_record(self):
        m = LLMMetrics()
        m.record_request("openai", "gpt-4o", 100, 0.01, 50.0, True)
        d = m.to_dict()
        assert d["requests"] == 1

    def test_avg_latency(self):
        m = LLMMetrics()
        m.record_request("openai", "gpt-4o", 100, 0.01, 50.0)
        assert m.get_avg_latency() > 0

    def test_error_rate(self):
        m = LLMMetrics()
        m.record_request("openai", "gpt-4o", 100, 0.01, 50.0, True)
        m.record_request("openai", "gpt-4o", 100, 0.01, 50.0, False)
        rate = m.get_error_rate()
        assert 0 < rate < 1

    def test_reset(self):
        m = LLMMetrics()
        m.record_request("openai", "gpt-4o", 100, 0.01, 50.0)
        m.reset()
        assert m.to_dict()["requests"] == 0


class TestLLMHealth:
    def test_stats(self):
        h = LLMHealth()
        s = h.get_stats()
        assert isinstance(s, dict)


class TestLLMMemory:
    def test_set_get(self):
        m = LLMMemory()
        m.set("key1", "cached_value")
        val = m.get("key1")
        assert val == "cached_value"

    def test_miss(self):
        m = LLMMemory()
        val = m.get("nonexistent")
        assert val is None

    def test_delete(self):
        m = LLMMemory()
        m.set("key1", "val")
        assert m.delete("key1") is True

    def test_stats(self):
        m = LLMMemory()
        m.set("k", "v")
        s = m.get_stats()
        assert s["entries"] == 1


class TestLLMBuilder:
    def test_build(self):
        mgr = LLMBuilder().provider("openai").model("gpt-4o").temperature(0.5).build()
        assert mgr is not None
        assert mgr.config.default_provider == "openai"

    def test_build_with_budget(self):
        mgr = LLMBuilder().budget(50.0).build()
        assert mgr.config.budget_limit == 50.0


class TestLLMFallback:
    def test_set_chain(self):
        fb = LLMFallback()
        fb.set_chain("primary", ["openai", "claude", "gemini"])
        assert fb.get_next("primary") == "openai"

    def test_report_failure(self):
        fb = LLMFallback()
        fb.set_chain("primary", ["openai", "claude"])
        next_p = fb.report_failure("primary")
        assert next_p == "claude"

    def test_report_success(self):
        fb = LLMFallback()
        fb.set_chain("primary", ["openai", "claude"])
        fb.report_failure("primary")
        fb.report_success("primary")
        assert fb.get_next("primary") == "openai"

    def test_stats(self):
        fb = LLMFallback()
        fb.set_chain("p", ["a", "b"])
        s = fb.get_stats()
        assert s["chains"] == 1


class TestLLMPool:
    def test_register(self):
        pool = LLMPool()
        pool.register("openai", "gpt-4o")
        s = pool.get_stats()
        assert s["total"] == 1

    def test_acquire_release(self):
        pool = LLMPool()
        entry = pool.register("openai", "gpt-4o")
        acquired = pool.acquire("openai")
        assert acquired is not None
        pool.release(acquired)
        s = pool.get_stats()
        assert s["available"] >= 1


# ═══════════════════════════════════════════════════════════════════════
# MODULE 2: Model Provider Framework
# ═══════════════════════════════════════════════════════════════════════

class TestProviderBase:
    def test_openai_provider(self):
        p = OpenAIProvider()
        assert p.name == "openai"
        assert len(p.supported_models) > 0

    def test_provider_initialize(self):
        p = OpenAIProvider()
        assert p.initialize() is True
        assert p.is_initialized

    def test_provider_generate(self):
        p = OpenAIProvider()
        p.initialize()
        req = ProviderRequest("Hello", "gpt-4o", "openai")
        resp = p.generate(req)
        assert resp.content
        assert resp.provider == "openai"

    def test_provider_chat(self):
        p = OpenAIProvider()
        p.initialize()
        resp = p.chat([{"role": "user", "content": "Hi"}])
        assert resp.content

    def test_provider_is_available(self):
        p = OpenAIProvider()
        p.initialize()
        assert p.is_available()

    def test_provider_stats(self):
        p = OpenAIProvider()
        p.initialize()
        s = p.get_stats()
        assert "name" in s

    def test_provider_reset_metrics(self):
        p = OpenAIProvider()
        p.reset_metrics()
        s = p.get_stats()
        assert s["metrics"]["requests"] == 0

    def test_validate_model(self):
        p = OpenAIProvider()
        assert p.validate_model("gpt-4o") is True

    def test_get_model_info(self):
        p = OpenAIProvider()
        info = p.get_model_info("gpt-4o")
        assert "provider" in info


class TestAllProviders:
    def _test_provider(self, cls, name, model):
        p = cls()
        assert p.name == name
        p.initialize()
        req = ProviderRequest("Test", model, name)
        resp = p.generate(req)
        assert resp.content
        assert resp.provider == name
        return resp

    def test_claude(self):
        self._test_provider(ClaudeProvider, "claude", "claude-sonnet-4-20250514")

    def test_gemini(self):
        self._test_provider(GeminiProvider, "gemini", "gemini-2.0-flash")

    def test_deepseek(self):
        self._test_provider(DeepSeekProvider, "deepseek", "deepseek-chat")

    def test_grok(self):
        self._test_provider(GrokProvider, "grok", "grok-2")

    def test_mistral(self):
        self._test_provider(MistralProvider, "mistral", "mistral-large-latest")

    def test_cohere(self):
        self._test_provider(CohereProvider, "cohere", "command-r-plus")

    def test_ollama(self):
        self._test_provider(OllamaProvider, "ollama", "llama3.1")

    def test_llama(self):
        self._test_provider(LlamaProvider, "llama", "llama-3.1-70b")

    def test_qwen(self):
        self._test_provider(QwenProvider, "qwen", "qwen-max")

    def test_openrouter(self):
        self._test_provider(OpenRouterProvider, "openrouter", "openai/gpt-4o")

    def test_provider_chat_all(self):
        for cls, name in [(OpenAIProvider, "openai"), (ClaudeProvider, "claude"),
                           (GeminiProvider, "gemini"), (DeepSeekProvider, "deepseek"),
                           (GrokProvider, "grok"), (MistralProvider, "mistral"),
                           (CohereProvider, "cohere"), (OllamaProvider, "ollama"),
                           (LlamaProvider, "llama"), (QwenProvider, "qwen"),
                           (OpenRouterProvider, "openrouter")]:
            p = cls()
            p.initialize()
            resp = p.chat([{"role": "user", "content": "Hi"}])
            assert resp.provider == name


class TestProviderRegistry:
    def test_register_get(self):
        r = ProviderRegistry()
        p = OpenAIProvider()
        r.register(p)
        assert r.get("openai") is not None
        assert r.has_provider("openai")

    def test_unregister(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        assert r.unregister("openai") is True
        assert r.unregister("openai") is False

    def test_get_all(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        r.register(ClaudeProvider())
        assert r.count() == 2

    def test_get_available(self):
        r = ProviderRegistry()
        p = OpenAIProvider()
        p.initialize()
        r.register(p)
        assert len(r.get_available()) >= 1

    def test_alias(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        r.add_alias("gpt", "openai")
        assert r.get("gpt") is not None

    def test_list_names(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        assert "openai" in r.list_names()

    def test_to_dict(self):
        r = ProviderRegistry()
        d = r.to_dict()
        assert "providers" in d

    def test_clear(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        r.clear()
        assert r.count() == 0

    def test_get_by_capability(self):
        r = ProviderRegistry()
        r.register(OpenAIProvider())
        result = r.get_by_capability("chat")
        assert isinstance(result, list)


class TestProviderFactory:
    def test_create_after_register(self):
        ProviderFactory.register("openai", OpenAIProvider)
        p = ProviderFactory.create("openai")
        assert p is not None
        assert p.name == "openai"
        ProviderFactory.clear()

    def test_create_unknown(self):
        p = ProviderFactory.create("nonexistent_xyz")
        assert p is None

    def test_register_and_supported(self):
        ProviderFactory.register("test_prov", OpenAIProvider)
        supported = ProviderFactory.get_supported()
        assert "test_prov" in supported
        ProviderFactory.clear()

    def test_has_provider(self):
        ProviderFactory.register("openai", OpenAIProvider)
        assert ProviderFactory.has_provider("openai") is True
        ProviderFactory.clear()


class TestProviderLoader:
    def test_load(self):
        ProviderFactory.register("openai", OpenAIProvider)
        r = ProviderRegistry()
        l = ProviderLoader(r)
        result = l.load("openai", {})
        assert result is True
        assert r.has_provider("openai")
        ProviderFactory.clear()

    def test_load_all(self):
        ProviderFactory.register("openai", OpenAIProvider)
        ProviderFactory.register("claude", ClaudeProvider)
        r = ProviderRegistry()
        l = ProviderLoader(r)
        count = l.load_all({"openai": {}, "claude": {}})
        assert count >= 2
        ProviderFactory.clear()

    def test_get_loaded(self):
        ProviderFactory.register("openai", OpenAIProvider)
        r = ProviderRegistry()
        l = ProviderLoader(r)
        l.load("openai")
        assert "openai" in l.get_loaded()
        ProviderFactory.clear()

    def test_unload(self):
        ProviderFactory.register("openai", OpenAIProvider)
        r = ProviderRegistry()
        l = ProviderLoader(r)
        l.load("openai")
        assert l.unload("openai") is True
        ProviderFactory.clear()


class TestProviderContext:
    def test_create(self):
        ctx = ProviderContext("openai", "gpt-4o")
        assert ctx.provider == "openai"

    def test_trace(self):
        ctx = ProviderContext("openai", "gpt-4o")
        ctx.add_trace("request", {"prompt": "hi"})
        assert len(ctx.trace) == 1

    def test_to_dict(self):
        d = ProviderContext("openai", "gpt-4o").to_dict()
        assert "provider" in d


class TestProviderMetrics:
    def test_record(self):
        m = ProviderMetrics()
        m.record("openai", 50.0, 100, 0.01, True)
        assert m.get("openai")["requests"] == 1

    def test_error_rate(self):
        m = ProviderMetrics()
        m.record("openai", 50, 100, 0.01, True)
        m.record("openai", 50, 100, 0.01, False)
        rate = m.get_error_rate("openai")
        assert 0 < rate < 1

    def test_total_cost(self):
        m = ProviderMetrics()
        m.record("openai", 50, 100, 0.5, True)
        assert m.get_total_cost() >= 0.5

    def test_reset(self):
        m = ProviderMetrics()
        m.record("openai", 50, 100, 0.01, True)
        m.reset("openai")
        assert m.get("openai") == {}

    def test_to_dict(self):
        m = ProviderMetrics()
        m.record("openai", 50, 100, 0.01, True)
        d = m.to_dict()
        assert "openai" in d


class TestProviderHealth:
    def test_check(self):
        h = ProviderHealth()
        result = h.check("openai", True, 10.0)
        assert result["status"] == "healthy"

    def test_is_healthy(self):
        h = ProviderHealth()
        h.check("openai", True)
        assert h.is_healthy("openai") is True

    def test_failure_rate(self):
        h = ProviderHealth()
        h.check("openai", True)
        h.check("openai", False)
        rate = h.get_failure_rate("openai")
        assert 0 < rate < 1

    def test_to_dict(self):
        h = ProviderHealth()
        h.check("openai", True)
        d = h.to_dict()
        assert "openai" in d


class TestProviderValidator:
    def test_valid_request(self):
        v = ProviderValidator()
        req = ProviderRequest("Hello", "gpt-4o", "openai")
        assert v.is_valid_request(req) is True

    def test_invalid_temperature(self):
        v = ProviderValidator()
        req = ProviderRequest("Hello", "gpt-4o", "openai")
        req.temperature = 5.0
        errors = v.validate_request(req)
        assert len(errors) > 0

    def test_empty_request(self):
        v = ProviderValidator()
        req = ProviderRequest()
        errors = v.validate_request(req)
        assert len(errors) > 0

    def test_validate_model(self):
        v = ProviderValidator()
        assert v.validate_model("gpt-4o", ["gpt-4o", "gpt-3.5"]) is True
        assert v.validate_model("unknown", ["gpt-4o"]) is False

    def test_validate_config(self):
        v = ProviderValidator()
        errors = v.validate_config({"api_key": "sk-test"})
        assert len(errors) == 0

    def test_validate_config_missing(self):
        v = ProviderValidator()
        errors = v.validate_config({})
        assert len(errors) > 0


class TestProviderEvents:
    def test_publish_subscribe(self):
        ev = ProviderEvents()
        received = []
        ev.subscribe("test", lambda e: received.append(e))
        ev.publish("test", "openai", {"msg": "hi"})
        assert len(received) == 1

    def test_wildcard(self):
        ev = ProviderEvents()
        received = []
        ev.subscribe("*", lambda e: received.append(e))
        ev.publish("any_event", "openai")
        assert len(received) == 1

    def test_history(self):
        ev = ProviderEvents()
        ev.publish("test", "openai")
        ev.publish("test", "claude")
        assert len(ev.get_history(provider="openai")) == 1

    def test_clear(self):
        ev = ProviderEvents()
        ev.publish("test", "openai")
        ev.clear()
        assert len(ev.get_history()) == 0


class TestProviderCache:
    def test_set_get(self):
        c = ProviderCache()
        c.set("openai", "gpt-4o", "hello", "response")
        val = c.get("openai", "gpt-4o", "hello")
        assert val == "response"

    def test_miss(self):
        c = ProviderCache()
        val = c.get("openai", "gpt-4o", "notfound")
        assert val is None

    def test_invalidate(self):
        c = ProviderCache()
        c.set("openai", "gpt-4o", "hello", "response")
        removed = c.invalidate("openai")
        assert removed >= 1

    def test_stats(self):
        c = ProviderCache()
        s = c.get_stats()
        assert "hit_rate" in s

    def test_max_entries(self):
        c = ProviderCache(max_entries=2)
        c.set("p1", "m1", "a", "1")
        c.set("p2", "m2", "b", "2")
        c.set("p3", "m3", "c", "3")
        assert c.get_stats()["entries"] <= 2

    def test_clear(self):
        c = ProviderCache()
        c.set("p", "m", "a", "b")
        c.clear()
        assert c.get_stats()["entries"] == 0


class TestProviderCost:
    def test_record(self):
        cost = ProviderCost()
        c = cost.record("openai", "gpt-4o", 100, 50)
        assert c >= 0

    def test_total_cost(self):
        cost = ProviderCost()
        cost.record("openai", "gpt-4o", 100, 50)
        assert cost.get_total_cost() >= 0

    def test_budget(self):
        cost = ProviderCost()
        cost.set_budget(0.0001)
        cost.record("openai", "gpt-4o", 100000, 100000)
        assert cost.is_over_budget() is True

    def test_breakdown(self):
        cost = ProviderCost()
        cost.record("openai", "gpt-4o", 100, 50)
        bd = cost.get_breakdown()
        assert "openai" in bd

    def test_remaining_budget(self):
        cost = ProviderCost()
        cost.set_budget(10.0)
        cost.record("openai", "gpt-4o", 100, 50)
        assert cost.get_remaining_budget() > 0

    def test_to_dict(self):
        cost = ProviderCost()
        d = cost.to_dict()
        assert "total" in d


class TestProviderLimits:
    def test_check(self):
        lim = ProviderLimits()
        assert lim.check("openai") is True

    def test_record(self):
        lim = ProviderLimits()
        lim.record("openai", 100)
        usage = lim.get_usage("openai")
        assert usage["tokens"] == 100

    def test_set_limits(self):
        lim = ProviderLimits()
        lim.set_limits("custom", rpm=10)
        assert lim.check("custom") is True

    def test_reset(self):
        lim = ProviderLimits()
        lim.record("openai", 100)
        lim.reset("openai")
        assert lim.get_usage("openai")["tokens"] == 0

    def test_to_dict(self):
        lim = ProviderLimits()
        lim.record("openai", 50)
        d = lim.to_dict()
        assert "openai" in d


class TestProviderRetry:
    def test_delay(self):
        r = ProviderRetry()
        d = r.get_delay(0)
        assert d > 0

    def test_should_retry(self):
        r = ProviderRetry(max_retries=3)
        assert r.should_retry("openai", 1, "timeout") is True
        assert r.should_retry("openai", 5, "timeout") is False

    def test_execute_with_retry(self):
        r = ProviderRetry(max_retries=2)
        result = r.execute_with_retry(lambda: "ok", "openai")
        assert result == "ok"

    def test_to_dict(self):
        r = ProviderRetry()
        d = r.to_dict()
        assert "max_retries" in d


class TestProviderTimeout:
    def test_default(self):
        t = ProviderTimeout()
        assert t.get_timeout("any") == 60.0

    def test_override(self):
        t = ProviderTimeout()
        t.set_timeout("openai", 30.0)
        assert t.get_timeout("openai") == 30.0

    def test_to_dict(self):
        t = ProviderTimeout()
        d = t.to_dict()
        assert "default" in d


class TestProviderReport:
    def test_generate(self):
        rp = ProviderReport()
        report = rp.generate({"openai": {"requests": 10}}, {"openai": {"status": "healthy"}},
                              {"total": 0.5})
        assert "summary" in report

    def test_history(self):
        rp = ProviderReport()
        rp.generate({"a": {"requests": 1}}, {"a": {"status": "ok"}}, {"total": 0.1})
        h = rp.get_history()
        assert len(h) == 1


class TestProviderConfig:
    def test_create(self):
        c = ProviderConfig("openai", "sk-test")
        assert c.name == "openai"

    def test_to_dict(self):
        c = ProviderConfig("openai")
        d = c.to_dict()
        assert "name" in d

    def test_from_dict(self):
        c = ProviderConfig.from_dict({"name": "claude", "api_key": "sk-ant"})
        assert c.name == "claude"


class TestProviderStream:
    def test_create_stream(self):
        s = ProviderStream()
        chunks = list(s.create_stream(["Hello", " World"]))
        # 2 input chunks + 1 final = 3
        assert len(chunks) == 3

    def test_callback(self):
        s = ProviderStream()
        received = []
        s.on_chunk(lambda c: received.append(c.delta))
        list(s.create_stream(["a", "b"]))
        assert len(received) == 3

    def test_get_full_content(self):
        s = ProviderStream()
        full = s.get_full_content(["Hello", " World"])
        assert full == "Hello World"

    def test_final_chunk(self):
        s = ProviderStream()
        chunks = list(s.create_stream(["a"]))
        assert chunks[-1].finish_reason == "stop"


class TestProviderBatch:
    def test_create_job(self):
        b = ProviderBatch()
        job = b.create_job("job1", [ProviderRequest("a"), ProviderRequest("b")])
        assert job.job_id == "job1"
        assert len(job.requests) == 2

    def test_process(self):
        b = ProviderBatch()
        job = b.create_job("job1", [ProviderRequest("a")])
        result = b.process("job1", lambda req: "done")
        assert result.status == "completed"

    def test_get_job(self):
        b = ProviderBatch()
        b.create_job("job1", [ProviderRequest("a")])
        job = b.get_job("job1")
        assert job.job_id == "job1"


class TestProviderEmbed:
    def test_generate(self):
        e = ProviderEmbed()
        r = e.generate("Hello world")
        assert r.dimensions > 0
        assert r.provider == "openai"

    def test_similarity(self):
        e = ProviderEmbed()
        a = e.generate("Hello")
        b = e.generate("Hello")
        sim = e.similarity(a, b)
        assert sim > 0.99

    def test_batch(self):
        e = ProviderEmbed()
        results = e.batch_generate(["a", "b", "c"])
        assert len(results) == 3

    def test_cache(self):
        e = ProviderEmbed()
        e.generate("test")
        stats = e.get_cache_stats()
        assert stats["cached_embeddings"] >= 1


class TestProviderFineTune:
    def test_create_job(self):
        ft = ProviderFineTune()
        job = ft.create_job("gpt-4o", "openai")
        assert job.status == "created"

    def test_list_jobs(self):
        ft = ProviderFineTune()
        ft.create_job("gpt-4o", "openai")
        assert len(ft.list_jobs()) == 1

    def test_cancel(self):
        ft = ProviderFineTune()
        job = ft.create_job("gpt-4o", "openai")
        assert ft.cancel_job(job.job_id) is True

    def test_stats(self):
        ft = ProviderFineTune()
        ft.create_job("gpt-4o", "openai")
        s = ft.get_stats()
        assert s["total_jobs"] == 1


class TestProviderSecurity:
    def test_store_get(self):
        s = ProviderSecurity()
        s.store_key("openai", "sk-test123456")
        assert s.get_key("openai") == "sk-test123456"

    def test_has_key(self):
        s = ProviderSecurity()
        assert s.has_key("openai") is False
        s.store_key("openai", "sk-test")
        assert s.has_key("openai") is True

    def test_masked(self):
        s = ProviderSecurity()
        s.store_key("openai", "sk-1234567890")
        masked = s.get_masked_key("openai")
        assert "*" in masked

    def test_validate_format(self):
        s = ProviderSecurity()
        assert s.validate_key_format("openai", "sk-test123") is True

    def test_remove_key(self):
        s = ProviderSecurity()
        s.store_key("openai", "sk-test")
        assert s.remove_key("openai") is True
        assert s.has_key("openai") is False


class TestProviderABTest:
    def test_create(self):
        t = ProviderABTest()
        test = t.create_test("t1", "openai", "claude")
        assert test.test_id == "t1"

    def test_select(self):
        t = ProviderABTest()
        t.create_test("t1", "openai", "claude")
        provider = t.select_provider("t1")
        assert provider in ("openai", "claude")

    def test_evaluate(self):
        t = ProviderABTest()
        t.create_test("t1", "openai", "claude")
        for _ in range(5):
            t.record_result("t1", "openai", 0.8)
            t.record_result("t1", "claude", 0.6)
        winner = t.evaluate("t1")
        assert winner == "openai"

    def test_get_all(self):
        t = ProviderABTest()
        t.create_test("t1", "a", "b")
        assert len(t.get_all_tests()) == 1


class TestProviderFallback:
    def test_add_chain(self):
        f = ProviderFallback()
        chain = f.add_chain("default", ["openai", "claude", "gemini"])
        assert len(chain.chain) == 3

    def test_get_next(self):
        f = ProviderFallback()
        f.add_chain("default", ["openai", "claude"])
        assert f.get_next_provider("default") == "openai"

    def test_advance(self):
        f = ProviderFallback()
        f.add_chain("default", ["openai", "claude"])
        f.advance("default")
        assert f.get_next_provider("default") == "claude"

    def test_record_failure(self):
        f = ProviderFallback()
        count = f.record_failure("openai")
        assert count == 1

    def test_reset(self):
        f = ProviderFallback()
        f.add_chain("d", ["a", "b"])
        f.advance("d")
        f.reset("d")
        assert f.get_next_provider("d") == "a"

    def test_to_dict(self):
        f = ProviderFallback()
        f.add_chain("d", ["a"])
        d = f.to_dict()
        assert "chains" in d


class TestProviderLogger:
    def test_log(self):
        log = ProviderLogger()
        log.info("openai", "request sent")
        entries = log.get_entries("openai")
        assert len(entries) == 1

    def test_levels(self):
        log = ProviderLogger()
        log.info("openai", "info")
        log.warning("openai", "warn")
        log.error("openai", "err")
        stats = log.get_stats()
        assert stats["total_entries"] == 3

    def test_clear(self):
        log = ProviderLogger()
        log.info("openai", "msg")
        log.clear()
        assert log.get_stats()["total_entries"] == 0

    def test_debug(self):
        log = ProviderLogger()
        log.debug("openai", "debug msg")
        entries = log.get_entries(level="debug")
        assert len(entries) == 1


class TestProviderAnalytics:
    def test_session(self):
        a = ProviderAnalytics()
        a.start_session("s1", "openai")
        a.record("s1", tokens=100, cost=0.01)
        s = a.get_session("s1")
        assert s["requests"] == 1

    def test_global(self):
        a = ProviderAnalytics()
        a.start_session("s1", "openai")
        a.record("s1", 100, 0.01)
        g = a.get_global_stats()
        assert g["total_requests"] >= 1

    def test_provider_stats(self):
        a = ProviderAnalytics()
        a.start_session("s1", "openai")
        a.record("s1", 100, 0.01)
        ps = a.get_provider_stats("openai")
        assert ps["requests"] >= 1

    def test_end_session(self):
        a = ProviderAnalytics()
        a.start_session("s1", "openai")
        ended = a.end_session("s1")
        assert ended["provider"] == "openai"

    def test_to_dict(self):
        a = ProviderAnalytics()
        d = a.to_dict()
        assert "global" in d
