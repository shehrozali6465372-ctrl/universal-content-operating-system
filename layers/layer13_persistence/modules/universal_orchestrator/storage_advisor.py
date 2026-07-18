"""storage_advisor.py — Storage advisor."""
from __future__ import annotations
from typing import Any, Dict, List


class StorageAdvisor:
    """Provides storage recommendations."""

    def __init__(self) -> None:
        self._recommendations: List[Dict[str, Any]] = []

    def analyze(self, metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
        recs = []
        if metrics.get("storage_used_gb", 0) > 100:
            recs.append({"type": "archive", "message": "Consider archiving old data"})
        if metrics.get("cache_hit_rate", 1.0) < 0.5:
            recs.append({"type": "cache", "message": "Increase cache size"})
        if metrics.get("query_latency_ms", 0) > 200:
            recs.append({"type": "index", "message": "Add indexes for slow queries"})
        self._recommendations.extend(recs)
        return recs

    def get_recommendations(self) -> List[Dict[str, Any]]:
        return list(self._recommendations)

    def stats(self) -> Dict[str, Any]:
        return {"recommendations": len(self._recommendations)}
