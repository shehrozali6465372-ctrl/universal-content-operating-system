"""Memory Search — Search published history by topic, platform, date, tags."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.publishing_memory.publish_history import (
    PublishHistory, PublishRecord,
)


class SearchFilter:
    """Filter criteria for searching memory."""

    __slots__ = ("platform", "content_type", "tags", "success_only",
                 "after_date", "before_date", "text_query")

    def __init__(self) -> None:
        self.platform: str = ""
        self.content_type: str = ""
        self.tags: List[str] = []
        self.success_only: bool = False
        self.after_date: float = 0.0
        self.before_date: float = 0.0
        self.text_query: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "content_type": self.content_type,
            "tags": self.tags,
            "success_only": self.success_only,
            "after_date": self.after_date,
            "before_date": self.before_date,
            "text_query": self.text_query,
        }


class SearchResult:
    """Search result with records and metadata."""

    __slots__ = ("records", "total_matches", "search_time_ms")

    def __init__(self) -> None:
        self.records: List[PublishRecord] = []
        self.total_matches: int = 0
        self.search_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_matches": self.total_matches,
            "search_time_ms": round(self.search_time_ms, 2),
            "records": [r.to_dict() for r in self.records[:20]],
        }


class MemorySearch:
    """Search published history with flexible filters."""

    def __init__(self, history: Optional[PublishHistory] = None) -> None:
        self._history = history or PublishHistory()
        self._search_count = 0

    def search(self, search_filter: SearchFilter) -> SearchResult:
        start = time.time()
        result = SearchResult()
        records = self._history.get_all()

        if search_filter.platform:
            records = [r for r in records if r.platform == search_filter.platform]
        if search_filter.content_type:
            records = [r for r in records if r.content_type == search_filter.content_type]
        if search_filter.tags:
            records = [r for r in records if any(t in r.tags for t in search_filter.tags)]
        if search_filter.success_only:
            records = [r for r in records if r.success]
        if search_filter.after_date > 0:
            records = [r for r in records if r.published_at >= search_filter.after_date]
        if search_filter.before_date > 0:
            records = [r for r in records if r.published_at <= search_filter.before_date]
        if search_filter.text_query:
            q = search_filter.text_query.lower()
            records = [r for r in records if q in r.content_summary.lower()]

        result.records = records
        result.total_matches = len(records)
        result.search_time_ms = (time.time() - start) * 1000
        self._search_count += 1
        return result

    def find_similar(self, record: PublishRecord, limit: int = 5) -> List[PublishRecord]:
        all_records = self._history.get_all()
        scored: List[tuple] = []
        for r in all_records:
            if r.record_id == record.record_id:
                continue
            score = 0.0
            if r.platform == record.platform:
                score += 0.4
            if r.content_type == record.content_type:
                score += 0.3
            shared_tags = set(r.tags) & set(record.tags)
            score += min(0.3, len(shared_tags) * 0.1)
            scored.append((r, score))
        scored.sort(key=lambda x: x[1], reverse=True)
        return [r for r, _ in scored[:limit]]

    @property
    def search_count(self) -> int:
        return self._search_count
