"""ObjectMapper — bidirectional object mapping with type safety."""
from __future__ import annotations
from typing import Any, Callable, Dict, List, Optional, Type


class ObjectMapping:
    __slots__ = ("source_type", "target_type", "mappings", "transforms")

    def __init__(self, source_type: str, target_type: str) -> None:
        self.source_type = source_type
        self.target_type = target_type
        self.mappings: Dict[str, str] = {}
        self.transforms: Dict[str, Callable] = {}

    def map_field(self, source_field: str, target_field: str,
                  transform: Optional[Callable] = None) -> None:
        self.mappings[source_field] = target_field
        if transform:
            self.transforms[target_field] = transform


class ObjectMapper:
    def __init__(self) -> None:
        self._mappings: Dict[str, ObjectMapping] = {}

    def register(self, source_type: str, target_type: str) -> ObjectMapping:
        key = f"{source_type}->{target_type}"
        mapping = ObjectMapping(source_type, target_type)
        self._mappings[key] = mapping
        return mapping

    def map_object(self, source_type: str, target_type: str,
                   source: Dict[str, Any]) -> Dict[str, Any]:
        key = f"{source_type}->{target_type}"
        mapping = self._mappings.get(key)
        if not mapping:
            return dict(source)
        result = {}
        for src_field, tgt_field in mapping.mappings.items():
            val = source.get(src_field)
            if tgt_field in mapping.transforms:
                val = mapping.transforms[tgt_field](val)
            result[tgt_field] = val
        return result

    def map_batch(self, source_type: str, target_type: str,
                  sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [self.map_object(source_type, target_type, s) for s in sources]

    def list_mappings(self) -> List[str]:
        return list(self._mappings.keys())
