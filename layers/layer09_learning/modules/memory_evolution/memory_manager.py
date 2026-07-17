"""Memory Manager — Orchestrate the full memory evolution pipeline."""
from __future__ import annotations
import itertools
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.memory_evolution.memory_classifier import MemoryClassifier
from layers.layer09_learning.modules.memory_evolution.memory_merger import MemoryMerger
from layers.layer09_learning.modules.memory_evolution.memory_cleanup import MemoryCleanup
from layers.layer09_learning.modules.memory_evolution.memory_ranker import MemoryRanker
from layers.layer09_learning.modules.memory_evolution.memory_expiry import MemoryExpiry
from layers.layer09_learning.modules.memory_evolution.memory_archive import MemoryArchive
from layers.layer09_learning.modules.memory_evolution.memory_search import MemorySearch
from layers.layer09_learning.modules.memory_evolution.memory_optimizer import MemoryOptimizer
from layers.layer09_learning.modules.memory_evolution.memory_metrics import MemoryEvolutionMetrics

_MEMGR_COUNTER = itertools.count(1)


class EvolutionCycleResult:
    """Result of a full memory evolution cycle."""

    __slots__ = (
        "cycle_id", "entries_processed", "entries_after",
        "classification_count", "merge_count", "cleanup_report",
        "optimization_report", "archived_count", "timestamp", "duration_ms",
    )

    def __init__(self) -> None:
        self.cycle_id: str = f"mcy_{next(_MEMGR_COUNTER)}"
        self.entries_processed: int = 0
        self.entries_after: int = 0
        self.classification_count: int = 0
        self.merge_count: int = 0
        self.cleanup_report = None
        self.optimization_report = None
        self.archived_count: int = 0
        self.timestamp: float = time.time()
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "entries_processed": self.entries_processed,
            "entries_after": self.entries_after,
            "classification_count": self.classification_count,
            "merge_count": self.merge_count,
            "archived_count": self.archived_count,
            "reduction_pct": round(
                (1 - self.entries_after / max(1, self.entries_processed)) * 100, 1,
            ),
            "duration_ms": round(self.duration_ms, 1),
        }


class MemoryManager:
    """Orchestrate the full memory evolution pipeline.

    Flow: Classify → Rank → Merge → Cleanup → Optimize → Archive
    """

    def __init__(self) -> None:
        self.classifier = MemoryClassifier()
        self.merger = MemoryMerger()
        self.cleanup = MemoryCleanup()
        self.ranker = MemoryRanker()
        self.expiry = MemoryExpiry()
        self.archive = MemoryArchive()
        self.search = MemorySearch()
        self.optimizer = MemoryOptimizer()
        self.metrics = MemoryEvolutionMetrics()
        self._cycles: List[EvolutionCycleResult] = []
        self._events: List[Dict[str, Any]] = []

    def run_evolution_cycle(self, entries: List[Dict[str, Any]]) -> EvolutionCycleResult:
        start = time.time()
        result = EvolutionCycleResult()
        result.entries_processed = len(entries)

        # Step 1: Classify
        for entry in entries:
            self.classifier.classify(
                memory_id=entry.get("entry_id", ""),
                source_type=entry.get("source_type", "lesson"),
                confidence=entry.get("confidence", 0.5),
                usage_count=entry.get("usage_count", 0),
                age_days=entry.get("age_days", 0.0),
                tags=entry.get("tags", []),
            )
        result.classification_count = len(self.classifier.get_classified())

        # Step 2: Rank
        self.ranker.rank(entries)

        # Step 3: Merge
        merge_results = self.merger.merge_by_keyword(entries)
        result.merge_count = len(merge_results)
        if merge_results:
            self.metrics.record_merge(sum(m.source_count for m in merge_results))

        # Step 4: Cleanup
        cleanup_report = self.cleanup.cleanup(entries)
        result.cleanup_report = cleanup_report
        self.metrics.record_cleanup(cleanup_report.space_freed)

        # Step 5: Optimize
        opt_report = self.optimizer.optimize(entries)
        result.optimization_report = opt_report
        self.metrics.record_optimization()

        # Step 6: Archive expired entries
        for entry in entries:
            age = entry.get("age_days", 0.0)
            check = self.expiry.check_entry(
                entry.get("entry_id", ""), age,
                entry.get("category", "default"),
                entry.get("usage_count", 0),
            )
            if check.action == "expire":
                self.archive.archive(
                    entry.get("entry_id", ""), entry,
                    reason="expired",
                    tags=entry.get("tags", []),
                )
                result.archived_count += 1
                self.metrics.record_archive()

        result.entries_after = max(0, result.entries_processed - cleanup_report.space_freed - result.archived_count)

        result.duration_ms = (time.time() - start) * 1000
        self._cycles.append(result)
        self._events.append({
            "event": "evolution_cycle_completed",
            "cycle_id": result.cycle_id,
            "entries_processed": result.entries_processed,
            "reduction_pct": result.to_dict()["reduction_pct"],
        })
        return result

    def search_memory(self, entries: List[Dict[str, Any]], query: str = "",
                      tags: Optional[List[str]] = None, limit: int = 20) -> List[Dict[str, Any]]:
        results = self.search.search(entries, query=query, tags=tags, limit=limit)
        self.metrics.record_search(results=len(results))
        return [r.to_dict() for r in results]

    def archive_entry(self, entry_id: str, data: Dict[str, Any],
                      reason: str = "manual") -> Dict[str, Any]:
        entry = self.archive.archive(entry_id, data, reason)
        self.metrics.record_archive()
        return entry.to_dict()

    def restore_entry(self, archive_id: str) -> Optional[Dict[str, Any]]:
        data = self.archive.restore(archive_id)
        if data:
            self.metrics.record_restore()
        return data

    def get_health(self) -> Dict[str, Any]:
        return {
            "total_cycles": len(self._cycles),
            "archive_stats": self.archive.get_stats(),
            "metrics": self.metrics.get_summary(),
        }

    def get_recent_cycles(self, count: int = 5) -> List[EvolutionCycleResult]:
        return list(self._cycles[-count:])

    @property
    def events(self) -> List[Dict[str, Any]]:
        return list(self._events)

    @property
    def cycle_count(self) -> int:
        return len(self._cycles)
