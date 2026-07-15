"""Intelligence Memory Manager — Central orchestrator for Intelligence Memory."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer03_intelligence.modules.intelligence_memory.intel_cache import IntelligenceCache
from layers.layer03_intelligence.modules.intelligence_memory.intelligence_store import IntelligenceStore
from layers.layer03_intelligence.modules.intelligence_memory.pattern_indexer import PatternIndexer
from layers.layer03_intelligence.modules.intelligence_memory.case_retriever import CaseRetriever
from layers.layer03_intelligence.modules.intelligence_memory.memory_consolidator import MemoryConsolidator
from layers.layer03_intelligence.modules.intelligence_memory.memory_pruner import MemoryPruner
from layers.layer03_intelligence.modules.intelligence_memory.memory_versioning import MemoryVersioner
from layers.layer03_intelligence.modules.intelligence_memory.confidence_history import ConfidenceHistory
from layers.layer03_intelligence.modules.intelligence_memory.memory_searcher import MemorySearcher


class IntelMemoryResult:
    """Result from the Intelligence Memory pipeline."""
    __slots__ = ("operation", "data", "stats", "metadata", "timestamp")

    def __init__(self, operation: str = "") -> None:
        self.operation = operation
        self.data: Any = None
        self.stats: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation": self.operation,
            "stats": self.stats,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class IntelMemoryManager:
    """Central orchestrator for Intelligence Memory.

    Provides unified interface for:
    - Caching (IntelligenceCache)
    - Storage (IntelligenceStore)
    - Pattern indexing (PatternIndexer)
    - Case retrieval (CaseRetriever)
    - Memory consolidation (MemoryConsolidator)
    - Memory pruning (MemoryPruner)
    - Versioning (MemoryVersioner)
    - Confidence tracking (ConfidenceHistory)
    - Search (MemorySearcher)
    """

    def __init__(
        self,
        cache: Optional[IntelligenceCache] = None,
        store: Optional[IntelligenceStore] = None,
        patterns: Optional[PatternIndexer] = None,
        cases: Optional[CaseRetriever] = None,
        consolidator: Optional[MemoryConsolidator] = None,
        pruner: Optional[MemoryPruner] = None,
        versioner: Optional[MemoryVersioner] = None,
        confidence: Optional[ConfidenceHistory] = None,
        searcher: Optional[MemorySearcher] = None,
    ) -> None:
        self.cache = cache or IntelligenceCache()
        self.store = store or IntelligenceStore()
        self.patterns = patterns or PatternIndexer()
        self.cases = cases or CaseRetriever()
        self.consolidator = consolidator or MemoryConsolidator()
        self.pruner = pruner or MemoryPruner()
        self.versioner = versioner or MemoryVersioner()
        self.confidence = confidence or ConfidenceHistory()
        self.searcher = searcher or MemorySearcher()
        self._setup_searcher()
        self._operation_count = 0

    def _setup_searcher(self) -> None:
        self.searcher.register_store("store", self.store)
        self.searcher.register_store("cases", self.cases)

    def remember(self, category: str, data: Dict[str, Any], confidence: float = 0.5,
                 tags: Optional[List[str]] = None, source: str = "") -> IntelMemoryResult:
        """Store a new intelligence entry with full pipeline."""
        entry = self.store.store(category, data, confidence=confidence, tags=tags, source=source)
        self.cache.store(f"{category}_{entry.entry_id}", data)
        self.versioner.create_version(entry.entry_id, data, change_summary="initial creation")
        self.confidence.record(topic=category, module="memory", confidence=confidence)

        result = IntelMemoryResult(operation="remember")
        result.data = entry.to_dict()
        result.stats = self.store.stats()
        self._operation_count += 1
        return result

    def recall(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an entry from cache or store."""
        cached = self.cache.get(entry_id)
        if cached:
            return cached
        entry = self.store.get(entry_id)
        if entry:
            return entry.data
        return None

    def learn_pattern(self, pattern_type: str, description: str, confidence: float = 0.5,
                      tags: Optional[List[str]] = None) -> IntelMemoryResult:
        """Index a new pattern."""
        pat = self.patterns.index(pattern_type, description, confidence=confidence, tags=tags)
        result = IntelMemoryResult(operation="learn_pattern")
        result.data = pat.to_dict()
        self._operation_count += 1
        return result

    def find_similar_cases(self, topic: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Find similar past cases."""
        cases = self.cases.get_similar(topic, limit=limit)
        return [c.to_dict() for c in cases]

    def store_case(self, topic: str, decision: str, outcome: str = "unknown",
                   score: float = 0.0, tags: Optional[List[str]] = None) -> IntelMemoryResult:
        """Store a decision case."""
        case = self.cases.store(topic=topic, decision=decision, outcome=outcome, score=score, tags=tags)
        result = IntelMemoryResult(operation="store_case")
        result.data = case.to_dict()
        self._operation_count += 1
        return result

    def get_confidence_trend(self, topic: str) -> Dict[str, Any]:
        """Get confidence trend for a topic."""
        return self.confidence.get_trend(topic)

    def consolidate(self, entries: List[Dict[str, Any]]) -> IntelMemoryResult:
        """Consolidate similar entries."""
        consolidated = self.consolidator.consolidate(entries)
        result = IntelMemoryResult(operation="consolidate")
        result.data = [c.to_dict() for c in consolidated]
        result.stats = {"consolidated_groups": len(consolidated)}
        self._operation_count += 1
        return result

    def prune(self) -> IntelMemoryResult:
        """Analyze what needs pruning."""
        all_entries = [{"id": e.entry_id, "timestamp": e.updated_at, "value": e.value}
                       for e in self.store.get_by_category("")]
        analysis = self.pruner.analyze(all_entries)
        result = IntelMemoryResult(operation="prune")
        result.data = analysis.to_dict()
        self._operation_count += 1
        return result

    def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search across all memory stores."""
        results = self.searcher.search(query, limit=limit)
        return [{"relevance": r.relevance, "match_type": r.match_type} for r in results]

    def get_stats(self) -> Dict[str, Any]:
        """Get overall memory statistics."""
        return {
            "store": self.store.stats(),
            "cache_size": self.cache.size(),
            "cache_hit_rate": self.cache.hit_rate(),
            "patterns": self.patterns.count,
            "cases": self.cases.count,
            "confidence_records": self.confidence.count,
            "total_versions": self.versioner.total_versions(),
            "operations": self._operation_count,
        }
