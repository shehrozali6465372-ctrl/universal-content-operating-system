"""LongTermMemory — Persistent AI memory with consolidation and forgetting.

Features:
- Remember/forget facts and knowledge
- Memory consolidation (short-term → long-term)
- Importance scoring
- Temporal decay (less relevant memories fade)
- Memory categories (fact, preference, event, lesson)
- Memory search and retrieval
- Memory statistics and health
"""
from __future__ import annotations
import time
import hashlib
import math
import threading
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum


class MemoryType(str, Enum):
    FACT = "fact"
    PREFERENCE = "preference"
    EVENT = "event"
    LESSON = "lesson"
    PERSON = "person"
    TOPIC = "topic"


class Memory:
    """A single memory entry."""

    def __init__(self, content: str, memory_type: MemoryType = MemoryType.FACT,
                 importance: float = 0.5, metadata: Dict[str, Any] = None):
        self.memory_id = hashlib.sha256(
            f"{time.time()}:{content[:100]}".encode()
        ).hexdigest()[:16]
        self.content = content
        self.memory_type = memory_type
        self.importance = max(0.0, min(1.0, importance))
        self.metadata = metadata or {}
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
        self.consolidated = False  # True = long-term memory

    def access(self):
        """Record an access event."""
        self.last_accessed = time.time()
        self.access_count += 1

    def decay(self, half_life_days: float = 30.0):
        """Apply temporal decay to importance."""
        age_days = (time.time() - self.created_at) / 86400
        decay_factor = math.pow(0.5, age_days / half_life_days)
        # Access recency boosts importance
        access_boost = min(0.3, self.access_count * 0.05)
        self.importance = max(0.0, self.importance * decay_factor + access_boost)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "content": self.content[:500],
            "type": self.memory_type.value,
            "importance": round(self.importance, 3),
            "consolidated": self.consolidated,
            "access_count": self.access_count,
            "age_hours": round((time.time() - self.created_at) / 3600, 1),
        }


class LongTermMemory:
    """AI memory system with consolidation and forgetting."""

    def __init__(self, embedding_engine: Any = None, store: Any = None):
        self._engine = embedding_engine
        self._store = store
        self._lock = threading.Lock()

        # Memory stores
        self._short_term: Dict[str, Memory] = {}  # Recent, unconsolidated
        self._long_term: Dict[str, Memory] = {}   # Consolidated
        self._memories: Dict[str, Memory] = {}     # All memories

        # Configuration
        self._max_short_term = 1000
        self._consolidation_threshold = 3  # Access count to promote
        self._forgetting_threshold = 0.05  # Importance below this = forget
        self._half_life_days = 30.0

        # Stats
        self._total_remembered = 0
        self._total_forgotten = 0
        self._total_consolidated = 0

    def remember(self, content: str, memory_type: str = "fact",
                 importance: float = 0.5, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Store a new memory.

        Args:
            content: What to remember
            memory_type: fact, preference, event, lesson, person, topic
            importance: 0.0 to 1.0
            metadata: Additional metadata

        Returns:
            Memory info dict
        """
        mt = MemoryType(memory_type) if memory_type in [t.value for t in MemoryType] else MemoryType.FACT
        memory = Memory(content, mt, importance, metadata)

        with self._lock:
            self._memories[memory.memory_id] = memory
            self._short_term[memory.memory_id] = memory
            self._total_remembered += 1

        # Store vector for semantic search
        if self._engine and self._store:
            vector = self._engine.embed(content)
            self._store.upsert(
                record_id=f"mem_{memory.memory_id}",
                vector=vector,
                metadata={
                    "text": content,
                    "memory_id": memory.memory_id,
                    "memory_type": memory_type,
                    "importance": importance,
                    "source": "long_term_memory",
                },
                namespace="memory",
            )

        return memory.to_dict()

    def forget(self, memory_id: str) -> bool:
        """Forget a specific memory."""
        with self._lock:
            memory = self._memories.pop(memory_id, None)
            if memory:
                self._short_term.pop(memory_id, None)
                self._long_term.pop(memory_id, None)
                self._total_forgotten += 1

                # Remove from vector store
                if self._store:
                    self._store.delete(f"mem_{memory_id}")

                return True
            return False

    def forget_by_type(self, memory_type: str) -> int:
        """Forget all memories of a specific type."""
        to_forget = [
            mid for mid, m in self._memories.items()
            if m.memory_type.value == memory_type
        ]
        for mid in to_forget:
            self.forget(mid)
        return len(to_forget)

    def recall(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Recall a specific memory by ID."""
        memory = self._memories.get(memory_id)
        if memory:
            memory.access()
            return memory.to_dict()
        return None

    def search(self, query: str, top_k: int = 5, memory_type: str = None,
               min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """Semantic search through memories.

        Args:
            query: Search query
            top_k: Number of results
            memory_type: Filter by type
            min_importance: Minimum importance score

        Returns:
            List of matching memories
        """
        results = []

        # Text search
        query_lower = query.lower()
        for memory in self._memories.values():
            if memory_type and memory.memory_type.value != memory_type:
                continue
            if memory.importance < min_importance:
                continue

            # Simple text match
            content_lower = memory.content.lower()
            words = query_lower.split()
            match_score = sum(1 for w in words if w in content_lower) / max(1, len(words))

            if match_score > 0:
                memory.access()
                results.append({
                    **memory.to_dict(),
                    "match_score": round(match_score, 3),
                })

        # Sort by combined importance and match
        results.sort(key=lambda x: x["importance"] * 0.5 + x["match_score"] * 0.5, reverse=True)
        return results[:top_k]

    def consolidate(self) -> Dict[str, Any]:
        """Consolidate short-term memories into long-term.

        Memories with enough access counts get promoted.
        Unimportant old memories get forgotten.
        """
        promoted = 0
        forgotten = 0

        with self._lock:
            to_promote = []
            to_forget = []

            for mid, memory in list(self._short_term.items()):
                memory.decay(self._half_life_days)

                if memory.importance < self._forgetting_threshold:
                    to_forget.append(mid)
                elif memory.access_count >= self._consolidation_threshold:
                    to_promote.append(mid)

            for mid in to_promote:
                memory = self._short_term.pop(mid, None)
                if memory:
                    memory.consolidated = True
                    self._long_term[mid] = memory
                    promoted += 1
                    self._total_consolidated += 1

            for mid in to_forget:
                memory = self._short_term.pop(mid, None)
                if memory:
                    self._memories.pop(mid, None)
                    forgotten += 1
                    self._total_forgotten += 1

        return {
            "promoted_to_long_term": promoted,
            "forgotten": forgotten,
            "short_term_count": len(self._short_term),
            "long_term_count": len(self._long_term),
        }

    def get_by_type(self, memory_type: str) -> List[Dict[str, Any]]:
        """Get all memories of a specific type."""
        return [
            m.to_dict() for m in self._memories.values()
            if m.memory_type.value == memory_type
        ]

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recently created memories."""
        sorted_memories = sorted(
            self._memories.values(),
            key=lambda m: m.created_at, reverse=True,
        )
        return [m.to_dict() for m in sorted_memories[:limit]]

    def get_important(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most important memories."""
        sorted_memories = sorted(
            self._memories.values(),
            key=lambda m: m.importance, reverse=True,
        )
        return [m.to_dict() for m in sorted_memories[:limit]]

    def count(self) -> Dict[str, int]:
        """Count memories by category."""
        by_type = {}
        for m in self._memories.values():
            t = m.memory_type.value
            by_type[t] = by_type.get(t, 0) + 1
        return {
            "total": len(self._memories),
            "short_term": len(self._short_term),
            "long_term": len(self._long_term),
            "by_type": by_type,
        }

    def stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        counts = self.count()
        avg_importance = 0.0
        if self._memories:
            avg_importance = sum(m.importance for m in self._memories.values()) / len(self._memories)

        return {
            **counts,
            "avg_importance": round(avg_importance, 3),
            "total_remembered": self._total_remembered,
            "total_forgotten": self._total_forgotten,
            "total_consolidated": self._total_consolidated,
            "consolidation_threshold": self._consolidation_threshold,
            "forgetting_threshold": self._forgetting_threshold,
        }
