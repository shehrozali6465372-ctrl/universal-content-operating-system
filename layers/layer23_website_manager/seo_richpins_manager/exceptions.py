"""Custom exceptions for SEO & Rich Pins Manager."""
from __future__ import annotations

class KeywordGenerationError(Exception): pass
class MetaGenerationError(Exception): pass
class RichPinError(Exception): pass
class SchemaError(Exception): pass
class SitemapError(Exception): pass
class RobotsError(Exception): pass
class SEOValidationError(Exception): pass
class DuplicateMetadataError(Exception): pass
class OpenGraphError(Exception): pass
class TwitterCardError(Exception): pass
