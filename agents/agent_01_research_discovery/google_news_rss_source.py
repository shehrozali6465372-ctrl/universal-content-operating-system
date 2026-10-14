"""Google News RSS real-source adapter for UCOS Agent 01.

Uses the public Google News RSS endpoint and resolves each article redirect to
the original publisher over HTTPS. Items pointing only to Google News are
rejected, so source independence uses actual publisher hosts, not one shared
news.google.com redirect hostname.
"""
from __future__ import annotations

import html
import ipaddress
import re
import xml.etree.ElementTree as ET
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener


_FEED_ENDPOINT = "https://news.google.com/rss/search"
_USER_AGENT = "UCOSAgent01Research/1.0"
_MAX_QUERY_LENGTH = 500
_MAX_CONTENT_LENGTH = 6000
_MAX_RESULTS = 10
_GOOGLE_HOSTS = {
    "google.com", "www.google.com", "news.google.com",
    "news.googleusercontent.com",
}


class GoogleNewsSourceError(RuntimeError):
    """Sanitized real-provider error."""


def _is_safe_https_url(value: str, *, permit_google: bool = False) -> bool:
    try:
        parts = urlsplit(str(value or "").strip())
        host = (parts.hostname or "").rstrip(".").lower()
        if parts.scheme.lower() != "https" or not host or parts.username or parts.password:
            return False
        if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
            return False
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            address = None
        if address is not None and (
            not address.is_global or address.is_multicast or address.is_unspecified
        ):
            return False
        if not permit_google and (
            host in _GOOGLE_HOSTS
            or host.endswith(".google.com")
            or host.endswith(".googleusercontent.com")
        ):
            return False
        return True
    except (TypeError, ValueError):
        return False


class _SafeHTTPSRedirectHandler(HTTPRedirectHandler):
    """Follow HTTPS redirects only; reject local/private IP-literal targets."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _is_safe_https_url(newurl, permit_google=True):
            raise GoogleNewsSourceError("Google News article redirected to an unsafe URL")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _strip_html(value: Any, limit: int) -> str:
    raw = html.unescape(str(value or ""))
    raw = re.sub(r"<[^>]{0,1000}>", " ", raw)
    return re.sub(r"\s+", " ", raw).strip()[:limit]


class GoogleNewsRSSResearchSource:
    """Real public RSS search that returns source-attributed publisher article URLs."""

    name = "google_news_rss"
    max_candidates_per_run = 5

    def __init__(self, *, timeout_seconds: float = 12.0, opener: Any = None) -> None:
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not 3 <= timeout_seconds <= 30:
            raise ValueError("timeout_seconds must be between 3 and 30")
        self.timeout_seconds = float(timeout_seconds)
        self._opener = opener or build_opener(_SafeHTTPSRedirectHandler())
        self.request_count = 0

    @staticmethod
    def _host(url: str) -> str:
        host = (urlsplit(url).hostname or "").lower()
        return host[4:] if host.startswith("www.") else host

    def _resolve_publisher_url(self, url: str) -> str:
        if not _is_safe_https_url(url, permit_google=True):
            return ""
        parts = urlsplit(url)
        host = (parts.hostname or "").lower()
        if not (
            host == "news.google.com"
            or host.endswith(".google.com")
            or host.endswith(".googleusercontent.com")
        ):
            return url if _is_safe_https_url(url) else ""
        request = Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        })
        self.request_count += 1
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                final_url = str(response.geturl() or "")
                if status < 200 or status >= 400 or not _is_safe_https_url(final_url):
                    return ""
                return final_url
        except GoogleNewsSourceError:
            raise
        except (HTTPError, URLError, TimeoutError, OSError, ValueError):
            return ""

    def search(self, query: str, *, max_results: int = 5) -> list[dict[str, Any]]:
        query = _strip_html(query, _MAX_QUERY_LENGTH)
        if not query:
            raise ValueError("query is required")
        if isinstance(max_results, bool) or not isinstance(max_results, int) or not 1 <= max_results <= _MAX_RESULTS:
            raise ValueError(f"max_results must be between 1 and {_MAX_RESULTS}")
        params = {"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"}
        url = _FEED_ENDPOINT + "?" + urlencode(params)
        request = Request(url, headers={
            "User-Agent": _USER_AGENT,
            "Accept": "application/rss+xml,application/xml,text/xml,*/*;q=0.8",
        })
        self.request_count += 1
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                status = int(getattr(response, "status", 200))
                raw = response.read(2_000_000)
            if status < 200 or status >= 300:
                raise GoogleNewsSourceError(f"Google News RSS returned HTTP {status}")
            root = ET.fromstring(raw)
        except GoogleNewsSourceError:
            raise
        except HTTPError as exc:
            raise GoogleNewsSourceError(f"Google News RSS returned HTTP {int(exc.code)}") from None
        except URLError as exc:
            kind = "timed out" if isinstance(getattr(exc, "reason", None), TimeoutError) else "network request failed"
            raise GoogleNewsSourceError(f"Google News RSS {kind}") from None
        except TimeoutError:
            raise GoogleNewsSourceError("Google News RSS timed out") from None
        except (ET.ParseError, UnicodeDecodeError):
            raise GoogleNewsSourceError("Google News RSS returned invalid XML") from None
        except OSError:
            raise GoogleNewsSourceError("Google News RSS network request failed") from None

        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
        normalized: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        seen_hosts: set[str] = set()
        for item in items:
            if len(normalized) >= max_results:
                break
            title = _strip_html(item.findtext("title"), 300)
            link = _strip_html(item.findtext("link"), 2048)
            description = _strip_html(item.findtext("description"), _MAX_CONTENT_LENGTH)
            source_node = item.find("source")
            publisher = _strip_html(source_node.text if source_node is not None else "", 200)
            published = _strip_html(item.findtext("pubDate"), 64)
            if not title or not description or not link:
                continue
            article_url = self._resolve_publisher_url(link)
            if not article_url or article_url in seen_urls:
                continue
            host = self._host(article_url)
            if not host or host in seen_hosts:
                continue
            seen_urls.add(article_url)
            seen_hosts.add(host)
            normalized.append({
                "title": title,
                "url": article_url,
                "source": host or publisher or "unknown",
                "publisher": publisher,
                "content": description,
                "relevance": None,
                "published_date": published,
            })
        return normalized

    def discover_candidates(self, account_id: str, niche: str, limit: int) -> list[dict[str, Any]]:
        if not str(account_id or "").strip():
            raise ValueError("account_id is required")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        results = self.search(
            f"current audience questions, new developments, and helpful topic ideas in {_strip_html(niche, 120) or 'general'}",
            max_results=min(limit, self.max_candidates_per_run),
        )
        return [{
            "topic": item["title"],
            "description": item["content"][:1600],
            "source_relevance_score": None,
            "evidence": [{
                "source": item["source"],
                "title": item["title"],
                "url": item["url"],
                "content": item["content"],
                "published_at": item["published_date"],
            }],
        } for item in results]

    def fetch_evidence(self, topic: str, niche: str, limit: int = 5) -> list[dict[str, str]]:
        if not str(topic or "").strip():
            return []
        bounded = max(1, min(int(limit), _MAX_RESULTS))
        results = self.search(
            f"{_strip_html(topic, 250)}; {_strip_html(niche, 120)}; reporting, expert guidance, and factual background",
            max_results=bounded,
        )
        return [{
            "source": item["source"],
            "title": item["title"],
            "url": item["url"],
            "content": item["content"],
            "published_at": item["published_date"],
        } for item in results]
