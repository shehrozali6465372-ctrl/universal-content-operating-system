"""Trend Collector — Collects and normalizes trend data from multiple sources."""
from __future__ import annotations
import hashlib
import time
from typing import Any, Dict, List, Optional


class TrendEntry:
    """A single trend data point."""
    __slots__ = ("topic", "source", "score", "volume", "timestamp",
                 "region", "category", "metadata")

    def __init__(self, topic: str = "", source: str = "", score: float = 0.0,
                 volume: int = 0, timestamp: float = 0.0, region: str = "global",
                 category: str = "general", metadata: Optional[Dict] = None):
        self.topic = topic
        self.source = source
        self.score = score
        self.volume = volume
        self.timestamp = timestamp or time.time()
        self.region = region
        self.category = category
        self.metadata = metadata or {}

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic, "source": self.source, "score": round(self.score, 3),
            "volume": self.volume, "timestamp": self.timestamp, "region": self.region,
            "category": self.category, "metadata": dict(self.metadata),
        }

    @property
    def entry_id(self) -> str:
        return hashlib.sha256(f"{self.topic}:{self.source}:{self.timestamp}".encode()).hexdigest()[:16]


class TrendCollector:
    """Collects trend data from registered sources and deduplicates."""

    def __init__(self) -> None:
        self._entries: List[TrendEntry] = []
        self._seen_ids: set = set()

    def collect(self, topic: str, source: str, score: float = 0.0,
                volume: int = 0, region: str = "global",
                category: str = "general", metadata: Optional[Dict] = None,
                timestamp: float = 0.0) -> TrendEntry:
        entry = TrendEntry(topic, source, score, volume, timestamp or time.time(), region, category, metadata)
        if entry.entry_id not in self._seen_ids:
            self._entries.append(entry)
            self._seen_ids.add(entry.entry_id)
        return entry

    def collect_batch(self, entries: List[Dict[str, Any]]) -> List[TrendEntry]:
        results = []
        for e in entries:
            r = self.collect(
                topic=e.get("topic", ""), source=e.get("source", ""),
                score=e.get("score", 0.0), volume=e.get("volume", 0),
                region=e.get("region", "global"), category=e.get("category", "general"),
                metadata=e.get("metadata"),
            )
            results.append(r)
        return results

    def get_entries(self, topic: Optional[str] = None, source: Optional[str] = None) -> List[TrendEntry]:
        result = self._entries
        if topic:
            result = [e for e in result if topic.lower() in e.topic.lower()]
        if source:
            result = [e for e in result if e.source == source]
        return result

    def get_topics(self) -> List[str]:
        return list(dict.fromkeys(e.topic for e in self._entries))

    def count(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        self._entries.clear()
        self._seen_ids.clear()

    def to_dict(self) -> Dict:
        return {"entries": [e.to_dict() for e in self._entries], "count": self.count()}
