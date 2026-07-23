"""VectorDBManager — Enterprise Vector Database manager integrating all components.

Features:
- Vector storage with namespaces
- Embedding generation (multiple strategies)
- Semantic search (hybrid ranking, RRF)
- RAG pipeline (retrieve → augment → generate)
- Long-term memory (consolidate, forget, recall)
- Similarity detection (exact + near-duplicate)
- Knowledge retrieval (multi-source, context-aware)
- Health monitoring and statistics
"""
from __future__ import annotations
import os
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone

from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
from layers.layer13_persistence.modules.vector_database_platform.embedding_engine import EmbeddingEngine
from layers.layer13_persistence.modules.vector_database_platform.semantic_search import SemanticSearch
from layers.layer13_persistence.modules.vector_database_platform.rag_pipeline import RAGPipeline
from layers.layer13_persistence.modules.vector_database_platform.long_term_memory import LongTermMemory
from layers.layer13_persistence.modules.vector_database_platform.similarity_detector import SimilarityDetector
from layers.layer13_persistence.modules.vector_database_platform.knowledge_retrieval import KnowledgeRetrieval


class VectorDBManager:
    """Main Vector Database manager with full enterprise features."""

    def __init__(self, dimensions: int = 384, embedding_strategy: str = "tfidf"):
        self._dimensions = dimensions
        self._embedding_strategy = embedding_strategy
        self._initialized = False

        # Core components
        self.store: Optional[VectorStore] = None
        self.embedding_engine: Optional[EmbeddingEngine] = None
        self.semantic_search: Optional[SemanticSearch] = None
        self.rag_pipeline: Optional[RAGPipeline] = None
        self.memory: Optional[LongTermMemory] = None
        self.similarity_detector: Optional[SimilarityDetector] = None
        self.knowledge_retrieval: Optional[KnowledgeRetrieval] = None

    def initialize(self) -> bool:
        """Initialize all vector database components."""
        if self._initialized:
            return True

        # Core storage
        self.store = VectorStore(dimensions=self._dimensions)

        # Embedding engine
        self.embedding_engine = EmbeddingEngine(
            dimensions=self._dimensions,
            strategy=self._embedding_strategy,
        )

        # Semantic search
        self.semantic_search = SemanticSearch(self.store, self.embedding_engine)

        # RAG pipeline
        self.rag_pipeline = RAGPipeline(self.store, self.semantic_search, self.embedding_engine)

        # Long-term memory
        self.memory = LongTermMemory(self.embedding_engine, self.store)

        # Similarity detector
        self.similarity_detector = SimilarityDetector(
            self.embedding_engine, self.store, similarity_threshold=0.85,
        )

        # Knowledge retrieval
        self.knowledge_retrieval = KnowledgeRetrieval(
            self.store, self.semantic_search, self.memory,
        )

        self._initialized = True
        return True

    # ─── Ingestion Shortcuts ──────────────────────────────────────

    def ingest_text(self, text: str, metadata: Dict[str, Any] = None,
                    namespace: str = "knowledge") -> List[Dict[str, Any]]:
        """Ingest text into the knowledge base."""
        return self.rag_pipeline.ingest(text, metadata, namespace)

    def ingest_batch(self, texts: List[str], metadata: Dict[str, Any] = None,
                     namespace: str = "knowledge") -> int:
        """Ingest multiple texts. Returns count ingested."""
        count = 0
        for text in texts:
            result = self.ingest_text(text, metadata, namespace)
            count += len(result)
        return count

    # ─── Search Shortcuts ─────────────────────────────────────────

    def search(self, query: str, top_k: int = 5, namespace: str = None) -> List[Dict[str, Any]]:
        """Semantic search."""
        return self.semantic_search.search(query, top_k, namespace)

    def multi_search(self, queries: List[str], top_k: int = 5) -> List[Dict[str, Any]]:
        """Multi-query search with RRF fusion."""
        return self.semantic_search.multi_query_search(queries, top_k)

    # ─── RAG Shortcuts ────────────────────────────────────────────

    def query(self, question: str, top_k: int = 5, namespace: str = "knowledge") -> Dict[str, Any]:
        """Full RAG query: retrieve → augment → generate."""
        return self.rag_pipeline.generate(question, top_k, namespace)

    def retrieve_context(self, query: str, max_tokens: int = 4000) -> Dict[str, Any]:
        """Get context window for LLM."""
        return self.knowledge_retrieval.get_context_window(query, max_tokens)

    # ─── Memory Shortcuts ─────────────────────────────────────────

    def remember(self, content: str, memory_type: str = "fact",
                 importance: float = 0.5) -> Dict[str, Any]:
        """Remember a fact or piece of knowledge."""
        return self.memory.remember(content, memory_type, importance)

    def recall(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Recall a specific memory."""
        return self.memory.recall(memory_id)

    def forget(self, memory_id: str) -> bool:
        """Forget a specific memory."""
        return self.memory.forget(memory_id)

    def search_memory(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search through memories."""
        return self.memory.search(query, top_k)

    # ─── Deduplication Shortcuts ──────────────────────────────────

    def check_duplicate(self, text: str) -> Dict[str, Any]:
        """Check if content is a duplicate."""
        exact = self.similarity_detector.check_exact(text)
        near = self.similarity_detector.check_near_duplicate(text)
        return {
            "is_exact_duplicate": exact is not None,
            "exact_duplicate_of": exact,
            "near_duplicates": near,
        }

    # ─── Health & Status ──────────────────────────────────────────

    def get_vector_db_status(self) -> Dict[str, Any]:
        """Get comprehensive VectorDB status — for --vector-db-status command."""
        store_stats = self.store.stats() if self.store else {}
        engine_stats = self.embedding_engine.stats() if self.embedding_engine else {}
        search_stats = self.semantic_search.stats() if self.semantic_search else {}
        rag_stats = self.rag_pipeline.stats() if self.rag_pipeline else {}
        memory_stats = self.memory.stats() if self.memory else {}
        dedup_stats = self.similarity_detector.stats() if self.similarity_detector else {}
        retrieval_stats = self.knowledge_retrieval.stats() if self.knowledge_retrieval else {}

        total_knowledge = (
            store_stats.get("total_records", 0) +
            memory_stats.get("total", 0)
        )

        overall = "Healthy" if self._initialized else "Not Initialized"

        return {
            "overall": overall,
            "initialized": self._initialized,
            "dimensions": self._dimensions,
            "embedding_strategy": self._embedding_strategy,
            "storage": store_stats,
            "embedding": engine_stats,
            "search": search_stats,
            "rag": rag_stats,
            "memory": memory_stats,
            "deduplication": dedup_stats,
            "retrieval": retrieval_stats,
            "total_knowledge_items": total_knowledge,
        }

    def health_check(self) -> Dict[str, Any]:
        """Check vector DB health."""
        return {
            "initialized": self._initialized,
            "store_healthy": self.store is not None,
            "engine_healthy": self.embedding_engine is not None,
            "search_healthy": self.semantic_search is not None,
            "overall": "healthy" if self._initialized else "uninitialized",
        }

    def close(self):
        """Cleanup resources."""
        self._initialized = False


# Singleton
_vectordb_instance: Optional[VectorDBManager] = None


def get_vectordb(dimensions: int = 384, strategy: str = "tfidf") -> VectorDBManager:
    """Get or create VectorDB manager singleton."""
    global _vectordb_instance
    if _vectordb_instance is None:
        _vectordb_instance = VectorDBManager(dimensions=dimensions, embedding_strategy=strategy)
        _vectordb_instance.initialize()
    return _vectordb_instance
