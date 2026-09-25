"""Trend Collector — Collects and normalizes trend data from multiple sources."""
from __future__ import annotations
import hashlib
import time
import copy
import math
from threading import RLock
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

    def __init__(self, max_entries: int = 5000) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self._entries: List[TrendEntry] = []
        self._seen_ids: set = set()
        self._max_entries = max_entries
        self._lock = RLock()

    def collect(self, topic: str, source: str, score: float = 0.0,
                volume: int = 0, region: str = "global",
                category: str = "general", metadata: Optional[Dict] = None,
                timestamp: float = 0.0) -> TrendEntry:
        if not topic.strip() or not source.strip():
            raise ValueError("topic and source must not be empty")
        if not isinstance(score, (int, float)) or not math.isfinite(float(score)):
            raise ValueError("score must be finite")
        if volume < 0:
            raise ValueError("volume must be non-negative")
        entry = TrendEntry(topic, source, float(score), volume, timestamp or time.time(), region, category, copy.deepcopy(metadata or {}))
        with self._lock:
            if entry.entry_id not in self._seen_ids:
                self._entries.append(entry)
                self._seen_ids.add(entry.entry_id)
                if len(self._entries) > self._max_entries:
                    evicted = self._entries.pop(0)
                    self._seen_ids.discard(evicted.entry_id)
            return copy.deepcopy(entry)

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
        with self._lock:
            result = self._entries
            if topic:
                result = [e for e in result if topic.lower() in e.topic.lower()]
            if source:
                result = [e for e in result if e.source == source]
            return copy.deepcopy(result)

    def get_topics(self) -> List[str]:
        with self._lock:
            return list(dict.fromkeys(e.topic for e in self._entries))

    def count(self) -> int:
        with self._lock:
            return len(self._entries)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self._seen_ids.clear()

    def to_dict(self) -> Dict:
        with self._lock:
            return {"entries": [e.to_dict() for e in self._entries], "count": len(self._entries)}
