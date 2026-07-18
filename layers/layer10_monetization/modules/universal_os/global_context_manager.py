"""GlobalContextManager — Store user, session, platform, AI, and goal context."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List

_GC_COUNTER = itertools.count(1)

CONTEXT_TYPES = ("user", "session", "platform", "ai", "goal", "global")


class ContextEntry:
    """A context entry."""

    __slots__ = ("entry_id", "context_type", "key", "value",
                 "metadata", "created_at", "updated_at")

    def __init__(self, context_type: str = "", key: str = "",
                 value: Any = None) -> None:
        self.entry_id: str = f"ctx_{next(_GC_COUNTER)}"
        self.context_type = context_type if context_type in CONTEXT_TYPES else "global"
        self.key = key
        self.value = value
        self.metadata: Dict[str, Any] = {}
        self.created_at: float = time.time()
        self.updated_at: float = time.time()


class GlobalContextManager:
    """Manage user, session, platform, AI, and goal context."""

    def __init__(self) -> None:
        self._entries: List[ContextEntry] = []
        self._index: Dict[str, ContextEntry] = {}

    def set(self, context_type: str, key: str, value: Any) -> ContextEntry:
        idx_key = f"{context_type}:{key}"
        if idx_key in self._index:
            entry = self._index[idx_key]
            entry.value = value
            entry.updated_at = time.time()
            return entry
        entry = ContextEntry(context_type, key, value)
        self._entries.append(entry)
        self._index[idx_key] = entry
        return entry

    def get(self, context_type: str, key: str) -> Any:
        entry = self._index.get(f"{context_type}:{key}")
        return entry.value if entry else None

    def get_all(self, context_type: str = "") -> List[ContextEntry]:
        if context_type:
            return [e for e in self._entries if e.context_type == context_type]
        return list(self._entries)

    def delete(self, context_type: str, key: str) -> bool:
        idx_key = f"{context_type}:{key}"
        entry = self._index.pop(idx_key, None)
        if entry:
            self._entries.remove(entry)
            return True
        return False

    def clear(self, context_type: str = "") -> int:
        if context_type:
            to_remove = [e for e in self._entries if e.context_type == context_type]
            for e in to_remove:
                self._index.pop(f"{e.context_type}:{e.key}", None)
                self._entries.remove(e)
            return len(to_remove)
        count = len(self._entries)
        self._entries.clear()
        self._index.clear()
        return count

    def to_dict(self, context_type: str = "") -> Dict[str, Any]:
        result: Dict[str, Any] = {}
        for e in self._entries:
            if context_type and e.context_type != context_type:
                continue
            result.setdefault(e.context_type, {})[e.key] = e.value
        return result

    def get_stats(self) -> Dict[str, Any]:
        types: Dict[str, int] = {}
        for e in self._entries:
            types[e.context_type] = types.get(e.context_type, 0) + 1
        return {"total": len(self._entries), "by_type": types}
