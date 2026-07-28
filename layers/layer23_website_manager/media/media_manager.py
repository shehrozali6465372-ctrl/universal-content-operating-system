"""MediaManager — Image upload, optimization, compression, and alt text management."""
from __future__ import annotations
import time
import os
import uuid
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.models.media_asset import MediaAsset
from layers.layer23_website_manager.exceptions import MediaUploadError


class MediaManager:
    """Manage website media assets — upload, optimize, compress."""

    def __init__(self, storage_dir: str = "media") -> None:
        self._assets: Dict[str, MediaAsset] = {}
        self._storage_dir = storage_dir
        self._allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif", "image/svg+xml"}
        self._max_file_size = 5 * 1024 * 1024  # 5MB

    # ─── Upload ────────────────────────────────────────────

    def upload(self, file_name: str, file_path: str = "", mime_type: str = "image/jpeg",
               alt_text: str = "", title: str = "", caption: str = "",
               is_featured: bool = False) -> MediaAsset:
        """Register a media asset."""
        if mime_type not in self._allowed_types:
            raise MediaUploadError(f"Unsupported media type: {mime_type}")

        # Get file size
        file_size = 0
        if file_path and os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            if file_size > self._max_file_size:
                raise MediaUploadError(f"File too large: {file_size} > {self._max_file_size}")

        asset = MediaAsset(
            asset_id=str(uuid.uuid4())[:12],
            file_name=file_name,
            file_path=file_path,
            alt_text=alt_text,
            title=title,
            caption=caption,
            mime_type=mime_type,
            file_size_bytes=file_size,
            is_featured=is_featured,
            url=f"/media/{file_name}",
            thumbnail_url=f"/media/thumb_{file_name}",
        )

        self._assets[asset.asset_id] = asset
        return asset

    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        """Get asset by ID."""
        return self._assets.get(asset_id)

    def get_all_assets(self, is_featured: Optional[bool] = None) -> List[MediaAsset]:
        """Get all assets, optionally filtered."""
        assets = list(self._assets.values())
        if is_featured is not None:
            assets = [a for a in assets if a.is_featured == is_featured]
        return sorted(assets, key=lambda a: a.uploaded_at, reverse=True)

    def delete_asset(self, asset_id: str) -> bool:
        """Delete a media asset."""
        if asset_id in self._assets:
            del self._assets[asset_id]
            return True
        return False

    # ─── Alt Text ──────────────────────────────────────────

    def set_alt_text(self, asset_id: str, alt_text: str) -> bool:
        """Set or update alt text for an asset."""
        asset = self._assets.get(asset_id)
        if not asset:
            return False
        asset.alt_text = alt_text
        return True

    def generate_alt_text(self, file_name: str) -> str:
        """Generate basic alt text from file name."""
        name = os.path.splitext(file_name)[0]
        name = name.replace("-", " ").replace("_", " ")
        return name.strip().capitalize()

    # ─── Featured Image ────────────────────────────────────

    def set_featured_image(self, asset_id: str, article_id: str) -> bool:
        """Set an asset as featured for an article."""
        # Unset all other featured
        for asset in self._assets.values():
            asset.is_featured = False
        # Set this one
        asset = self._assets.get(asset_id)
        if asset:
            asset.is_featured = True
            return True
        return False

    def get_featured_image(self) -> Optional[MediaAsset]:
        """Get the current featured image."""
        for asset in self._assets.values():
            if asset.is_featured:
                return asset
        return None

    # ─── Stats ─────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get media library statistics."""
        total_size = sum(a.file_size_bytes for a in self._assets.values())
        by_type: Dict[str, int] = {}
        for a in self._assets.values():
            by_type[a.mime_type] = by_type.get(a.mime_type, 0) + 1

        return {
            "total_assets": len(self._assets),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "by_type": by_type,
            "featured_count": sum(1 for a in self._assets.values() if a.is_featured),
        }
