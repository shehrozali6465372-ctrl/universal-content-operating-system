"""Focused production-contract tests for Layer 12 provider adapters."""
import io

import pytest

from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import (
    ProviderRequest,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import (
    OpenAIProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.claude_provider import (
    ClaudeProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.gemini_provider import (
    GeminiProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.deepseek_provider import (
    DeepSeekProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.grok_provider import (
    GrokProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.mistral_provider import (
    MistralProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.cohere_provider import (
    CohereProvider,
)
from layers.layer12_ai_foundation.modules.model_provider_framework.openrouter_provider import (
    OpenRouterProvider,
)


@pytest.mark.parametrize(
    "provider_cls",
    [
        OpenAIProvider,
        ClaudeProvider,
        GeminiProvider,
        DeepSeekProvider,
        GrokProvider,
        MistralProvider,
        CohereProvider,
        OpenRouterProvider,
    ],
)
def test_cloud_providers_fail_closed_without_credentials(monkeypatch, provider_cls):
    for name in (
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "DEEPSEEK_API_KEY",
        "XAI_API_KEY",
        "MISTRAL_API_KEY",
        "COHERE_API_KEY",
        "OPENROUTER_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    provider = provider_cls({})
    assert provider.initialize() is False
    assert provider.is_available() is False
    with pytest.raises(RuntimeError):
        provider.generate(ProviderRequest("test", "", provider.name))


def test_llm_manager_refuses_simulation_in_production(monkeypatch):
    from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_manager import (
        LLMManager,
    )

    monkeypatch.setenv("UCOS_ENV", "production")
    with pytest.raises(RuntimeError, match="refusing simulated AI output"):
        LLMManager().generate("production test")


def test_cache_isolated_by_provider_and_parameters():
    from layers.layer12_ai_foundation.modules.universal_llm_manager.llm_cache import (
        LLMCache,
    )

    cache = LLMCache()
    cache.set("same", "model", "openai-result", "openai", "system", 0.1, 100)
    assert (
        cache.get("same", "model", "openai", "system", 0.1, 100)
        == "openai-result"
    )
    assert cache.get("same", "model", "gemini", "system", 0.1, 100) is None
    assert cache.get("same", "model", "openai", "different", 0.1, 100) is None


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self):
        return self._payload


def test_openai_retries_transient_http_failures(monkeypatch):
    attempts = {"count": 0}

    def fake_urlopen(request, timeout):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise __import__("urllib.error").error.HTTPError(
                request.full_url,
                503,
                "temporary",
                {},
                io.BytesIO(b"{}"),
            )
        return _FakeResponse(
            b'{"id":"req_test","choices":[{"message":{"content":"ok"},'
            b'"finish_reason":"stop"}],"usage":{"prompt_tokens":2,'
            b'"completion_tokens":3,"total_tokens":5}}'
        )

    monkeypatch.setattr(
        "layers.layer12_ai_foundation.modules.model_provider_framework."
        "openai_provider.urllib.request.urlopen",
        fake_urlopen,
    )
    monkeypatch.setattr(
        "layers.layer12_ai_foundation.modules.model_provider_framework."
        "openai_provider.time.sleep",
        lambda _: None,
    )

    provider = OpenAIProvider({"api_key": "test-key", "max_retries": 2})
    assert provider.initialize() is True
    response = provider.generate(ProviderRequest("hello", "gpt-4o-mini", "openai"))

    assert response.content == "ok"
    assert response.request_id == "req_test"
    assert response.usage["total_tokens"] == 5
    assert attempts["count"] == 3


def test_openai_does_not_retry_non_transient_http_failures(monkeypatch):
    attempts = {"count": 0}

    def fake_urlopen(request, timeout):
        attempts["count"] += 1
        raise __import__("urllib.error").error.HTTPError(
            request.full_url,
            401,
            "unauthorized",
            {},
            io.BytesIO(b"{}"),
        )

    monkeypatch.setattr(
        "layers.layer12_ai_foundation.modules.model_provider_framework."
        "openai_provider.urllib.request.urlopen",
        fake_urlopen,
    )

    provider = OpenAIProvider({"api_key": "test-key", "max_retries": 3})
    provider.initialize()
    with pytest.raises(RuntimeError, match="HTTPError"):
        provider.generate(ProviderRequest("hello", "gpt-4o-mini", "openai"))
    assert attempts["count"] == 1
