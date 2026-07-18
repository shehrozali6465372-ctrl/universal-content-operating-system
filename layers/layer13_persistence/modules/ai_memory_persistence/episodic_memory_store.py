"""episodic_memory_store.py — Episodic memory persistence."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class EpisodicMemory:
    """Single episodic memory."""
    __slots__ = ("episode_id", "event", "context", "outcome", "timestamp",
                 "emotional_valence", "importance", "retrieval_count")
    _counter = 0

    def __init__(self, event: str, context: Dict[str, Any] = None,
                 outcome: str = "") -> None:
        EpisodicMemory._counter += 1
        self.episode_id: int = EpisodicMemory._counter
        self.event = event
        self.context = context or {}
        self.outcome = outcome
        self.timestamp: float = time.time()
        self.emotional_valence: float = 0.0
        self.importance: float = 0.5
        self.retrieval_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.episode_id, "event": self.event,
                "importance": self.importance, "retrievals": self.retrieval_count}


class EpisodicMemoryStore(BaseMemoryStore):
    """Stores episodic memories (events, experiences)."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("episodic", max_entries)
        self._episodes: Dict[str, EpisodicMemory] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "episodic")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        episode = EpisodicMemory(str(value), metadata)
        self._episodes[key] = episode
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        episode = self._episodes.get(key)
        if episode:
            episode.retrieval_count += 1
        return entry

    def store_episode(self, key: str, episode: EpisodicMemory) -> None:
        self._episodes[key] = episode

    def get_episode(self, key: str) -> Optional[EpisodicMemory]:
        return self._episodes.get(key)

    def search_by_importance(self, min_importance: float = 0.5,
                              limit: int = 10) -> List[EpisodicMemory]:
        episodes = [e for e in self._episodes.values() if e.importance >= min_importance]
        episodes.sort(key=lambda e: e.importance, reverse=True)
        return episodes[:limit]

    def get_recent(self, limit: int = 10) -> List[EpisodicMemory]:
        episodes = sorted(self._episodes.values(), key=lambda e: e.timestamp, reverse=True)
        return episodes[:limit]

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["episodes"] = len(self._episodes)
        return base
