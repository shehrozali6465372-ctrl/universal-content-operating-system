"""metadata_manager.py — Object metadata management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class ObjectMetadata:
    """Metadata for a stored object."""
    __slots__ = ("object_id", "metadata", "tags", "headers")

    def __init__(self, object_id: str) -> None:
        self.object_id = object_id
        self.metadata: Dict[str, str] = {}
        self.tags: List[str] = []
        self.headers: Dict[str, str] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"object_id": self.object_id, "metadata": dict(self.metadata),
                "tags": list(self.tags)}


class MetadataManager:
    """Manages object metadata."""

    def __init__(self) -> None:
        self._metadata: Dict[str, ObjectMetadata] = {}

    def set_metadata(self, object_id: str, key: str, value: str) -> None:
        if object_id not in self._metadata:
            self._metadata[object_id] = ObjectMetadata(object_id)
        self._metadata[object_id].metadata[key] = value

    def get_metadata(self, object_id: str) -> Optional[ObjectMetadata]:
        return self._metadata.get(object_id)

    def get_value(self, object_id: str, key: str) -> Optional[str]:
        meta = self._metadata.get(object_id)
        return meta.metadata.get(key) if meta else None

    def set_tags(self, object_id: str, tags: List[str]) -> None:
        if object_id not in self._metadata:
            self._metadata[object_id] = ObjectMetadata(object_id)
        self._metadata[object_id].tags = tags

    def search_by_tag(self, tag: str) -> List[str]:
        return [oid for oid, m in self._metadata.items() if tag in m.tags]

    def delete(self, object_id: str) -> bool:
        return self._metadata.pop(object_id, None) is not None

    def count(self) -> int:
        return len(self._metadata)
