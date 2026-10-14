"""Keyless GDELT Context API adapter for UCOS Agent 01.

Uses the public GDELT Context 2.0 API to return real article-linked matching
sentences. It is a fallback for environments without a Tavily key, not a
replacement for claim verification. The worker requires two independent source
hosts before handing a topic to AG06.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable, Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen
from typing import Any

_ENDPOINT = "https://api.gdeltproject.org/api/v2/context/context"
_MAX_RESULTS = 10
_MAX_QUERY_LENGTH = 500


class GDELTSourceError(RuntimeError):
    """Sanitized public-provider error."""


class GDELTContextResearchSource:
    name = "gdelt_context"
    max_candidates_per_run = 3

    def __init__(self, *, timeout_seconds: float = 12.0, opener: Callable[..., Any] | None = None,
                 min_interval_seconds: float = 5.0) -> None:
        if not 3 <= float(timeout_seconds) <= 30:
            raise ValueError("timeout_seconds must be between 3 and 30")
        if not 5 <= float(min_interval_seconds) <= 60:
            raise ValueError("min_interval_seconds must be between 5 and 60")
        self.timeout_seconds = float(timeout_seconds)
        self.min_interval_seconds = float(min_interval_seconds)
        self._opener = opener or urlopen
        self._last_request_at = 0.0
        self.request_count = 0

    @staticmethod
    def _valid_url(value: Any) -> str:
        raw = str(value or "").strip()
        try:
            parts = urlsplit(raw)
            if parts.scheme.lower() in {"http", "https"} and parts.hostname and len(raw) <= 2048:
                return raw
        except ValueError:
            pass
        return ""

    @staticmethod
    def _text(value: Any, limit: int) -> str:
        return str(value or "").strip()[:limit]

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        query = self._text(query, _MAX_QUERY_LENGTH)
        if not query:
            raise ValueError("query is required")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= _MAX_RESULTS:
            raise ValueError(f"max_results must be between 1 and {_MAX_RESULTS}")

        wait = self.min_interval_seconds - (time.monotonic() - self._last_request_at)
        if self._last_request_at and wait > 0:
            time.sleep(wait)
        params = urlencode({
            "query": query, "mode": "artlist", "format": "json",
            "maxrecords": max_results, "timespan": "72h",
        })
        request = Request(
            f"{_ENDPOINT}?{params}",
            headers={"Accept": "application/json", "User-Agent": "UCOS-Agent01/1.0 (research discovery)"},
            method="GET",
        )
        self._last_request_at = time.monotonic()
        self.request_count += 1
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(1_000_000)
            if status < 200 or status >= 300:
                raise GDELTSourceError(f"GDELT Context returned HTTP {status}")
            decoded = json.loads(raw.decode("utf-8"))
        except GDELTSourceError:
            raise
        except HTTPError as exc:
            raise GDELTSourceError(f"GDELT Context returned HTTP {int(exc.code)}") from None
        except URLError as exc:
            if isinstance(getattr(exc, "reason", None), TimeoutError):
                raise GDELTSourceError("GDELT Context timed out") from None
            raise GDELTSourceError("GDELT Context network request failed") from None
        except TimeoutError:
            raise GDELTSourceError("GDELT Context timed out") from None
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GDELTSourceError("GDELT Context returned invalid JSON") from None
        except OSError:
            raise GDELTSourceError("GDELT Context network request failed") from None
        except Exception as exc:
            raise GDELTSourceError(f"GDELT Context failed ({type(exc).__name__})") from None

        if not isinstance(decoded, Mapping):
            raise GDELTSourceError("GDELT Context response has invalid shape")
        rows = decoded.get("sentences") or decoded.get("results") or decoded.get("articles")
        if not isinstance(rows, list):
            # GDELT sometimes returns HTTP 200 with plain-text quota/query errors.
            raise GDELTSourceError("GDELT Context response has no results list")
        normalized = []
        seen = set()
        for item in rows[:max_results]:
            if not isinstance(item, Mapping):
                continue
            url = self._valid_url(item.get("url") or item.get("url_mobile"))
            title = self._text(item.get("title") or item.get("name"), 300)
            # Do not synthesize article content from titles. Require a sentence/snippet
            # actually returned by the source API before it can count as evidence.
            content = self._text(
                item.get("sentence") or item.get("context") or item.get("snippet") or item.get("content") or item.get("description"), 4000
            )
            if not url or not title or not content or url in seen:
                continue
            seen.add(url)
            host = (urlsplit(url).hostname or "").lower()
            if host.startswith("www."):
                host = host[4:]
            normalized.append({
                "title": title, "url": url, "source": host or "unknown",
                "content": content, "relevance": None,
                "published_date": self._text(item.get("seendate") or item.get("published_at"), 64),
            })
        return normalized

    @staticmethod
    def _or_query(terms: list[str]) -> str:
        clean: list[str] = []
        seen: set[str] = set()
        for term in terms:
            value = " ".join(str(term or "").replace('"', "").split())[:180]
            key = value.casefold()
            if value and key not in seen:
                seen.add(key)
                clean.append(f'"{value}"')
        return "(" + " OR ".join(clean[:12]) + ")"

    def _niche_search_terms(self, niche: str) -> list[str]:
        value = self._text(niche, 120)
        terms = [value, f"{value} trends", f"{value} ideas", f"{value} tips", f"{value} guide"]
        normalized = value.casefold().replace("-", " ")
        if "home decor" in normalized or "home decoration" in normalized:
            terms.extend([
                "interior design", "home styling", "room makeover",
                "decor trends", "decor ideas", "home design",
            ])
        elif any(word in normalized for word in ("skin care", "skincare", "beauty")):
            terms.extend(["skin care routine", "beauty trends", "skin health", "makeup tips"])
        elif any(word in normalized for word in ("technology", "tech", "artificial intelligence", "ai")):
            terms.extend(["technology trends", "artificial intelligence", "digital tools", "tech news"])
        return terms

    def discover_candidates(self, account_id: str, niche: str, limit: int) -> list[dict[str, Any]]:
        if not str(account_id or "").strip():
            raise ValueError("account_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        results = self.search(
            self._or_query(self._niche_search_terms(niche)),
            max_results=min(limit, self.max_candidates_per_run),
        )
        return [{
            "topic": item["title"],
            "description": item["content"][:1600],
            "evidence": [{
                "source": item["source"], "title": item["title"], "url": item["url"],
                "content": item["content"], "published_at": item["published_date"],
            }],
        } for item in results]

    def fetch_evidence(self, topic: str, niche: str, limit: int = 5) -> list[dict[str, str]]:
        """Gather real sentence-level evidence using bounded query diversification.

        A single broad OR query often returns multiple snippets from one publisher,
        which cannot satisfy AG01's independent-source requirement. Search the exact
        topic first, then distinct topic phrases, then niche-related phrases; merge
        only real article-linked sentences and stop once two publisher hosts exist.
        The shared search() method enforces the provider's five-second request gap.
        """
        topic_value = self._text(topic, 220)
        if not topic_value:
            return []
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")

        words = [
            word for word in __import__("re").findall(r"[A-Za-z][A-Za-z0-9'-]*", topic_value)
            if len(word) > 2 and word.casefold() not in {
                "the", "and", "for", "with", "from", "into", "your", "best",
                "top", "how", "why", "what", "when", "where", "this", "that",
            }
        ]
        phrases: list[str] = []
        for index in range(len(words) - 1):
            phrase = " ".join(words[index:index + 2])
            if phrase.casefold() != topic_value.casefold() and phrase.casefold() not in {
                item.casefold() for item in phrases
            }:
                phrases.append(phrase)
        query_variants = [
            self._or_query([topic_value]),
            self._or_query(phrases[:10] or [topic_value]),
            self._or_query(phrases[2:12] + self._niche_search_terms(niche)[:4] or [topic_value]),
        ]

        results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_hosts: set[str] = set()
        for query in query_variants:
            if len(results) >= min(limit, _MAX_RESULTS) and len(seen_hosts) >= 2:
                break
            try:
                rows = self.search(query, max_results=max(2, min(limit, _MAX_RESULTS)))
            except GDELTSourceError:
                # A failed query cannot be treated as evidence. Continue to the
                # next bounded query variant; if all fail, the agent will hold.
                continue
            for item in rows:
                url = item["url"]
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                host = (urlsplit(url).hostname or "").lower()
                if host.startswith("www."):
                    host = host[4:]
                if not host:
                    continue
                seen_hosts.add(host)
                results.append(item)
                if len(results) >= min(limit, _MAX_RESULTS):
                    break

        return [{
            "source": item["source"], "title": item["title"], "url": item["url"],
            "content": item["content"], "published_at": item["published_date"],
        } for item in results[:min(limit, _MAX_RESULTS)]]
