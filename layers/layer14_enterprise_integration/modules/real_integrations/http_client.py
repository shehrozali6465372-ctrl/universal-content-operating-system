"""Minimal dependency-free HTTPS client with retry/timeout/error boundaries."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen


class IntegrationError(RuntimeError):
    """Base error raised by external integration boundaries."""


class IntegrationConfigurationError(IntegrationError):
    """Raised when required provider credentials/config are missing."""


@dataclass(frozen=True)
class HTTPResponse:
    status: int
    data: Any
    headers: Mapping[str, str]


class HTTPClient:
    """HTTP transport with bounded retries and production TLS enforcement."""

    def __init__(self, timeout: float = 20.0, max_retries: int = 3) -> None:
        self.timeout = float(timeout)
        self.max_retries = max(1, int(max_retries))

    @staticmethod
    def _validate_url(url: str) -> None:
        parsed = urlsplit(url)
        if parsed.scheme not in {"https", "http"} or not parsed.netloc:
            raise IntegrationError("provider URL must be an absolute HTTP(S) URL")
        production = os.getenv("APP_ENV", "development").lower() in {"production", "prod"}
        local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
        if production and parsed.scheme != "https" and not local:
            raise IntegrationError("HTTP is disabled for non-local providers in production")
        if parsed.username or parsed.password:
            raise IntegrationError("provider URL must not embed credentials")

    @staticmethod
    def _decode(body: bytes, content_type: str) -> Any:
        text = body.decode("utf-8", errors="replace")
        if "json" in (content_type or "").lower() or text.lstrip().startswith(("{", "[")):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return text

    def request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        json_body: Any = None,
        accepted_statuses: tuple[int, ...] = (200, 201, 202, 204),
    ) -> HTTPResponse:
        self._validate_url(url)
        if params:
            parsed = urlsplit(url)
            query = urlencode({k: v for k, v in params.items() if v is not None}, doseq=True)
            url = urlunsplit((parsed.scheme, parsed.netloc, parsed.path, query, parsed.fragment))
        body = None
        request_headers = {"Accept": "application/json", **dict(headers or {})}
        if json_body is not None:
            body = json.dumps(json_body, separators=(",", ":")).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                req = Request(url, data=body, headers=request_headers, method=method.upper())
                with urlopen(req, timeout=self.timeout) as response:
                    raw = response.read()
                    decoded = self._decode(raw, response.headers.get("Content-Type", ""))
                    if response.status not in accepted_statuses:
                        raise IntegrationError(f"provider returned HTTP {response.status}")
                    return HTTPResponse(response.status, decoded, dict(response.headers.items()))
            except HTTPError as exc:
                raw = exc.read()
                decoded = self._decode(raw, exc.headers.get("Content-Type", ""))
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if not retryable or attempt + 1 >= self.max_retries:
                    raise IntegrationError(f"provider returned HTTP {exc.code}: {decoded}") from exc
                last_error = exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt + 1 >= self.max_retries:
                    raise IntegrationError(f"provider transport failed: {exc}") from exc
            time.sleep(min(2.0 ** attempt, 8.0))
        raise IntegrationError(f"provider request failed: {last_error}") from last_error
