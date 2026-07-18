"""Exceptions for backup/DR."""
from __future__ import annotations

class BackupCRError(Exception): """Base error."""
class BackupError(BackupCRError): """Backup failed."""
class RestoreCRError(BackupCRError): """Restore failed."""
class ReplicationCRError(BackupCRError): """Replication failed."""
class FailoverCRError(BackupCRError): """Failover failed."""
class DisasterRecoveryCRError(BackupCRError): """DR failed."""
