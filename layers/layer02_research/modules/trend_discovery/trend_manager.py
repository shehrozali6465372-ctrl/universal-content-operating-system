"""
Trend Manager Module
Layer 2: Research Engine — Module 1

Core trend discovery engine:
- Multi-source trend aggregation with adapter pattern
- Trend scoring (virality, relevance, freshness)
- Category/niche filtering
- Trend history and comparison
- Auto-expiration of stale trends
- Persistent storage
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from threading import Lock

from layers.layer02_research.modules.trend_discovery.trend_entry import TrendEntry
from layers.layer02_research.modules.trend_discovery.exceptions import (
    TrendSourceError, TrendNotFoundError, InvalidSourceError,
)


class TrendSource:
    """Base adapter for a trend data source."""

    def __init__(self, name: str, fetch_fn: Optional[Callable] = None,
                 reliability: float = 0.8):
        self.name = name
        self._fetch_fn = fetch_fn
        self.reliability = max(0.0, min(1.0, reliability))
        self._last_fetch = None
        self._fetch_count = 0
        self._error_count = 0

    def fetch(self, category: str = "general",
              limit: int = 20) -> List[TrendEntry]:
        """Fetch trends from this source."""
        if self._fetch_fn is None:
            return []
        try:
            results = self._fetch_fn(category=category, limit=limit)
            self._fetch_count += 1
            self._last_fetch = datetime.now(timezone.utc).isoformat()
            return results if isinstance(results, list) else []
        except Exception as e:
            self._error_count += 1
            raise TrendSourceError(f"Source '{self.name}' failed: {e}")

    def health(self) -> dict:
        return {
            "name": self.name,
            "reliability": self.reliability,
            "fetch_count": self._fetch_count,
            "error_count": self._error_count,
            "last_fetch": self._last_fetch,
        }


class TrendManager:
    """Core trend discovery engine with multi-source aggregation."""

    def __init__(self, storage_path: Optional[str] = None):
        self._trends: Dict[str, TrendEntry] = {}
        self._sources: Dict[str, TrendSource] = {}
        self._history: List[dict] = []
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None
        self._max_history = 500
        self._load()

    # ── Source Management ────────────────────

    def register_source(self, name: str, fetch_fn: Optional[Callable] = None,
                       reliability: float = 0.8) -> TrendSource:
        """Register a trend data source."""
        source = TrendSource(name, fetch_fn, reliability)
        with self._lock:
            self._sources[name] = source
        return source

    def unregister_source(self, name: str) -> bool:
        with self._lock:
            if name in self._sources:
                del self._sources[name]
                return True
        return False

    def list_sources(self) -> List[dict]:
        with self._lock:
            return [s.health() for s in self._sources.values()]

    # ── Trend CRUD ───────────────────────────

    def add_trend(self, keyword: str, category: str = "general",
                  source: str = "manual", **kwargs) -> TrendEntry:
        """Add a trend manually or from a source."""
        entry = TrendEntry(keyword=keyword, category=category, source=source,
                          **kwargs)
        with self._lock:
            self._trends[entry.trend_id] = entry
        self._record_history("add", entry.trend_id, keyword)
        return entry

    def get_trend(self, trend_id: str) -> TrendEntry:
        with self._lock:
            if trend_id not in self._trends:
                raise TrendNotFoundError(f"Trend '{trend_id}' not found")
            return self._trends[trend_id]

    def delete_trend(self, trend_id: str) -> bool:
        with self._lock:
            if trend_id not in self._trends:
                raise TrendNotFoundError(f"Trend '{trend_id}' not found")
            del self._trends[trend_id]
        self._record_history("delete", trend_id)
        return True

    def exists(self, keyword: str, source: str = "manual") -> bool:
        tid = f"{keyword.lower().replace(' ', '_')}_{source}"
        with self._lock:
            return tid in self._trends

    # ── Discovery (Multi-Source) ─────────────

    def discover(self, category: str = "general",
                 sources: Optional[List[str]] = None,
                 limit_per_source: int = 20) -> List[TrendEntry]:
        """Run discovery across registered sources."""
        discovered = []

        with self._lock:
            active_sources = {
                k: v for k, v in self._sources.items()
                if sources is None or k in sources
            }

        for name, source in active_sources.items():
            try:
                trends = source.fetch(category=category, limit=limit_per_source)
                with self._lock:
                    for t in trends:
                        self._trends[t.trend_id] = t
                discovered.extend(trends)
                self._record_history("discover", name, f"{len(trends)} trends from {name}")
            except TrendSourceError:
                continue

        return discovered

    # ── Queries & Filtering ──────────────────

    def get_trends(self, category: Optional[str] = None,
                   source: Optional[str] = None,
                   min_score: float = 0.0,
                   direction: Optional[str] = None,
                   include_expired: bool = False,
                   limit: int = 50) -> List[dict]:
        """Get filtered trends sorted by composite score."""
        with self._lock:
            trends = list(self._trends.values())

        results = []
        for t in trends:
            if not include_expired and t.is_expired():
                continue
            if category and t.category != category:
                continue
            if source and t.source != source:
                continue
            if t.composite_score < min_score:
                continue
            if direction and t.direction != direction:
                continue
            results.append(t)

        results.sort(key=lambda x: x.composite_score, reverse=True)
        return [t.to_dict() for t in results[:limit]]

    def top_trends(self, category: str = "general",
                   limit: int = 10) -> List[dict]:
        """Get top N trends by composite score."""
        return self.get_trends(category=category, limit=limit)

    def rising_trends(self, category: str = "general",
                      limit: int = 10) -> List[dict]:
        """Get rising trends only."""
        return self.get_trends(category=category, direction="rising", limit=limit)

    def search(self, keyword: str, limit: int = 10) -> List[dict]:
        """Search trends by keyword (case-insensitive, partial match)."""
        keyword_lower = keyword.lower()
        with self._lock:
            matches = [
                t for t in self._trends.values()
                if keyword_lower in t.keyword.lower()
                or keyword_lower in t.description.lower()
                or any(keyword_lower in rk.lower() for rk in t.related_keywords)
            ]
        matches.sort(key=lambda x: x.composite_score, reverse=True)
        return [t.to_dict() for t in matches[:limit]]

    # ── Comparison ───────────────────────────

    def compare_snapshots(self, snapshot_a: List[dict],
                         snapshot_b: List[dict]) -> dict:
        """Compare two trend snapshots. Returns new, removed, and common."""
        ids_a = {t["trend_id"] for t in snapshot_a}
        ids_b = {t["trend_id"] for t in snapshot_b}
        return {
            "new": [t for t in snapshot_b if t["trend_id"] not in ids_a],
            "removed": [t for t in snapshot_a if t["trend_id"] not in ids_b],
            "common": [t for t in snapshot_b if t["trend_id"] in ids_a],
        }

    # ── Expiration ───────────────────────────

    def cleanup_expired(self) -> int:
        """Remove expired trends. Returns count removed."""
        removed = 0
        with self._lock:
            expired_ids = [
                tid for tid, t in self._trends.items()
                if t.is_expired()
            ]
            for tid in expired_ids:
                del self._trends[tid]
                removed += 1
        if removed > 0:
            self._record_history("cleanup", "system", f"Removed {removed} expired trends")
        return removed

    # ── History ──────────────────────────────

    def _record_history(self, action: str, target: str,
                       details: str = "") -> None:
        entry = {
            "action": action,
            "target": target,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        with self._lock:
            self._history.append(entry)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

    def get_history(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return list(self._history[-limit:])

    # ── Persistence ──────────────────────────

    def _load(self) -> None:
        if self._storage_path and self._storage_path.exists():
            try:
                data = json.loads(self._storage_path.read_text())
                for key, t_data in data.get("trends", {}).items():
                    self._trends[key] = TrendEntry.from_dict(t_data)
                self._history = data.get("history", [])
            except (json.JSONDecodeError, KeyError):
                pass

    def save(self, filepath: Optional[str] = None) -> bool:
        path = Path(filepath) if filepath else self._storage_path
        if path is None:
            return False
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "trends": {k: v.to_dict() for k, v in self._trends.items()},
            "history": self._history[-200:],
        }
        path.write_text(json.dumps(data, indent=2, default=str))
        return True

    # ── Stats ────────────────────────────────

    def stats(self) -> dict:
        with self._lock:
            total = len(self._trends)
            categories = {}
            sources = {}
            directions = {"rising": 0, "stable": 0, "declining": 0}
            expired = 0
            for t in self._trends.values():
                categories[t.category] = categories.get(t.category, 0) + 1
                sources[t.source] = sources.get(t.source, 0) + 1
                directions[t.direction] = directions.get(t.direction, 0) + 1
                if t.is_expired():
                    expired += 1

        return {
            "total_trends": total,
            "categories": categories,
            "sources": sources,
            "directions": directions,
            "expired": expired,
            "active": total - expired,
        }

    # ── Health Check ─────────────────────────

    def health_check(self) -> dict:
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
            "overall": "PASS",
        }
        stats = self.stats()

        report["checks"]["trends"] = {
            "status": "PASS" if stats["total_trends"] > 0 else "WARN",
            "message": f"{stats['total_trends']} trends ({stats['active']} active)",
        }
        report["checks"]["sources"] = {
            "status": "PASS" if len(self._sources) > 0 else "WARN",
            "message": f"{len(self._sources)} sources registered",
        }
        report["checks"]["expired"] = {
            "status": "WARN" if stats["expired"] > 0 else "PASS",
            "message": f"{stats['expired']} expired trends",
        }

        statuses = [c["status"] for c in report["checks"].values()]
        if "FAIL" in statuses:
            report["overall"] = "FAIL"
        elif "WARN" in statuses:
            report["overall"] = "WARN"
        return report
