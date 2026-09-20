"""Discover Meta assets from the UCOS System User token without storing the token.

The token is supplied at runtime through META_ACCESS_TOKEN. Discovery is deliberately
read-only: it enumerates authorized Facebook Pages and linked Instagram Professional
accounts, then optionally provisions them into AccountRegistry.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry, AccountSpec


@dataclass(frozen=True)
class MetaAsset:
    platform: str
    asset_id: str
    display_name: str
    username: str = ""
    page_id: str = ""
    source: str = "meta"


class MetaAssetDiscovery:
    """Read-only Meta Graph discovery using one System User access token."""

    API_BASE = "https://graph.facebook.com"
    DEFAULT_VERSION = os.getenv("META_GRAPH_API_VERSION", "v26.0")

    def __init__(self, token: Optional[str] = None, *, api_version: Optional[str] = None) -> None:
        self._token = (
            os.getenv("META_ACCESS_TOKEN", "")
            if token is None
            else token
        ).strip()
        self.api_version = (api_version or self.DEFAULT_VERSION).strip().strip("/")
        if not self._token:
            raise RuntimeError("META_ACCESS_TOKEN is not configured")

    @property
    def token_configured(self) -> bool:
        return bool(self._token)

    def health(self) -> Dict[str, Any]:
        """Validate the configured System User token without returning token material."""
        try:
            data = self._get("/me", {"fields": "id,name"})
            return {
                "configured": True,
                "reachable": True,
                "valid": bool(data.get("id")),
                "asset_id": str(data.get("id") or ""),
            }
        except Exception as exc:
            return {
                "configured": True,
                "reachable": False,
                "valid": False,
                "error": str(exc),
            }

    def discover(self) -> Dict[str, List[MetaAsset]]:
        pages = self._discover_pages()
        instagram: Dict[str, MetaAsset] = {}
        for page in pages:
            page_id = page.asset_id
            linked = page.username
            ig = self._page_instagram_account(page_id)
            if ig:
                instagram[ig.asset_id] = ig
        return {"facebook": pages, "instagram": list(instagram.values())}

    def provision(self, registry: AccountRegistry, *, default_niche: str = "general") -> Dict[str, Any]:
        discovered = self.discover()
        provisioned: List[Dict[str, Any]] = []
        for asset in discovered["facebook"]:
            account_id = f"facebook:{asset.asset_id}"
            spec = AccountSpec(
                account_id=account_id,
                platform="facebook",
                niche=default_niche,
                display_name=asset.display_name,
                credentials_ref="META_ACCESS_TOKEN",
                capabilities=["post", "photo", "video", "comments", "insights"],
                constraints={"meta_asset_id": asset.asset_id, "credential_mode": "system_user"},
            )
            registry.register(spec)
            provisioned.append({"account_id": account_id, "platform": "facebook", "asset_id": asset.asset_id, "display_name": asset.display_name})
        for asset in discovered["instagram"]:
            account_id = f"instagram:{asset.asset_id}"
            spec = AccountSpec(
                account_id=account_id,
                platform="instagram",
                niche=default_niche,
                display_name=asset.display_name,
                audience=asset.username,
                credentials_ref="META_ACCESS_TOKEN",
                capabilities=["post", "photo", "video", "reel", "carousel", "comments", "insights"],
                constraints={"meta_asset_id": asset.asset_id, "page_id": asset.page_id, "credential_mode": "system_user"},
            )
            registry.register(spec)
            provisioned.append({"account_id": account_id, "platform": "instagram", "asset_id": asset.asset_id, "username": asset.username, "page_id": asset.page_id})
        return {
            "facebook_discovered": len(discovered["facebook"]),
            "instagram_discovered": len(discovered["instagram"]),
            "provisioned": provisioned,
        }

    def _discover_pages(self) -> List[MetaAsset]:
        fields = "id,name,access_token,instagram_business_account{id,username,name}"
        pages: List[MetaAsset] = []
        for item in self._paged_get("/me/accounts", {"fields": fields, "limit": 100}):
            asset_id = str(item.get("id") or "").strip()
            if not asset_id:
                continue
            pages.append(MetaAsset("facebook", asset_id, str(item.get("name") or asset_id)))
        if pages:
            return pages

        business_id = os.getenv("META_BUSINESS_ID", "").strip()
        if business_id:
            return [
                MetaAsset("facebook", str(item["id"]), str(item.get("name") or item["id"]))
                for item in self._paged_get(
                    f"/{business_id}/owned_pages", {"fields": "id,name", "limit": 100}
                )
                if item.get("id")
            ]
        return []

    def _paged_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Follow Graph API paging cursors without ever exposing the access token."""
        query = dict(params or {})
        items: List[Dict[str, Any]] = []
        seen_urls = set()
        while True:
            data = self._get(path, query)
            batch = data.get("data") or []
            if isinstance(batch, list):
                items.extend(item for item in batch if isinstance(item, dict))
            paging = data.get("paging") or {}
            next_url = str(paging.get("next") or "").strip()
            if not next_url or next_url in seen_urls:
                break
            seen_urls.add(next_url)
            parsed = urllib.parse.urlparse(next_url)
            if parsed.scheme != "https" or parsed.netloc != "graph.facebook.com":
                raise RuntimeError("Meta API returned an unexpected paging URL")
            path = parsed.path
            query = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
            query.pop("access_token", None)
        return items

    def _page_instagram_account(self, page_id: str) -> Optional[MetaAsset]:
        try:
            data = self._get(f"/{page_id}", {"fields": "id,name,instagram_business_account{id,username,name}"})
        except RuntimeError:
            return None
        linked = data.get("instagram_business_account") or {}
        asset_id = str(linked.get("id") or "").strip()
        if not asset_id:
            return None
        return MetaAsset(
            "instagram",
            asset_id,
            str(linked.get("name") or linked.get("username") or asset_id),
            str(linked.get("username") or ""),
            page_id=page_id,
        )

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        query = dict(params or {})
        query["access_token"] = self._token
        url = f"{self.API_BASE}/{self.api_version}{path}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            try:
                body = json.loads(exc.read().decode("utf-8", "replace"))
                message = body.get("error", {}).get("message") or str(body)
            except Exception:
                message = f"HTTP {exc.code}"
            raise RuntimeError(f"Meta API error: {message}") from exc
        except Exception as exc:
            raise RuntimeError(f"Meta API request failed: {exc}") from exc
        if isinstance(payload, dict) and payload.get("error"):
            raise RuntimeError(f"Meta API error: {payload['error']}")
        return payload if isinstance(payload, dict) else {}
