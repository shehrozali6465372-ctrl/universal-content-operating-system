"""ORM Layer — object-relational mapping abstraction."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional


class Field:
    __slots__ = ("name", "field_type", "default", "nullable", "primary_key",
                 "unique", "indexed", "max_length")

    def __init__(self, name: str, field_type: str = "str", default: Any = None,
                 nullable: bool = True, primary_key: bool = False,
                 unique: bool = False, indexed: bool = False,
                 max_length: Optional[int] = None) -> None:
        self.name = name
        self.field_type = field_type
        self.default = default
        self.nullable = nullable
        self.primary_key = primary_key
        self.unique = unique
        self.indexed = indexed
        self.max_length = max_length

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "type": self.field_type,
                "primary_key": self.primary_key, "nullable": self.nullable}


class ModelMeta:
    def __init__(self, table_name: str, fields: List[Field]) -> None:
        self.table_name = table_name
        self.fields = fields
        self.primary_key = next((f.name for f in fields if f.primary_key), "id")

    def to_dict(self) -> Dict[str, Any]:
        return {"table_name": self.table_name,
                "fields": [f.to_dict() for f in self.fields]}


class BaseModel:
    _meta: Optional[ModelMeta] = None
    _store: Dict[str, Dict[str, Any]] = {}

    def __init__(self, **kwargs: Any) -> None:
        for field in (self._meta.fields if self._meta else []):
            val = kwargs.get(field.name, field.default)
            if val is None and not field.nullable:
                raise ValueError(f"Field {field.name} cannot be null")
            setattr(self, field.name, val)

    def save(self) -> Dict[str, Any]:
        data = {}
        for field in (self._meta.fields if self._meta else []):
            data[field.name] = getattr(self, field.name, None)
        pk = data.get(self._meta.primary_key if self._meta else "id", str(id(self)))
        data["_saved_at"] = time.time()
        self.__class__._store[pk] = data
        return data

    @classmethod
    def get_by_id(cls, pk: str) -> Optional[Dict[str, Any]]:
        return cls._store.get(pk)

    @classmethod
    def all(cls) -> List[Dict[str, Any]]:
        return list(cls._store.values())

    @classmethod
    def filter_by(cls, **kwargs: Any) -> List[Dict[str, Any]]:
        results = []
        for record in cls._store.values():
            if all(record.get(k) == v for k, v in kwargs.items()):
                results.append(record)
        return results

    @classmethod
    def delete(cls, pk: str) -> bool:
        if pk in cls._store:
            del cls._store[pk]
            return True
        return False

    @classmethod
    def count(cls) -> int:
        return len(cls._store)

    @classmethod
    def clear(cls) -> int:
        count = len(cls._store)
        cls._store.clear()
        return count

    def to_dict(self) -> Dict[str, Any]:
        data = {}
        for field in (self._meta.fields if self._meta else []):
            data[field.name] = getattr(self, field.name, None)
        return data
