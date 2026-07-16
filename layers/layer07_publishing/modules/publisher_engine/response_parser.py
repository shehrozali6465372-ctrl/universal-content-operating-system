"""Response Parser — Parse and normalize platform API responses."""
from __future__ import annotations
from typing import Any, Dict, List


class ResponseParser:
    """Parse raw API responses into normalized result objects."""

    KNOWN_ERROR_PATTERNS = {
        "rate_limit": ["rate limit", "too many requests", "throttled"],
        "auth_error": ["unauthorized", "invalid token", "expired", "access denied"],
        "not_found": ["not found", "does not exist", "deleted"],
        "content_error": ["invalid content", "spam", "violates policy"],
        "network_error": ["timeout", "connection", "network", "unreachable"],
    }

    def parse_publish_response(
        self,
        raw_response: Dict[str, Any],
        platform: str = "",
    ) -> Dict[str, Any]:
        post_id = self.extract_post_id(raw_response, platform)
        url = self.extract_url(raw_response, platform)
        media_ids = self.extract_media_ids(raw_response)
        error = self.extract_error(raw_response)

        return {
            "success": not error and bool(post_id),
            "post_id": post_id,
            "url": url,
            "media_ids": media_ids,
            "error": error,
            "platform": platform,
            "raw_keys": list(raw_response.keys()),
        }

    def extract_post_id(self, response: Dict[str, Any], platform: str = "") -> str:
        id_fields = ["id", "post_id", "postId", "postId", "message_id"]
        for field in id_fields:
            val = response.get(field)
            if val:
                return str(val)
        nested = response.get("data", {})
        if isinstance(nested, dict):
            for field in id_fields:
                val = nested.get(field)
                if val:
                    return str(val)
        return ""

    def extract_url(self, response: Dict[str, Any], platform: str = "") -> str:
        url_fields = ["url", "permalink", "link", "post_url", "postUrl"]
        for field in url_fields:
            val = response.get(field)
            if val:
                return str(val)
        nested = response.get("data", {})
        if isinstance(nested, dict):
            for field in url_fields:
                val = nested.get(field)
                if val:
                    return str(val)
        return ""

    def extract_media_ids(self, response: Dict[str, Any]) -> List[str]:
        ids: List[str] = []
        media = response.get("media_ids", response.get("mediaIds", []))
        if isinstance(media, list):
            ids = [str(m) for m in media]
        nested = response.get("data", {})
        if isinstance(nested, dict):
            media2 = nested.get("media_ids", [])
            if isinstance(media2, list):
                ids.extend(str(m) for m in media2)
        return ids

    def extract_error(self, response: Dict[str, Any]) -> str:
        error = response.get("error", response.get("error_message", ""))
        if isinstance(error, dict):
            error = error.get("message", str(error))
        return str(error)[:500] if error else ""

    def classify_error(self, error_message: str) -> str:
        lower = error_message.lower()
        for category, patterns in self.KNOWN_ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern in lower:
                    return category
        return "unknown"

    def is_retryable(self, error_message: str) -> bool:
        category = self.classify_error(error_message)
        return category in ("rate_limit", "network_error")
