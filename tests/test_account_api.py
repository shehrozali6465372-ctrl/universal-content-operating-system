import tempfile
from pathlib import Path

from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import APIGateway


def test_account_api_provisions_isolated_workspace(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        monkeypatch.setenv("UCOS_ACCOUNT_REGISTRY_DB", str(root / "registry.sqlite3"))
        monkeypatch.setenv("UCOS_ACCOUNT_WORKSPACES", str(root / "workspaces"))
        gateway = APIGateway()
        response = gateway._handle_account_create({
            "account_id": "ig-food",
            "platform": "instagram",
            "niche": "food",
            "capabilities": ["post", "photo", "video"],
            "credentials_ref": "IG_FOOD",
        })
        assert response.status_code == 201
        assert response.data["account"]["account_id"] == "ig-food"
        assert sorted(response.data["provisioned_stores"]) == ["analytics", "content", "learning", "memory"]
        workspace = root / "workspaces" / "ig-food"
        assert (workspace / "account.json").exists()
        assert (workspace / "memory.sqlite3").exists()
        assert (workspace / "content.sqlite3").exists()
        assert (workspace / "analytics.sqlite3").exists()
        assert (workspace / "learning.sqlite3").exists()

        listed = gateway._handle_accounts({})
        assert listed.status_code == 200
        assert listed.data["count"] == 1
        assert listed.data["accounts"][0]["account_id"] == "ig-food"


def test_account_api_rejects_missing_identity_fields():
    gateway = APIGateway()
    response = gateway._handle_account_create({"platform": "instagram", "niche": "food"})
    assert response.status_code == 400
    assert "account_id" in response.error


def test_account_api_forwards_production_identity_hierarchy(monkeypatch):
    import layers.layer07_publishing.modules.account_control.account_registry as registry_module

    captured = {}

    class FakeRegistry:
        def register(self, spec):
            captured["spec"] = spec
            return Path("/tmp/ucos-account")

    monkeypatch.setattr(registry_module, "AccountRegistry", FakeRegistry)
    monkeypatch.setenv("APP_ENV", "production")

    gateway = APIGateway()
    response = gateway._handle_account_create({
        "account_id": "atoz:content-publishing",
        "platform": "website",
        "niche": "kitchen",
        "tenant_id": "tenant:atoz-product-hub",
        "workspace_id": "workspace:production",
        "brand_id": "brand:atoz-product-hub",
        "platform_account_id": "platform-account:atoz-website",
        "external_account_id": "atozproducthub-website.onrender.com",
        "tenant_name": "AtoZ Product Hub",
        "workspace_name": "Production",
        "brand_name": "AtoZ Product Hub",
        "platform_account_name": "AtoZ Product Hub Website",
    })

    assert response.status_code == 201
    spec = captured["spec"]
    assert spec.tenant_id == "tenant:atoz-product-hub"
    assert spec.workspace_id == "workspace:production"
    assert spec.brand_id == "brand:atoz-product-hub"
    assert spec.platform_account_id == "platform-account:atoz-website"
    assert spec.external_account_id == "atozproducthub-website.onrender.com"
