"""memory_indexer.py — Memory indexing for fast search."""
from __future__ import annotations
from typing import Any, Dict, List, Set


class MemoryIndexer:
    """Builds and maintains search indexes over memory stores."""

    def __init__(self) -> None:
        self._word_index: Dict[str, Set[str]] = {}

    def index_entry(self, key: str, value: Any) -> None:
        text = str(value).lower()
        words = set(text.split())
        for word in words:
            if word not in self._word_index:
                self._word_index[word] = set()
            self._word_index[word].add(key)

    def search(self, query: str, limit: int = 10) -> List[str]:
        words = query.lower().split()
        if not words:
            return []
        result_keys: Dict[str, int] = {}
        for word in words:
            for key in self._word_index.get(word, set()):
                result_keys[key] = result_keys.get(key, 0) + 1
        sorted_keys = sorted(result_keys.keys(), key=lambda k: result_keys[k], reverse=True)
        return sorted_keys[:limit]

    def remove_key(self, key: str) -> None:
        for word_keys in self._word_index.values():
            word_keys.discard(key)

    def word_count(self) -> int:
        return len(self._word_index)

    def stats(self) -> Dict[str, Any]:
        total_entries = sum(len(keys) for keys in self._word_index.values())
        return {"words": self.word_count(), "total_entries": total_entries}
