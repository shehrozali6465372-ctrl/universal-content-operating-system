"""MediaAsset — Image and media file model."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MediaAsset:
    """Media file associated with website content."""

    asset_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    file_name: str = ""
    file_path: str = ""
    alt_text: str = ""
    title: str = ""
    caption: str = ""
    mime_type: str = "image/jpeg"
    width: int = 0
    height: int = 0
    file_size_bytes: int = 0
    is_featured: bool = False
    url: str = ""
    thumbnail_url: str = ""
    optimized_url: str = ""
    uploaded_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "file_name": self.file_name,
            "alt_text": self.alt_text,
            "title": self.title,
            "caption": self.caption,
            "mime_type": self.mime_type,
            "width": self.width,
            "height": self.height,
            "file_size_bytes": self.file_size_bytes,
            "is_featured": self.is_featured,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "optimized_url": self.optimized_url,
            "uploaded_at": self.uploaded_at,
        }
