"""
Research Memory Manager
Layer 2: Research Engine — Module 7

Central manager for the research knowledge base:
- Entry storage and retrieval
- Semantic search
- Knowledge graph operations
- Evidence storage
- Citation indexing
- Decision trace recording
- Memory ranking
- Persistent storage
- Health check
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

from layers.layer02_research.modules.research_memory.research_index import ResearchIndex, ResearchEntry
from layers.layer02_research.modules.research_memory.semantic_search import SemanticSearch
from layers.layer02_research.modules.research_memory.knowledge_graph import KnowledgeGraph
from layers.layer02_research.modules.research_memory.evidence_store import EvidenceStore, EvidenceItem
from layers.layer02_research.modules.research_memory.citation_index import CitationIndex
from layers.layer02_research.modules.research_memory.memory_ranker import MemoryRanker
from layers.layer02_research.modules.research_memory.decision_trace import DecisionTraceEngine, DecisionTrace
from layers.layer02_research.shared.confidence_engine import ConfidenceEngine
from layers.layer02_research.modules.research_memory.exceptions import EntryNotFoundError


class ResearchMemoryManager:
    """Central research knowledge base and memory engine."""

    def __init__(self, storage_path: Optional[str] = None):
        self._lock = Lock()
        self._storage_path = Path(storage_path) if storage_path else None

        # Sub-components
        self.index = ResearchIndex()
        self.search_engine = SemanticSearch()
        self.knowledge_graph = KnowledgeGraph()
        self.evidence_store = EvidenceStore()
        self.citation_index = CitationIndex()
        self.ranker = MemoryRanker()
        self.trace_engine = DecisionTraceEngine()
        self.confidence_engine = ConfidenceEngine()

        self._history: List[dict] = []
        self._max_history = 500

        self._load()

    # ── Entry Management ────────────────────

    def store_entry(
        self,
        entry_id: str,
        title: str = "",
        content: str = "",
        summary: str = "",
        category: str = "general",
        tags: Optional[List[str]] = None,
        source: str = "",
        keywords: Optional[List[str]] = None,
        credibility_score: float = 0.5,
        relevance_score: float = 0.5,
        freshness_score: float = 0.5,
    ) -> ResearchEntry:
        """Store a research entry."""
        entry = ResearchEntry(
            entry_id=entry_id, title=title, content=content, summary=summary,
            category=category, tags=tags, source=source, keywords=keywords,
            credibility_score=credibility_score, relevance_score=relevance_score,
            freshness_score=freshness_score,
        )
        with self._lock:
            self.index.add(entry)
            self._record_event("entry_stored", entry_id, {"title": title[:100]})
            self._save()
        return entry

    def get_entry(self, entry_id: str) -> ResearchEntry:
        entry = self.index.get(entry_id)
        if entry is None:
            raise EntryNotFoundError(f"Entry '{entry_id}' not found")
        return entry

    def remove_entry(self, entry_id: str) -> bool:
        with self._lock:
            result = self.index.remove(entry_id)
            if result:
                self._record_event("entry_removed", entry_id, {})
                self._save()
        return result

    def list_entries(self, category: Optional[str] = None) -> List[ResearchEntry]:
        if category:
            return self.index.search_by_category(category)
        return self.index.list_all()

    # ── Search ──────────────────────────────

    def search(self, query: str, max_results: int = 20) -> List[ResearchEntry]:
        """Full-text search."""
        return self.index.search_text(query, max_results)

    def search_semantic(self, query: str, max_results: int = 10):
        """Semantic search using TF-IDF."""
        docs = {e.entry_id: e.content for e in self.index.list_all() if e.content}
        return self.search_engine.search(query, docs, max_results)

    def search_by_keyword(self, keyword: str) -> List[ResearchEntry]:
        return self.index.search_by_keyword(keyword)

    def search_by_tag(self, tag: str) -> List[ResearchEntry]:
        return self.index.search_by_tag(tag)

    # ── Knowledge Graph ─────────────────────

    def add_entity(self, entity_id: str, entity_type: str = "entity", label: str = ""):
        self.knowledge_graph.add_node(entity_id, entity_type, label)

    def add_relationship(self, source_id: str, target_id: str, relation: str = "related_to"):
        self.knowledge_graph.add_edge(source_id, target_id, relation)

    def find_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        return self.knowledge_graph.find_path(start_id, end_id)

    def get_neighbors(self, node_id: str) -> List:
        return self.knowledge_graph.get_neighbors(node_id)

    # ── Evidence ────────────────────────────

    def add_evidence(self, evidence_id: str, claim_id: str = "", text: str = "",
                     source: str = "", credibility: float = 0.5, supports: bool = True,
                     topic: str = "general") -> EvidenceItem:
        item = EvidenceItem(evidence_id, claim_id, text, source, credibility, supports, topic)
        self.evidence_store.add(item)
        return item

    def get_evidence_for_topic(self, topic: str) -> List[EvidenceItem]:
        return self.evidence_store.get_by_topic(topic)

    def get_evidence_confidence(self, topic: str) -> float:
        return self.evidence_store.aggregate_confidence(topic)

    # ── Citations ───────────────────────────

    def add_citation(self, citation_id: str, source_name: str = "",
                     claim_id: str = "", credibility: float = 0.5):
        self.citation_index.add(citation_id, source_name=source_name,
                                claim_id=claim_id, credibility=credibility)

    def get_citations_for_claim(self, claim_id: str):
        return self.citation_index.get_by_claim(claim_id)

    def get_top_sources(self, count: int = 10) -> List[str]:
        return self.citation_index.get_top_sources(count)

    # ── Decision Traces ─────────────────────

    def record_decision(self, trace: DecisionTrace) -> str:
        """Record a research decision trace."""
        trace_id = self.trace_engine.record(trace)
        with self._lock:
            self._record_event("decision_recorded", trace_id, {
                "topic": trace.topic, "confidence": trace.overall_confidence,
            })
            self._save()
        return trace_id

    def get_decision(self, trace_id: str) -> Optional[DecisionTrace]:
        return self.trace_engine.get(trace_id)

    def get_decisions_for_topic(self, topic: str) -> List[DecisionTrace]:
        return self.trace_engine.get_by_topic(topic)

    def get_decision_stats(self) -> Dict:
        return self.trace_engine.stats()

    def get_successful_patterns(self) -> Dict:
        return self.trace_engine.get_successful_patterns()

    # ── Ranking ─────────────────────────────

    def rank_entries(self, max_results: int = 20) -> List[dict]:
        entries = [e.to_dict() for e in self.index.list_all()]
        return self.ranker.rank(entries, max_results)

    def get_top_entries(self, count: int = 10) -> List[ResearchEntry]:
        return self.index.get_top_entries(count)

    # ── Health ──────────────────────────────

    def health_check(self) -> dict:
        return {
            "index_size": self.index.size(),
            "graph_nodes": self.knowledge_graph.stats()["total_nodes"],
            "graph_edges": self.knowledge_graph.stats()["total_edges"],
            "evidence_count": self.evidence_store.size(),
            "citations_count": self.citation_index.size(),
            "decisions_recorded": self.trace_engine.size(),
            "avg_decision_confidence": self.trace_engine.get_average_confidence(),
            "avg_decision_performance": self.trace_engine.get_average_performance(),
            "index_stats": self.index.stats(),
            "evidence_stats": self.evidence_store.stats(),
        }

    # ── Storage ─────────────────────────────

    def _record_event(self, event_type: str, item_id: str, data: dict):
        entry = {
            "event": event_type, "item_id": item_id,
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
            "index": {eid: e.to_dict() for eid, e in self.index._entries.items()},
            "graph": self.knowledge_graph.to_dict(),
            "traces": {tid: t.to_dict() for tid, t in self.trace_engine._traces.items()},
            "history": self._history[-50:],
        }
        self._storage_path.write_text(json.dumps(data, indent=2))

    def _load(self):
        if self._storage_path is None or not self._storage_path.exists():
            return
        try:
            data = json.loads(self._storage_path.read_text())
            for eid, ed in data.get("index", {}).items():
                entry = ResearchEntry.from_dict(ed)
                self.index.add(entry)
            graph_data = data.get("graph", {})
            if graph_data:
                self.knowledge_graph = KnowledgeGraph.from_dict(graph_data)
            for tid, td in data.get("traces", {}).items():
                trace = DecisionTrace.from_dict(td)
                self.trace_engine.record(trace)
            self._history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            pass
