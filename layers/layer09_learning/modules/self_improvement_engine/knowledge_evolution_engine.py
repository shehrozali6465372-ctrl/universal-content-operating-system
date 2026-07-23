"""KnowledgeEvolutionEngine — Merges new research/trends, retires outdated knowledge."""
from __future__ import annotations
import threading
import time
import uuid
from typing import Any, Dict, List, Optional


class KnowledgeEntry:
    __slots__ = ("id", "topic", "category", "content", "source",
                 "confidence", "importance", "status", "created_at",
                 "last_validated", "expires_at", "tags", "version",
                 "parent_id", "validation_count")

    def __init__(self, topic: str, content: str, category: str = "general",
                 source: str = "") -> None:
        self.id = str(uuid.uuid4())[:12]
        self.topic = topic
        self.content = content
        self.category = category
        self.source = source
        self.confidence = 50.0
        self.importance = 50.0
        self.status = "active"
        self.created_at = time.time()
        self.last_validated = time.time()
        self.expires_at = 0.0
        self.tags: List[str] = []
        self.version = 1
        self.parent_id = ""
        self.validation_count = 0

    @property
    def is_expired(self) -> bool:
        return self.expires_at > 0 and time.time() > self.expires_at

    @property
    def freshness_score(self) -> None:
        age_days = (time.time() - self.last_validated) / 86400
        return max(100 - age_days * 2, 0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id, "topic": self.topic, "category": self.category,
            "content": self.content[:200], "source": self.source,
            "confidence": round(self.confidence, 1),
            "importance": round(self.importance, 1),
            "status": self.status, "version": self.version,
            "validations": self.validation_count,
            "expired": self.is_expired,
        }


class KnowledgeEvolutionEngine:
    """Manages knowledge lifecycle: creation, validation, merging, retirement."""
    _instance: Optional["KnowledgeEvolutionEngine"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "KnowledgeEvolutionEngine":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._topic_index: Dict[str, List[str]] = {}
        self._category_index: Dict[str, List[str]] = {}
        self._evolution_log: List[Dict[str, Any]] = []

    def add_knowledge(self, topic: str, content: str, category: str = "general",
                      source: str = "", confidence: float = 50.0,
                      importance: float = 50.0, tags: List[str] = None,
                      ttl_days: int = 0) -> KnowledgeEntry:
        ke = KnowledgeEntry(topic, content, category, source)
        ke.confidence = confidence
        ke.importance = importance
        if tags:
            ke.tags = tags
        if ttl_days > 0:
            ke.expires_at = time.time() + (ttl_days * 86400)
        self._entries[ke.id] = ke
        self._topic_index.setdefault(topic.lower(), []).append(ke.id)
        self._category_index.setdefault(category, []).append(ke.id)
        return ke

    def get_entry(self, kid: str) -> Optional[KnowledgeEntry]:
        return self._entries.get(kid)

    def get_by_topic(self, topic: str) -> List[KnowledgeEntry]:
        ids = self._topic_index.get(topic.lower(), [])
        return sorted(
            [self._entries[i] for i in ids if i in self._entries and self._entries[i].status == "active"],
            key=lambda e: e.importance, reverse=True,
        )

    def get_by_category(self, category: str) -> List[KnowledgeEntry]:
        ids = self._category_index.get(category, [])
        return [self._entries[i] for i in ids if i in self._entries]

    def validate_entry(self, kid: str, confidence_boost: float = 5.0) -> bool:
        ke = self._entries.get(kid)
        if ke:
            ke.validation_count += 1
            ke.last_validated = time.time()
            ke.confidence = min(ke.confidence + confidence_boost, 100)
            return True
        return False

    def merge_knowledge(self, existing_id: str, new_content: str,
                        new_confidence: float = 60.0) -> Optional[KnowledgeEntry]:
        existing = self._entries.get(existing_id)
        if not existing:
            return None
        merged = self.add_knowledge(
            existing.topic, new_content, existing.category, existing.source,
            new_confidence, existing.importance,
        )
        merged.parent_id = existing_id
        merged.version = existing.version + 1
        merged.tags = existing.tags.copy()
        existing.status = "superseded"
        self._evolution_log.append({
            "action": "merge", "parent": existing_id,
            "child": merged.id, "timestamp": time.time(),
        })
        return merged

    def retire_entry(self, kid: str, reason: str = "") -> bool:
        ke = self._entries.get(kid)
        if ke:
            ke.status = "retired"
            self._evolution_log.append({
                "action": "retire", "entry_id": kid,
                "reason": reason, "timestamp": time.time(),
            })
            return True
        return False

    def retire_expired(self) -> int:
        count = 0
        for ke in self._entries.values():
            if ke.status == "active" and ke.is_expired:
                ke.status = "retired"
                count += 1
        return count

    def get_stale_entries(self, max_age_days: int = 90) -> List[KnowledgeEntry]:
        cutoff = time.time() - (max_age_days * 86400)
        return [
            ke for ke in self._entries.values()
            if ke.status == "active" and ke.last_validated < cutoff
        ]

    def get_knowledge_report(self) -> Dict[str, Any]:
        entries = list(self._entries.values())
        return {
            "total_entries": len(entries),
            "active": sum(1 for e in entries if e.status == "active"),
            "retired": sum(1 for e in entries if e.status == "retired"),
            "superseded": sum(1 for e in entries if e.status == "superseded"),
            "expired": sum(1 for e in entries if e.is_expired),
            "by_category": {c: len(ids) for c, ids in self._category_index.items()},
            "avg_confidence": round(
                sum(e.confidence for e in entries) / len(entries), 1
            ) if entries else 0,
            "total_validations": sum(e.validation_count for e in entries),
            "evolutions": len(self._evolution_log),
        }

    def stats(self) -> Dict[str, Any]:
        return {
            "entries": len(self._entries),
            "topics": len(self._topic_index),
            "categories": len(self._category_index),
        }


def get_knowledge_evolution() -> KnowledgeEvolutionEngine:
    return KnowledgeEvolutionEngine()
