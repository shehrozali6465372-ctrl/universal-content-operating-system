"""MemoryCompression — compress and summarize memories for efficiency."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import MemoryEntry


class MemoryCompression:
    """Compress and summarize memories for storage efficiency."""

    def __init__(self) -> None:
        self._compressions: List[Dict[str, Any]] = []

    def compress(self, entries: List[MemoryEntry],
                 max_length: int = 200) -> List[MemoryEntry]:
        compressed = []
        for e in entries:
            if len(e.content) > max_length:
                summary = e.content[:max_length] + "..."
                new_entry = MemoryEntry(
                    content=summary, memory_type=e.memory_type,
                    tags=e.tags, importance=e.importance,
                    metadata={**e.metadata, "compressed": True},
                )
                compressed.append(new_entry)
            else:
                compressed.append(e)
        self._compressions.append({"input": len(entries), "output": len(compressed)})
        return compressed

    def summarize_batch(self, entries: List[MemoryEntry]) -> str:
        if not entries:
            return ""
        parts = [f"[{e.memory_type.value}] {e.content[:80]}" for e in entries[:10]]
        return " | ".join(parts)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_compressions": len(self._compressions)}
