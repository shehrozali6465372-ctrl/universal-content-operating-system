"""KnowledgeBaseManager — Manage internal knowledge base."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.learning_connector.models.learning_models import KnowledgeEntry


class KnowledgeBaseManager:
    """Manage internal knowledge and best practices."""

    def __init__(self) -> None:
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._lock = threading.RLock()

    def add_entry(self, topic: str, content: str, source: str = "",
                  confidence: float = 0.5,
                  tags: Optional[List[str]] = None) -> KnowledgeEntry:
        entry = KnowledgeEntry(topic, content, source, confidence, tags)
        with self._lock:
            self._entries[entry.entry_id] = entry
        return entry

    def get_entry(self, entry_id: str) -> Optional[KnowledgeEntry]:
        return self._entries.get(entry_id)

    def search(self, query: str) -> List[KnowledgeEntry]:
        query_lower = query.lower()
        with self._lock:
            return [
                e for e in self._entries.values()
                if query_lower in e.topic.lower()
                or query_lower in e.content.lower()
                or any(query_lower in t.lower() for t in e.tags)
            ]

    def search_by_tag(self, tag: str) -> List[KnowledgeEntry]:
        with self._lock:
            return [e for e in self._entries.values() if tag in e.tags]

    def update_entry(self, entry_id: str, content: Optional[str] = None,
                     confidence: Optional[float] = None) -> bool:
        with self._lock:
            entry = self._entries.get(entry_id)
            if not entry:
                return False
            if content is not None:
                entry.content = content
            if confidence is not None:
                entry.confidence = confidence
            entry.updated_at = time.time()
            return True

    def remove_entry(self, entry_id: str) -> bool:
        with self._lock:
            return self._entries.pop(entry_id, None) is not None

    def get_all_entries(self) -> List[KnowledgeEntry]:
        return list(self._entries.values())

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "total_entries": len(self._entries),
                "topics": len(set(e.topic for e in self._entries.values())),
                "avg_confidence": round(
                    sum(e.confidence for e in self._entries.values()) /
                    max(len(self._entries), 1), 2
                ),
            }
