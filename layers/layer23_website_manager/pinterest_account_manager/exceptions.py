"""Custom exceptions for Pinterest Account Manager module."""
from __future__ import annotations


class AccountNotFoundError(Exception):
    """Raised when a Pinterest account is not found."""
    pass


class InvalidTokenError(Exception):
    """Raised when OAuth token is invalid or malformed."""
    pass


class TokenExpiredError(Exception):
    """Raised when OAuth token has expired."""
    pass


class WebsiteNotClaimedError(Exception):
    """Raised when website claim is required but missing."""
    pass


class BrandingError(Exception):
    """Raised when branding operation fails."""
    pass


class PermissionDeniedError(Exception):
    """Raised when account lacks required permission."""
    pass


class AccountSuspendedError(Exception):
    """Raised when account is suspended by Pinterest."""
    pass


class DuplicateAccountError(Exception):
    """Raised when trying to register an account that already exists."""
    pass


class AccountLimitError(Exception):
    """Raised when account limit is reached."""
    pass


class SelectionError(Exception):
    """Raised when no suitable account can be selected."""
    pass
