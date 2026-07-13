"""
Knowledge Collector Manager
Layer 2: Research Engine — Module 5

Central manager for knowledge collection:
- Knowledge entry CRUD
- Source management
- Content cleaning pipeline
- Deduplication
- Metadata extraction
- Caching
- Persistent storage
- Health check
- Evidence-based confidence
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.knowledge_collector.knowledge_entry import KnowledgeEntry
from layers.layer02_research.modules.knowledge_collector.source_registry import SourceRegistry
from layers.layer02_research.modules.knowledge_collector.content_cleaner import ContentCleaner
from layers.layer02_research.modules.knowledge_collector.deduplicator import Deduplicator
from layers.layer02_research.modules.knowledge_collector.metadata_extractor import MetadataExtractor
from layers.layer02_research.modules.knowledge_collector.cache_manager import KnowledgeCache
from layers.layer02_research.shared.confidence_engine import ConfidenceEngine, ConfidenceResult
from layers.layer02_research.modules.knowledge_collector.exceptions import (
    EntryNotFoundError,
)


class KnowledgeCollectorManager:
    """Central knowledge collection engine with evidence-based confidence."""

    def __init__(self, storage_path: Optional[str] = None, cache_size: int = 500):
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None

        # Sub-components
        self.source_registry = SourceRegistry()
        self.content_cleaner = ContentCleaner()
        self.deduplicator = Deduplicator()
        self.metadata_extractor = MetadataExtractor()
        self.cache = KnowledgeCache(max_size=cache_size)
        self.confidence_engine = ConfidenceEngine()

        self._history: List[dict] = []
        self._max_history = 500

        self._load()

    # ── CRUD ────────────────────────────────

    def collect(
        self,
        title: str = "",
        content: str = "",
        source: str = "",
        source_url: str = "",
        published_at: str = "",
        author: str = "",
        language: str = "en",
        keywords: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        category: str = "general",
        clean: bool = True,
        extract_metadata: bool = True,
        dedup: bool = True,
    ) -> KnowledgeEntry:
        """Collect a new knowledge entry with full pipeline."""
        # Clean content
        if clean:
            title = self.content_cleaner.clean(title)
            content = self.content_cleaner.clean(content)
            if not language or language == "unknown":
                language = self.content_cleaner.detect_language(content)

        # Create entry
        entry = KnowledgeEntry(
            title=title, source=source, source_url=source_url,
            published_at=published_at, author=author, language=language,
            content=content, keywords=keywords or [], tags=tags or [],
            category=category,
        )

        # Extract metadata
        if extract_metadata:
            meta = self.metadata_extractor.extract_all(content, title)
            if not entry.keywords:
                entry.keywords = [kw for kw, _ in meta.get("keywords", [])]
            if entry.category == "general":
                entry.category = meta.get("category", "general")
            if not tags:
                entry.tags.append(meta.get("sentiment", "neutral"))

        # Deduplication
        if dedup:
            existing = self.deduplicator.check_exact(entry)
            if existing:
                entry.is_duplicate = True
                entry.duplicate_of = existing

        with self._lock:
            self._entries[entry.entry_id] = entry
            self.deduplicator.register(entry)
            self._record_event("entry_collected", entry.entry_id, {
                "title": title[:100], "source": source, "duplicate": entry.is_duplicate,
            })
            self._save()

        # Cache it
        self.cache.put(entry.entry_id, entry.to_dict(), ttl=7200)

        return entry

    def get_entry(self, entry_id: str) -> KnowledgeEntry:
        # Try cache first
        cached = self.cache.get(entry_id)
        if cached:
            return KnowledgeEntry.from_dict(cached)

        with self._lock:
            entry = self._entries.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"Entry '{entry_id}' not found")
        self.cache.put(entry_id, entry.to_dict())
        return entry

    def update_entry(self, entry_id: str, **kwargs) -> KnowledgeEntry:
        with self._lock:
            entry = self._entries.get(entry_id)
            if entry is None:
                raise EntryNotFoundError(f"Entry '{entry_id}' not found")
            for key, val in kwargs.items():
                if hasattr(entry, key):
                    setattr(entry, key, val)
            self._record_event("entry_updated", entry_id, {"fields": list(kwargs.keys())})
            self._save()
            self.cache.delete(entry_id)
        return entry

    def delete_entry(self, entry_id: str) -> bool:
        with self._lock:
            if entry_id not in self._entries:
                raise EntryNotFoundError(f"Entry '{entry_id}' not found")
            del self._entries[entry_id]
            self._record_event("entry_deleted", entry_id, {})
            self._save()
            self.cache.delete(entry_id)
        return True

    def list_entries(
        self,
        source: Optional[str] = None,
        category: Optional[str] = None,
        status: Optional[str] = None,
        active_only: bool = True,
    ) -> List[KnowledgeEntry]:
        with self._lock:
            entries = list(self._entries.values())
        if active_only:
            entries = [e for e in entries if e.status == "active"]
        if source:
            entries = [e for e in entries if e.source == source]
        if category:
            entries = [e for e in entries if e.category == category]
        if status:
            entries = [e for e in entries if e.status == status]
        return entries

    def exists(self, content_hash: str) -> bool:
        with self._lock:
            return any(e.content_hash == content_hash for e in self._entries.values())

    # ── Intelligence ────────────────────────

    def get_top_entries(self, count: int = 10) -> List[KnowledgeEntry]:
        """Get highest scoring entries."""
        with self._lock:
            entries = list(self._entries.values())
        entries = [e for e in entries if e.status == "active" and not e.is_duplicate]
        return sorted(entries, key=lambda e: e.composite_score, reverse=True)[:count]

    def search_by_keyword(self, keyword: str, max_results: int = 20) -> List[KnowledgeEntry]:
        """Search entries by keyword."""
        kw = keyword.lower()
        results = []
        with self._lock:
            entries = list(self._entries.values())
        for entry in entries:
            if kw in entry.title.lower() or kw in entry.content.lower() or kw in [k.lower() for k in entry.keywords]:
                results.append(entry)
        results.sort(key=lambda e: e.composite_score, reverse=True)
        return results[:max_results]

    def search_by_category(self, category: str) -> List[KnowledgeEntry]:
        return self.list_entries(category=category, active_only=True)

    def deduplicate(self) -> int:
        """Run deduplication on all entries."""
        with self._lock:
            entries = list(self._entries.values())
        count = self.deduplicator.mark_duplicates(entries)
        if count > 0:
            with self._lock:
                self._save()
        return count

    def cleanup_expired(self) -> int:
        """Remove expired entries."""
        removed = 0
        with self._lock:
            expired_ids = [eid for eid, e in self._entries.items() if e.is_expired()]
            for eid in expired_ids:
                self._entries[eid].status = "expired"
                removed += 1
            if removed:
                self._save()
        return removed

    def build_evidence(self, entry_ids: Optional[List[str]] = None) -> ConfidenceResult:
        """Build evidence-based confidence from collected knowledge."""
        if entry_ids:
            entries = [self.get_entry(eid) for eid in entry_ids if self._cache.get(eid) is not None or eid in self._entries]
        else:
            with self._lock:
                entries = list(self._entries.values())

        active = [e for e in entries if e.status == "active" and not e.is_duplicate]

        evidence = []
        if not active:
            return ConfidenceResult(confidence=0.1, risk_level="CRITICAL", evidence=["No active entries"])

        # Evidence points
        avg_credibility = sum(e.credibility_score for e in active) / len(active)
        avg_freshness = sum(e.freshness_score for e in active) / len(active)
        avg_relevance = sum(e.relevance_score for e in active) / len(active)
        sources = set(e.source for e in active)

        if avg_credibility >= 0.7:
            evidence.append(f"Average credibility is high ({avg_credibility:.2f})")
        if avg_freshness >= 0.7:
            evidence.append(f"Content is fresh (avg freshness: {avg_freshness:.2f})")
        if avg_relevance >= 0.7:
            evidence.append(f"Content is relevant (avg relevance: {avg_relevance:.2f})")
        if len(sources) >= 3:
            evidence.append(f"Multiple sources corroborate ({len(sources)} sources)")
        if len(active) >= 5:
            evidence.append(f"Substantial evidence ({len(active)} entries)")

        factors = {
            "data_quality": avg_credibility / 10.0,
            "source_reliability": len(sources) / 10.0,
            "freshness": avg_freshness / 10.0,
            "consistency": avg_relevance / 10.0,
        }

        return self.confidence_engine.calculate(factors, evidence=evidence)

    def health_check(self) -> dict:
        with self._lock:
            entries = list(self._entries.values())
        active = sum(1 for e in entries if e.status == "active")
        duplicates = sum(1 for e in entries if e.is_duplicate)
        sources = len(self.source_registry.list_sources())
        cache_stats = self.cache.stats()
        return {
            "total_entries": len(entries),
            "active": active,
            "duplicates": duplicates,
            "sources_registered": sources,
            "cache_hit_rate": cache_stats["hit_rate"],
            "cache_size": cache_stats["size"],
            "dedup_stats": self.deduplicator.get_stats(),
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, entry_id: str, data: dict):
        entry = {
            "event": event_type, "entry_id": entry_id,
            "timestamp": datetime.now(timezone.utc).isoformat(), **data,
        }
        self._history.append(entry)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

    def _save(self):
        if self._storage_path is None:
            return
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "version": 1,
            "saved_at": datetime.now(timezone.utc).isoformat(),
            "entries": [e.to_dict() for e in self._entries.values()],
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for ed in data.get("entries", []):
                entry = KnowledgeEntry.from_dict(ed)
                self._entries[entry.entry_id] = entry
                self.deduplicator.register(entry)
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
