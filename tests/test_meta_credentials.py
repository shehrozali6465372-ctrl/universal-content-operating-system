from pathlib import Path

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec
from layers.layer07_publishing.modules.account_control.meta_credentials import MetaCredentialProvider


def test_meta_provider_derives_page_token_from_one_system_user_token(tmp_path: Path, monkeypatch):
    registry = AccountRegistry(str(tmp_path / "registry.sqlite3"), str(tmp_path / "workspaces"))
    registry.register(AccountSpec(
        account_id="facebook:p1",
        platform="facebook",
        niche="general",
        credentials_ref="META_ACCESS_TOKEN",
        constraints={"meta_asset_id": "p1"},
    ))

    class FakeRegistry:
        def get(self, account_id):
            return registry.get(account_id)

    monkeypatch.setattr(
        "layers.layer07_publishing.modules.account_control.meta_credentials.AccountRegistry",
        FakeRegistry,
    )

    provider = MetaCredentialProvider(token="system-token")

    monkeypatch.setattr(provider, "_pages", lambda: [
        {"id": "p1", "access_token": "derived-page-token", "name": "Page One"}
    ])

    credentials = provider.credentials_for("facebook", "facebook:p1")
    assert credentials == {"page_id": "p1", "access_token": "derived-page-token"}


def test_meta_provider_derives_instagram_credentials_from_linked_page(tmp_path: Path, monkeypatch):
    registry = AccountRegistry(str(tmp_path / "registry.sqlite3"), str(tmp_path / "workspaces"))
    registry.register(AccountSpec(
        account_id="instagram:ig1",
        platform="instagram",
        niche="general",
        credentials_ref="META_ACCESS_TOKEN",
        constraints={"meta_asset_id": "ig1", "page_id": "p1"},
    ))

    class FakeRegistry:
        def get(self, account_id):
            return registry.get(account_id)

    monkeypatch.setattr(
        "layers.layer07_publishing.modules.account_control.meta_credentials.AccountRegistry",
        FakeRegistry,
    )

    provider = MetaCredentialProvider(token="system-token")
    monkeypatch.setattr(provider, "_pages", lambda: [
        {
            "id": "p1",
            "access_token": "page-token",
            "instagram_business_account": {"id": "ig1", "username": "demo"},
        }
    ])

    credentials = provider.credentials_for("instagram", "instagram:ig1")
    assert credentials == {"account_id": "ig1", "access_token": "page-token"}

    
def test_meta_provider_follows_page_pagination_without_reusing_embedded_token(monkeypatch):
    provider = MetaCredentialProvider(token="system-token")
    calls = []

    def fake_get(path, params):
        calls.append((path, params))
        if len(calls) == 1:
            return {
                "data": [{"id": "p1", "access_token": "page-1"}],
                "paging": {"next": "https://graph.facebook.com/v26.0/me/accounts?after=cursor-2&access_token=system-token"},
            }
        return {
            "data": [{"id": "p2", "access_token": "page-2"}],
        }

    monkeypatch.setattr(provider, "_get", fake_get)
    pages = provider._pages()
    assert [p["id"] for p in pages] == ["p1", "p2"]
    assert "access_token" not in calls[1][1]
    assert calls[1][1]["after"] == "cursor-2"
