"""Contract tests for the live Tavily Search adapter; no external request is made."""
from __future__ import annotations

import json
from urllib.error import HTTPError
from urllib.request import Request

import pytest

from agents.agent_01_research_discovery.tavily_source import (
    TavilyResearchSource,
    TavilySourceError,
)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self.payload = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, limit):
        return self.payload[:limit]


def sample_payload():
    return {
        "results": [
            {
                "title": "Small-space storage guide",
                "url": "https://publisher-one.example/article",
                "content": "A source-backed excerpt about small-space storage.",
                "score": 0.87,
                "published_date": "2026-10-13",
            },
            {
                "title": "Apartment organization research",
                "url": "https://publisher-two.example/research",
                "content": "A second independent source about apartment organization.",
                "score": 0.75,
            },
            {
                "title": "Bad URL must be discarded",
                "url": "javascript:alert(1)",
                "content": "Unsafe scheme.",
                "score": 0.99,
            },
        ]
    }


def test_api_key_is_required_and_not_defaulted():
    with pytest.raises(ValueError, match="TAVILY_API_KEY"):
        TavilyResearchSource(api_key="")


def test_search_uses_official_endpoint_bearer_header_and_url_validation():
    captured = {}

    def opener(request, timeout):
        assert isinstance(request, Request)
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return FakeResponse(sample_payload())

    source = TavilyResearchSource("secret-test-key", opener=opener)
    rows = source.search("home organization", max_results=3)

    assert captured["url"] == "https://api.tavily.com/search"
    assert captured["authorization"] == "Bearer secret-test-key"
    assert captured["body"]["query"] == "home organization"
    assert captured["body"]["include_answer"] is False
    assert captured["timeout"] == 12.0
    assert len(rows) == 2
    assert rows[0]["source"] == "publisher-one.example"
    assert rows[0]["relevance"] == pytest.approx(0.87)
    assert rows[0]["published_date"] == "2026-10-13"
    assert all(row["url"].startswith(("http://", "https://")) for row in rows)
    assert "secret-test-key" not in json.dumps(rows)


def test_search_rejects_invalid_arguments_before_network_use():
    called = []
    source = TavilyResearchSource("key", opener=lambda *args, **kwargs: called.append(True))
    with pytest.raises(ValueError, match="query is required"):
        source.search(" ")
    with pytest.raises(ValueError, match="max_results"):
        source.search("topic", max_results=100)
    assert called == []


def test_http_error_is_sanitized_and_does_not_leak_key():
    def opener(request, timeout):
        raise HTTPError(request.full_url, 401, "unauthorized", {}, None)

    source = TavilyResearchSource("secret-key", opener=opener)
    with pytest.raises(TavilySourceError, match="HTTP 401") as error:
        source.search("niche")
    assert "secret-key" not in str(error.value)


def test_search_rejects_malformed_provider_contract():
    source = TavilyResearchSource(
        "key", opener=lambda request, timeout: FakeResponse({"results": "wrong-type"})
    )
    with pytest.raises(TavilySourceError, match="no results list"):
        source.search("niche")


def test_trend_contract_keeps_provider_relevance_separate_from_real_world_demand():
    source = TavilyResearchSource(
        "key", opener=lambda request, timeout: FakeResponse(sample_payload())
    )
    trends = source.fetch_trends(category="home decor", limit=3)

    assert len(trends) == 2
    assert trends[0].source == "tavily"
    assert trends[0].keyword == "Small-space storage guide"
    assert trends[0].relevance_score == pytest.approx(8.7)
    assert trends[0].virality_score == 0
    assert trends[0].freshness_score == 0
    assert "https://publisher-one.example/article" in trends[0].description


def test_evidence_adapter_returns_attributed_sources_only():
    source = TavilyResearchSource(
        "key", opener=lambda request, timeout: FakeResponse(sample_payload())
    )
    evidence = source.fetch_evidence("storage", "home decor", limit=3)

    assert len(evidence) == 2
    assert evidence[0]["source"] == "publisher-one.example"
    assert evidence[0]["url"] == "https://publisher-one.example/article"
    assert evidence[0]["content"].startswith("A source-backed excerpt")


def test_timeout_range_is_bounded():
    with pytest.raises(ValueError, match="between 3 and 30"):
        TavilyResearchSource("key", timeout_seconds=120)


def test_agent_auto_configures_tavily_only_when_key_is_present(tmp_path, monkeypatch):
    from tests.agents.test_agent_01_research_discovery import build_agent

    monkeypatch.setenv("TAVILY_API_KEY", "unit-test-key")
    agent, _writes, _components = build_agent(tmp_path)
    assert agent._tavily_source is not None
    assert agent._source_status["tavily_configured_from_environment"] is True
    assert callable(agent._evidence_provider)
    assert agent._tavily_source.max_candidates_per_run == 5
