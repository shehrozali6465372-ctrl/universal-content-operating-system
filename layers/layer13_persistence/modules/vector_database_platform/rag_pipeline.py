"""RAGPipeline — Retrieval-Augmented Generation pipeline.

Flow: Query → Retrieve → Augment → Generate → Store
Features:
- Context-aware retrieval
- Chunking strategies (fixed, sentence, semantic)
- Context window management
- Relevance scoring and filtering
- Citation tracking
- A/B testing for retrieval strategies
"""
from __future__ import annotations
import time
import hashlib
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline."""

    def __init__(self, store: Any, search: Any, embedding_engine: Any = None,
                 generator: Callable = None):
        self._store = store
        self._search = search
        self._engine = embedding_engine
        self._generator = generator  # Optional: actual LLM generator
        self._lock = threading.Lock()

        # Configuration
        self._chunk_size = 500  # chars per chunk
        self._chunk_overlap = 50  # overlap between chunks
        self._max_context_tokens = 4000
        self._relevance_threshold = 0.3

        # Stats
        self._total_queries = 0
        self._total_retrievals = 0
        self._total_generations = 0

    def ingest(self, text: str, metadata: Dict[str, Any] = None,
               namespace: str = "knowledge", chunk_strategy: str = "sentence") -> List[Dict[str, Any]]:
        """Ingest text into the knowledge base.

        Args:
            text: Text to ingest
            metadata: Additional metadata
            namespace: Storage namespace
            chunk_strategy: "fixed", "sentence", or "semantic"

        Returns:
            List of ingested chunks with their IDs
        """
        chunks = self._chunk_text(text, chunk_strategy)
        ingested = []

        for i, chunk in enumerate(chunks):
            chunk_id = hashlib.sha256(f"{namespace}:{chunk[:100]}:{i}".encode()).hexdigest()

            # Generate embedding
            vector = None
            if self._engine:
                vector = self._engine.embed(chunk)

            if vector:
                chunk_metadata = {
                    "text": chunk,
                    "source": metadata.get("source", "unknown") if metadata else "unknown",
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_strategy": chunk_strategy,
                    "parent_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
                }
                if metadata:
                    chunk_metadata.update(metadata)

                self._store.upsert(
                    record_id=chunk_id,
                    vector=vector,
                    metadata=chunk_metadata,
                    namespace=namespace,
                )

                ingested.append({
                    "chunk_id": chunk_id,
                    "text": chunk[:200],
                    "chunk_index": i,
                })

        return ingested

    def retrieve(self, query: str, top_k: int = 5, namespace: str = "knowledge",
                 min_relevance: float = None) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query.

        Args:
            query: User query
            top_k: Number of context chunks to retrieve
            namespace: Knowledge namespace
            min_relevance: Minimum relevance threshold

        Returns:
            List of relevant chunks with scores
        """
        threshold = min_relevance if min_relevance is not None else self._relevance_threshold
        results = self._search.search(
            query, top_k=top_k, namespace=namespace, min_score=threshold,
        )

        with self._lock:
            self._total_retrievals += len(results)

        return results

    def augment(self, query: str, context_chunks: List[Dict[str, Any]],
                template: str = None) -> Dict[str, Any]:
        """Augment a query with retrieved context.

        Args:
            query: Original query
            context_chunks: Retrieved context
            template: Custom prompt template

        Returns:
            Augmented prompt with context
        """
        # Build context string
        context_parts = []
        total_chars = 0
        max_chars = self._max_context_tokens * 4  # ~4 chars per token

        for chunk in context_chunks:
            text = chunk.get("text", "")
            if total_chars + len(text) > max_chars:
                break
            context_parts.append(text)
            total_chars += len(text)

        context_str = "\n\n---\n\n".join(context_parts)

        # Build augmented prompt
        if template:
            augmented = template.format(query=query, context=context_str)
        else:
            augmented = f"""Context:
{context_str}

Question: {query}

Answer based on the context above:"""

        # Track citations
        citations = []
        for chunk in context_chunks:
            citations.append({
                "text": chunk.get("text", "")[:100],
                "score": chunk.get("score", 0),
                "source": chunk.get("metadata", {}).get("source", "unknown"),
            })

        return {
            "augmented_prompt": augmented,
            "context_used": context_parts,
            "context_chars": total_chars,
            "citations": citations,
            "chunks_retrieved": len(context_chunks),
        }

    def generate(self, query: str, top_k: int = 5, namespace: str = "knowledge",
                 template: str = None) -> Dict[str, Any]:
        """Full RAG pipeline: retrieve → augment → generate.

        Args:
            query: User query
            top_k: Number of context chunks
            namespace: Knowledge namespace
            template: Custom prompt template

        Returns:
            Complete RAG result with response, context, and metadata
        """
        start = time.time()

        # Step 1: Retrieve
        context = self.retrieve(query, top_k, namespace)

        # Step 2: Augment
        augmented = self.augment(query, context, template)

        # Step 3: Generate (if generator is available)
        response = None
        if self._generator:
            try:
                response = self._generator(augmented["augmented_prompt"])
                with self._lock:
                    self._total_generations += 1
            except Exception as e:
                response = f"[Generation error: {str(e)[:200]}]"

        elapsed_ms = (time.time() - start) * 1000

        with self._lock:
            self._total_queries += 1

        return {
            "query": query,
            "response": response,
            "context": augmented["context_used"],
            "citations": augmented["citations"],
            "chunks_retrieved": augmented["chunks_retrieved"],
            "elapsed_ms": round(elapsed_ms, 1),
            "namespace": namespace,
        }

    def _chunk_text(self, text: str, strategy: str = "sentence") -> List[str]:
        """Split text into chunks."""
        if strategy == "fixed":
            return self._chunk_fixed(text)
        elif strategy == "sentence":
            return self._chunk_sentences(text)
        elif strategy == "semantic":
            return self._chunk_semantic(text)
        return self._chunk_fixed(text)

    def _chunk_fixed(self, text: str) -> List[str]:
        """Fixed-size chunking with overlap."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + self._chunk_size
            chunks.append(text[start:end])
            start = end - self._chunk_overlap
        return chunks

    def _chunk_sentences(self, text: str) -> List[str]:
        """Sentence-based chunking."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        chunks = []
        current = ""
        for sent in sentences:
            if len(current) + len(sent) > self._chunk_size and current:
                chunks.append(current.strip())
                current = sent
            else:
                current = current + " " + sent if current else sent
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def _chunk_semantic(self, text: str) -> List[str]:
        """Semantic chunking based on paragraph breaks."""
        paragraphs = text.split("\n\n")
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) > self._chunk_size and current:
                chunks.append(current.strip())
                current = para
            else:
                current = current + "\n\n" + para if current else para
        if current.strip():
            chunks.append(current.strip())
        return chunks

    def stats(self) -> Dict[str, Any]:
        """Get pipeline statistics."""
        return {
            "total_queries": self._total_queries,
            "total_retrievals": self._total_retrievals,
            "total_generations": self._total_generations,
            "chunk_size": self._chunk_size,
            "chunk_overlap": self._chunk_overlap,
            "max_context_tokens": self._max_context_tokens,
            "relevance_threshold": self._relevance_threshold,
        }
