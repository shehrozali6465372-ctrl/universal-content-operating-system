"""Data models for AI Memory Layer."""
from __future__ import annotations

import uuid
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class MemoryType(str, Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SEMANTIC = "semantic"
    EPISODIC = "episodic"
    CONVERSATIONAL = "conversational"
    PROCEDURAL = "procedural"
    WORKING = "working"


@dataclass
class MemoryEntry:
    """Single memory entry."""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    content: str = ""
    memory_type: MemoryType = MemoryType.SHORT_TERM
    embedding: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    importance: float = 0.5
    confidence: float = 1.0
    access_count: int = 0
    created_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    expires_at: Optional[float] = None

    @property
    def is_expired(self) -> bool:
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def touch(self) -> None:
        self.last_accessed = time.time()
        self.access_count += 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id, "content": self.content[:200],
            "memory_type": self.memory_type.value, "tags": self.tags,
            "importance": self.importance, "confidence": self.confidence,
            "access_count": self.access_count,
            "created_at": self.created_at, "last_accessed": self.last_accessed,
        }


@dataclass
class MemoryQuery:
    """Query for searching memories."""
    query_text: str = ""
    memory_type: Optional[MemoryType] = None
    tags: List[str] = field(default_factory=list)
    min_importance: float = 0.0
    limit: int = 10
    include_expired: bool = False
    sort_by: str = "relevance"  # relevance, recency, importance

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_text": self.query_text[:100],
            "memory_type": self.memory_type.value if self.memory_type else None,
            "tags": self.tags, "limit": self.limit,
        }
