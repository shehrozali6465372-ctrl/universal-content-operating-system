"""ExecutionContext — shared context passed through all layer executions."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional


class ExecutionContext:
    def __init__(self, context_id: Optional[str] = None,
                 parent_id: Optional[str] = None) -> None:
        self.context_id = context_id or str(uuid.uuid4())[:12]
        self.parent_id = parent_id
        self.created_at = time.time()
        self._data: Dict[str, Any] = {}
        self._history: List[Dict[str, Any]] = []
        self._tags: List[str] = []

    def set(self, key: str, value: Any) -> None:
        old = self._data.get(key)
        self._data[key] = value
        self._history.append({"action": "set", "key": key,
                              "old": old, "new": str(value)[:100], "time": time.time()})

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        return key in self._data

    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            self._history.append({"action": "delete", "key": key, "time": time.time()})
            return True
        return False

    def clear(self) -> None:
        self._data.clear()
        self._history.clear()

    def update(self, data: Dict[str, Any]) -> None:
        for k, v in data.items():
            self.set(k, v)

    def keys(self) -> List[str]:
        return list(self._data.keys())

    def values(self) -> List[Any]:
        return list(self._data.values())

    def items(self) -> List[tuple]:
        return list(self._data.items())

    def add_tag(self, tag: str) -> None:
        if tag not in self._tags:
            self._tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self._tags

    def remove_tag(self, tag: str) -> bool:
        if tag in self._tags:
            self._tags.remove(tag)
            return True
        return False

    def snapshot(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "data": dict(self._data),
                "tags": list(self._tags), "history_length": len(self._history)}

    def restore(self, snapshot: Dict[str, Any]) -> None:
        self._data = dict(snapshot.get("data", {}))
        self._tags = list(snapshot.get("tags", []))

    def get_history(self) -> List[Dict[str, Any]]:
        return list(self._history)

    def to_dict(self) -> Dict[str, Any]:
        return {"context_id": self.context_id, "parent_id": self.parent_id,
                "data": dict(self._data), "tags": list(self._tags),
                "history_length": len(self._history)}

    def fork(self) -> ExecutionContext:
        child = ExecutionContext(parent_id=self.context_id)
        child._data = dict(self._data)
        child._tags = list(self._tags)
        return child
