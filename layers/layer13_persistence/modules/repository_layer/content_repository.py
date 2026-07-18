"""content_repository.py — Content repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class ContentEntity(BaseEntity):
    __slots__ = ("title", "body", "content_type", "platform", "status", "quality_score")

    def __init__(self, title: str, body: str = "", content_type: str = "post") -> None:
        super().__init__()
        self.title = title
        self.body = body
        self.content_type = content_type
        self.platform: str = ""
        self.status: str = "draft"
        self.quality_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"title": self.title, "type": self.content_type,
                      "status": self.status, "score": self.quality_score})
        return base


class ContentRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("content")

    def find_by_platform(self, platform: str) -> List[ContentEntity]:
        return self.find(platform=platform)

    def find_by_status(self, status: str) -> List[ContentEntity]:
        return self.find(status=status)

    def find_published(self) -> List[ContentEntity]:
        return self.find(status="published")
