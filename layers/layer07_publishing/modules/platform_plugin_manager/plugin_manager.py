"""Plugin Manager — Orchestrates plugin operations."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import (
    BasePublisher, PublishResult, PlatformCapabilities,
)
from layers.layer07_publishing.modules.platform_plugin_manager.plugin_registry import PluginRegistry
from layers.layer07_publishing.modules.platform_plugin_manager.exceptions import (
    PluginNotFoundError, AuthenticationError,
)


class PluginManager:
    """Manage platform plugins: registration, auth, publish, capabilities."""

    def __init__(self, registry: Optional[PluginRegistry] = None) -> None:
        self.registry = registry or PluginRegistry()
        self._operation_count = 0

    def register(self, platform: str, publisher_class: type) -> None:
        self.registry.register(platform, publisher_class)

    def authenticate(self, platform: str, credentials: Dict[str, str]) -> bool:
        publisher = self._get_or_raise(platform)
        result = publisher.authenticate(credentials)
        self._operation_count += 1
        if not result:
            raise AuthenticationError(f"Auth failed for {platform}")
        return result

    def publish(
        self, platform: str, content: str,
        media_paths: Optional[List[str]] = None,
        content_type: str = "post", **kwargs: Any,
    ) -> PublishResult:
        publisher = self._get_or_raise(platform)
        result = publisher.publish(content, media_paths, content_type, **kwargs)
        self._operation_count += 1
        return result

    def edit(self, platform: str, post_id: str, content: str, **kwargs: Any) -> PublishResult:
        publisher = self._get_or_raise(platform)
        result = publisher.edit(post_id, content, **kwargs)
        self._operation_count += 1
        return result

    def delete(self, platform: str, post_id: str) -> bool:
        publisher = self._get_or_raise(platform)
        result = publisher.delete(post_id)
        self._operation_count += 1
        return result

    def get_post(self, platform: str, post_id: str) -> Optional[Dict[str, Any]]:
        publisher = self._get_or_raise(platform)
        return publisher.get_post(post_id)

    def get_status(self, platform: str, post_id: str) -> str:
        publisher = self._get_or_raise(platform)
        return publisher.get_status(post_id)

    def get_analytics(self, platform: str, post_id: str) -> Dict[str, Any]:
        publisher = self._get_or_raise(platform)
        return publisher.get_analytics(post_id)

    def get_capabilities(self, platform: str) -> PlatformCapabilities:
        publisher = self._get_or_raise(platform)
        return publisher.get_capabilities()

    def get_all_capabilities(self) -> Dict[str, Dict]:
        return self.registry.list_capabilities()

    def supports(self, platform: str, feature: str) -> bool:
        caps = self.get_capabilities(platform)
        return caps.supports(feature)

    def find_platforms_with_feature(self, feature: str) -> List[str]:
        results = []
        for platform in self.registry.list_platforms():
            if self.supports(platform, feature):
                results.append(platform)
        return results

    def _get_or_raise(self, platform: str) -> BasePublisher:
        publisher = self.registry.get_instance(platform)
        if publisher is None:
            raise PluginNotFoundError(f"No plugin registered for '{platform}'")
        return publisher

    @property
    def operation_count(self) -> int:
        return self._operation_count
