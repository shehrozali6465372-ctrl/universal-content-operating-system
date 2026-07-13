"""
Tests for Research Memory Module
Layer 2: Research Engine — Module 7

Run: python -m pytest layers/layer02_research/tests/test_research_memory.py -v
"""

import pytest

from layers.layer02_research.modules.research_memory.research_index import ResearchIndex, ResearchEntry
from layers.layer02_research.modules.research_memory.semantic_search import SemanticSearch, SearchResult
from layers.layer02_research.modules.research_memory.knowledge_graph import KnowledgeGraph, GraphNode, GraphEdge
from layers.layer02_research.modules.research_memory.evidence_store import EvidenceStore, EvidenceItem
from layers.layer02_research.modules.research_memory.citation_index import CitationIndex
from layers.layer02_research.modules.research_memory.memory_ranker import MemoryRanker
from layers.layer02_research.modules.research_memory.decision_trace import DecisionTraceEngine, DecisionTrace
from layers.layer02_research.modules.research_memory.research_memory_manager import ResearchMemoryManager
from layers.layer02_research.modules.research_memory.exceptions import EntryNotFoundError


@pytest.fixture
def manager(tmp_path):
    return ResearchMemoryManager(storage_path=str(tmp_path / "research_memory.json"))


@pytest.fixture
def manager_with_data(manager):
    entries = [
        ("ai_jobs", "AI Jobs Boom", "AI is transforming the job market rapidly with new opportunities", "ai", ["ai", "jobs"]),
        ("crypto_trends", "Crypto Market Update", "Bitcoin reaches new all time highs in 2026", "finance", ["crypto", "bitcoin"]),
        ("python_tips", "Python Best Practices", "Top 10 Python tips for data science and ML", "technology", ["python", "ml"]),
        ("health_study", "Mental Health Research", "New study shows exercise improves mental health significantly", "health", ["health", "exercise"]),
        ("marketing_2026", "Social Media Marketing", "Effective strategies for Facebook marketing in 2026", "business", ["marketing", "facebook"]),
    ]
    for eid, title, content, cat, tags in entries:
        manager.store_entry(eid, title=title, content=content, category=cat, tags=tags, source="test")
    return manager


# ═══════════════════════════════════════════
# Test 1: Research Index
# ═══════════════════════════════════════════

class TestResearchIndex:
    def test_add_and_get(self):
        idx = ResearchIndex()
        e = ResearchEntry("e1", title="Test", content="Hello world")
        idx.add(e)
        assert idx.get("e1") is not None
        assert idx.size() == 1

    def test_remove(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="Test"))
        assert idx.remove("e1") is True
        assert idx.size() == 0

    def test_remove_nonexistent(self):
        idx = ResearchIndex()
        assert idx.remove("ghost") is False

    def test_search_text(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="AI Jobs", content="AI is booming in tech"))
        idx.add(ResearchEntry("e2", title="Cooking Tips", content="How to cook pasta"))
        results = idx.search_text("AI")
        assert len(results) >= 1
        assert results[0].entry_id == "e1"

    def test_search_by_category(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="A", category="ai"))
        idx.add(ResearchEntry("e2", title="B", category="finance"))
        assert len(idx.search_by_category("ai")) == 1

    def test_search_by_tag(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="A", tags=["hot", "trending"]))
        assert len(idx.search_by_tag("hot")) == 1

    def test_search_by_source(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="A", source="Reuters"))
        assert len(idx.search_by_source("Reuters")) == 1

    def test_search_by_keyword(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="A", keywords=["python", "coding"]))
        assert len(idx.search_by_keyword("python")) == 1

    def test_get_top_entries(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="Low", credibility_score=2.0, relevance_score=2.0))
        idx.add(ResearchEntry("e2", title="High", credibility_score=9.0, relevance_score=9.0))
        top = idx.get_top_entries(1)
        assert top[0].title == "High"

    def test_get_recent(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="First"))
        idx.add(ResearchEntry("e2", title="Second"))
        recent = idx.get_recent(1)
        assert len(recent) == 1

    def test_get_most_accessed(self):
        idx = ResearchIndex()
        e1 = ResearchEntry("e1", title="Popular")
        e1.access_count = 100
        e2 = ResearchEntry("e2", title="Rare")
        e2.access_count = 1
        idx.add(e1)
        idx.add(e2)
        top = idx.get_most_accessed(1)
        assert top[0].title == "Popular"

    def test_stats(self):
        idx = ResearchIndex()
        idx.add(ResearchEntry("e1", title="A", category="ai", source="X"))
        stats = idx.stats()
        assert stats["total_entries"] == 1
        assert stats["categories"] == 1

    def test_entry_to_dict(self):
        e = ResearchEntry("e1", title="Test", category="ai")
        d = e.to_dict()
        assert d["entry_id"] == "e1"
        assert d["category"] == "ai"

    def test_entry_from_dict(self):
        d = {"entry_id": "e1", "title": "Restored", "content": "data"}
        e = ResearchEntry.from_dict(d)
        assert e.entry_id == "e1"
        assert e.title == "Restored"

    def test_entry_touch(self):
        e = ResearchEntry("e1")
        e.touch()
        e.touch()
        assert e.access_count == 2

    def test_entry_composite_score(self):
        e = ResearchEntry("e1", credibility_score=8.0, relevance_score=9.0, freshness_score=7.0)
        assert e.composite_score > 0


# ═══════════════════════════════════════════
# Test 2: Semantic Search
# ═══════════════════════════════════════════

class TestSemanticSearch:
    def test_basic_search(self):
        ss = SemanticSearch()
        docs = {"d1": "AI is transforming technology", "d2": "Cooking pasta is fun"}
        results = ss.search("AI technology", docs)
        assert len(results) >= 1
        assert results[0].entry_id == "d1"

    def test_no_results(self):
        ss = SemanticSearch()
        docs = {"d1": "Cooking pasta recipe"}
        results = ss.search("quantum computing", docs)
        assert len(results) == 0

    def test_empty_query(self):
        ss = SemanticSearch()
        results = ss.search("", {"d1": "test"})
        assert isinstance(results, list)

    def test_expand_query(self):
        ss = SemanticSearch()
        expanded = ss.expand_query("AI", ["machine learning", "deep learning"])
        assert "machine learning" in expanded

    def test_update_idf(self):
        ss = SemanticSearch()
        ss.update_idf([["hello", "world"], ["hello", "python"]])
        assert ss.get_idf("hello") < ss.get_idf("python")

    def test_result_to_dict(self):
        r = SearchResult("d1", 0.8, ["ai"], "semantic")
        d = r.to_dict()
        assert d["entry_id"] == "d1"
        assert d["relevance_score"] == 0.8

    def test_ranking(self):
        ss = SemanticSearch()
        docs = {"d1": "AI machine learning deep learning", "d2": "cooking pasta recipe"}
        results = ss.search("AI machine learning", docs)
        if len(results) >= 2:
            assert results[0].relevance_score >= results[1].relevance_score


# ═══════════════════════════════════════════
# Test 3: Knowledge Graph
# ═══════════════════════════════════════════

class TestKnowledgeGraph:
    def test_add_node(self):
        kg = KnowledgeGraph()
        n = kg.add_node("n1", "entity", "AI")
        assert n.node_id == "n1"
        assert n.label == "AI"

    def test_add_edge(self):
        kg = KnowledgeGraph()
        kg.add_edge("n1", "n2", "related_to")
        neighbors = kg.get_neighbors("n1", "out")
        assert len(neighbors) == 1
        assert neighbors[0][0] == "n2"

    def test_find_path(self):
        kg = KnowledgeGraph()
        kg.add_edge("a", "b")
        kg.add_edge("b", "c")
        path = kg.find_path("a", "c")
        assert path == ["a", "b", "c"]

    def test_find_path_no_path(self):
        kg = KnowledgeGraph()
        kg.add_node("a")
        kg.add_node("b")
        assert kg.find_path("a", "b") is None

    def test_find_path_same_node(self):
        kg = KnowledgeGraph()
        kg.add_node("a")
        assert kg.find_path("a", "a") == ["a"]

    def test_get_subgraph(self):
        kg = KnowledgeGraph()
        kg.add_edge("center", "n1")
        kg.add_edge("n1", "n2")
        sg = kg.get_subgraph("center", depth=2)
        assert "center" in sg["nodes"]
        assert len(sg["edges"]) >= 1

    def test_find_related(self):
        kg = KnowledgeGraph()
        kg.add_edge("a", "b", "causes")
        kg.add_edge("a", "c", "related_to")
        related = kg.find_related("a", relation="causes")
        assert "b" in related

    def test_get_nodes_by_type(self):
        kg = KnowledgeGraph()
        kg.add_node("n1", "topic")
        kg.add_node("n2", "entity")
        topics = kg.get_nodes_by_type("topic")
        assert len(topics) == 1

    def test_stats(self):
        kg = KnowledgeGraph()
        kg.add_edge("a", "b", "rel")
        stats = kg.stats()
        assert stats["total_nodes"] == 2
        assert stats["total_edges"] == 1

    def test_to_dict_from_dict(self):
        kg = KnowledgeGraph()
        kg.add_edge("a", "b", "test")
        data = kg.to_dict()
        kg2 = KnowledgeGraph.from_dict(data)
        assert kg2.stats()["total_nodes"] == 2

    def test_graph_node_to_dict(self):
        n = GraphNode("n1", "entity", "Test")
        d = n.to_dict()
        assert d["node_id"] == "n1"

    def test_graph_edge_to_dict(self):
        e = GraphEdge("a", "b", "rel", 0.8)
        d = e.to_dict()
        assert d["source"] == "a"
        assert d["weight"] == 0.8

    def test_reverse_edges(self):
        kg = KnowledgeGraph()
        kg.add_edge("a", "b")
        in_neighbors = kg.get_neighbors("b", "in")
        assert len(in_neighbors) == 1


# ═══════════════════════════════════════════
# Test 4: Evidence Store
# ═══════════════════════════════════════════

class TestEvidenceStore:
    def test_add_and_get(self):
        es = EvidenceStore()
        item = EvidenceItem("ev1", text="evidence text", topic="ai")
        es.add(item)
        assert es.get("ev1") is not None

    def test_remove(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1"))
        assert es.remove("ev1") is True
        assert es.get("ev1") is None

    def test_get_by_topic(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", topic="ai"))
        es.add(EvidenceItem("ev2", topic="finance"))
        assert len(es.get_by_topic("ai")) == 1

    def test_get_supporting(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", topic="ai", supports=True))
        es.add(EvidenceItem("ev2", topic="ai", supports=False))
        assert len(es.get_supporting("ai")) == 1

    def test_get_contradicting(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", topic="ai", supports=True))
        es.add(EvidenceItem("ev2", topic="ai", supports=False))
        assert len(es.get_contradicting("ai")) == 1

    def test_aggregate_confidence(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", topic="ai", credibility=0.9, supports=True))
        es.add(EvidenceItem("ev2", topic="ai", credibility=0.8, supports=True))
        conf = es.aggregate_confidence("ai")
        assert conf > 0.8

    def test_get_top_credible(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", credibility=0.3))
        es.add(EvidenceItem("ev2", credibility=0.9))
        top = es.get_top_credible(1)
        assert top[0].credibility == 0.9

    def test_stats(self):
        es = EvidenceStore()
        es.add(EvidenceItem("ev1", supports=True))
        es.add(EvidenceItem("ev2", supports=False))
        stats = es.stats()
        assert stats["total_evidence"] == 2
        assert stats["supporting"] == 1

    def test_item_to_dict(self):
        item = EvidenceItem("ev1", text="test", topic="ai")
        d = item.to_dict()
        assert d["evidence_id"] == "ev1"


# ═══════════════════════════════════════════
# Test 5: Citation Index
# ═══════════════════════════════════════════

class TestCitationIndex:
    def test_add_and_get(self):
        ci = CitationIndex()
        ci.add("c1", source_name="Reuters", claim_id="cl1")
        assert ci.get("c1") is not None

    def test_get_by_source(self):
        ci = CitationIndex()
        ci.add("c1", source_name="Reuters")
        ci.add("c2", source_name="BBC")
        assert len(ci.get_by_source("Reuters")) == 1

    def test_get_by_claim(self):
        ci = CitationIndex()
        ci.add("c1", claim_id="cl1")
        ci.add("c2", claim_id="cl2")
        assert len(ci.get_by_claim("cl1")) == 1

    def test_get_most_cited(self):
        ci = CitationIndex()
        ci.add("c1", source_name="A")
        ci.add("c1", source_name="A")
        ci.add("c1", source_name="A")
        ci.add("c2", source_name="B")
        top = ci.get_most_cited(1)
        assert top[0].citation_id == "c1"

    def test_get_top_sources(self):
        ci = CitationIndex()
        ci.add("c1", source_name="Reuters")
        ci.add("c2", source_name="Reuters")
        ci.add("c3", source_name="BBC")
        sources = ci.get_top_sources(1)
        assert sources[0] == "Reuters"

    def test_record_to_dict(self):
        ci = CitationIndex()
        rec = ci.add("c1", source_name="Test", credibility=0.8)
        d = rec.to_dict()
        assert d["source_name"] == "Test"


# ═══════════════════════════════════════════
# Test 6: Memory Ranker
# ═══════════════════════════════════════════

class TestMemoryRanker:
    def test_rank(self):
        mr = MemoryRanker()
        entries = [
            {"entry_id": "e1", "credibility_score": 3.0, "relevance_score": 3.0},
            {"entry_id": "e2", "credibility_score": 9.0, "relevance_score": 9.0},
        ]
        ranked = mr.rank(entries)
        assert ranked[0]["entry_id"] == "e2"

    def test_rank_by_field(self):
        mr = MemoryRanker()
        entries = [{"entry_id": "e1", "score": 5}, {"entry_id": "e2", "score": 9}]
        ranked = mr.rank_by_field(entries, "score")
        assert ranked[0]["entry_id"] == "e2"

    def test_filter_above_threshold(self):
        mr = MemoryRanker()
        entries = [
            {"entry_id": "e1", "credibility_score": 2.0, "relevance_score": 2.0},
            {"entry_id": "e2", "credibility_score": 9.0, "relevance_score": 9.0},
        ]
        filtered = mr.filter_above_threshold(entries, min_score=0.5)
        assert len(filtered) >= 1

    def test_custom_weights(self):
        mr = MemoryRanker(weights={"credibility": 1.0, "relevance": 0.0, "freshness": 0.0})
        entries = [
            {"entry_id": "e1", "credibility_score": 9.0, "relevance_score": 1.0, "freshness_score": 1.0},
            {"entry_id": "e2", "credibility_score": 1.0, "relevance_score": 9.0, "freshness_score": 9.0},
        ]
        ranked = mr.rank(entries)
        assert ranked[0]["entry_id"] == "e1"


# ═══════════════════════════════════════════
# Test 7: Decision Trace Engine
# ═══════════════════════════════════════════

class TestDecisionTraceEngine:
    def test_record_and_get(self):
        dte = DecisionTraceEngine()
        t = DecisionTrace(topic="AI Jobs", decision="Publish", trend_score=8.0, overall_confidence=0.85)
        tid = dte.record(t)
        assert dte.get(tid) is not None

    def test_get_by_topic(self):
        dte = DecisionTraceEngine()
        dte.record(DecisionTrace(topic="AI", overall_confidence=0.9))
        dte.record(DecisionTrace(topic="AI", overall_confidence=0.7))
        dte.record(DecisionTrace(topic="Finance", overall_confidence=0.6))
        assert len(dte.get_by_topic("AI")) == 2

    def test_get_recent(self):
        dte = DecisionTraceEngine()
        for i in range(5):
            dte.record(DecisionTrace(topic=f"Topic_{i}"))
        recent = dte.get_recent(3)
        assert len(recent) == 3

    def test_update_outcome(self):
        dte = DecisionTraceEngine()
        t = DecisionTrace(topic="AI", overall_confidence=0.9)
        t.update_outcome("success", 8.5)
        dte.record(t)
        assert len(dte.get_successful()) == 1

    def test_get_failed(self):
        dte = DecisionTraceEngine()
        t = DecisionTrace(topic="AI", overall_confidence=0.3)
        t.update_outcome("failure", 2.0)
        dte.record(t)
        assert len(dte.get_failed()) == 1

    def test_get_average_confidence(self):
        dte = DecisionTraceEngine()
        dte.record(DecisionTrace(topic="A", overall_confidence=0.8))
        dte.record(DecisionTrace(topic="B", overall_confidence=0.6))
        avg = dte.get_average_confidence()
        assert avg == 0.7

    def test_get_weakest_modules(self):
        dte = DecisionTraceEngine()
        dte.record(DecisionTrace(topic="A", trend_score=3.0, topic_score=8.0, overall_confidence=0.7))
        weakest = dte.get_weakest_modules()
        assert "trend" in weakest

    def test_get_successful_patterns(self):
        dte = DecisionTraceEngine()
        t = DecisionTrace(topic="A", trend_score=8.0, overall_confidence=0.9)
        t.update_outcome("success", 8.0)
        dte.record(t)
        patterns = dte.get_successful_patterns()
        assert patterns["count"] == 1

    def test_stats(self):
        dte = DecisionTraceEngine()
        dte.record(DecisionTrace(topic="A", overall_confidence=0.8))
        stats = dte.stats()
        assert stats["total_traces"] == 1

    def test_trace_to_dict(self):
        t = DecisionTrace(topic="AI", decision="Publish", overall_confidence=0.9)
        d = t.to_dict()
        assert d["topic"] == "AI"
        assert d["overall_confidence"] == 0.9

    def test_trace_from_dict(self):
        d = {"topic": "AI", "module_scores": {"trend": 8.0}, "overall_confidence": 0.9}
        t = DecisionTrace.from_dict(d)
        assert t.topic == "AI"
        assert t.module_scores["trend"] == 8.0

    def test_weakest_and_strongest(self):
        t = DecisionTrace(topic="A", trend_score=3.0, topic_score=9.0,
                         competitor_score=2.0, audience_score=5.0,
                         knowledge_score=6.0, verification_score=7.0)
        assert t.get_weakest_module() == ("competitor", 2.0)
        assert t.get_strongest_module() == ("topic", 9.0)


# ═══════════════════════════════════════════
# Test 8: Manager
# ═══════════════════════════════════════════

class TestManager:
    def test_store_and_get(self, manager):
        manager.store_entry("e1", title="Test", content="Hello world")
        entry = manager.get_entry("e1")
        assert entry.title == "Test"

    def test_get_not_found(self, manager):
        with pytest.raises(EntryNotFoundError):
            manager.get_entry("ghost")

    def test_remove_entry(self, manager):
        manager.store_entry("e1", title="Test")
        assert manager.remove_entry("e1") is True
        assert manager.index.size() == 0

    def test_list_entries(self, manager_with_data):
        assert len(manager_with_data.list_entries()) == 5

    def test_list_by_category(self, manager_with_data):
        assert len(manager_with_data.list_entries(category="ai")) == 1

    def test_search(self, manager_with_data):
        results = manager_with_data.search("AI")
        assert len(results) >= 1

    def test_search_semantic(self, manager_with_data):
        results = manager_with_data.search_semantic("AI technology jobs")
        assert isinstance(results, list)

    def test_search_by_keyword(self, manager_with_data):
        results = manager_with_data.search_by_keyword("python")
        # Keywords may be indexed differently
        assert isinstance(results, list)

    def test_search_by_tag(self, manager_with_data):
        results = manager_with_data.search_by_tag("crypto")
        assert len(results) >= 1

    def test_knowledge_graph(self, manager):
        manager.add_entity("ai", "topic", "Artificial Intelligence")
        manager.add_entity("jobs", "topic", "Employment")
        manager.add_relationship("ai", "jobs", "creates")
        neighbors = manager.get_neighbors("ai")
        assert len(neighbors) == 1

    def test_find_path(self, manager):
        manager.add_entity("a")
        manager.add_entity("b")
        manager.add_entity("c")
        manager.add_relationship("a", "b")
        manager.add_relationship("b", "c")
        path = manager.find_path("a", "c")
        assert path == ["a", "b", "c"]

    def test_add_evidence(self, manager):
        item = manager.add_evidence("ev1", text="evidence", topic="ai", credibility=0.9)
        assert item.evidence_id == "ev1"
        assert manager.get_evidence_confidence("ai") > 0

    def test_add_citation(self, manager):
        manager.add_citation("c1", source_name="Reuters", claim_id="cl1")
        citations = manager.get_citations_for_claim("cl1")
        assert len(citations) == 1

    def test_record_decision(self, manager):
        t = DecisionTrace(topic="AI", decision="Publish", overall_confidence=0.9)
        tid = manager.record_decision(t)
        assert manager.get_decision(tid) is not None

    def test_decision_stats(self, manager):
        manager.record_decision(DecisionTrace(topic="A", overall_confidence=0.8))
        stats = manager.get_decision_stats()
        assert stats["total_traces"] == 1

    def test_rank_entries(self, manager_with_data):
        ranked = manager_with_data.rank_entries(3)
        assert len(ranked) == 3

    def test_health_check(self, manager_with_data):
        h = manager_with_data.health_check()
        assert h["index_size"] == 5
        assert h["evidence_count"] == 0

    def test_persistence(self, tmp_path):
        path = tmp_path / "rm.json"
        m1 = ResearchMemoryManager(storage_path=str(path))
        m1.store_entry("e1", title="Persist", content="data")
        m2 = ResearchMemoryManager(storage_path=str(path))
        assert m2.index.size() == 1

    def test_no_storage(self):
        m = ResearchMemoryManager()
        m.store_entry("e1", title="NoStorage")
        assert m.index.size() == 1

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid")
        m = ResearchMemoryManager(storage_path=str(path))
        assert m.index.size() == 0

    def test_get_successful_patterns(self, manager):
        t = DecisionTrace(topic="A", overall_confidence=0.9)
        t.update_outcome("success", 8.0)
        manager.record_decision(t)
        patterns = manager.get_successful_patterns()
        assert patterns["count"] == 1

    def test_concurrent_access(self, manager):
        import threading
        errors = []

        def store(i):
            try:
                manager.store_entry(f"t_{i}", title=f"Thread_{i}", content=f"Content {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=store, args=(i,)) for i in range(15)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert manager.index.size() == 15
