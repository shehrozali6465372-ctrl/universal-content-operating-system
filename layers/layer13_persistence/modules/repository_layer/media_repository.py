"""media_repository.py — Media repository."""
from __future__ import annotations
from typing import Any, Dict, List
from layers.layer13_persistence.modules.repository_layer.base_repository import BaseRepository, BaseEntity


class MediaEntity(BaseEntity):
    __slots__ = ("filename", "media_type", "size_bytes", "url", "metadata")

    def __init__(self, filename: str, media_type: str = "image") -> None:
        super().__init__()
        self.filename = filename
        self.media_type = media_type
        self.size_bytes: int = 0
        self.url: str = ""
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({"filename": self.filename, "type": self.media_type,
                      "size": self.size_bytes})
        return base


class MediaRepository(BaseRepository):
    def __init__(self) -> None:
        super().__init__("media")

    def find_by_type(self, media_type: str) -> List[MediaEntity]:
        return self.find(media_type=media_type)

    def total_size(self) -> int:
        return sum(e.size_bytes for e in self._store.values())
