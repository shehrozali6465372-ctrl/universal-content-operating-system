"""YouTube account-credential isolation regression tests."""
from __future__ import annotations


def test_youtube_authenticate_does_not_use_process_environment(monkeypatch):
    from layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher import YouTubePublisher

    monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN", "global-token-must-not-be-used")
    publisher = YouTubePublisher()
    assert publisher.authenticate({}) is False
    assert publisher.token == ""
    assert publisher.authenticated is False


def test_youtube_authenticate_uses_explicit_account_credential(monkeypatch):
    from layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher import YouTubePublisher

    monkeypatch.setenv("YOUTUBE_ACCESS_TOKEN", "global-token-must-not-be-used")
    publisher = YouTubePublisher()
    publisher._get = lambda *args, **kwargs: {"items": [{"id": "channel-account"}]}

    assert publisher.authenticate({"access_token": "account-token"}) is True
    assert publisher.token == "account-token"
    assert publisher.authenticated is True
