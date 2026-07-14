"""
Plugin System
Extensible architecture for adding new research sources, platforms, etc.

Usage:
    from layers.shared.plugin_system import PluginManager, Plugin

    manager = PluginManager()
    manager.register("facebook", FacebookPlugin)
    manager.activate("facebook")
    plugin = manager.get("facebook")
    plugin.publish(content)
"""
from layers.shared.plugin_system.plugin_manager import PluginManager, Plugin, PluginMetadata

__all__ = ["PluginManager", "Plugin", "PluginMetadata"]
