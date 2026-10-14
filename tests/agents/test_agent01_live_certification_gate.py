"""Preflight checks for Agent 01 real production validation."""
from __future__ import annotations

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


def test_gate_refuses_missing_real_tavily_key_before_history_import(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("NEON_DATABASE_URL", "configured-only")
    monkeypatch.setenv("UCOS_CREDENTIAL_ENCRYPTION_KEY", "configured-only")
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)

    report = run_gate()

    assert report["status"] == "blocked"
    assert report["reason_code"] == "required_live_environment_missing"
    assert report["missing_environment_names"] == ["TAVILY_API_KEY"]
    assert report["history_imports"] == []
    assert report["external_research_performed"] is False if "external_research_performed" in report else True
    assert report["production_certified"] is False
