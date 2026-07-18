"""plugin_repository.py — Plugin repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class PluginEntity(BaseEntity):
    __slots__ = ("name", "version", "platform", "enabled", "config")

    def __init__(self, name: str, version: str = "1.0.0", platform: str = "") -> None:
        super().__init__()
        self.name = name
        self.version = version
        self.platform = platform
        self.enabled: bool = True
        self.config: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "version": self.version,
                      "platform": self.platform, "enabled": self.enabled})
        return base


class PluginRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("plugin")

    def find_by_platform(self, platform: str) -> List[PluginEntity]:
        return self.find(platform=platform)

    def find_enabled(self) -> List[PluginEntity]:
        return self.find(enabled=True)
