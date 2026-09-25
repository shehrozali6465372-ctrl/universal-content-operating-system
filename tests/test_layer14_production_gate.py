"""Strict production gate tests for Layer 14 enterprise integration."""
from __future__ import annotations

import hashlib
import hmac
import time

import pytest


CORE_MODULES = (
    "layers.layer14_enterprise_integration.modules.api_gateway.api_gateway",
    "layers.layer14_enterprise_integration.modules.config.config_loader",
    "layers.layer14_enterprise_integration.modules.config.config_validator",
    "layers.layer14_enterprise_integration.modules.di_container.di_container",
    "layers.layer14_enterprise_integration.modules.di_container.di_builder",
    "layers.layer14_enterprise_integration.modules.event_bus.event_bus_integration",
    "layers.layer14_enterprise_integration.modules.event_bridge.event_bridge",
    "layers.layer14_enterprise_integration.modules.execution_context.execution_context",
    "layers.layer14_enterprise_integration.modules.health_check.health_system",
    "layers.layer14_enterprise_integration.modules.health_manager.health_manager",
    "layers.layer14_enterprise_integration.modules.integration.integration_framework",
    "layers.layer14_enterprise_integration.modules.integration_kernel.integration_kernel",
    "layers.layer14_enterprise_integration.modules.layer_registry.layer_registry",
    "layers.layer14_enterprise_integration.modules.lifecycle_manager.lifecycle_manager",
    "layers.layer14_enterprise_integration.modules.master_orchestrator.control_plane",
    "layers.layer14_enterprise_integration.modules.master_orchestrator.integration_orchestrator",
    "layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring",
    "layers.layer14_enterprise_integration.modules.memory_bridge.memory_bridge",
    "layers.layer14_enterprise_integration.modules.metrics.metrics_system",
    "layers.layer14_enterprise_integration.modules.pipeline_engine.pipeline_engine",
    "layers.layer14_enterprise_integration.modules.production_certification.production_certifier",
    "layers.layer14_enterprise_integration.modules.production_certification.proof_verifier",
    "layers.layer14_enterprise_integration.modules.query_bus.query_bus",
    "layers.layer14_enterprise_integration.modules.real_integrations.config",
    "layers.layer14_enterprise_integration.modules.real_integrations.gateway",
    "layers.layer14_enterprise_integration.modules.real_integrations.http_client",
    "layers.layer14_enterprise_integration.modules.real_integrations.lineage",
    "layers.layer14_enterprise_integration.modules.response_router.response_router",
    "layers.layer14_enterprise_integration.modules.security.security_middleware",
    "layers.layer14_enterprise_integration.modules.service_locator.service_locator",
    "layers.layer14_enterprise_integration.modules.shared_state.shared_state",
    "layers.layer14_enterprise_integration.modules.system_verifier.system_verifier",
    "layers.layer14_enterprise_integration.modules.transaction_manager.transaction_manager",
    "layers.layer14_enterprise_integration.modules.workflow_engine.workflow_engine",
)


def test_all_core_layer14_modules_import():
    import importlib

    for module_name in CORE_MODULES:
        importlib.import_module(module_name)


def test_production_pipeline_rejects_empty_topic():
    from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
        ContentRequest,
        PipelineWiring,
    )

    request = ContentRequest("")
    with pytest.raises(ValueError, match="topic is required"):
        PipelineWiring().execute(request)


def test_production_ai_path_fails_closed_without_provider(monkeypatch):
    from layers.layer14_enterprise_integration.modules.master_orchestrator.pipeline_wiring import (
        ContentRequest,
        ContentResponse,
        PipelineWiring,
    )

    monkeypatch.setenv("APP_ENV", "production")
    for key in (
        "GEMINI_API_KEY_1",
        "GEMINI_API_KEY_2",
        "GEMINI_API_KEY_3",
        "GEMINIAPIKEY2",
        "GEMINIAPIKEY3",
    ):
        monkeypatch.delenv(key, raising=False)

    pipeline = PipelineWiring()
    response = ContentResponse(ContentRequest("production gate", include_image=False))
    ctx = {}
    result = pipeline._ai(response.request, ctx, response)

    assert result["offline"] is True
    assert ctx["ai_model"] == "offline-draft"


def test_aios_hmac_nonce_replay_is_rejected(monkeypatch):
    from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

    secret = "layer14-test-secret"
    monkeypatch.setenv("AIOS_API_KEY", secret)
    gateway = APIGateway()

    method = "POST"
    path = "/v1/jobs"
    timestamp = str(int(time.time()))
    nonce = "layer14-production-gate-nonce"
    body = b'{"job_id":"gate-1"}'
    canonical = (
        method + "\n" + path + "\n" + timestamp + "\n" + nonce + "\n"
        + body.decode("utf-8")
    ).encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), canonical, hashlib.sha256).hexdigest()
    headers = {
        "X-AIOS-Timestamp": timestamp,
        "X-AIOS-Nonce": nonce,
        "X-AIOS-Signature": signature,
    }

    assert gateway._aios_authorized(method, path, body, headers) is True
    assert gateway._aios_authorized(method, path, body, headers) is False


def test_integration_config_rejects_insecure_production_urls(monkeypatch):
    from layers.layer14_enterprise_integration.modules.real_integrations.config import (
        IntegrationConfig,
    )

    monkeypatch.setenv("APP_ENV", "production")
    config = IntegrationConfig(
        affiliate_base_url="http://affiliate.example",
        wordpress_url="http://wordpress.example",
    )
    result = config.validation()

    assert result["valid"] is False
    assert any("affiliate_base_url" in error for error in result["errors"])
    assert any("wordpress_url" in error for error in result["errors"])


def test_layer14_logging_is_not_print_based():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / "layers" / "layer14_enterprise_integration"
    critical = (
        root / "modules" / "master_orchestrator" / "pipeline_wiring.py",
        root / "modules" / "api_gateway" / "api_gateway.py",
    )
    for path in critical:
        source = path.read_text(encoding="utf-8")
        assert "print(" not in source, path
