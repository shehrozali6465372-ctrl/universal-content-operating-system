"""Focused production-contract tests for Layer 12 provider adapters."""
import os
import pytest

from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.claude_provider import ClaudeProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.gemini_provider import GeminiProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.deepseek_provider import DeepSeekProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.grok_provider import GrokProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.mistral_provider import MistralProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.cohere_provider import CohereProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.openrouter_provider import OpenRouterProvider

@pytest.mark.parametrize("provider_cls", [
    OpenAIProvider, ClaudeProvider, GeminiProvider, DeepSeekProvider,
    GrokProvider, MistralProvider, CohereProvider, OpenRouterProvider,
])
def test_cloud_providers_fail_closed_without_credentials(monkeypatch, provider_cls):
    for name in ("OPENAI_API_KEY","ANTHROPIC_API_KEY","GEMINI_API_KEY","DEEPSEEK_API_KEY",
                 "XAI_API_KEY","MISTRAL_API_KEY","COHERE_API_KEY","OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    provider = provider_cls({})
    assert provider.initialize() is False
    assert provider.is_available() is False
    with pytest.raises(RuntimeError):
        provider.generate(ProviderRequest("test", "", provider.name))

def test_llm_manager_refuses_simulation_in_production(monkeypatch):
    from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import LLMManager
    monkeypatch.setenv("UCOS_ENV", "production")
    with pytest.raises(RuntimeError, match="refusing simulated AI output"):
        LLMManager().generate("production test")

def test_cache_isolated_by_provider_and_parameters():
    from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cache import LLMCache
    cache = LLMCache()
    cache.set("same", "model", "openai-result", "openai", "system", 0.1, 100)
    assert cache.get("same", "model", "openai", "system", 0.1, 100) == "openai-result"
    assert cache.get("same", "model", "gemini", "system", 0.1, 100) is None
    assert cache.get("same", "model", "openai", "different", 0.1, 100) is None
