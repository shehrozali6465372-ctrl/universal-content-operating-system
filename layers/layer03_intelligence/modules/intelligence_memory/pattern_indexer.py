"""Pattern Indexer — Index and retrieve patterns from past decisions."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional


class Pattern:
    """A learned pattern from past intelligence."""
    __slots__ = ("pattern_id", "pattern_type", "description", "frequency",
                 "confidence_trend", "tags", "metadata", "created_at", "last_seen")

    def __init__(self, pattern_type: str = "", description: str = "") -> None:
        self.pattern_id = f"pat_{next(_PAT_COUNTER)}"
        self.pattern_type = pattern_type  # topic, timing, audience, content, engagement
        self.description = description
        self.frequency = 1
        self.confidence_trend: List[float] = []
        self.tags: List[str] = []
        self.metadata: Dict[str, Any] = {}
        self.created_at = time.time()
        self.last_seen = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "confidence_avg": round(sum(self.confidence_trend) / max(len(self.confidence_trend), 1), 3),
            "tags": self.tags,
        }


_PAT_COUNTER = itertools.count(1)


class PatternIndexer:
    """Indexes and retrieves patterns from intelligence history."""

    def __init__(self) -> None:
        self._patterns: Dict[str, Pattern] = {}
        self._type_index: Dict[str, List[str]] = {}
        self._tag_index: Dict[str, List[str]] = {}

    def index(self, pattern_type: str, description: str, confidence: float = 0.5,
              tags: Optional[List[str]] = None, metadata: Optional[Dict] = None) -> Pattern:
        """Index a new pattern or update existing one."""
        # Check for similar existing pattern
        existing = self._find_similar(pattern_type, description)
        if existing:
            existing.frequency += 1
            existing.confidence_trend.append(confidence)
            existing.last_seen = time.time()
            if tags:
                existing.tags = list(set(existing.tags + tags))
            return existing

        p = Pattern(pattern_type=pattern_type, description=description)
        p.confidence_trend.append(confidence)
        p.tags = tags or []
        p.metadata = metadata or {}

        self._patterns[p.pattern_id] = p
        self._type_index.setdefault(pattern_type, []).append(p.pattern_id)
        for tag in p.tags:
            self._tag_index.setdefault(tag, []).append(p.pattern_id)
        return p

    def get(self, pattern_id: str) -> Optional[Pattern]:
        return self._patterns.get(pattern_id)

    def search(self, pattern_type: Optional[str] = None, tag: Optional[str] = None,
               min_frequency: int = 1, min_confidence: float = 0.0) -> List[Pattern]:
        """Search patterns by criteria."""
        candidates: List[Pattern] = []
        if pattern_type:
            ids = self._type_index.get(pattern_type, [])
            candidates = [self._patterns[i] for i in ids if i in self._patterns]
        elif tag:
            ids = self._tag_index.get(tag, [])
            candidates = [self._patterns[i] for i in ids if i in self._patterns]
        else:
            candidates = list(self._patterns.values())

        return [
            p for p in candidates
            if p.frequency >= min_frequency
            and (sum(p.confidence_trend) / max(len(p.confidence_trend), 1)) >= min_confidence
        ]

    def get_frequent(self, top_k: int = 10) -> List[Pattern]:
        """Get most frequent patterns."""
        sorted_p = sorted(self._patterns.values(), key=lambda p: p.frequency, reverse=True)
        return sorted_p[:top_k]

    def get_high_confidence(self, min_conf: float = 0.7, top_k: int = 10) -> List[Pattern]:
        """Get patterns with high average confidence."""
        scored = [(p, sum(p.confidence_trend) / max(len(p.confidence_trend), 1)) for p in self._patterns.values()]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, s in scored if s >= min_conf][:top_k]

    def _find_similar(self, pattern_type: str, description: str) -> Optional[Pattern]:
        for p in self._patterns.values():
            if p.pattern_type == pattern_type and p.description.lower() == description.lower():
                return p
        return None

    @property
    def count(self) -> int:
        return len(self._patterns)

    def clear(self) -> None:
        self._patterns.clear()
        self._type_index.clear()
        self._tag_index.clear()
