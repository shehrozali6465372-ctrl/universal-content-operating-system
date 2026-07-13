"""
Source Registry
Layer 2: Research Engine — Module 5

Manages knowledge sources:
- Register and track sources
- Source reliability scoring
- Source health monitoring
- Source filtering by type and reliability
"""

from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional


class KnowledgeSource:
    """A registered knowledge source."""

    __slots__ = (
        "source_id", "name", "source_type", "url",
        "reliability", "fetch_fn", "category",
        "is_active", "fetch_count", "error_count",
        "last_fetch", "last_error", "avg_fetch_time_ms",
    )

    SOURCE_TYPES = ["web", "rss", "api", "document", "manual", "social"]

    def __init__(
        self,
        name: str,
        source_type: str = "web",
        url: str = "",
        reliability: float = 0.7,
        fetch_fn: Optional[Callable] = None,
        category: str = "general",
    ):
        self.source_id = f"src_{name.lower().replace(' ', '_')}_{int(datetime.now(timezone.utc).timestamp())}"
        self.name = name
        self.source_type = source_type if source_type in self.SOURCE_TYPES else "web"
        self.url = url
        self.reliability = max(0.0, min(1.0, reliability))
        self.fetch_fn = fetch_fn
        self.category = category
        self.is_active = True
        self.fetch_count = 0
        self.error_count = 0
        self.last_fetch: Optional[str] = None
        self.last_error: Optional[str] = None
        self.avg_fetch_time_ms = 0.0

    def health(self) -> dict:
        success_rate = (
            (self.fetch_count - self.error_count) / self.fetch_count
            if self.fetch_count > 0 else 0.0
        )
        return {
            "source_id": self.source_id, "name": self.name,
            "type": self.source_type, "active": self.is_active,
            "reliability": self.reliability, "success_rate": round(success_rate, 3),
            "fetch_count": self.fetch_count, "error_count": self.error_count,
            "last_fetch": self.last_fetch, "last_error": self.last_error,
        }

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id, "name": self.name,
            "source_type": self.source_type, "url": self.url,
            "reliability": self.reliability, "category": self.category,
            "is_active": self.is_active, "fetch_count": self.fetch_count,
            "error_count": self.error_count, "last_fetch": self.last_fetch,
            "last_error": self.last_error, "avg_fetch_time_ms": self.avg_fetch_time_ms,
        }


class SourceRegistry:
    """Registry for knowledge sources."""

    def __init__(self):
        self._sources: Dict[str, KnowledgeSource] = {}

    def register(
        self,
        name: str,
        source_type: str = "web",
        url: str = "",
        reliability: float = 0.7,
        fetch_fn: Optional[Callable] = None,
        category: str = "general",
    ) -> KnowledgeSource:
        """Register a new source."""
        src = KnowledgeSource(name, source_type, url, reliability, fetch_fn, category)
        self._sources[src.source_id] = src
        return src

    def unregister(self, source_id: str) -> bool:
        if source_id in self._sources:
            del self._sources[source_id]
            return True
        return False

    def get(self, source_id: str) -> Optional[KnowledgeSource]:
        return self._sources.get(source_id)

    def get_by_name(self, name: str) -> Optional[KnowledgeSource]:
        for src in self._sources.values():
            if src.name.lower() == name.lower():
                return src
        return None

    def list_sources(self, source_type: Optional[str] = None, active_only: bool = True) -> List[KnowledgeSource]:
        sources = list(self._sources.values())
        if active_only:
            sources = [s for s in sources if s.is_active]
        if source_type:
            sources = [s for s in sources if s.source_type == source_type]
        return sources

    def get_top_sources(self, count: int = 5) -> List[KnowledgeSource]:
        """Get most reliable sources."""
        return sorted(self._sources.values(), key=lambda s: s.reliability, reverse=True)[:count]

    def get_by_category(self, category: str) -> List[KnowledgeSource]:
        return [s for s in self._sources.values() if s.category == category]

    def deactivate(self, source_id: str) -> bool:
        src = self._sources.get(source_id)
        if src:
            src.is_active = False
            return True
        return False

    def activate(self, source_id: str) -> bool:
        src = self._sources.get(source_id)
        if src:
            src.is_active = True
            return True
        return False

    def health_report(self) -> List[dict]:
        """Health report for all sources."""
        return [s.health() for s in self._sources.values()]
