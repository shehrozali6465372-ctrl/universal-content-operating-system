"""Canonical L20 media asset contract."""
from __future__ import annotations

import os
from typing import Any, Dict, List


SUPPORTED_IMAGE_FORMATS = {"jpg", "jpeg", "png", "gif", "webp", "bmp", "tiff"}
SUPPORTED_VIDEO_FORMATS = {"mp4", "mov", "avi", "mkv", "webm", "flv"}
SUPPORTED_DOC_FORMATS = {"pdf", "doc", "docx", "pptx", "xlsx"}
ALL_SUPPORTED_FORMATS = SUPPORTED_IMAGE_FORMATS | SUPPORTED_VIDEO_FORMATS | SUPPORTED_DOC_FORMATS


class MediaAsset:
    """Media semantics object owned by L20."""

    __slots__ = (
        "asset_id", "file_path", "file_name", "media_type", "format",
        "size_bytes", "width", "height", "duration_seconds", "thumbnail_path",
        "alt_text", "caption", "tags", "checksum", "optimized",
        "platform_ready", "metadata",
    )

    def __init__(self, file_path: str = "", media_type: str = "image") -> None:
        self.asset_id = ""
        self.file_path = file_path
        self.file_name = os.path.basename(file_path) if file_path else ""
        self.media_type = media_type
        self.format = ""
        self.size_bytes = 0
        self.width = 0
        self.height = 0
        self.duration_seconds = 0.0
        self.thumbnail_path = ""
        self.alt_text = ""
        self.caption = ""
        self.tags: List[str] = []
        self.checksum = ""
        self.optimized = False
        self.platform_ready = False
        self.metadata: Dict[str, Any] = {}

    def compute_checksum(self, content: bytes = b"") -> str:
        if content:
            import hashlib
            self.checksum = hashlib.sha256(content).hexdigest()
        elif self.file_path and os.path.exists(self.file_path):
            from .runtime_media import RuntimeMedia
            self.checksum = RuntimeMedia.checksum(self.file_path)
        else:
            import hashlib
            self.checksum = hashlib.sha256(self.file_name.encode()).hexdigest()
        return self.checksum

    def get_extension(self) -> str:
        return self.file_name.rsplit(".", 1)[-1].lower() if "." in self.file_name else ""

    def is_image(self) -> bool:
        return (self.format.lower() in SUPPORTED_IMAGE_FORMATS) if self.format else self.media_type == "image"

    def is_video(self) -> bool:
        return (self.format.lower() in SUPPORTED_VIDEO_FORMATS) if self.format else self.media_type == "video"

    def is_document(self) -> bool:
        return (self.format.lower() in SUPPORTED_DOC_FORMATS) if self.format else self.media_type == "document"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id, "file_path": self.file_path,
            "file_name": self.file_name, "media_type": self.media_type,
            "format": self.format, "size_bytes": self.size_bytes,
            "width": self.width, "height": self.height, "duration_seconds": self.duration_seconds,
            "alt_text": self.alt_text, "checksum": self.checksum,
            "optimized": self.optimized, "platform_ready": self.platform_ready,
        }
