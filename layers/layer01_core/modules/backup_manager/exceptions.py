"""
Backup Manager Exceptions
Layer 1: Core System — Module 10
"""


class BackupError(Exception):
    """Base exception for backup operations."""


class BackupNotFoundError(BackupError):
    """Raised when requested backup does not exist."""


class BackupIntegrityError(BackupError):
    """Raised when backup integrity check fails."""


class BackupEncryptionError(BackupError):
    """Raised when encryption or decryption fails."""


class RestoreError(BackupError):
    """Raised when restore operation fails."""


class DisasterRecoveryError(BackupError):
    """Raised when disaster recovery procedure fails."""
