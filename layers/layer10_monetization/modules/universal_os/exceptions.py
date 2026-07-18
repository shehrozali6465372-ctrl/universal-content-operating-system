"""Custom exceptions for Universal AI Operating System Core."""
from __future__ import annotations


class SystemError(Exception):
    """Base exception for OS core errors."""


class KernelError(SystemError):
    """Raised when kernel operations fail."""


class PluginError(SystemError):
    """Raised when plugin operations fail."""


class SecurityError(SystemError):
    """Raised when security operations fail."""


class MigrationError(SystemError):
    """Raised when migration operations fail."""


class BackupError(SystemError):
    """Raised when backup operations fail."""


class ResourceError(SystemError):
    """Raised when resource operations fail."""


class ServiceError(SystemError):
    """Raised when service operations fail."""


class ConfigurationError(SystemError):
    """Raised when configuration operations fail."""
