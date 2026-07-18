"""prompt_memory_store.py — Prompt memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class PromptMemoryStore(BaseMemoryStore):
    """Stores prompts and their performance data."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("prompt", max_entries)
        self._performances: Dict[str, List[float]] = {}

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "prompt")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def record_performance(self, prompt_key: str, score: float) -> None:
        if prompt_key not in self._performances:
            self._performances[prompt_key] = []
        self._performances[prompt_key].append(score)

    def get_best_prompts(self, limit: int = 10) -> List[MemoryEntry]:
        entries_with_score = []
        for key, entry in self._store.items():
            scores = self._performances.get(key, [])
            avg = sum(scores) / len(scores) if scores else 0
            entries_with_score.append((entry, avg))
        entries_with_score.sort(key=lambda x: x[1], reverse=True)
        return [e for e, _ in entries_with_score[:limit]]

    def get_performance(self, prompt_key: str) -> Dict[str, Any]:
        scores = self._performances.get(prompt_key, [])
        return {"count": len(scores), "avg": sum(scores) / max(1, len(scores)),
                "min": min(scores) if scores else 0, "max": max(scores) if scores else 0}

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["with_performance"] = len(self._performances)
        return base
