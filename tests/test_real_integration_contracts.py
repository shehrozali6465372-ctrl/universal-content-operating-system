import os

import pytest

from layers.layer14_enterprise_integration.modules.real_integrations.config import IntegrationConfig
from layers.layer14_enterprise_integration.modules.real_integrations.gateway import IntegrationGateway
from layers.layer14_enterprise_integration.modules.real_integrations.http_client import (
    HTTPClient,
    IntegrationError,
)
from layers.layer14_enterprise_integration.modules.real_integrations.lineage import (
    LineageStore,
    STAGES,
)


def test_integration_config_is_explicit_and_secret_free(monkeypatch):
    for key in list(os.environ):
        if key.startswith("UCOS_"):
            monkeypatch.delenv(key, raising=False)
    config = IntegrationConfig.from_env()
    status = config.status()
    assert status["serpapi"] is False
    assert status["affiliate_network"] is False
    assert status["google_analytics_4"] is False
    assert status["wordpress"] is False
    assert status["validation"]["valid"] is True


def test_real_gateway_fails_closed_without_credentials(monkeypatch):
    monkeypatch.delenv("UCOS_SERPAPI_API_KEY", raising=False)
    gateway = IntegrationGateway()
    with pytest.raises(Exception, match="UCOS_SERPAPI_API_KEY"):
        gateway.search("test query")


def test_production_rejects_plain_http_provider(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("UCOS_AFFILIATE_BASE_URL", "http://affiliate.example")
    monkeypatch.setenv("UCOS_AFFILIATE_API_KEY", "secret")
    config = IntegrationConfig.from_env()
    assert config.validation()["valid"] is False
    with pytest.raises(IntegrationError):
        HTTPClient().request("GET", "http://affiliate.example/health")


def test_lineage_requires_order_and_is_idempotent(tmp_path):
    store = LineageStore(db_path=str(tmp_path / "lineage.sqlite3"))
    lineage_id = "lineage-test"
    parent = None
    events = {}
    for stage in STAGES:
        event = store.record(
            lineage_id=lineage_id,
            stage=stage,
            entity_id=f"{stage}-1",
            source="test-source",
            source_id=f"src-{stage}",
            provider="test",
            status="observed",
            payload={"stage": stage},
            parent_event_id=parent,
        )
        events[stage] = event
        parent = event.event_id
    assert len(store.get_lineage(lineage_id)) == len(STAGES)
    duplicate = store.record(
        lineage_id=lineage_id,
        stage="revenue",
        entity_id="revenue-1",
        source="test-source",
        source_id="src-revenue",
        provider="test",
        status="observed",
        payload={"stage": "revenue"},
        parent_event_id=parent,
    )
    assert duplicate.event_id == events["revenue"].event_id
    assert len(store.get_lineage(lineage_id)) == len(STAGES)
    store.close()


def test_lineage_rejects_broken_parent(tmp_path):
    store = LineageStore(db_path=str(tmp_path / "lineage.sqlite3"))
    store.record(
        lineage_id="l1",
        stage="source",
        entity_id="s1",
        source="x",
        source_id="x1",
        provider="p",
        status="observed",
        payload={"ok": True},
    )
    with pytest.raises(ValueError, match="requires a recorded parent stage niche"):
        store.record(
            lineage_id="l1",
            stage="keyword",
            entity_id="k1",
            source="x",
            source_id="k1",
            provider="p",
            status="observed",
            payload={"ok": True},
        )
    store.close()


def test_wordpress_requires_all_credentials(monkeypatch):
    monkeypatch.delenv("UCOS_WORDPRESS_URL", raising=False)
    monkeypatch.delenv("UCOS_WORDPRESS_USERNAME", raising=False)
    monkeypatch.delenv("UCOS_WORDPRESS_APPLICATION_PASSWORD", raising=False)
    with pytest.raises(Exception, match="WordPress URL"):
        IntegrationGateway().wordpress_publish(title="x", content="y")
