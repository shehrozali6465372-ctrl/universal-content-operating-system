"""
Plugin System
Extensible architecture for platform connectors, research sources, etc.

Features:
- Plugin registration and discovery
- Activation/deactivation
- Lifecycle hooks (init, start, stop)
- Capability queries
- Plugin metadata
- Priority ordering
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional


class PluginMetadata:
    """Metadata for a plugin."""

    __slots__ = ("name", "version", "author", "description", "category", "tags")

    def __init__(
        self,
        name: str,
        version: str = "1.0.0",
        author: str = "",
        description: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
    ):
        self.name = name
        self.version = version
        self.author = author
        self.description = description
        self.category = category
        self.tags = tags or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
        }


class Plugin(ABC):
    """Base class for all plugins."""

    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this plugin provides."""
        ...

    def on_init(self):
        """Called when the plugin is first loaded."""
        pass

    def on_activate(self):
        """Called when the plugin is activated."""
        pass

    def on_deactivate(self):
        """Called when the plugin is deactivated."""
        pass

    def on_destroy(self):
        """Called when the plugin is unloaded."""
        pass


class PluginEntry:
    """Internal record for a registered plugin."""

    __slots__ = ("plugin_class", "instance", "metadata", "active", "priority", "loaded_at")

    def __init__(self, plugin_class: type, priority: int = 0):
        self.plugin_class = plugin_class
        self.instance: Optional[Plugin] = None
        self.metadata: Optional[PluginMetadata] = None
        self.active = False
        self.priority = priority
        self.loaded_at = ""


class PluginManager:
    """Manages plugin lifecycle and discovery."""

    def __init__(self):
        self._plugins: Dict[str, PluginEntry] = {}
        self._hooks: Dict[str, List[Callable]] = {}

    def register(self, name: str, plugin_class: type, priority: int = 0) -> bool:
        """Register a plugin class."""
        if name in self._plugins:
            return False

        entry = PluginEntry(plugin_class, priority)

        # Instantiate to get metadata
        try:
            instance = plugin_class()
            entry.instance = instance
            entry.metadata = instance.metadata()
            instance.on_init()
        except Exception:
            entry.instance = None

        self._plugins[name] = entry
        return True

    def unregister(self, name: str) -> bool:
        """Unregister a plugin."""
        entry = self._plugins.get(name)
        if not entry:
            return False

        if entry.active and entry.instance:
            entry.instance.on_deactivate()
        if entry.instance:
            entry.instance.on_destroy()

        del self._plugins[name]
        return True

    def activate(self, name: str) -> bool:
        """Activate a registered plugin."""
        entry = self._plugins.get(name)
        if not entry or entry.active:
            return False

        if entry.instance:
            entry.instance.on_activate()
        entry.active = True
        self._fire_hook("activated", name)
        return True

    def deactivate(self, name: str) -> bool:
        """Deactivate a plugin."""
        entry = self._plugins.get(name)
        if not entry or not entry.active:
            return False

        if entry.instance:
            entry.instance.on_deactivate()
        entry.active = False
        self._fire_hook("deactivated", name)
        return True

    def get(self, name: str) -> Optional[Plugin]:
        """Get an active plugin instance."""
        entry = self._plugins.get(name)
        if entry and entry.active:
            return entry.instance
        return None

    def get_metadata(self, name: str) -> Optional[PluginMetadata]:
        entry = self._plugins.get(name)
        return entry.metadata if entry else None

    def list_plugins(self, active_only: bool = False) -> List[str]:
        """List registered plugin names."""
        if active_only:
            return [n for n, e in self._plugins.items() if e.active]
        return list(self._plugins.keys())

    def list_by_category(self, category: str) -> List[str]:
        """List plugins in a category."""
        return [
            name for name, entry in self._plugins.items()
            if entry.metadata and entry.metadata.category == category
        ]

    def list_by_capability(self, capability: str) -> List[str]:
        """List plugins that have a specific capability."""
        result = []
        for name, entry in self._plugins.items():
            if entry.instance and entry.active:
                caps = entry.instance.get_capabilities()
                if capability in caps:
                    result.append(name)
        return result

    def has_capability(self, capability: str) -> bool:
        """Check if any active plugin provides a capability."""
        return len(self.list_by_capability(capability)) > 0

    def activate_all(self):
        """Activate all registered plugins (by priority)."""
        sorted_plugins = sorted(
            self._plugins.items(),
            key=lambda x: -x[1].priority,
        )
        for name, _ in sorted_plugins:
            self.activate(name)

    def deactivate_all(self):
        """Deactivate all plugins."""
        for name in list(self._plugins.keys()):
            self.deactivate(name)

    def on(self, event: str, callback: Callable):
        """Register a hook callback."""
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)

    def _fire_hook(self, event: str, plugin_name: str):
        """Fire a hook event."""
        for cb in self._hooks.get(event, []):
            try:
                cb(plugin_name)
            except Exception:
                pass

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system stats."""
        total = len(self._plugins)
        active = sum(1 for e in self._plugins.values() if e.active)
        categories = set()
        for entry in self._plugins.values():
            if entry.metadata:
                categories.add(entry.metadata.category)

        return {
            "total_registered": total,
            "active": active,
            "inactive": total - active,
            "categories": list(categories),
        }

    def reset(self):
        """Deactivate and unregister all plugins."""
        self.deactivate_all()
        for entry in self._plugins.values():
            if entry.instance:
                entry.instance.on_destroy()
        self._plugins.clear()
        self._hooks.clear()
