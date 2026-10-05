"""Authenticated AtoZ Product Hub Content API client for UCOS machine publishing.

Production publishing is fail-closed: credentials and API endpoints must be
explicitly injected through the runtime environment. Secrets are never logged.
"""

from __future__ import annotations

import json
import os
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AtozContentApiError(RuntimeError):
    """Raised when the AtoZ Content API rejects or cannot process a request."""


class AtozContentApiClient:
    def __init__(self, auth_base_url: str, content_base_url: str, client_id: str, client_secret: str):
        self.auth_base_url = auth_base_url.rstrip("/")
        self.content_base_url = content_base_url.rstrip("/")
        self.client_id = client_id
        self.client_secret = client_secret
        self._lock = threading.Lock()
        self._access_token = ""
        self._token_expires_at = 0.0

    @classmethod
    def from_env(cls) -> "AtozContentApiClient":
        values = {
            "UCOS_ATOZ_AUTH_API_BASE_URL": os.getenv("UCOS_ATOZ_AUTH_API_BASE_URL", "").strip(),
            "UCOS_ATOZ_CONTENT_API_BASE_URL": os.getenv("UCOS_ATOZ_CONTENT_API_BASE_URL", "").strip(),
            "UCOS_ATOZ_CLIENT_ID": os.getenv("UCOS_ATOZ_CLIENT_ID", "").strip(),
            "UCOS_ATOZ_CLIENT_SECRET": os.getenv("UCOS_ATOZ_CLIENT_SECRET", "").strip(),
        }
        missing = [name for name, value in values.items() if not value]
        if missing:
            raise AtozContentApiError(
                "AtoZ Content API machine publishing is fail-closed; missing: "
                + ", ".join(missing)
            )
        return cls(
            auth_base_url=values["UCOS_ATOZ_AUTH_API_BASE_URL"],
            content_base_url=values["UCOS_ATOZ_CONTENT_API_BASE_URL"],
            client_id=values["UCOS_ATOZ_CLIENT_ID"],
            client_secret=values["UCOS_ATOZ_CLIENT_SECRET"],
        )

    @staticmethod
    def _json_request(request: Request) -> tuple[int, Any]:
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read()
                return response.status, json.loads(raw) if raw else None
        except HTTPError as exc:
            raw = exc.read()
            try:
                payload = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                payload = {}
            detail = payload.get("detail") or payload.get("error") or f"HTTP {exc.code}"
            raise AtozContentApiError(f"AtoZ Content API request failed: {detail}") from exc
        except URLError as exc:
            raise AtozContentApiError("AtoZ Content API is unavailable.") from exc
        except TimeoutError as exc:
            raise AtozContentApiError("AtoZ Content API request timed out.") from exc

    def _token(self) -> str:
        with self._lock:
            if self._access_token and time.time() < self._token_expires_at:
                return self._access_token
            body = json.dumps({"username": self.client_id, "password": self.client_secret}).encode()
            request = Request(
                f"{self.auth_base_url}/api/v1/auth/token",
                data=body,
                headers={"Content-Type": "application/json", "Accept": "application/json"},
                method="POST",
            )
            _, payload = self._json_request(request)
            token = str((payload or {}).get("access_token") or "")
            if not token:
                raise AtozContentApiError("AtoZ authentication returned no access token.")
            expires_in = int((payload or {}).get("expires_in") or 900)
            self._access_token = token
            self._token_expires_at = time.time() + max(30, expires_in - 30)
            return token

    def _admin_request(
        self,
        method: str,
        path: str,
        *,
        niche_id: str,
        payload: dict[str, Any] | None = None,
    ) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {
            "Authorization": f"Bearer {self._token()}",
            "Accept": "application/json",
            "X-Niche-Id": niche_id,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = Request(
            f"{self.content_base_url}/api/v1/admin/{path.lstrip('/')}",
            data=body,
            headers=headers,
            method=method,
        )
        _, response = self._json_request(request)
        return response

    def list_niches(self) -> list[dict[str, Any]]:
        headers = {"Authorization": f"Bearer {self._token()}", "Accept": "application/json"}
        request = Request(
            f"{self.content_base_url}/api/v1/admin/niches",
            headers=headers,
            method="GET",
        )
        _, payload = self._json_request(request)
        return list(payload or [])

    def create_article(self, niche_id: str, article: dict[str, Any]) -> dict[str, Any]:
        return dict(self._admin_request("POST", "/articles", niche_id=niche_id, payload=article))

    def lifecycle(self, niche_id: str, article_id: str, action: str) -> dict[str, Any]:
        return dict(
            self._admin_request(
                "POST",
                f"/articles/{article_id}/lifecycle",
                niche_id=niche_id,
                payload={"action": action},
            )
        )
