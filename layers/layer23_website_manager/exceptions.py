"""Custom exceptions for Website Manager module."""
from __future__ import annotations


class WebsiteConfigError(Exception):
    """Raised when website configuration is invalid."""
    pass


class PublishError(Exception):
    """Raised when article publishing fails."""
    pass


class InvalidSlugError(Exception):
    """Raised when URL slug is invalid or already exists."""
    pass


class MediaUploadError(Exception):
    """Raised when media upload fails."""
    pass


class SitemapError(Exception):
    """Raised when sitemap generation or update fails."""
    pass


class SEOValidationError(Exception):
    """Raised when SEO meta fails validation."""
    pass


class WebsiteNotFoundError(Exception):
    """Raised when no website configuration is found."""
    pass


class DuplicateArticleError(Exception):
    """Raised when an article with the same slug exists."""
    pass
