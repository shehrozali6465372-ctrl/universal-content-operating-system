"""Plugin Manager — canonical registration for production platform adapters."""
from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, List, Optional, Type

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher,
    PlatformCapabilities,
    PublishResult,
)
from layers.layer07_publishing.modules.platform_plugin_manager.exceptions import (
    AuthenticationError,
    PluginNotFoundError,
)
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_registry import PluginRegistry

LOGGER = logging.getLogger(__name__)


class PluginManager:
    """Register and expose platform adapters without silent load failures."""

    _BUILTINS = {
        "facebook": (
            "layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_publisher",
            "FacebookPublisher",
        ),
        "instagram": (
            "layers.layer07_publishing.modules.platform_plugin_manager.instagram.instagram_publisher",
            "InstagramPublisher",
        ),
        "pinterest": (
            "layers.layer07_publishing.modules.platform_plugin_manager.pinterest.pinterest_publisher",
            "PinterestPublisher",
        ),
        "youtube": (
            "layers.layer07_publishing.modules.platform_plugin_manager.youtube.youtube_publisher",
            "YouTubePublisher",
        ),
        "tiktok": (
            "layers.layer07_publishing.modules.platform_plugin_manager.tiktok.tiktok_publisher",
            "TikTokPublisher",
        ),
    }

    def __init__(self, registry: Optional[PluginRegistry] = None) -> None:
        self.registry = registry or PluginRegistry()
        self._operation_count = 0
        self._load_errors: Dict[str, str] = {}
        self._register_builtin_plugins()

    def _register_builtin_plugins(self) -> None:
        for platform, (module, class_name) in self._BUILTINS.items():
            if self.registry.is_registered(platform):
                continue
            try:
                publisher_class = getattr(importlib.import_module(module), class_name)
                self.registry.register(platform, publisher_class)
            except (ImportError, AttributeError, TypeError) as exc:
                message = f"{type(exc).__name__}: {exc}"
                self._load_errors[platform] = message
                LOGGER.error("Failed to load Layer 7 publisher %s: %s", platform, message)

    def register(self, platform: str, publisher_class: Type[BasePublisher]) -> None:
        if not platform.strip():
            raise ValueError("Platform is required")
        self.registry.register(platform.strip().lower(), publisher_class)

    def authenticate(self, platform: str, credentials: Dict[str, str]) -> bool:
        publisher = self._get_or_raise(platform)
        ok = publisher.authenticate(credentials)
        self._operation_count += 1
        if not ok:
            raise AuthenticationError(f"Auth failed for {platform}")
        return ok

    def publish(self, platform: str, content: str,
                media_paths: Optional[List[str]] = None,
                content_type: str = "post", **kwargs: Any) -> PublishResult:
        publisher = self._get_or_raise(platform)
        result = publisher.publish(content, media_paths, content_type, **kwargs)
        self._operation_count += 1
        return result

    def edit(self, platform: str, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        return self._get_or_raise(platform).edit(post_id, content, **kwargs)

    def delete(self, platform: str, post_id: str) -> bool:
        return self._get_or_raise(platform).delete(post_id)

    def get_post(self, platform: str, post_id: str) -> Optional[Dict[str, Any]]:
        return self._get_or_raise(platform).get_post(post_id)

    def get_status(self, platform: str, post_id: str) -> str:
        return self._get_or_raise(platform).get_status(post_id)

    def get_analytics(self, platform: str, post_id: str) -> Dict[str, Any]:
        return self._get_or_raise(platform).get_analytics(post_id)

    def get_capabilities(self, platform: str) -> PlatformCapabilities:
        return self._get_or_raise(platform).get_capabilities()

    def get_all_capabilities(self) -> Dict[str, PlatformCapabilities]:
        return self.registry.list_capabilities()

    def supports(self, platform: str, feature: str) -> bool:
        return self.get_capabilities(platform).supports(feature)

    def find_platforms_with_feature(self, feature: str) -> List[str]:
        return [
            platform for platform in self.registry.list_platforms()
            if self.supports(platform, feature)
        ]

    def _get_or_raise(self, platform: str) -> BasePublisher:
        publisher = self.registry.get_instance(platform.strip().lower())
        if publisher is None:
            detail = self._load_errors.get(platform.strip().lower())
            suffix = f" Load error: {detail}" if detail else ""
            raise PluginNotFoundError(
                f"No production publisher registered for '{platform}'.{suffix}"
            )
        return publisher

    @property
    def operation_count(self) -> int:
        return self._operation_count

    @property
    def load_errors(self) -> Dict[str, str]:
        """Return immutable-by-copy adapter load diagnostics."""
        return dict(self._load_errors)
