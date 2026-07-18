"""business_memory_store.py — Business memory persistence."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.ai_memory_persistence.base_memory_store import BaseMemoryStore, MemoryEntry


class BusinessMemoryStore(BaseMemoryStore):
    """Stores business-related memories (campaigns, strategies, revenue)."""

    def __init__(self, max_entries: int = 5000) -> None:
        super().__init__("business", max_entries)
        self._campaigns: Dict[str, Dict[str, Any]] = {}
        self._revenue_history: List[Dict[str, Any]] = []

    def store(self, key: str, value: Any, metadata: Dict[str, Any] = None) -> MemoryEntry:
        entry = MemoryEntry(key, value, "business")
        if metadata:
            entry.metadata = metadata
        self._store[key] = entry
        return entry

    def retrieve(self, key: str) -> Optional[MemoryEntry]:
        entry = self._store.get(key)
        if entry:
            entry.access_count += 1
        return entry

    def store_campaign(self, campaign_id: str, data: Dict[str, Any]) -> None:
        self._campaigns[campaign_id] = data

    def get_campaign(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        return self._campaigns.get(campaign_id)

    def record_revenue(self, amount: float, source: str, metadata: Dict[str, Any] = None) -> None:
        import time
        self._revenue_history.append({"amount": amount, "source": source,
                                       "timestamp": time.time(), "metadata": metadata or {}})

    def get_revenue_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self._revenue_history[-limit:]

    def total_revenue(self) -> float:
        return sum(r["amount"] for r in self._revenue_history)

    def stats(self) -> Dict[str, Any]:
        base = super().stats()
        base["campaigns"] = len(self._campaigns)
        base["revenue_entries"] = len(self._revenue_history)
        return base
