from __future__ import annotations

from layers.layer14_enterprise_integration.modules.real_integrations.config import IntegrationConfig
from layers.layer14_enterprise_integration.modules.real_integrations.gateway import IntegrationGateway
from layers.layer14_enterprise_integration.modules.real_integrations.http_client import HTTPResponse


class FakeHTTPClient:
    def request(self, method, url, **kwargs):
        assert method == "GET"
        assert url == "https://news.google.com/rss/search"
        return HTTPResponse(
            200,
            """<?xml version="1.0"?><rss><channel>
            <item><title>Home organization ideas</title><link>https://example.com/story</link>
            <description>Practical organization ideas.</description></item>
            </channel></rss>""",
            {"Content-Type": "application/rss+xml"},
        )


def test_keyless_google_news_rss_search_is_real_and_non_synthetic(monkeypatch):
    monkeypatch.delenv("UCOS_SERPAPI_API_KEY", raising=False)
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    gateway = IntegrationGateway(
        IntegrationConfig(serpapi_key=""),
        client=FakeHTTPClient(),
    )

    result = gateway.search("practical home organization tips")

    assert result["provider"] == "google_news_rss"
    assert result["source"] == "google_news_rss"
    assert result["results"][0]["title"] == "Home organization ideas"
    assert result["results"][0]["link"] == "https://example.com/story"
    assert result["results"][0]["source_id"]
