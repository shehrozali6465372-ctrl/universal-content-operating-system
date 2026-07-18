"""PluginEcosystem — Manage platform, AI, analytics, and research plugins."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

PLUGIN_CATEGORIES = ("platform", "ai_model", "analytics", "research", "monetization", "utility")


class PluginInfo:
    """Information about a registered plugin."""

    __slots__ = ("plugin_id", "name", "category", "version",
                 "status", "config", "registered_at", "last_health_check")

    def __init__(self, name: str = "", category: str = "") -> None:
        self.plugin_id: str = f"plugin_{name}"
        self.name = name
        self.category = category if category in PLUGIN_CATEGORIES else "utility"
        self.version: str = "1.0.0"
        self.status: str = "registered"
        self.config: Dict[str, Any] = {}
        self.registered_at: float = time.time()
        self.last_health_check: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {"plugin_id": self.plugin_id, "name": self.name,
                "category": self.category, "version": self.version,
                "status": self.status}


class PluginEcosystem:
    """Manage platform, AI, analytics, research, and monetization plugins."""

    def __init__(self) -> None:
        self._plugins: Dict[str, PluginInfo] = {}

    def register(self, name: str, category: str = "platform",
                 version: str = "1.0.0",
                 config: Optional[Dict[str, Any]] = None) -> PluginInfo:
        if name in self._plugins:
            return self._plugins[name]
        plugin = PluginInfo(name, category)
        plugin.version = version
        if config:
            plugin.config = dict(config)
        self._plugins[name] = plugin
        return plugin

    def unregister(self, name: str) -> bool:
        return self._plugins.pop(name, None) is not None

    def get(self, name: str) -> Optional[PluginInfo]:
        return self._plugins.get(name)

    def activate(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if plugin:
            plugin.status = "active"
            return True
        return False

    def deactivate(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if plugin:
            plugin.status = "inactive"
            return True
        return False

    def get_by_category(self, category: str) -> List[PluginInfo]:
        return [p for p in self._plugins.values() if p.category == category]

    def get_active(self) -> List[PluginInfo]:
        return [p for p in self._plugins.values() if p.status == "active"]

    def get_all(self) -> List[PluginInfo]:
        return list(self._plugins.values())

    def health_check(self, name: str) -> bool:
        plugin = self._plugins.get(name)
        if plugin:
            plugin.last_health_check = time.time()
            return plugin.status == "active"
        return False

    def get_stats(self) -> Dict[str, Any]:
        categories: Dict[str, int] = {}
        statuses: Dict[str, int] = {}
        for p in self._plugins.values():
            categories[p.category] = categories.get(p.category, 0) + 1
            statuses[p.status] = statuses.get(p.status, 0) + 1
        return {"total": len(self._plugins), "by_category": categories,
                "by_status": statuses}
