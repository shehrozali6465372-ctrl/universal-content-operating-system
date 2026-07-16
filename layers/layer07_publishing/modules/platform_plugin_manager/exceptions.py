"""Custom exceptions for Platform Plugin Manager."""
from __future__ import annotations


class PluginError(Exception):
    """Base exception for plugin errors."""


class PluginNotFoundError(PluginError):
    """Raised when requested plugin is not registered."""


class AuthenticationError(PluginError):
    """Raised when authentication fails."""


class PublishError(PluginError):
    """Raised when publishing fails."""
