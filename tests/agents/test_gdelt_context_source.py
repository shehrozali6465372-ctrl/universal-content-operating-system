"""Contract tests for the real GDELT Context API adapter."""
from __future__ import annotations

import io
import json
from urllib.parse import parse_qs, urlsplit

import pytest

from agents.agent_01_research_discovery.gdelt_context_source import (
    GDELTContextResearchSource,
    GDELTSourceError,
)


class Response:
    status = 200

    def __init__(self, body):
        self.body = json.dumps(body).encode()

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return self.body


def test_search_uses_public_https_endpoint_and_requires_real_sentence():
    seen = []

    def opener(request, timeout):
        seen.append((request, timeout))
        return Response({"sentences": [
            {"title": "Headline with evidence", "url": "https://publisher.example/a",
             "domain": "publisher.example", "context": "A real sentence returned by the Context API."},
            {"title": "Headline only", "url": "https://other.example/b", "domain": "other.example"},
            {"title": "Bad URL", "url": "javascript:alert(1)", "sentence": "not accepted"},
        ]})

    source = GDELTContextResearchSource(opener=opener)
    rows = source.search("home decor", max_results=3)

    assert len(rows) == 1
    assert rows[0]["source"] == "publisher.example"
    assert rows[0]["content"] == "A real sentence returned by the Context API."
    assert urlsplit(seen[0][0].full_url).scheme == "https"
    assert urlsplit(seen[0][0].full_url).hostname == "api.gdeltproject.org"
    assert parse_qs(urlsplit(seen[0][0].full_url).query)["format"] == ["json"]
    assert parse_qs(urlsplit(seen[0][0].full_url).query)["timespan"] == ["72h"]
    assert seen[0][1] == 12.0
    assert source.request_count == 1


def test_non_json_quota_error_fails_closed():
    class BadResponse(Response):
        def __init__(self):
            self.body = b"rate limit exceeded"

    source = GDELTContextResearchSource(opener=lambda *_args, **_kwargs: BadResponse())
    with pytest.raises(GDELTSourceError, match="invalid JSON"):
        source.search("home decor")


def test_empty_query_and_invalid_limits_are_rejected():
    source = GDELTContextResearchSource(opener=lambda *_args, **_kwargs: Response({"results": []}))
    with pytest.raises(ValueError):
        source.search("")
    with pytest.raises(ValueError):
        source.search("decor", max_results=0)
