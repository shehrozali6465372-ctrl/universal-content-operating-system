"""Custom exceptions for Affiliate Manager."""
from __future__ import annotations


class AffiliateNetworkError(Exception):
    """Raised when an affiliate network operation fails."""
    pass


class MerchantNotFoundError(Exception):
    """Raised when a merchant is not found."""
    pass


class ProductNotFoundError(Exception):
    """Raised when a product is not found."""
    pass


class BrokenAffiliateLinkError(Exception):
    """Raised when an affiliate link is broken or invalid."""
    pass


class InvalidCommissionError(Exception):
    """Raised when commission rate is invalid."""
    pass


class ComplianceError(Exception):
    """Raised when compliance check fails."""
    pass


class RevenueTrackingError(Exception):
    """Raised when revenue tracking fails."""
    pass


class ProductMatchingError(Exception):
    """Raised when product matching fails."""
    pass


class LinkGenerationError(Exception):
    """Raised when link generation fails."""
    pass


class InsertionError(Exception):
    """Raised when auto link insertion fails."""
    pass
