"""Plugin Registry — Register and manage platform plugins."""
from __future__ import annotations
from typing import Dict, List, Optional, Type

from layers.layer07_publishing.modules.platform_plugin_manager.base_publisher import BasePublisher


class PluginRegistry:
    """Central registry for platform publisher plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, Type[BasePublisher]] = {}
        self._instances: Dict[str, BasePublisher] = {}

    def register(self, platform: str, publisher_class: Type[BasePublisher]) -> None:
        """Register a publisher class for a platform."""
        self._plugins[platform.lower()] = publisher_class

    def unregister(self, platform: str) -> bool:
        """Unregister a platform plugin."""
        if platform.lower() in self._plugins:
            del self._plugins[platform.lower()]
            self._instances.pop(platform.lower(), None)
            return True
        return False

    def get_class(self, platform: str) -> Optional[Type[BasePublisher]]:
        """Get registered publisher class."""
        return self._plugins.get(platform.lower())

    def get_instance(self, platform: str) -> Optional[BasePublisher]:
        """Get or create a publisher instance."""
        key = platform.lower()
        if key not in self._instances:
            cls = self._plugins.get(key)
            if cls:
                self._instances[key] = cls()
        return self._instances.get(key)

    def is_registered(self, platform: str) -> bool:
        return platform.lower() in self._plugins

    def list_platforms(self) -> List[str]:
        return sorted(self._plugins.keys())

    def list_capabilities(self) -> Dict[str, Dict]:
        """List capabilities of all registered plugins."""
        caps = {}
        for platform, cls in self._plugins.items():
            instance = cls()
            caps[platform] = instance.get_capabilities().to_dict()
        return caps

    @property
    def count(self) -> int:
        return len(self._plugins)
