"""brand_repository.py — Brand repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class BrandEntity(BaseEntity):
    __slots__ = ("name", "guideline_type", "content", "platform")

    def __init__(self, name: str, guideline_type: str = "tone", content: str = "") -> None:
        super().__init__()
        self.name = name
        self.guideline_type = guideline_type
        self.content = content
        self.platform: str = "universal"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"name": self.name, "type": self.guideline_type,
                      "platform": self.platform})
        return base


class BrandRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("brand")

    def find_by_platform(self, platform: str) -> List[BrandEntity]:
        return self.find(platform=platform)

    def find_by_type(self, guideline_type: str) -> List[BrandEntity]:
        return self.find(guideline_type=guideline_type)
