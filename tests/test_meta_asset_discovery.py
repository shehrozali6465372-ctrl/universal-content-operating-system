import json
from pathlib import Path

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry
from layers.layer07_publishing.modules.account_control.meta_asset_discovery import MetaAssetDiscovery


class FakeDiscovery(MetaAssetDiscovery):
    def __init__(self, responses):
        super().__init__(token="secret", api_version="v26.0")
        self.responses = responses
        self.calls = []

    def _get(self, path, params=None):
        self.calls.append((path, params))
        if path == "/me/accounts":
            return self.responses["pages"]
        return self.responses.get(path, {})


def test_discovers_pages_and_linked_instagram_accounts_without_exposing_token():
    client = FakeDiscovery({
        "pages": {"data": [
            {"id": "p1", "name": "Page One"},
            {"id": "p2", "name": "Page Two"},
        ]},
        "/p1": {"id": "p1", "instagram_business_account": {"id": "ig1", "username": "one"}},
        "/p2": {"id": "p2", "instagram_business_account": {"id": "ig2", "username": "two"}},
    })
    result = client.discover()
    assert [a.asset_id for a in result["facebook"]] == ["p1", "p2"]
    assert [a.asset_id for a in result["instagram"]] == ["ig1", "ig2"]
    assert all("secret" not in str(call) for call in client.calls)


def test_provision_is_idempotent_and_uses_one_credential_reference(tmp_path: Path):
    client = FakeDiscovery({
        "pages": {"data": [{"id": "p1", "name": "Page One"}]},
        "/p1": {"id": "p1", "instagram_business_account": {"id": "ig1", "username": "one"}},
    })
    registry = AccountRegistry(str(tmp_path / "registry.sqlite3"), str(tmp_path / "workspaces"))
    first = client.provision(registry)
    second = client.provision(registry)
    assert first["facebook_discovered"] == 1
    assert first["instagram_discovered"] == 1
    assert second["facebook_discovered"] == 1
    assert len(registry.list(enabled_only=False)) == 2
    assert {a.credentials_ref for a in registry.list(enabled_only=False)} == {"META_ACCESS_TOKEN"}


def test_missing_token_is_explicit():
    try:
        MetaAssetDiscovery(token="")
    except RuntimeError as exc:
        assert "META_ACCESS_TOKEN" in str(exc)
    else:
        raise AssertionError("missing Meta token must fail explicitly")

    
def test_discovery_follows_graph_paging_without_forwarding_token():
    client = FakeDiscovery({
        "pages": {
            "data": [{"id": "p1", "name": "Page One"}],
            "paging": {"next": "https://graph.facebook.com/v26.0/me/accounts?after=cursor-2&access_token=secret"},
        },
        "/p1": {"id": "p1", "name": "Page One"},
    })
    original_get = client._get
    calls = []

    def paged_get(path, params=None):
        calls.append((path, params))
        if len(calls) == 1:
            return {"data": [{"id": "p1", "name": "Page One"}],
                    "paging": {"next": "https://graph.facebook.com/v26.0/me/accounts?after=cursor-2&access_token=secret"}}
        if len(calls) == 2:
            return {"data": [{"id": "p2", "name": "Page Two"}]}
        return original_get(path, params)

    client._get = paged_get
    result = client.discover()
    assert [a.asset_id for a in result["facebook"]] == ["p1", "p2"]
    assert "secret" not in str(calls[1][1])
