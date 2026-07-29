"""Custom exceptions for Content Mapping Engine."""
from __future__ import annotations


class ContentClassificationError(Exception):
    """Raised when content classification fails."""
    pass


class WebsiteMappingError(Exception):
    """Raised when website mapping fails."""
    pass


class AccountMappingError(Exception):
    """Raised when Pinterest account mapping fails."""
    pass


class BoardMappingError(Exception):
    """Raised when board mapping fails."""
    pass


class AffiliateMappingError(Exception):
    """Raised when affiliate product mapping fails."""
    pass


class ImageMappingError(Exception):
    """Raised when image mapping fails."""
    pass


class SchedulingMappingError(Exception):
    """Raised when scheduling mapping fails."""
    pass


class ValidationError(Exception):
    """Raised when AI validation fails."""
    pass


class RelationshipError(Exception):
    """Raised when relationship building fails."""
    pass


class RecommendationError(Exception):
    """Raised when recommendation fails."""
    pass


class SEOMappingError(Exception):
    """Raised when SEO mapping fails."""
    pass


class PinStrategyError(Exception):
    """Raised when pin strategy selection fails."""
    pass
