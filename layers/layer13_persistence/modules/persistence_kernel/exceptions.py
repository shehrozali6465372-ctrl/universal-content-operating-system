"""Exceptions for persistence kernel."""
from __future__ import annotations


class PersistenceError(Exception):
    """Base persistence error."""


class StorageError(PersistenceError):
    """Storage operation failed."""


class ConnectionError(PersistenceError):
    """Database connection failed."""


class TransactionError(PersistenceError):
    """Transaction failed."""


class QueryError(PersistenceError):
    """Query execution failed."""


class MigrationError(PersistenceError):
    """Migration failed."""


class BackupError(PersistenceError):
    """Backup operation failed."""


class RestoreError(PersistenceError):
    """Restore operation failed."""


class CacheError(PersistenceError):
    """Cache operation failed."""


class ValidationError(PersistenceError):
    """Validation failed."""


class ConfigurationError(PersistenceError):
    """Configuration error."""


class HealthCheckError(PersistenceError):
    """Health check failed."""


class VersionError(PersistenceError):
    """Version mismatch."""
