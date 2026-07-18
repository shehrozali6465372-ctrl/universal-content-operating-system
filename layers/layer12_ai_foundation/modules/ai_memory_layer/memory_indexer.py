"""MemoryIndexer — index memories for efficient search."""
from __future__ import annotations

from typing import Any, Dict, List, Set

from .models import MemoryEntry


class MemoryIndexer:
    """Index memories by tags, content words, and importance."""

    def __init__(self) -> None:
        self._tag_index: Dict[str, Set[str]] = {}  # tag -> set of entry_ids
        self._word_index: Dict[str, Set[str]] = {}  # word -> set of entry_ids

    def index(self, entry: MemoryEntry) -> None:
        # Index by tags
        for tag in entry.tags:
            self._tag_index.setdefault(tag, set()).add(entry.entry_id)
        # Index by content words
        words = set(entry.content.lower().split())
        for word in words:
            if len(word) >= 2:
                self._word_index.setdefault(word, set()).add(entry.entry_id)

    def remove(self, entry: MemoryEntry) -> None:
        for tag in entry.tags:
            if tag in self._tag_index:
                self._tag_index[tag].discard(entry.entry_id)
        words = set(entry.content.lower().split())
        for word in words:
            if word in self._word_index:
                self._word_index[word].discard(entry.entry_id)

    def search_by_tag(self, tag: str) -> Set[str]:
        return self._tag_index.get(tag, set())

    def search_by_word(self, word: str) -> Set[str]:
        return self._word_index.get(word.lower(), set())

    def search_by_words(self, words: List[str]) -> Set[str]:
        if not words:
            return set()
        results: Set[str] = set()
        for i, word in enumerate(words):
            ids = self._word_index.get(word.lower(), set())
            if i == 0:
                results = ids
            else:
                results &= ids
        return results

    def rebuild(self, entries: List[MemoryEntry]) -> None:
        self._tag_index.clear()
        self._word_index.clear()
        for entry in entries:
            self.index(entry)

    def stats(self) -> Dict[str, Any]:
        return {"tag_count": len(self._tag_index), "word_count": len(self._word_index)}

    def clear(self) -> None:
        self._tag_index.clear()
        self._word_index.clear()
