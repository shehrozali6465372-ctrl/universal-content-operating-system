"""Memory Consolidator — Merge and consolidate similar memory entries."""
from __future__ import annotations
from typing import Any, Dict, List


class ConsolidatedEntry:
    """A consolidated memory entry from multiple similar entries."""
    __slots__ = ("topic", "entries", "merged_data", "confidence", "frequency",
                 "sources", "consolidation_score")

    def __init__(self, topic: str = "") -> None:
        self.topic = topic
        self.entries: List[Dict[str, Any]] = []
        self.merged_data: Dict[str, Any] = {}
        self.confidence = 0.0
        self.frequency = 0
        self.sources: List[str] = []
        self.consolidation_score = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "entry_count": len(self.entries),
            "frequency": self.frequency,
            "confidence": round(self.confidence, 3),
            "sources": self.sources,
            "consolidation_score": round(self.consolidation_score, 3),
        }


class MemoryConsolidator:
    """Consolidates similar memory entries into unified representations."""

    def __init__(self, similarity_threshold: float = 0.7) -> None:
        self._threshold = similarity_threshold

    def consolidate(self, entries: List[Dict[str, Any]]) -> List[ConsolidatedEntry]:
        """Group similar entries and consolidate."""
        if not entries:
            return []

        groups: Dict[str, List[Dict]] = {}
        for entry in entries:
            topic = entry.get("topic", "").lower()
            merged = False
            for key in list(groups.keys()):
                if self._similar(key, topic):
                    groups[key].append(entry)
                    merged = True
                    break
            if not merged:
                groups[topic] = [entry]

        results: List[ConsolidatedEntry] = []
        for topic, group in groups.items():
            ce = ConsolidatedEntry(topic=topic)
            ce.entries = group
            ce.frequency = len(group)
            ce.confidence = self._avg_confidence(group)
            ce.sources = list({e.get("source", "unknown") for e in group})
            ce.merged_data = self._merge_data(group)
            ce.consolidation_score = self._calc_score(ce)
            results.append(ce)

        return sorted(results, key=lambda c: c.consolidation_score, reverse=True)

    def _similar(self, a: str, b: str) -> bool:
        if a == b:
            return True
        words_a = set(a.split())
        words_b = set(b.split())
        if not words_a or not words_b:
            return False
        overlap = len(words_a & words_b) / max(len(words_a | words_b), 1)
        return overlap >= self._threshold

    def _avg_confidence(self, group: List[Dict]) -> float:
        confs = [e.get("confidence", 0.5) for e in group]
        return sum(confs) / max(len(confs), 1)

    def _merge_data(self, group: List[Dict]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for entry in group:
            for k, v in entry.items():
                if k not in ("topic", "source", "confidence"):
                    if k not in merged:
                        merged[k] = v
        return merged

    def _calc_score(self, ce: ConsolidatedEntry) -> float:
        freq_score = min(ce.frequency / 5.0, 1.0)
        return round(0.4 * freq_score + 0.4 * ce.confidence + 0.2 * min(len(ce.sources) / 3.0, 1.0), 3)
