"""Exceptions for vector database platform."""
from __future__ import annotations

class VectorDBError(Exception):
    """Base vector DB error."""

class ConnectionError(VectorDBError):
    """Connection failed."""

class EmbeddingError(VectorDBError):
    """Embedding operation failed."""

class SearchError(VectorDBError):
    """Search operation failed."""

class CollectionError(VectorDBError):
    """Collection operation failed."""

class IndexError(VectorDBError):
    """Index operation failed."""

class ValidationError(VectorDBError):
    """Validation failed."""

class BackupError(VectorDBError):
    """Backup failed."""

class RestoreError(VectorDBError):
    """Restore failed."""
