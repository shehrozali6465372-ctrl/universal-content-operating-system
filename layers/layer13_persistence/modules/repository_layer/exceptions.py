"""Exceptions for repository layer."""
from __future__ import annotations

class RepositoryError(Exception): """Base error."""
class NotFoundError(RepositoryError): """Entity not found."""
class DuplicateError(RepositoryError): """Duplicate entity."""
class IntegrityError(RepositoryError): """Data integrity error."""
class QueryError(RepositoryError): """Query error."""
