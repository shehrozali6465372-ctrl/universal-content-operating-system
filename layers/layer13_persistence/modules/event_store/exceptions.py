"""Exceptions for event store."""
from __future__ import annotations

class EventStoreError(Exception): """Base error."""
class AppendError(EventStoreError): """Append failed."""
class ReplayError(EventStoreError): """Replay failed."""
class SnapshotError(EventStoreError): """Snapshot failed."""
class VersionError(EventStoreError): """Version conflict."""
