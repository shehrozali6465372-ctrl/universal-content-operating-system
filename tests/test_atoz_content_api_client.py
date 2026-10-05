import json

import pytest

from layers.layer23_website_manager.integration.atoz_content_api_client import (
    AtozContentApiClient,
    AtozContentApiError,
)


def test_client_is_fail_closed_without_machine_credentials(monkeypatch):
    for key in (
        "UCOS_ATOZ_AUTH_API_BASE_URL",
        "UCOS_ATOZ_CONTENT_API_BASE_URL",
        "UCOS_ATOZ_CLIENT_ID",
        "UCOS_ATOZ_CLIENT_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(AtozContentApiError, match="fail-closed"):
        AtozContentApiClient.from_env()


def test_client_exchanges_machine_credential_and_publishes(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, status, payload):
            self.status = status
            self.payload = payload

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

        def read(self):
            return json.dumps(self.payload).encode()

    def fake_urlopen(request, timeout):
        calls.append(request)
        if request.full_url.endswith("/api/v1/auth/token"):
            return FakeResponse(200, {"access_token": "jwt", "expires_in": 900})
        if request.full_url.endswith("/api/v1/admin/articles"):
            assert request.get_header("Authorization") == "Bearer jwt"
            assert request.get_header("X-niche-id") == "niche-1"
            return FakeResponse(201, {"id": "article-1", "status": "draft"})
        if request.full_url.endswith("/api/v1/admin/articles/article-1/lifecycle"):
            assert request.get_header("Authorization") == "Bearer jwt"
            assert request.get_header("X-niche-id") == "niche-1"
            return FakeResponse(200, {"id": "article-1", "status": "published"})
        raise AssertionError(request.full_url)

    monkeypatch.setattr(
        "layers.layer23_website_manager.integration.atoz_content_api_client.urlopen",
        fake_urlopen,
    )
    client = AtozContentApiClient(
        "https://api.example",
        "https://content.example",
        "client-1",
        "secret-1",
    )
    draft = client.create_article("niche-1", {"title": "Real", "body": "Body"})
    published = client.lifecycle("niche-1", draft["id"], "publish")

    assert published["status"] == "published"
    assert len(calls) == 3
