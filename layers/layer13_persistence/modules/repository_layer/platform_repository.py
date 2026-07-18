"""platform_repository.py — Platform repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class PlatformEntity(BaseEntity):
    __slots__ = ("name", "platform_type", "config", "enabled", "api_version")

    def __init__(self, name: str, platform_type: str = "social") -> None:
        super().__init__()
        self.name = name
        self.platform_type = platform_type
        self.config: Dict[str, Any] = {}
        self.enabled: bool = True
        self.api_version: str = "v1"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "type": self.platform_type,
                      "enabled": self.enabled})
        return base


class PlatformRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("platform")

    def find_by_type(self, platform_type: str) -> List[PlatformEntity]:
        return self.find(platform_type=platform_type)

    def find_enabled(self) -> List[PlatformEntity]:
        return self.find(enabled=True)
