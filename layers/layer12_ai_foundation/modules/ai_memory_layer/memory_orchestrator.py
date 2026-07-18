"""MemoryOrchestrator — full memory system pipeline."""
from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .memory_router import MemoryRouter
from .semantic_memory import SemanticMemory
from .episodic_memory import EpisodicMemory
from .vector_memory import VectorMemory
from .conversation_memory import ConversationMemory
from .long_term_memory import LongTermMemory
from .working_memory import WorkingMemory
from .memory_cache import MemoryCache
from .memory_metrics import MemoryMetrics
from .memory_events import MemoryEvents
from .memory_health import MemoryHealth


class MemoryOrchestrator:
    """Full memory system pipeline orchestrator."""

    def __init__(self) -> None:
        self.router = MemoryRouter()
        self.semantic = SemanticMemory()
        self.episodic = EpisodicMemory()
        self.vector = VectorMemory()
        self.conversation = ConversationMemory()
        self.long_term = LongTermMemory()
        self.working = WorkingMemory()
        self.cache = MemoryCache()
        self.metrics = MemoryMetrics()
        self.events = MemoryEvents()
        self.health = MemoryHealth()
        self._is_running = False

    def start(self) -> bool:
        self._is_running = True
        self.events.publish("memory_started")
        return True

    def stop(self) -> bool:
        self._is_running = False
        self.events.publish("memory_stopped")
        return True

    def store(self, content: str, memory_type: str = "semantic",
              tags: Optional[List[str]] = None, importance: float = 0.5) -> Dict[str, Any]:
        start = time.time()
        from .models import MemoryEntry, MemoryType
        mt = MemoryType(memory_type) if memory_type in [t.value for t in MemoryType] else MemoryType.SEMANTIC
        entry = MemoryEntry(content=content, memory_type=mt,
                           tags=tags or [], importance=importance)
        self.router.store(entry)
        self.metrics.record_store()
        elapsed = (time.time() - start) * 1000
        self.metrics.record_latency(elapsed)
        self.events.publish("memory_stored", {"entry_id": entry.entry_id})
        return entry.to_dict()

    def retrieve(self, entry_id: str) -> Optional[Dict[str, Any]]:
        cached = self.cache.get(entry_id)
        if cached:
            self.metrics.record_retrieval(True)
            return cached.to_dict()
        entry = self.router.retrieve(entry_id)
        hit = entry is not None
        self.metrics.record_retrieval(hit)
        if entry:
            self.cache.set(entry)
            return entry.to_dict()
        return None

    def search(self, query: str, memory_type: Optional[str] = None,
               limit: int = 10) -> List[Dict[str, Any]]:
        self.metrics.record_search()
        from .models import MemoryType, MemoryQuery
        mt = MemoryType(memory_type) if memory_type else None
        q = MemoryQuery(query_text=query, memory_type=mt, limit=limit)
        results = self.router.search(q)
        return [e.to_dict() for e in results]

    def get_health(self) -> Dict[str, Any]:
        return self.health.overall_health()

    def get_stats(self) -> Dict[str, Any]:
        return {**self.router.stats(), "metrics": self.metrics.to_dict()}
