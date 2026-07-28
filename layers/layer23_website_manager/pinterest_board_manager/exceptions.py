"""Custom exceptions for Pinterest Board Manager module."""
from __future__ import annotations


class BoardNotFoundError(Exception):
    """Raised when a Pinterest board is not found."""
    pass


class DuplicateBoardError(Exception):
    """Raised when trying to create a board that already exists."""
    pass


class InvalidBoardNameError(Exception):
    """Raised when board name is empty or invalid."""
    pass


class BoardCreationError(Exception):
    """Raised when board creation fails."""
    pass


class SEOOptimizationError(Exception):
    """Raised when SEO optimization fails."""
    pass


class BoardMappingError(Exception):
    """Raised when board-to-account mapping fails."""
    pass


class BoardPermissionError(Exception):
    """Raised when user lacks permission for board operation."""
    pass


class EmptyBoardError(Exception):
    """Raised when board has no pins."""
    pass


class BoardLimitError(Exception):
    """Raised when account board limit is reached."""
    pass
