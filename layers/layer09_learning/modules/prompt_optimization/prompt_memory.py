"""Prompt Memory — Store and retrieve prompt learnings."""
from __future__ import annotations
import time
import itertools
from typing import Any, Dict, List, Optional

_MEM_COUNTER = itertools.count(1)


class PromptMemoryEntry:
    """A stored learning about a prompt."""

    __slots__ = ("entry_id", "profile_id", "learning_type", "description",
                 "confidence", "created_at", "tags", "archived")

    def __init__(self, profile_id: str = "", learning_type: str = "insight") -> None:
        self.entry_id: str = f"pme_{next(_MEM_COUNTER)}"
        self.profile_id = profile_id
        self.learning_type = learning_type
        self.description: str = ""
        self.confidence: float = 0.5
        self.created_at: float = time.time()
        self.tags: List[str] = []
        self.archived: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "profile_id": self.profile_id,
            "learning_type": self.learning_type,
            "description": self.description,
            "confidence": round(self.confidence, 3),
            "tags": self.tags,
        }


class PromptMemory:
    """Store and retrieve prompt optimization learnings."""

    def __init__(self, max_entries: int = 5000) -> None:
        self._max_entries = max_entries
        self._entries: List[PromptMemoryEntry] = []

    def store(self, profile_id: str, learning_type: str, description: str,
              confidence: float = 0.5, tags: Optional[List[str]] = None) -> PromptMemoryEntry:
        entry = PromptMemoryEntry(profile_id, learning_type)
        entry.description = description
        entry.confidence = confidence
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, profile_id: str = "", learning_type: str = "",
               tag: str = "", limit: int = 50) -> List[PromptMemoryEntry]:
        results = [e for e in self._entries if not e.archived]
        if profile_id:
            results = [e for e in results if e.profile_id == profile_id]
        if learning_type:
            results = [e for e in results if e.learning_type == learning_type]
        if tag:
            results = [e for e in results if tag in e.tags]
        return results[-limit:]

    def get_recent(self, count: int = 10) -> List[PromptMemoryEntry]:
        return [e for e in self._entries if not e.archived][-count:]

    def archive(self, entry_id: str) -> bool:
        for e in self._entries:
            if e.entry_id == entry_id:
                e.archived = True
                return True
        return False

    def get_by_id(self, entry_id: str) -> Optional[PromptMemoryEntry]:
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def get_stats(self) -> Dict[str, Any]:
        active = [e for e in self._entries if not e.archived]
        by_type: Dict[str, int] = {}
        for e in active:
            by_type[e.learning_type] = by_type.get(e.learning_type, 0) + 1
        return {
            "total": len(self._entries),
            "active": len(active),
            "archived": len(self._entries) - len(active),
            "by_type": by_type,
        }

    @property
    def entry_count(self) -> int:
        return len([e for e in self._entries if not e.archived])

    @property
    def max_entries(self) -> int:
        return self._max_entries
