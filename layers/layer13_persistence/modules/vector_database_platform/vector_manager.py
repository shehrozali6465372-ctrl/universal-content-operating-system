"""vector_manager.py — Unified vector database manager."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer13_persistence.modules.vector_database_platform.vector_store import VectorStore
from layers.layer13_persistence.modules.vector_database_platform.embedding_manager import EmbeddingManager
from layers.layer13_persistence.modules.vector_database_platform.collection_manager import CollectionManager


class VectorManager:
    """Unified vector database management."""

    def __init__(self) -> None:
        self._stores: Dict[str, VectorStore] = {}
        self._embedding_manager = EmbeddingManager()
        self._collection_manager = CollectionManager()

    def create_store(self, name: str, dimensions: int = 1536) -> VectorStore:
        store = VectorStore(dimensions)
        self._stores[name] = store
        self._collection_manager.create(name, dimensions)
        return store

    def get_store(self, name: str) -> Optional[VectorStore]:
        return self._stores.get(name)

    def upsert(self, store_name: str, vector: List[float],
               metadata: Dict[str, Any] = None):
        store = self._stores.get(store_name)
        if store:
            return store.upsert(vector, metadata)
        return None

    def search(self, store_name: str, query: List[float], top_k: int = 10):
        store = self._stores.get(store_name)
        if store:
            return store.search(query, top_k)
        return []

    def delete(self, store_name: str, record_id: int) -> bool:
        store = self._stores.get(store_name)
        if store:
            return store.delete(record_id)
        return False

    def list_stores(self) -> List[str]:
        return list(self._stores.keys())

    def stats(self) -> Dict[str, Any]:
        return {"stores": len(self._stores), "collections": self._collection_manager.count()}
