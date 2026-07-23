"""Tests for Vector Database Enterprise Features.

Covers:
- VectorStore (upsert, search, namespaces, batch, metrics)
- EmbeddingEngine (embed, batch, cache, similarity)
- SemanticSearch (search, multi-query, find_similar)
- RAGPipeline (ingest, retrieve, augment, generate)
- LongTermMemory (remember, forget, recall, consolidate)
- SimilarityDetector (exact, near-duplicate, clusters)
- KnowledgeRetrieval (multi-source, context window)
- VectorDBManager (integration, status)
"""
from __future__ import annotations
import os
import sys
import time
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── VectorStore Tests ───────────────────────────────────────────

class TestVectorStore:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
        self.store = VectorStore(dimensions=8)

    def test_upsert(self):
        record = self.store.upsert("r1", [1.0, 0.0, 0.0, 0, 0, 0, 0, 0], {"text": "hello"})
        assert record.record_id == "r1"
        assert self.store.count() == 1

    def test_upsert_update(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], {"v": 1})
        self.store.upsert("r1", [0.0, 1.0, 0, 0, 0, 0, 0, 0], {"v": 2})
        record = self.store.get("r1")
        assert record.metadata["v"] == 2
        assert record.version == 2

    def test_get(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0])
        assert self.store.get("r1") is not None
        assert self.store.get("nonexistent") is None

    def test_delete(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0])
        assert self.store.delete("r1") is True
        assert self.store.count() == 0

    def test_search(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], {"text": "cat"})
        self.store.upsert("r2", [0.0, 1.0, 0, 0, 0, 0, 0, 0], {"text": "dog"})
        results = self.store.search([1.0, 0, 0, 0, 0, 0, 0, 0], top_k=2)
        assert len(results) == 2
        assert results[0][0].record_id == "r1"

    def test_search_namespace(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], namespace="ns1")
        self.store.upsert("r2", [1.0, 0, 0, 0, 0, 0, 0, 0], namespace="ns2")
        results = self.store.search([1.0, 0, 0, 0, 0, 0, 0, 0], namespace="ns1")
        assert len(results) == 1

    def test_search_filter(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], {"type": "a"})
        self.store.upsert("r2", [1.0, 0, 0, 0, 0, 0, 0, 0], {"type": "b"})
        results = self.store.search(
            [1.0, 0, 0, 0, 0, 0, 0, 0],
            filter_fn=lambda r: r.metadata.get("type") == "a",
        )
        assert len(results) == 1

    def test_batch_upsert(self):
        items = [{"id": f"r{i}", "vector": [float(i)] + [0.0] * 7, "metadata": {"i": i}}
                 for i in range(5)]
        results = self.store.batch_upsert(items)
        assert len(results) == 5

    def test_batch_delete(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0])
        self.store.upsert("r2", [0.0, 1.0, 0, 0, 0, 0, 0, 0])
        count = self.store.batch_delete(["r1", "r2", "r3"])
        assert count == 2

    def test_delete_namespace(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], namespace="ns")
        self.store.upsert("r2", [0.0, 1.0, 0, 0, 0, 0, 0, 0], namespace="ns")
        count = self.store.delete_namespace("ns")
        assert count == 2

    def test_namespaces(self):
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0], namespace="a")
        self.store.upsert("r2", [0.0, 1.0, 0, 0, 0, 0, 0, 0], namespace="b")
        assert set(self.store.list_namespaces()) == {"a", "b"}

    def test_count(self):
        assert self.store.count() == 0
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0])
        assert self.store.count() == 1

    def test_metrics(self):
        self.store.set_metric("euclidean")
        self.store.upsert("r1", [1.0, 0, 0, 0, 0, 0, 0, 0])
        self.store.search([1.0, 0, 0, 0, 0, 0, 0, 0])
        stats = self.store.stats()
        assert stats["metric"] == "euclidean"
        assert stats["total_upserts"] >= 1
        assert stats["total_searches"] >= 1

    def test_cosine_similarity(self):
        self.store.upsert("r1", [1.0, 0.0, 0.0, 0, 0, 0, 0, 0])
        self.store.upsert("r2", [0.707, 0.707, 0.0, 0, 0, 0, 0, 0])
        results = self.store.search([1.0, 0.0, 0.0, 0, 0, 0, 0, 0])
        assert results[0][1] > results[1][1]


# ─── EmbeddingEngine Tests ──────────────────────────────────────

class TestEmbeddingEngine:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
        self.engine = EmbeddingEngine(dimensions=32, strategy="tfidf")

    def test_embed(self):
        vec = self.engine.embed("hello world")
        assert len(vec) == 32
        assert any(v != 0.0 for v in vec)

    def test_embed_normalized(self):
        vec = self.engine.embed("test text", normalize=True)
        import math
        norm = math.sqrt(sum(x * x for x in vec))
        assert abs(norm - 1.0) < 0.01

    def test_batch_embed(self):
        vectors = self.engine.batch_embed(["hello", "world", "test"])
        assert len(vectors) == 3
        assert all(len(v) == 32 for v in vectors)

    def test_cache(self):
        vec1 = self.engine.embed("cached text")
        vec2 = self.engine.embed("cached text")
        assert vec1 == vec2
        stats = self.engine.stats()
        assert stats["cache_hit_rate"] > 0

    def test_similarity(self):
        sim = self.engine.similarity("hello world", "hello world")
        assert sim > 0.99
        sim_diff = self.engine.similarity("hello world", "completely different text")
        assert sim_diff < sim

    def test_strategies(self):
        from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
        for strategy in ["tfidf", "contextual", "hybrid", "hash"]:
            engine = EmbeddingEngine(dimensions=16, strategy=strategy)
            vec = engine.embed("test")
            assert len(vec) == 16

    def test_stats(self):
        self.engine.embed("test")
        stats = self.engine.stats()
        assert stats["total_generated"] >= 1
        assert stats["vocab_size"] > 0

    def test_empty_text(self):
        vec = self.engine.embed("")
        assert len(vec) == 32


# ─── SemanticSearch Tests ────────────────────────────────────────

class TestSemanticSearch:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
        from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
        from layers.layer13_persistence.modules.vector_database_platform.semantic_search import SemanticSearch
        self.store = VectorStore(dimensions=32)
        self.engine = EmbeddingEngine(dimensions=32, strategy="contextual")
        self.search = SemanticSearch(self.store, self.engine)

        # Seed data
        texts = [
            "Python is a programming language",
            "Machine learning uses algorithms",
            "Data science analyzes data",
            "Web development builds websites",
            "Artificial intelligence mimics human intelligence",
        ]
        for i, text in enumerate(texts):
            vec = self.engine.embed(text)
            self.store.upsert(f"doc{i}", vec, {"text": text}, namespace="docs")

    def test_search(self):
        results = self.search.search("programming language", top_k=3, namespace="docs")
        assert len(results) > 0
        assert all("text" in r for r in results)

    def test_search_empty(self):
        results = self.search.search("nonexistent topic", top_k=5, namespace="empty")
        assert isinstance(results, list)  # Returns empty or results from cross-namespace

    def test_multi_query(self):
        results = self.search.multi_query_search(
            ["programming", "data analysis"], top_k=3, namespace="docs",
        )
        assert len(results) > 0

    def test_find_similar(self):
        results = self.search.find_similar("doc0", top_k=3, namespace="docs")
        assert len(results) > 0
        assert all(r["record_id"] != "doc0" for r in results)

    def test_history(self):
        self.search.search("test", namespace="docs")
        history = self.search.get_history()
        assert len(history) >= 1

    def test_stats(self):
        self.search.search("test", namespace="docs")
        stats = self.search.stats()
        assert stats["total_searches"] >= 1


# ─── RAGPipeline Tests ──────────────────────────────────────────

class TestRAGPipeline:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
        from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
        from layers.layer13_persistence.modules.vector_database_platform.semantic_search import SemanticSearch
        from layers.layer13_persistence.modules.vector_database_platform.rag_pipeline import RAGPipeline
        self.store = VectorStore(dimensions=32)
        self.engine = EmbeddingEngine(dimensions=32, strategy="tfidf")
        search = SemanticSearch(self.store, self.engine)
        self.rag = RAGPipeline(self.store, search, self.engine)

    def test_ingest(self):
        result = self.rag.ingest("Python is great for AI. It has many libraries.")
        assert len(result) > 0

    def test_ingest_batch(self):
        texts = ["Topic A", "Topic B", "Topic C"]
        for t in texts:
            self.rag.ingest(t)

        results = self.rag.retrieve("Topic", namespace="knowledge")
        assert len(results) > 0

    def test_retrieve(self):
        self.rag.ingest("Machine learning is a subset of AI")
        results = self.rag.retrieve("machine learning", top_k=3, min_relevance=0.0)
        assert len(results) > 0

    def test_augment(self):
        self.rag.ingest("Python is a programming language")
        context = self.rag.retrieve("Python", min_relevance=0.0)
        augmented = self.rag.augment("What is Python?", context)
        assert "augmented_prompt" in augmented
        assert "Python" in augmented["augmented_prompt"]

    def test_generate_without_llm(self):
        self.rag.ingest("AI is transforming industries")
        result = self.rag.generate("How is AI transforming industries?")
        assert result["query"] == "How is AI transforming industries?"
        assert result["chunks_retrieved"] >= 0

    def test_chunking_strategies(self):
        long_text = "First sentence. Second sentence. Third sentence. Fourth sentence."
        for strategy in ["fixed", "sentence", "semantic"]:
            result = self.rag.ingest(long_text, chunk_strategy=strategy)
            assert len(result) > 0

    def test_stats(self):
        stats = self.rag.stats()
        assert "chunk_size" in stats
        assert "relevance_threshold" in stats


# ─── LongTermMemory Tests ───────────────────────────────────────

class TestLongTermMemory:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.long_term_memory import LongTermMemory
        self.memory = LongTermMemory()

    def test_remember(self):
        result = self.memory.remember("Python is a language", "fact", 0.8)
        assert result["content"] == "Python is a language"
        assert result["type"] == "fact"
        assert result["importance"] == 0.8

    def test_recall(self):
        result = self.memory.remember("Remember this", "fact")
        recalled = self.memory.recall(result["memory_id"])
        assert recalled is not None
        assert recalled["access_count"] >= 1

    def test_forget(self):
        result = self.memory.remember("Forget me", "fact")
        assert self.memory.forget(result["memory_id"]) is True
        assert self.memory.recall(result["memory_id"]) is None

    def test_forget_by_type(self):
        self.memory.remember("fact1", "fact")
        self.memory.remember("fact2", "fact")
        self.memory.remember("pref1", "preference")
        forgotten = self.memory.forget_by_type("fact")
        assert forgotten == 2
        remaining = self.memory.get_by_type("preference")
        assert len(remaining) == 1

    def test_search(self):
        self.memory.remember("Python programming", "fact")
        self.memory.remember("Java programming", "fact")
        results = self.memory.search("Python")
        assert len(results) > 0

    def test_consolidation(self):
        # Add memory and access it multiple times
        result = self.memory.remember("Important fact", "fact", 0.9)
        for _ in range(5):
            self.memory.recall(result["memory_id"])

        consolidated = self.memory.consolidate()
        assert consolidated["promoted_to_long_term"] >= 1

    def test_get_recent(self):
        self.memory.remember("old fact", "fact")
        time.sleep(0.01)
        self.memory.remember("new fact", "fact")
        recent = self.memory.get_recent(limit=1)
        assert len(recent) == 1

    def test_get_important(self):
        self.memory.remember("low", "fact", 0.1)
        self.memory.remember("high", "fact", 0.9)
        important = self.memory.get_important(limit=1)
        assert important[0]["importance"] == 0.9

    def test_count(self):
        self.memory.remember("f1", "fact")
        self.memory.remember("p1", "preference")
        counts = self.memory.count()
        assert counts["total"] == 2
        assert counts["by_type"]["fact"] == 1

    def test_stats(self):
        self.memory.remember("test", "fact")
        stats = self.memory.stats()
        assert stats["total"] == 1
        assert stats["total_remembered"] == 1


# ─── SimilarityDetector Tests ───────────────────────────────────

class TestSimilarityDetector:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.similarity_detector import SimilarityDetector
        self.detector = SimilarityDetector(similarity_threshold=0.85)

    def test_exact_duplicate(self):
        self.detector.register("c1", "Hello World")
        result = self.detector.check_exact("Hello World")
        assert result == "c1"

    def test_exact_no_duplicate(self):
        result = self.detector.check_exact("Unique text")
        assert result is None

    def test_register_unique(self):
        result = self.detector.register("c1", "Unique content")
        assert result["is_unique"] is True
        assert result["is_exact_duplicate"] is False

    def test_register_duplicate(self):
        self.detector.register("c1", "Same content")
        result = self.detector.register("c2", "Same content")
        assert result["is_exact_duplicate"] is True
        assert result["exact_duplicate_of"] == "c1"

    def test_unregister(self):
        self.detector.register("c1", "Content")
        assert self.detector.unregister("c1") is True
        assert self.detector.check_exact("Content") is None

    def test_stats(self):
        self.detector.register("c1", "Text")
        self.detector.check_exact("Text")
        stats = self.detector.stats()
        assert stats["registered_content"] == 1
        assert stats["total_checked"] >= 1


# ─── KnowledgeRetrieval Tests ───────────────────────────────────

class TestKnowledgeRetrieval:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
        from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
        from layers.layer13_persistence.modules.vector_database_platform.semantic_search import SemanticSearch
        from layers.layer13_persistence.modules.vector_database_platform.long_term_memory import LongTermMemory
        from layers.layer13_persistence.modules.vector_database_platform.knowledge_retrieval import KnowledgeRetrieval

        self.store = VectorStore(dimensions=32)
        self.engine = EmbeddingEngine(dimensions=32, strategy="contextual")
        search = SemanticSearch(self.store, self.engine)
        self.memory = LongTermMemory()
        self.retrieval = KnowledgeRetrieval(self.store, search, self.memory)

        # Seed
        for i, text in enumerate(["Python basics", "Data analysis with Python", "ML algorithms"]):
            vec = self.engine.embed(text)
            self.store.upsert(f"k{i}", vec, {"text": text, "source": "docs"}, namespace="knowledge")

    def test_retrieve(self):
        results = self.retrieval.retrieve("Python", top_k=3)
        assert len(results) > 0

    def test_retrieve_with_memory(self):
        self.memory.remember("Python is popular", "fact")
        results = self.retrieval.retrieve("Python", top_k=5, namespaces=["knowledge", "memory"])
        assert len(results) > 0

    def test_context_window(self):
        context = self.retrieval.get_context_window("Python basics", max_tokens=4000)
        assert "context_text" in context
        assert "sources" in context

    def test_stats(self):
        self.retrieval.retrieve("test")
        stats = self.retrieval.stats()
        assert stats["total_retrievals"] >= 1


# ─── VectorDBManager Integration Tests ──────────────────────────

class TestVectorDBManager:
    def setup_method(self):
        from layers.layer13_persistence.modules.vector_database_platform.vector_db_manager import VectorDBManager
        self.vdb = VectorDBManager(dimensions=32, embedding_strategy="tfidf")
        self.vdb.initialize()

    def teardown_method(self):
        self.vdb.close()

    def test_initialize(self):
        assert self.vdb._initialized is True
        assert self.vdb.store is not None
        assert self.vdb.embedding_engine is not None

    def test_ingest(self):
        result = self.vdb.ingest_text("Python is great for AI")
        assert len(result) > 0

    def test_search(self):
        self.vdb.ingest_text("Machine learning algorithms")
        results = self.vdb.search("machine learning")
        assert isinstance(results, list)

    def test_remember_recall(self):
        result = self.vdb.remember("Important fact", "fact", 0.9)
        recalled = self.vdb.recall(result["memory_id"])
        assert recalled is not None

    def test_forget(self):
        result = self.vdb.remember("Temporary", "fact")
        assert self.vdb.forget(result["memory_id"]) is True

    def test_search_memory(self):
        self.vdb.remember("Python is popular", "fact")
        results = self.vdb.search_memory("Python")
        assert len(results) > 0

    def test_check_duplicate(self):
        self.vdb.ingest_text("Unique text")
        # Store the text for exact check
        from layers.layer13_persistence.modules.vector_database_platform.similarity_detector import SimilarityDetector
        self.vdb.similarity_detector.register("c1", "Duplicate text")
        result = self.vdb.check_duplicate("Duplicate text")
        assert result["is_exact_duplicate"] is True

    def test_query(self):
        self.vdb.ingest_text("AI transforms industries through automation")
        result = self.vdb.query("How does AI transform industries?")
        assert "query" in result
        assert result["query"] == "How does AI transform industries?"

    def test_retrieve_context(self):
        self.vdb.ingest_text("Python programming basics")
        context = self.vdb.retrieve_context("Python basics")
        assert "context_text" in context

    def test_get_vector_db_status(self):
        status = self.vdb.get_vector_db_status()
        assert status["overall"] == "Healthy"
        assert status["initialized"] is True
        assert "storage" in status
        assert "embedding" in status
        assert "memory" in status

    def test_health_check(self):
        health = self.vdb.health_check()
        assert health["overall"] == "healthy"

    def test_full_enterprise_stack(self):
        """Test all components working together."""
        # Ingest knowledge
        self.vdb.ingest_text("Python is a versatile programming language used in AI, web, and data science.")
        self.vdb.ingest_text("Machine learning is a subset of artificial intelligence.")
        self.vdb.ingest_text("Data science combines statistics and programming.")

        # Search
        results = self.vdb.search("programming")
        assert len(results) > 0

        # Remember
        self.vdb.remember("User prefers Python over Java", "preference", 0.8)
        self.vdb.remember("Important project deadline Friday", "event", 0.9)

        # Recall
        memories = self.vdb.search_memory("Python")
        assert len(memories) > 0

        # RAG
        rag_result = self.vdb.query("What is Python used for?")
        assert rag_result["chunks_retrieved"] >= 0

        # Status
        status = self.vdb.get_vector_db_status()
        assert status["total_knowledge_items"] > 0
