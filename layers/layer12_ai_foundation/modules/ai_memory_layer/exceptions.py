"""Custom exceptions for AI Memory Layer."""
from __future__ import annotations


class MemoryLayerError(Exception):
    """Base error for AI memory layer."""


class StorageError(MemoryLayerError):
    """Memory storage failure."""


class RetrievalError(MemoryLayerError):
    """Memory retrieval failure."""


class IndexingError(MemoryLayerError):
    """Memory indexing failure."""


class SyncError(MemoryLayerError):
    """Memory synchronization failure."""


class MemoryFullError(MemoryLayerError):
    """Memory capacity exceeded."""


class MemoryCorruptionError(MemoryLayerError):
    """Memory data corruption detected."""


class EmbeddingError(MemoryLayerError):
    """Embedding generation failure."""
