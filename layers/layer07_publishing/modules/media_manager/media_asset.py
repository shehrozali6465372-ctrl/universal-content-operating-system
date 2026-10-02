"""Compatibility facade for canonical L20 media asset semantics."""
from layers.layer20_image_pipeline.modules.media_lifecycle.media_asset import (
    ALL_SUPPORTED_FORMATS, SUPPORTED_DOC_FORMATS, SUPPORTED_IMAGE_FORMATS,
    SUPPORTED_VIDEO_FORMATS, MediaAsset,
)
__all__ = [
    "MediaAsset", "SUPPORTED_IMAGE_FORMATS", "SUPPORTED_VIDEO_FORMATS",
    "SUPPORTED_DOC_FORMATS", "ALL_SUPPORTED_FORMATS",
]
