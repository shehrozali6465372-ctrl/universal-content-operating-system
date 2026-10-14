"""Tests for Layer 12 — Enterprise AI Foundation."""
from __future__ import annotations

import time

import pytest

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
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.claude_provider import ClaudeProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.deepseek_provider import DeepSeekProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.grok_provider import GrokProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.mistral_provider import MistralProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.cohere_provider import CohereProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.ollama_provider import OllamaProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.openrouter_provider import OpenRouterProvider


# ═══════════════════════════════════════════════════════════════════════
# MODULE 1: Universal LLM Manager
# ═══════════════════════════════════════════════════════════════════════

class TestLLMManager:
    def setup_method(self):
        self.manager = LLMManager(generator=lambda **kwargs: "mock provider response")

    def test_start_stop(self):
        assert self.manager.start() is True
        assert self.manager.stop() is True

    def test_generate(self):
        self.manager.start()
        resp = self.manager.generate("Hello world")
        assert resp.model
        assert resp.provider

    def test_generate_with_model(self):
        resp = self.manager.generate("Test prompt", model="gpt-5.6-luna")
        assert resp.model == "gpt-5.6-luna"

    def test_generate_with_provider(self):
        resp = self.manager.generate("Test", provider="claude")
        assert resp.provider == "claude"

    def test_chat(self):
        msgs = [{"role": "user", "content": "Hi there"}]
        resp = self.manager.chat(msgs)
        assert resp.model
        assert resp.provider

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
        assert cfg.default_provider == "deepseek"
        assert cfg.default_model == "deepseek-flash"
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
        assert p.initialize() is False
        assert p.is_initialized is False

    def test_provider_generate(self):
        p = OpenAIProvider()
        with pytest.raises(RuntimeError, match="API key is not configured"):
            p.generate(ProviderRequest("Hello", "gpt-4o", "openai"))

    def test_provider_chat(self):
        p = OpenAIProvider()
        with pytest.raises(RuntimeError, match="API key is not configured"):
            p.chat([{"role": "user", "content": "Hi"}])

    def test_provider_is_available(self):
        p = OpenAIProvider()
        p.initialize()
        assert p.is_available() is False

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
        assert p.initialize() is False
        with pytest.raises(RuntimeError):
            p.generate(ProviderRequest("Test", model, name))

    def test_claude(self):
        self._test_provider(ClaudeProvider, "claude", "claude-sonnet-4-6")

    def test_gemini(self):
        self._test_provider(GeminiProvider, "gemini", "gemini-3.8-flash")

    def test_deepseek(self):
        self._test_provider(DeepSeekProvider, "deepseek", "deepseek-flash")

    def test_grok(self):
        self._test_provider(GrokProvider, "grok", "grok-2")

    def test_mistral(self):
        self._test_provider(MistralProvider, "mistral", "mistral-large-latest")

    def test_cohere(self):
        self._test_provider(CohereProvider, "cohere", "command-r-plus")

    def test_ollama(self):
        self._test_provider(OllamaProvider, "ollama", "llama3.1")

    def test_openrouter(self):
        self._test_provider(OpenRouterProvider, "openrouter", "openai/gpt-4o")

    def test_provider_chat_all(self):
        for cls, name in [(OpenAIProvider, "openai"), (ClaudeProvider, "claude"),
                           (GeminiProvider, "gemini"), (DeepSeekProvider, "deepseek"),
                           (GrokProvider, "grok"), (MistralProvider, "mistral"),
                           (CohereProvider, "cohere"), (OllamaProvider, "ollama"),
                           (OpenRouterProvider, "openrouter")]:
            p = cls()
            assert p.initialize() is False
            with pytest.raises(RuntimeError):
                p.chat([{"role": "user", "content": "Hi"}])


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
        assert r.get_available() == []

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


# MODULE 3: Multi Model Intelligence
# ═══════════════════════════════════════════════════════════════════════

from layers.layer12_ai_foundation.modules.multi_model_intelligence.models import (
    ModelResponse, VoteResult, RankEntry, ConsensusResult,
)
from layers.layer12_ai_foundation.modules.multi_model_intelligence.consensus_engine import ConsensusEngine
from layers.layer12_ai_foundation.modules.multi_model_intelligence.voting_engine import VotingEngine
from layers.layer12_ai_foundation.modules.multi_model_intelligence.ranking_engine import RankingEngine
from layers.layer12_ai_foundation.modules.multi_model_intelligence.reasoning_merger import ReasoningMerger
from layers.layer12_ai_foundation.modules.multi_model_intelligence.confidence_engine import ConfidenceEngine
from layers.layer12_ai_foundation.modules.multi_model_intelligence.response_selector import ResponseSelector
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_reasoning import ParallelReasoning
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_generation import ParallelGeneration
from layers.layer12_ai_foundation.modules.multi_model_intelligence.parallel_review import ParallelReview
from layers.layer12_ai_foundation.modules.multi_model_intelligence.ensemble_ai import EnsembleAI
from layers.layer12_ai_foundation.modules.multi_model_intelligence.multi_model_router import MultiModelRouter
from layers.layer12_ai_foundation.modules.multi_model_intelligence.multi_model_strategy import MultiModelStrategy
from layers.layer12_ai_foundation.modules.multi_model_intelligence.multi_model_executor import MultiModelExecutor
from layers.layer12_ai_foundation.modules.multi_model_intelligence.multi_model_fallback import MultiModelFallback


# ─── Models ──────────────────────────────────────────────────────────

class TestModels:
    def test_model_response_success(self):
        r = ModelResponse(model="gpt-4o", provider="openai", content="Hello", confidence=0.9)
        assert r.is_success
        assert r.model == "gpt-4o"

    def test_model_response_error(self):
        r = ModelResponse(model="gpt-4o", provider="openai", content="", error="timeout")
        assert not r.is_success

    def test_model_response_to_dict(self):
        r = ModelResponse(model="gpt-4o", provider="openai", content="Hi")
        d = r.to_dict()
        assert d["model"] == "gpt-4o"
        assert "response_id" in d

    def test_vote_result(self):
        v = VoteResult(candidate="A", votes=3, voters=["m1", "m2", "m3"])
        d = v.to_dict()
        assert d["votes"] == 3

    def test_rank_entry(self):
        r = RankEntry(rank=1, score=0.9)
        d = r.to_dict()
        assert d["rank"] == 1

    def test_consensus_result(self):
        c = ConsensusResult(agreed_content="X", agreement_score=0.8, participating_models=3)
        d = c.to_dict()
        assert d["agreement_score"] == 0.8


# ─── ConsensusEngine ─────────────────────────────────────────────────

class TestConsensusEngine:
    def setup_method(self):
        self.engine = ConsensusEngine("majority")

    def test_empty(self):
        r = self.engine.find_consensus([])
        assert r.participating_models == 0

    def test_single_response(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="Answer", confidence=0.9)]
        r = self.engine.find_consensus(resp)
        assert r.agreed_content == "Answer"
        assert r.participating_models == 1

    def test_majority_consensus(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="Same answer", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="Same answer", confidence=0.85),
            ModelResponse(model="gemini", provider="google", content="Different", confidence=0.7),
        ]
        r = self.engine.find_consensus(resp)
        assert r.method == "majority"
        assert r.participating_models == 3
        assert r.agreement_score > 0

    def test_weighted_consensus(self):
        engine = ConsensusEngine("weighted")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.8),
        ]
        weights = {"gpt-4o": 2.0, "claude": 1.0}
        r = engine.find_consensus(resp, weights)
        assert r.method == "weighted"
        assert "scores" in r.details

    def test_best_match_consensus(self):
        engine = ConsensusEngine("best_match")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="the cat sat on the mat", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="the cat sat on the mat", confidence=0.85),
            ModelResponse(model="gemini", provider="google", content="completely different text here", confidence=0.7),
        ]
        r = engine.find_consensus(resp)
        assert r.method == "best_match"
        assert r.agreement_score > 0

    def test_all_failed(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="", error="fail"),
            ModelResponse(model="claude", provider="anthropic", content="", error="fail"),
        ]
        r = self.engine.find_consensus(resp)
        assert r.participating_models == 0

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="X", confidence=0.9)]
        self.engine.find_consensus(resp)
        assert len(self.engine.get_history()) == 1

    def test_normalize(self):
        assert ConsensusEngine._normalize("Hello, World!") == "hello world"

    def test_similarity(self):
        sim = ConsensusEngine._similarity("the cat sat", "the cat sat on the mat")
        assert 0.0 < sim <= 1.0

    def test_invalid_method_fallback(self):
        engine = ConsensusEngine("invalid_method")
        assert engine.method == "majority"


# ─── VotingEngine ────────────────────────────────────────────────────

class TestVotingEngine:
    def setup_method(self):
        self.engine = VotingEngine("plurality")

    def test_empty_vote(self):
        assert self.engine.vote([]) is None

    def test_single_vote(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        v = self.engine.vote(resp)
        assert v is not None
        assert v.candidate == "A"

    def test_plurality_vote(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.8),
        ]
        v = self.engine.vote(resp)
        assert v.votes == 2

    def test_ranked_choice(self):
        engine = VotingEngine("ranked_choice")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        v = engine.vote(resp)
        assert v is not None

    def test_borda_count(self):
        engine = VotingEngine("borda_count")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
            ModelResponse(model="gemini", provider="google", content="C", confidence=0.5),
        ]
        v = engine.vote(resp)
        assert v is not None

    def test_weighted_vote(self):
        engine = VotingEngine("weighted", weights={"gpt-4o": 2.0})
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.95),
        ]
        v = engine.vote(resp)
        assert v.candidate == "A"  # gpt-4o has 2x weight

    def test_history(self):
        engine = VotingEngine("weighted")
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        engine.vote(resp)
        assert len(engine.get_history()) == 1


# ─── RankingEngine ──────────────────────────────────────────────────

class TestRankingEngine:
    def setup_method(self):
        self.engine = RankingEngine()

    def test_empty_rank(self):
        assert self.engine.rank([]) == []

    def test_single_rank(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        ranks = self.engine.rank(resp)
        assert len(ranks) == 1
        assert ranks[0].rank == 1

    def test_multi_rank(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="Short", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B " * 100, confidence=0.7),
            ModelResponse(model="gemini", provider="google", content="Medium text content here", confidence=0.8),
        ]
        ranks = self.engine.rank(resp)
        assert len(ranks) == 3
        assert ranks[0].rank == 1
        assert ranks[-1].rank == 3

    def test_top_n(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        top = self.engine.get_top(resp, top_n=1)
        assert len(top) == 1

    def test_custom_criteria(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        ranks = self.engine.rank(resp, criteria={"quality": 1.0})
        assert len(ranks) == 2

    def test_score_criteria(self):
        r = ModelResponse(model="test", provider="test", content="A" * 30, confidence=0.8)
        assert RankingEngine._score_criterion(r, "quality") > 0
        assert RankingEngine._score_criterion(r, "relevance") == 0.8
        assert RankingEngine._score_criterion(r, "conciseness") > 0

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        self.engine.rank(resp)
        assert len(self.engine.get_history()) == 1


# ─── ReasoningMerger ─────────────────────────────────────────────────

class TestReasoningMerger:
    def setup_method(self):
        self.merger = ReasoningMerger("weighted_merge")

    def test_empty_merge(self):
        r = self.merger.merge([])
        assert r["sources"] == 0

    def test_single_merge(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="Answer", confidence=0.9)]
        r = self.merger.merge(resp)
        assert r["merged"] == "Answer"
        assert r["confidence"] > 0

    def test_concatenate_merge(self):
        merger = ReasoningMerger("concatenate")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.8),
        ]
        r = merger.merge(resp)
        assert "gpt-4o" in r["merged"]

    def test_best_pick_merge(self):
        merger = ReasoningMerger("best_pick")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        r = merger.merge(resp)
        assert r["merged"] == "A"

    def test_all_failed_merge(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="", error="fail")]
        r = self.merger.merge(resp)
        assert r["sources"] == 0

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="X", confidence=0.9)]
        self.merger.merge(resp)
        assert len(self.merger.get_history()) == 1


# ─── ConfidenceEngine ────────────────────────────────────────────────

class TestConfidenceEngine:
    def setup_method(self):
        self.engine = ConfidenceEngine()

    def test_empty(self):
        r = self.engine.calculate([])
        assert r["overall_confidence"] == 0.0

    def test_single(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.8)]
        r = self.engine.calculate(resp)
        assert r["overall_confidence"] == 0.8
        assert r["agreement"] == 1.0

    def test_high_agreement(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.85),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.83),
        ]
        r = self.engine.calculate(resp)
        assert r["agreement"] > 0.9

    def test_low_agreement(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.2),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.9),
        ]
        r = self.engine.calculate(resp)
        assert r["agreement"] < 1.0

    def test_calibrate(self):
        engine = ConfidenceEngine(calibration_offset=0.1)
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.5)]
        r = engine.calculate(resp)
        assert r["overall_confidence"] == 0.6

    def test_is_confident(self):
        assert self.engine.is_confident(0.8, 0.6)
        assert not self.engine.is_confident(0.3, 0.6)

    def test_all_failed(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="", error="fail")]
        r = self.engine.calculate(resp)
        assert r["overall_confidence"] == 0.0

    def test_std_dev(self):
        std = ConfidenceEngine._std_dev([0.5, 0.5, 0.5])
        assert std == 0.0

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.8)]
        self.engine.calculate(resp)
        assert len(self.engine.get_history()) == 1


# ─── ResponseSelector ────────────────────────────────────────────────

class TestResponseSelector:
    def setup_method(self):
        self.selector = ResponseSelector("highest_confidence")

    def test_empty_select(self):
        assert self.selector.select([]) is None

    def test_single_select(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        best = self.selector.select(resp)
        assert best.model == "gpt-4o"

    def test_best_confidence(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        best = self.selector.select(resp)
        assert best.model == "gpt-4o"

    def test_best_ranked(self):
        selector = ResponseSelector("best_ranked")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.7),
        ]
        scores = {"gpt-4o": 0.5, "claude": 0.9}
        best = selector.select(resp, scores=scores)
        assert best.model == "claude"

    def test_quality_first(self):
        selector = ResponseSelector("quality_first")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9, latency_ms=100),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.9, latency_ms=50),
        ]
        best = selector.select(resp)
        assert best.model == "claude"  # same confidence, lower latency

    def test_ensemble_select(self):
        selector = ResponseSelector("ensemble")
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9, latency_ms=100),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.8, latency_ms=200),
        ]
        best = selector.select(resp)
        assert best is not None

    def test_all_failed(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="", error="fail")]
        assert self.selector.select(resp) is None

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        self.selector.select(resp)
        assert len(self.selector.get_history()) == 1


# ─── ParallelReasoning ──────────────────────────────────────────────

class TestParallelReasoning:
    def setup_method(self):
        self.engine = ParallelReasoning(max_concurrent=3)

    def test_reason_without_callback_fails_closed(self):
        with pytest.raises(ValueError, match="real provider callback"):
            self.engine.reason("test prompt", ["gpt-4o", "claude", "gemini"])

    def test_reason_with_callback(self):
        def fake_call(prompt, model):
            return ModelResponse(model=model, provider="test", content="OK", confidence=0.9)
        results = self.engine.reason("test", ["gpt-4o", "claude"], call_fn=fake_call)
        assert len(results) == 2
        assert results[0].model == "gpt-4o"

    def test_reason_with_error(self):
        def fail_call(prompt, model):
            raise ValueError("boom")
        results = self.engine.reason("test", ["gpt-4o"], call_fn=fail_call)
        assert not results[0].is_success
        assert "boom" in results[0].error

    def test_history(self):
        def call(prompt, model):
            return ModelResponse(model=model, provider="test", content="reasoned")
        self.engine.reason("test", ["gpt-4o"], call_fn=call)
        assert len(self.engine.get_history()) == 1


# ─── ParallelGeneration ─────────────────────────────────────────────

class TestParallelGeneration:
    def setup_method(self):
        self.engine = ParallelGeneration(max_parallel=3)

    def test_generate_without_callback_fails_closed(self):
        with pytest.raises(ValueError, match="real provider callback"):
            self.engine.generate("Write a blog", ["gpt-4o", "claude"])

    def test_generate_with_callback(self):
        def fake_call(prompt, model):
            return ModelResponse(model=model, provider="test", content="Content", confidence=0.8)
        results = self.engine.generate("Write", ["gpt-4o"], call_fn=fake_call)
        assert results[0].content == "Content"

    def test_max_parallel(self):
        def call(prompt, model):
            return ModelResponse(model=model, provider="test", content=model)
        results = self.engine.generate("Write", ["m1", "m2", "m3", "m4", "m5"], call_fn=call)
        assert len(results) == 3

    def test_history(self):
        def call(prompt, model):
            return ModelResponse(model=model, provider="test", content="generated")
        self.engine.generate("Write", ["gpt-4o"], call_fn=call)
        assert len(self.engine.get_history()) == 1


# ─── ParallelReview ─────────────────────────────────────────────────

class TestParallelReview:
    def setup_method(self):
        self.reviewer = ParallelReview(max_concurrent=3)

    def test_review_without_callback_fails_closed(self):
        with pytest.raises(ValueError, match="real provider callback"):
            self.reviewer.review("Great content", ["critic1", "critic2"])

    def test_review_with_callback(self):
        def fake_review(content, reviewer):
            return ModelResponse(model=reviewer, provider="test", content="Looks good", confidence=0.85)
        results = self.reviewer.review("Text", ["c1"], call_fn=fake_review)
        assert results[0].is_success

    def test_history(self):
        def call(content, reviewer):
            return ModelResponse(model=reviewer, provider="test", content="review")
        self.reviewer.review("Text", ["c1"], call_fn=call)
        assert len(self.reviewer.get_history()) == 1


# ─── EnsembleAI ──────────────────────────────────────────────────────

class TestEnsembleAI:
    def setup_method(self):
        self.ensemble = EnsembleAI()

    def test_empty_ensemble(self):
        r = self.ensemble.ensemble([])
        assert r["best"] is None

    def test_single_ensemble(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        r = self.ensemble.ensemble(resp)
        assert r["best"].model == "gpt-4o"
        assert r["consensus"] is not None
        assert r["confidence"]["overall_confidence"] > 0

    def test_multi_ensemble(self):
        resp = [
            ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9),
            ModelResponse(model="claude", provider="anthropic", content="B", confidence=0.8),
            ModelResponse(model="gemini", provider="google", content="C", confidence=0.7),
        ]
        r = self.ensemble.ensemble(resp)
        assert r["model_count"] == 3
        assert len(r["ranking"]) == 3

    def test_all_failed(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="", error="fail")]
        r = self.ensemble.ensemble(resp)
        assert r["best"] is None

    def test_history(self):
        resp = [ModelResponse(model="gpt-4o", provider="openai", content="A", confidence=0.9)]
        self.ensemble.ensemble(resp)
        assert len(self.ensemble.get_history()) == 1


# ─── Config, Context, Request, Response ─────────────────────────────

# ─── Metrics ─────────────────────────────────────────────────────────

# ─── Events ──────────────────────────────────────────────────────────

# ─── Health ──────────────────────────────────────────────────────────

# ─── Profiler ────────────────────────────────────────────────────────

# ─── Validator ───────────────────────────────────────────────────────

# ─── Memory ──────────────────────────────────────────────────────────

# ─── Report ──────────────────────────────────────────────────────────

# ─── Cache ───────────────────────────────────────────────────────────

# ─── Router ──────────────────────────────────────────────────────────

class TestMultiModelRouter:
    def test_route_generation(self):
        r = MultiModelRouter()
        models = r.route("generation")
        assert "gpt-4o" in models

    def test_route_custom(self):
        r = MultiModelRouter()
        r.register_route("custom_task", ["m1", "m2"])
        models = r.route("custom_task")
        assert models == ["m1", "m2"]

    def test_route_override(self):
        r = MultiModelRouter()
        models = r.route("generation", models=["only_this"])
        assert models == ["only_this"]

    def test_unregister(self):
        r = MultiModelRouter()
        r.register_route("temp", ["m1"])
        assert r.unregister_route("temp")
        assert not r.unregister_route("nonexistent")

    def test_all_routes(self):
        r = MultiModelRouter()
        all_r = r.get_all_routes()
        assert "generation" in all_r


# ─── Registry ────────────────────────────────────────────────────────

# ─── Strategy ────────────────────────────────────────────────────────

class TestMultiModelStrategy:
    def test_balanced(self):
        s = MultiModelStrategy("balanced")
        assert s.get("prefer_low_latency") is True

    def test_custom(self):
        s = MultiModelStrategy("fastest")
        s.set("custom_key", "custom_val")
        assert s.get("custom_key") == "custom_val"

    def test_to_dict(self):
        d = MultiModelStrategy("best_quality").to_dict()
        assert "name" in d

    def test_available(self):
        strategies = MultiModelStrategy.available_strategies()
        assert "balanced" in strategies
        assert "fastest" in strategies


# ─── Executor ────────────────────────────────────────────────────────

class TestMultiModelExecutor:
    def test_execute_requires_real_provider_callback(self):
        e = MultiModelExecutor()
        with pytest.raises(ValueError, match="real provider callback"):
            e.execute("test", ["gpt-4o", "claude"])
        assert e.execution_count == 0

    def test_execute_with_callback(self):
        def fake(prompt, model):
            return ModelResponse(model=model, provider="test", content="OK", confidence=0.9)
        e = MultiModelExecutor()
        results = e.execute("test", ["gpt-4o"], call_fn=fake)
        assert results[0].is_success

    def test_retry(self):
        call_count = {"n": 0}
        def flaky(prompt, model):
            call_count["n"] += 1
            if call_count["n"] == 1:
                raise ValueError("fail")
            return ModelResponse(model=model, provider="test", content="OK", confidence=0.9)
        e = MultiModelExecutor(max_retries=2)
        results = e.execute("test", ["gpt-4o"], call_fn=flaky)
        assert results[0].is_success

    def test_timeout_does_not_return_late_provider_result_as_success(self):
        def slow_provider(prompt, model):
            time.sleep(0.01)
            return ModelResponse(model=model, provider="test", content="late result", confidence=0.9)

        e = MultiModelExecutor(max_retries=0, timeout=0.001)
        results = e.execute("test", ["gpt-4o"], call_fn=slow_provider)
        assert len(results) == 1
        assert results[0].provider == "timeout"
        assert not results[0].is_success


# ─── Scheduler ───────────────────────────────────────────────────────

# ─── Monitor ─────────────────────────────────────────────────────────

# ─── Optimizer ───────────────────────────────────────────────────────

# ─── Policy ──────────────────────────────────────────────────────────

# ─── Fallback ────────────────────────────────────────────────────────

class TestMultiModelFallback:
    def test_fallback_without_callback_fails_closed(self):
        f = MultiModelFallback()
        with pytest.raises(ValueError, match="real provider callback"):
            f.attempt_fallback("prompt", ["gpt-4o"])

    def test_fallback_with_callback(self):
        def fake(prompt, model):
            return ModelResponse(model=model, provider="test", content="OK", confidence=0.8)
        f = MultiModelFallback()
        resp = f.attempt_fallback("p", ["gpt-4o"], call_fn=fake)
        assert resp.is_success

    def test_all_models_failed(self):
        f = MultiModelFallback(fallback_models=["gpt-4o"])
        resp = f.attempt_fallback("p", ["gpt-4o"])
        assert resp is None  # gpt-4o in both fallback and failed list

    def test_fallback_available_uses_real_callback(self):
        f = MultiModelFallback(fallback_models=["gpt-4o"])
        def call(prompt, model):
            return ModelResponse(model=model, provider="test", content="real response")
        resp = f.attempt_fallback("p", ["claude"], call_fn=call)
        assert resp is not None and resp.is_success
    def test_no_available(self):
        f = MultiModelFallback(fallback_models=["gpt-4o"])
        resp = f.attempt_fallback("p", ["gpt-4o", "gpt-4o"])  # all failed
        # fallback_models has gpt-4o but it's in failed list
        # The logic checks `m not in failed_models` — gpt-4o IS in failed list
        # So we need to verify: failed_models = ["gpt-4o"], fallback = ["gpt-4o"]
        # available = [m for m in fallback if m not in failed] = []
        assert resp is None

    def test_history(self):
        f = MultiModelFallback()
        def fail(prompt, model):
            raise RuntimeError("offline")
        f.attempt_fallback("p", [], call_fn=fail)
        history = f.get_history()
        assert len(history) == 2
        assert all(item["success"] is False for item in history)

    def test_callback_error(self):
        def fail(prompt, model):
            raise ValueError("boom")
        f = MultiModelFallback()
        resp = f.attempt_fallback("p", [], call_fn=fail)
        assert resp is None  # all fallbacks failed

# ═══════════════════════════════════════════════════════════════════════
# MODULE 7: Canonical cost pricing registry
# Keep only the price registry used by the real LLM manager.

from layers.layer12_ai_foundation.modules.ai_cost_optimizer.price_calculator import PriceCalculator


class TestPriceCalculator:
    def test_calculate(self):
        cost = PriceCalculator.calculate("gpt-5.6-luna", 1000, 500)
        assert cost > 0

    def test_compare(self):
        costs = PriceCalculator.compare_models(1000, 500, ["gpt-5.6-luna", "gpt-5.6-sol"])
        assert "gpt-5.6-sol" in costs
        assert costs["gpt-5.6-luna"] < costs["gpt-5.6-sol"]
