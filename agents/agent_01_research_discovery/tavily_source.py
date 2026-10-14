"""Tavily-backed live web source for UCOS Agent 01.

API contract is based on Tavily's documented POST /search endpoint:
https://docs.tavily.com/documentation/api-reference/endpoint/search

Network calls use the Python standard library. API keys are read only from the
environment and are never placed in request bodies, reports, or exception text.
"""
from __future__ import annotations

import json
import math
import os
from collections.abc import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from typing import Any

from layers.layer02_research.modules.trend_discovery.trend_entry import TrendEntry


_ENDPOINT = "https://api.tavily.com/search"
_MAX_RESULTS = 10
_MAX_QUERY_LENGTH = 1000
_MAX_CONTENT_LENGTH = 12000


class TavilySourceError(RuntimeError):
    """Safe, sanitized source error; never carries a credential or response body."""


class TavilyResearchSource:
    """Search real web pages and convert them into UCOS trend/evidence contracts."""

    name = "tavily"
    max_candidates_per_run = 5

    def __init__(
        self,
        api_key: str | None = None,
        *,
        timeout_seconds: float = 12.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self._api_key = str(api_key if api_key is not None else os.environ.get("TAVILY_API_KEY", "")).strip()
        if not self._api_key:
            raise ValueError("TAVILY_API_KEY is required to configure Tavily research")
        if not math.isfinite(float(timeout_seconds)) or not 3 <= float(timeout_seconds) <= 30:
            raise ValueError("timeout_seconds must be between 3 and 30")
        self.timeout_seconds = float(timeout_seconds)
        self._opener = opener or urlopen
        self.request_count = 0

    @classmethod
    def from_env(cls, *, opener: Callable[..., Any] | None = None) -> "TavilyResearchSource":
        raw_timeout = os.environ.get("UCOS_TAVILY_TIMEOUT_SECONDS", "12")
        try:
            timeout = float(raw_timeout)
        except (TypeError, ValueError) as exc:
            raise ValueError("UCOS_TAVILY_TIMEOUT_SECONDS must be numeric") from exc
        return cls(timeout_seconds=timeout, opener=opener)

    @staticmethod
    def _valid_url(value: Any) -> str:
        raw = str(value or "").strip()
        if len(raw) > 2048:
            return ""
        try:
            parts = urlsplit(raw)
            if parts.scheme.lower() in {"http", "https"} and parts.hostname:
                return raw
        except ValueError:
            return ""
        return ""

    @staticmethod
    def _text(value: Any, limit: int) -> str:
        return str(value or "").strip()[:limit]

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        """Return normalized, URL-backed result records from Tavily Search."""
        query = self._text(query, _MAX_QUERY_LENGTH)
        if not query:
            raise ValueError("query is required")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= _MAX_RESULTS:
            raise ValueError(f"max_results must be between 1 and {_MAX_RESULTS}")

        payload = {
            "query": query,
            "topic": "general",
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": False,
            "include_raw_content": False,
            "include_images": False,
        }
        request = Request(
            _ENDPOINT,
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        self.request_count += 1
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(2_000_000)
            if status < 200 or status >= 300:
                raise TavilySourceError(f"Tavily Search returned HTTP {status}")
            decoded = json.loads(raw.decode("utf-8"))
        except TavilySourceError:
            raise
        except HTTPError as exc:
            raise TavilySourceError(f"Tavily Search returned HTTP {int(exc.code)}") from None
        except URLError as exc:
            reason = getattr(exc, "reason", None)
            if isinstance(reason, TimeoutError):
                raise TavilySourceError("Tavily Search timed out") from None
            raise TavilySourceError("Tavily Search network request failed") from None
        except TimeoutError:
            raise TavilySourceError("Tavily Search timed out") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise TavilySourceError("Tavily Search returned invalid JSON") from None
        except OSError:
            raise TavilySourceError("Tavily Search network request failed") from None
        except Exception as exc:
            # Do not relay arbitrary exception strings; some HTTP stacks echo headers.
            raise TavilySourceError(f"Tavily Search failed ({type(exc).__name__})") from None

        results = decoded.get("results") if isinstance(decoded, Mapping) else None
        if not isinstance(results, list):
            raise TavilySourceError("Tavily Search response has no results list")

        normalized: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for item in results[:max_results]:
            if not isinstance(item, Mapping):
                continue
            url = self._valid_url(item.get("url"))
            title = self._text(item.get("title"), 300)
            content = self._text(item.get("content") or item.get("raw_content") or item.get("snippet"), _MAX_CONTENT_LENGTH)
            if not url or not title or not content or url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                raw_score = float(item.get("score", 0.0))
                relevance = max(0.0, min(1.0, raw_score)) if math.isfinite(raw_score) else 0.0
            except (TypeError, ValueError):
                relevance = 0.0
            host = (urlsplit(url).hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            normalized.append({
                "title": title,
                "url": url,
                "source": host or "unknown",
                "content": content,
                "relevance": relevance,
                "published_date": self._text(item.get("published_date"), 64),
            })
        return normalized

    def fetch_trends(self, *, category: str = "general", limit: int = 5) -> list[TrendEntry]:
        """Provide live search-discovered topic candidates to Layer 02's trend contract."""
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        topic = self._text(category, 120) or "general"
        results = self.search(
            f"current content trends, questions, and underserved topic ideas in {topic}",
            max_results=min(limit, self.max_candidates_per_run),
        )
        trends: list[TrendEntry] = []
        for item in results:
            score = round(item["relevance"] * 10.0, 2)
            trends.append(TrendEntry(
                keyword=item["title"],
                category=topic,
                source=self.name,
                relevance_score=score,
                description=f"{item['content'][:1200]}\nSource: {item['url']}",
                related_keywords=[],
                tags=["live-web-search", "source-attributed"],
                expires_in_hours=24,
            ))
        return trends

    def fetch_evidence(self, topic: str, niche: str, limit: int = 5) -> list[dict[str, str]]:
        """Fetch independent, traceable source material for one candidate topic."""
        if not str(topic or "").strip():
            return []
        bounded = max(1, min(int(limit), _MAX_RESULTS))
        results = self.search(
            f"{self._text(topic, 350)}; {self._text(niche, 120)}; factual background and audience questions",
            max_results=bounded,
        )
        return [
            {
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "content": item["content"],
                "published_at": item["published_date"],
            }
            for item in results
        ]
