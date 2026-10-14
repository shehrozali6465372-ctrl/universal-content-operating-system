"""Tests for the UCOS agent dispatcher and source-readiness contract."""
from __future__ import annotations

import pytest

from agents.dispatcher import (
    AgentDispatcher,
    AgentNotImplementedError,
    AgentNotProductionReadyError,
)


def test_dispatcher_lists_exactly_28_workers():
    agents = AgentDispatcher().list_agents()
    assert len(agents) == 28
    assert agents[0]["id"] == "AG01"
    assert sum(row["status"] != "planned" for row in agents) == 1


def test_planned_worker_cannot_be_dispatched():
    dispatcher = AgentDispatcher()
    with pytest.raises(AgentNotImplementedError, match="planned"):
        dispatcher.dispatch("AG02", constructor_kwargs={}, input_payload={}, mode="staging")


def test_agent_01_cannot_be_dispatched_to_production_before_certification():
    dispatcher = AgentDispatcher()
    with pytest.raises(AgentNotProductionReadyError, match="production_ready"):
        dispatcher.dispatch(
            "AG01",
            constructor_kwargs={"account_id": "account-a"},
            input_payload={},
            mode="production",
        )


def test_dispatch_uses_registered_staging_factory_and_preserves_account():
    class FakeAgent:
        def __init__(self, account_id):
            self.account_id = account_id

        def run(self, topic):
            return {"account_id": self.account_id, "topic": topic, "status": "test"}

    dispatcher = AgentDispatcher(factories={"AG01": FakeAgent})
    result = dispatcher.dispatch(
        "AG01",
        constructor_kwargs={"account_id": "account-a"},
        input_payload={"topic": "living room storage"},
        mode="staging",
    )
    assert result["account_id"] == "account-a"
    assert result["topic"] == "living room storage"


def test_dispatch_rejects_account_mismatch():
    class FakeAgent:
        def __init__(self, account_id):
            self.account_id = account_id

        def run(self):
            return {"account_id": "account-b"}

    dispatcher = AgentDispatcher(factories={"AG01": FakeAgent})
    with pytest.raises(RuntimeError, match="account_id"):
        dispatcher.dispatch(
            "AG01",
            constructor_kwargs={"account_id": "account-a"},
            input_payload={},
            mode="test",
        )

def test_certification_dispatch_is_production_only(monkeypatch):
    dispatcher = AgentDispatcher()
    monkeypatch.setenv("APP_ENV", "development")
    with pytest.raises(AgentNotProductionReadyError, match="production"):
        dispatcher.dispatch(
            "AG01",
            constructor_kwargs={"account_id": "account-a"},
            input_payload={"limit": 1},
            mode="certification",
        )


def test_certification_dispatch_rejects_injected_factories_in_production(monkeypatch):
    class FakeAgent:
        def __init__(self, account_id):
            self.account_id = account_id

        def run(self, limit=1):
            return {"account_id": self.account_id, "status": "fake"}

    monkeypatch.setenv("APP_ENV", "production")
    dispatcher = AgentDispatcher(factories={"AG01": FakeAgent})
    with pytest.raises(AgentNotProductionReadyError, match="injected factories"):
        dispatcher.dispatch(
            "AG01",
            constructor_kwargs={"account_id": "account-a"},
            input_payload={"limit": 1},
            mode="certification",
        )


def test_api_gateway_registers_agent01_research_route():
    from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

    gateway = APIGateway()
    assert callable(gateway._routes["POST /agents/AG01/research"])

def test_agent01_certification_endpoint_is_production_only(monkeypatch):
    from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

    monkeypatch.setenv("APP_ENV", "development")
    response = APIGateway()._handle_agent01_research({
        "account_id": "account-a",
        "mode": "certification",
    })
    assert response.status_code == 403


def test_agent01_research_endpoint_requires_account_id():
    from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway

    response = APIGateway()._handle_agent01_research({"mode": "certification"})
    assert response.status_code == 400
