import os
from unittest.mock import patch

from layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher import InstagramPublisher


def test_instagram_ignores_global_credentials(monkeypatch):
    monkeypatch.setenv("INSTAGRAM_ACCOUNT_ID", "global-account")
    monkeypatch.setenv("FACEBOOK_ACCESS_TOKEN", "global-token")
    publisher = InstagramPublisher()
    with patch.object(publisher, "_api_get") as api_get:
        assert publisher.authenticate({}) is False
        api_get.assert_not_called()


def test_instagram_accepts_explicit_account_credentials():
    publisher = InstagramPublisher()
    with patch.object(publisher, "_api_get", return_value={"id": "account-a", "username": "demo"}) as api_get:
        assert publisher.authenticate({"account_id": "account-a", "access_token": "token-a"}) is True
        assert publisher._authenticated is True
        api_get.assert_called_once()


def test_instagram_failed_remote_validation_does_not_authenticate():
    publisher = InstagramPublisher()
    with patch.object(publisher, "_api_get", return_value={"id": "different-account"}):
        assert publisher.authenticate({"account_id": "account-a", "access_token": "token-a"}) is False
        assert publisher._authenticated is False
