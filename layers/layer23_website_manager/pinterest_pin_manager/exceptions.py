"""Custom exceptions for Pinterest Pin Manager."""
from __future__ import annotations


class PinNotFoundError(Exception):
    """Raised when a pin is not found."""
    pass


class InvalidImageError(Exception):
    """Raised when image is invalid or missing."""
    pass


class InvalidPinTitleError(Exception):
    """Raised when pin title is empty or invalid."""
    pass


class DuplicatePinError(Exception):
    """Raised when duplicate pin detected."""
    pass


class PublishFailedError(Exception):
    """Raised when pin publishing fails."""
    pass


class SchedulingError(Exception):
    """Raised when scheduling fails."""
    pass


class BrokenWebsiteLinkError(Exception):
    """Raised when website link is broken."""
    pass


class RichPinError(Exception):
    """Raised when rich pin metadata is invalid."""
    pass


class RateLimitError(Exception):
    """Raised when Pinterest API rate limit is hit."""
    pass


class PinterestAPIError(Exception):
    """Raised when Pinterest API returns an error."""
    pass


class PinLimitError(Exception):
    """Raised when board pin limit is reached."""
    pass
