"""ContentMemory — Store generation patterns and lessons."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

_CM_COUNTER = itertools.count(1)


class ContentMemoryEntry:
    """A stored content generation memory."""

    __slots__ = ("entry_id", "content_type", "platform", "topic",
                 "quality_score", "engagement_score", "tags", "created_at")

    def __init__(self, content_type: str = "", platform: str = "") -> None:
        self.entry_id: str = f"cmem_{next(_CM_COUNTER)}"
        self.content_type = content_type
        self.platform = platform
        self.topic: str = ""
        self.quality_score: float = 0.0
        self.engagement_score: float = 0.0
        self.tags: List[str] = []
        self.created_at: float = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "content_type": self.content_type,
            "platform": self.platform, "quality_score": round(self.quality_score, 3),
        }


class ContentMemory:
    """Store and retrieve content generation patterns."""

    def __init__(self, max_entries: int = 3000) -> None:
        self._max_entries = max_entries
        self._entries: List[ContentMemoryEntry] = []

    def store(self, content_type: str, platform: str, topic: str = "",
              quality_score: float = 0.0, tags: Optional[List[str]] = None) -> ContentMemoryEntry:
        entry = ContentMemoryEntry(content_type, platform)
        entry.topic = topic
        entry.quality_score = quality_score
        if tags:
            entry.tags = list(tags)
        self._entries.append(entry)
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]
        return entry

    def search(self, content_type: str = "", platform: str = "",
               min_quality: float = 0.0, limit: int = 50) -> List[ContentMemoryEntry]:
        results = self._entries
        if content_type:
            results = [e for e in results if e.content_type == content_type]
        if platform:
            results = [e for e in results if e.platform == platform]
        if min_quality > 0:
            results = [e for e in results if e.quality_score >= min_quality]
        return results[-limit:]

    def get_top_performers(self, count: int = 10) -> List[ContentMemoryEntry]:
        return sorted(self._entries, key=lambda e: e.quality_score, reverse=True)[:count]

    def get_stats(self) -> Dict[str, Any]:
        platforms = {}
        for e in self._entries:
            platforms[e.platform] = platforms.get(e.platform, 0) + 1
        return {"total": len(self._entries), "by_platform": platforms}
