"""Layer 12 production certification gate tests."""
from __future__ import annotations

import pytest

from layers.layer12_ai_foundation.modules.ai_orchestrator.ai_gateway import AIGateway
from layers.layer12_ai_foundation.modules.ai_orchestrator.ai_orchestrator import AIOrchestrator
from layers.layer12_ai_foundation.modules.model_provider_framework.openai_provider import OpenAIProvider
from layers.layer12_ai_foundation.modules.model_provider_framework.provider_base import ProviderRequest


def test_openai_provider_requires_credentials_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UCOS_ENV", "production")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider = OpenAIProvider()
    assert provider.initialize() is False
    assert provider.is_available() is False


def test_orchestrator_requires_start_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UCOS_ENV", "production")
    result = AIOrchestrator().process("test-task", {})
    assert result["success"] is False
    assert result["error_code"] == "ORCHESTRATOR_NOT_RUNNING"


def test_orchestrator_rejects_unlinked_route_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UCOS_ENV", "production")
    orchestrator = AIOrchestrator()
    orchestrator.start()
    result = orchestrator.process("test-task", {})
    assert result["success"] is False
    assert result["error_code"] == "TASK_EXECUTION_FAILED"


def test_gateway_rejects_invalid_payload() -> None:
    gateway = AIGateway()
    gateway.register_handler("test", lambda payload: payload)
    result = gateway.handle("test", "not-a-dict")  # type: ignore[arg-type]
    assert result["success"] is False
    assert result["error_code"] == "INVALID_PAYLOAD"


def test_provider_uses_live_transport_when_credentials_exist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("UCOS_ENV", "production")
    provider = OpenAIProvider({"api_key": "test-key", "base_url": "http://127.0.0.1:9"})
    assert provider.initialize() is True
    assert provider.is_available() is True
    with pytest.raises(RuntimeError, match="OpenAI request failed"):
        provider.generate(ProviderRequest("hello", "gpt-4o-mini", "openai"))
