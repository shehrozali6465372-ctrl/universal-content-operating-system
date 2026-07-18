"""Exceptions for AI memory persistence."""
from __future__ import annotations

class MemoryPersistenceError(Exception): """Base error."""
class StorageError(MemoryPersistenceError): """Storage failed."""
class RetrievalError(MemoryPersistenceError): """Retrieval failed."""
class SearchError(MemoryPersistenceError): """Search failed."""
class CompactionError(MemoryPersistenceError): """Compaction failed."""
class SnapshotError(MemoryPersistenceError): """Snapshot failed."""
class VersionError(MemoryPersistenceError): """Version error."""
