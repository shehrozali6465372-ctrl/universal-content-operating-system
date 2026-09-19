"""Runtime credentials for Meta assets backed by one System User token."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry


class MetaCredentialProvider:
    """Derive Page/Instagram credentials from META_ACCESS_TOKEN without persisting child tokens."""

    API_BASE = "https://graph.facebook.com"
    API_VERSION = os.getenv("META_GRAPH_API_VERSION", "v26.0")

    def __init__(self, token: Optional[str] = None, *, api_version: Optional[str] = None) -> None:
        self.token = (token or os.getenv("META_ACCESS_TOKEN", "")).strip()
        self.api_version = (api_version or self.API_VERSION).strip().strip("/")
        if not self.token:
            raise RuntimeError("META_ACCESS_TOKEN is not configured")

    def credentials_for(self, platform: str, account_id: str) -> Dict[str, str]:
        account = AccountRegistry().get(account_id)
        if account is None:
            raise LookupError(f"account {account_id!r} is not registered")
        if account.platform != platform:
            raise ValueError(f"account {account_id!r} is registered for {account.platform}, not {platform}")
        asset_id = str(account.constraints.get("meta_asset_id") or "").strip()
        page_id = str(account.constraints.get("page_id") or "").strip()
        if platform == "facebook":
            page_id = asset_id or page_id
            if not page_id:
                raise RuntimeError(f"Meta Facebook account {account_id!r} has no page asset id")
            page = self._find_page(page_id)
            token = str(page.get("access_token") or "").strip()
            if not token:
                raise RuntimeError(f"Meta did not return a Page Access Token for {page_id}")
            return {"page_id": page_id, "access_token": token}
        if platform == "instagram":
            ig_id = asset_id
            if not ig_id:
                raise RuntimeError(f"Meta Instagram account {account_id!r} has no Instagram asset id")
            for page in self._pages():
                linked = page.get("instagram_business_account") or {}
                if str(linked.get("id") or "") == ig_id:
                    token = str(page.get("access_token") or "").strip()
                    if not token:
                        raise RuntimeError(f"Meta did not return a Page Access Token for Instagram account {ig_id}")
                    return {"account_id": ig_id, "access_token": token}
            raise RuntimeError(f"Instagram account {ig_id} is not linked to an authorized Meta Page")
        raise ValueError(f"Meta credentials are not supported for platform {platform!r}")

    def _find_page(self, page_id: str) -> Dict[str, Any]:
        for page in self._pages():
            if str(page.get("id") or "") == page_id:
                return page
        raise RuntimeError(f"Meta Page {page_id} is not authorized for this System User")

    def _pages(self):
        data = self._get("/me/accounts", {
            "fields": "id,name,access_token,tasks,instagram_business_account{id,username,name}",
            "limit": 100,
        })
        return list(data.get("data") or [])

    def _get(self, path: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = dict(params)
        query["access_token"] = self.token
        url = f"{self.API_BASE}/{self.api_version}{path}?{urllib.parse.urlencode(query)}"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8", "replace"))
                message = payload.get("error", {}).get("message") or str(payload)
            except Exception:
                message = f"HTTP {exc.code}"
            raise RuntimeError(f"Meta API error: {message}") from exc
        except Exception as exc:
            raise RuntimeError(f"Meta API request failed: {exc}") from exc
        if payload.get("error"):
            raise RuntimeError(f"Meta API error: {payload['error']}")
        return payload
