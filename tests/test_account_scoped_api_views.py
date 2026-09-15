import tempfile
from pathlib import Path

from layers.layer07_publishing.modules.account_control.account_data_store import AccountDataStore
from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway


def test_account_views_never_read_global_pipeline_data(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        monkeypatch.setenv("UCOS_ACCOUNT_REGISTRY_DB", str(root / "registry.sqlite3"))
        monkeypatch.setenv("UCOS_ACCOUNT_WORKSPACES", str(root / "workspaces"))
        registry = AccountRegistry()
        registry.register(AccountSpec(account_id="a", platform="instagram", niche="food"))
        registry.register(AccountSpec(account_id="b", platform="instagram", niche="tech"))
        store = AccountDataStore(registry)
        store.append("a", "content", "execution_history", {"topic": "food only", "template_id": "tpl-a"})
        store.append("a", "analytics", "execution_outcomes", {"topic": "food only", "analytics": "UNKNOWN"})
        store.append("b", "content", "execution_history", {"topic": "tech only", "template_id": "tpl-b"})
        store.append("b", "analytics", "execution_outcomes", {"topic": "tech only", "analytics": "UNKNOWN"})

        gateway = APIGateway()
        history = gateway._handle_history({"account_id": ["a"]})
        analytics = gateway._handle_analytics({"account_id": ["a"]})
        templates = gateway._handle_templates({"account_id": ["a"]})

        assert history.status_code == 200
        assert [x["topic"] for x in history.data["history"]] == ["food only"]
        assert analytics.data["account_id"] == "a"
        assert [x["topic"] for x in analytics.data["analytics"]] == ["food only"]
        assert templates.data["account_id"] == "a"
        assert [x["template_id"] for x in templates.data["rankings"]] == ["tpl-a"]


def test_account_sensitive_views_require_account_id(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        monkeypatch.setenv("UCOS_ACCOUNT_REGISTRY_DB", str(root / "registry.sqlite3"))
        monkeypatch.setenv("UCOS_ACCOUNT_WORKSPACES", str(root / "workspaces"))
        gateway = APIGateway()
        assert gateway._handle_history({}).status_code == 400
        assert gateway._handle_analytics({}).status_code == 400
        assert gateway._handle_templates({}).status_code == 400
