"""EvidenceCollector — gather and weight evidence for reasoning."""
from __future__ import annotations

from typing import Any, Dict, List


class EvidenceCollector:
    """Gather and weight evidence for reasoning chains."""

    def __init__(self) -> None:
        self._evidence: List[Dict[str, Any]] = []

    def add(self, content: str, source: str = "", weight: float = 1.0,
            confidence: float = 0.8) -> Dict[str, Any]:
        entry = {"content": content, "source": source,
                 "weight": weight, "confidence": confidence}
        self._evidence.append(entry)
        return entry

    def get_sorted(self, by: str = "confidence") -> List[Dict[str, Any]]:
        return sorted(self._evidence, key=lambda e: e.get(by, 0), reverse=True)

    def get_top(self, n: int = 5) -> List[Dict[str, Any]]:
        return self.get_sorted()[:n]

    def filter_by_source(self, source: str) -> List[Dict[str, Any]]:
        return [e for e in self._evidence if e["source"] == source]

    def aggregate_confidence(self) -> float:
        if not self._evidence:
            return 0.0
        total = sum(e["confidence"] * e["weight"] for e in self._evidence)
        weights = sum(e["weight"] for e in self._evidence)
        return total / weights if weights else 0.0

    def count(self) -> int:
        return len(self._evidence)

    def clear(self) -> None:
        self._evidence.clear()
