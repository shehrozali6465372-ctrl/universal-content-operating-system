"""Safe Facebook Page connection and publishing service.

This module provides the account/page connection boundary for UCOS.
Secrets are read from the environment or supplied at runtime and are never
persisted by this module.

Environment variables:
    FACEBOOK_PAGE_ID
    FACEBOOK_ACCESS_TOKEN
    FACEBOOK_APP_ID (optional)
    FACEBOOK_APP_SECRET (optional)
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher import (
    FacebookPublisher,
)
from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import PublishResult


class FacebookPagePublisher(FacebookPublisher):
    """Facebook publisher with side-effect-free authentication.

    The existing FacebookPublisher attempts a temporary POST during token
    resolution. A connection check must never create a real Facebook post,
    even temporarily, so this subclass resolves user tokens through the
    read-only /me/accounts endpoint and validates the configured Page with a
    read-only Page lookup.
    """

    def authenticate(self, credentials: Dict[str, str]) -> bool:
        self._page_id = credentials.get("page_id", "") or os.environ.get("FACEBOOK_PAGE_ID", "")
        self._access_token = credentials.get("access_token", "") or os.environ.get("FACEBOOK_ACCESS_TOKEN", "")
        self._app_id = credentials.get("app_id", "") or os.environ.get("FACEBOOK_APP_ID", "")
        self._app_secret = credentials.get("app_secret", "") or os.environ.get("FACEBOOK_APP_SECRET", "")

        if not self._page_id or not self._access_token:
            self._authenticated = False
            return False

        self._access_token = self._resolve_page_token_safe(self._access_token, self._page_id)
        if not self._access_token:
            self._authenticated = False
            return False

        page = self._api_get(
            f"/{self._page_id}",
            {"fields": "id,name,category"},
        )
        self._authenticated = bool(page and page.get("id") == self._page_id)
        return self._authenticated

    def _resolve_page_token_safe(self, token: str, page_id: str) -> str:
        """Resolve a user token to the configured Page token without POSTing."""
        if not token or not page_id:
            return ""

        # A Page token can be validated directly with a read-only Page lookup.
        page = self._api_get(
            f"/{page_id}",
            {"fields": "id", "access_token": token},
        )
        if page and page.get("id") == page_id:
            return token

        # Otherwise treat the supplied token as a user token and resolve the
        # Page token from /me/accounts. This is read-only.
        try:
            data = self._api_get(
                "/me/accounts",
                {"fields": "id,name,access_token", "access_token": token},
            ) or {}
            for page_data in data.get("data", []):
                if page_data.get("id") == page_id and page_data.get("access_token"):
                    return str(page_data["access_token"])
        except Exception:
            return ""
        return ""


class FacebookPageConnection:
    """Small service boundary for UCOS Facebook Page operations."""

    def __init__(self, publisher: Optional[FacebookPagePublisher] = None) -> None:
        self.publisher = publisher or FacebookPagePublisher()

    def connect(self, credentials: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Connect and return non-secret Page status."""
        ok = self.publisher.authenticate(credentials or {})
        info = self.publisher.get_page_info() if ok else {}
        return {
            "connected": ok,
            "platform": "facebook",
            "page_id": info.get("id", "") if info else "",
            "page_name": info.get("name", "") if info else "",
            "category": info.get("category", "") if info else "",
        }

    def status(self) -> Dict[str, Any]:
        """Return connection status without exposing credentials."""
        stats = self.publisher.get_stats()
        return {
            "connected": bool(stats.get("authenticated")),
            "platform": "facebook",
            "page_id": stats.get("page_id", ""),
            "requests": stats.get("total_requests", 0),
            "successful": stats.get("successful", 0),
            "errors": stats.get("errors", 0),
        }

    def publish(
        self,
        content: str,
        media_paths: Optional[List[str]] = None,
        content_type: str = "post",
        **kwargs: Any,
    ) -> PublishResult:
        """Publish through the connected Facebook Page."""
        return self.publisher.publish(
            content,
            media_paths=media_paths,
            content_type=content_type,
            **kwargs,
        )

    def page_info(self) -> Dict[str, Any]:
        """Return the connected Page's public Graph API information."""
        return self.publisher.get_page_info()
