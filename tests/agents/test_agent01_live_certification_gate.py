"""Preflight checks for Agent 01 real production validation."""
from __future__ import annotations

import json

from scripts import agent01_live_certification_gate as gate
from scripts.agent01_live_certification_gate import run_gate


def test_gate_refuses_nonproduction_before_network_or_database(monkeypatch):
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("NEON_DATABASE_URL", "configured-only")
    monkeypatch.setenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", "configured-only")
    monkeypatch.setenv("TAVILY_API_KEY", "configured-only")

    report = run_gate()

    assert report["status"] == "blocked"
    assert report["reason_code"] == "APP_ENV_must_be_production"
    assert report["history_imports"] == []
    assert report["live_smokes"] == []
    assert report["production_certified"] is False


def test_gate_refuses_missing_neon_url_before_history_import(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("NEON_DATABASE_URL", raising=False)
    monkeypatch.setenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", "configured-only")
    monkeypatch.setenv("TAVILY_API_KEY", "configured-only")

    report = run_gate()

    assert report["status"] == "blocked"
    assert report["reason_code"] == "required_live_environment_missing"
    assert report["missing_environment_names"] == ["NEON_DATABASE_URL"]
    assert report["history_imports"] == []
    assert report["external_research_performed"] is False
    assert report["production_certified"] is False


def test_gate_refuses_missing_encryption_key_before_history_import(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("NEON_DATABASE_URL", "configured-only")
    monkeypatch.delenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "configured-only")

    report = run_gate()

    assert report["status"] == "blocked"
    assert report["missing_environment_names"] == ["UCOS_CREDENTIAL_ENCRYPTION_KEY"]
    assert report["history_imports"] == []
    assert report["external_research_performed"] is False
    assert report["production_certified"] is False

def test_deployed_api_smoke_signer_matches_gateway_hmac(monkeypatch):
    from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", "test-root-secret")
    monkeypatch.setenv("UCOS_API_BASE_URL", "https://ucos.example")
    gateway = APIGateway()

    class Response:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self, _limit):
            return json.dumps({
                "success": True,
                "status": 200,
                "data": {"status": "passed_live_smoke", "content_published": False},
            }).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == 180
        request_headers = {key.lower(): value for key, value in request.header_items()}
        headers = {
            "X-UCOS-Agent01-Timestamp": request_headers["x-ucos-agent01-timestamp"],
            "X-UCOS-Agent01-Nonce": request_headers["x-ucos-agent01-nonce"],
            "X-UCOS-Agent01-Signature": request_headers["x-ucos-agent01-signature"],
        }
        assert gateway._agent01_dispatch_hmac_authorized(
            "POST", "/agents/AG01/research", request.data, headers
        )
        return Response()

    monkeypatch.setattr(gate, "urlopen", fake_urlopen)
    result = gate._call_deployed_api_smoke("account-a", dispatch_mode="certification")

    assert result["status"] == "passed_live_smoke"
    assert result["request_path_verified"] is True
    assert result["dispatch_mode"] == "certification"
