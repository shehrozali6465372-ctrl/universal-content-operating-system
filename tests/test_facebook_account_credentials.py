"""Facebook account credential isolation regressions."""
from __future__ import annotations


def test_facebook_authenticate_does_not_use_process_environment(monkeypatch):
    from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "global-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "global-token")
    pub = FacebookPublisher()
    assert pub.authenticate({}) is False
    assert pub._page_id == ""
    assert pub._access_token == ""
    assert pub._authenticated is False


def test_facebook_authenticate_uses_explicit_account_credentials(monkeypatch):
    from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
    monkeypatch.setenv("FACEBOOK_PAGE_ID", "global-page")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "global-token")
    pub = FacebookPublisher()
    pub._api_get = lambda endpoint, params=None, token=None: {"id": "account-page", "name": "Account Page"}
    assert pub.authenticate({"page_id": "account-page", "access_token": "account-token"}) is True
    assert pub._page_id == "account-page"
    assert pub._access_token == "account-token"
    assert pub._authenticated is True


def test_facebook_failed_remote_validation_never_marks_authenticated():
    from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import FacebookPublisher
    pub = FacebookPublisher()
    pub._api_get = lambda *args, **kwargs: {}
    assert pub.authenticate({"page_id": "account-page", "access_token": "account-token"}) is False
    assert pub._authenticated is False
