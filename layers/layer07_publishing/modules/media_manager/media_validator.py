"""Media Validator — Validate media assets for platform compatibility."""
from __future__ import annotations
import os
from typing import Dict, List

from layers.layer07_publishing.modules.media_manager.media_asset import (
    MediaAsset, SUPPORTED_IMAGE_FORMATS, SUPPORTED_VIDEO_FORMATS,
)


class ValidationIssue:
    """A media validation issue."""

    __slots__ = ("field", "severity", "message", "suggestion")

    def __init__(self, field: str = "", severity: str = "low", message: str = "", suggestion: str = "") -> None:
        self.field = field
        self.severity = severity
        self.message = message
        self.suggestion = suggestion

    def to_dict(self) -> dict:
        return {"field": self.field, "severity": self.severity, "message": self.message, "suggestion": self.suggestion}


class MediaValidator:
    """Validate media assets against platform requirements."""

    # Platform-specific limits
    PLATFORM_LIMITS: Dict[str, Dict[str, int]] = {
        "facebook": {"max_image_mb": 10, "max_video_mb": 4096, "max_images": 10, "max_video_seconds": 14400},
        "instagram": {"max_image_mb": 8, "max_video_mb": 650, "max_images": 10, "max_video_seconds": 3600},
        "twitter": {"max_image_mb": 5, "max_video_mb": 512, "max_images": 4, "max_video_seconds": 140},
        "linkedin": {"max_image_mb": 10, "max_video_mb": 5000, "max_images": 20, "max_video_seconds": 600},
        "tiktok": {"max_video_mb": 287, "max_video_seconds": 600},
        "youtube": {"max_video_mb": 12288, "max_video_seconds": 43200},
        "pinterest": {"max_image_mb": 20, "max_images": 1},
    }

    def __init__(self) -> None:
        self._check_count = 0

    def validate(self, asset: MediaAsset, platform: str = "facebook") -> List[ValidationIssue]:
        """Validate a media asset for a specific platform."""
        issues: List[ValidationIssue] = []

        # Format check
        fmt = asset.format.lower() if asset.format else asset.get_extension()
        if asset.is_image() and fmt not in SUPPORTED_IMAGE_FORMATS:
            issues.append(ValidationIssue("format", "high", f"Unsupported image format: {fmt}", f"Use: {', '.join(SUPPORTED_IMAGE_FORMATS)}"))
        if asset.is_video() and fmt not in SUPPORTED_VIDEO_FORMATS:
            issues.append(ValidationIssue("format", "high", f"Unsupported video format: {fmt}", f"Use: {', '.join(SUPPORTED_VIDEO_FORMATS)}"))

        # File existence
        if asset.file_path and not os.path.exists(asset.file_path):
            issues.append(ValidationIssue("file", "critical", f"File not found: {asset.file_path}", "Check file path"))

        # Platform-specific limits
        limits = self.PLATFORM_LIMITS.get(platform, {})
        max_image_mb = limits.get("max_image_mb", 10)
        max_video_mb = limits.get("max_video_mb", 5000)

        if asset.is_image() and asset.size_bytes > max_image_mb * 1024 * 1024:
            issues.append(ValidationIssue("size", "high", f"Image exceeds {platform} limit ({asset.size_bytes / 1024 / 1024:.1f}MB > {max_image_mb}MB)", "Compress or resize"))

        if asset.is_video() and asset.size_bytes > max_video_mb * 1024 * 1024:
            issues.append(ValidationIssue("size", "high", f"Video exceeds {platform} limit", "Compress video"))

        # Alt text
        if asset.is_image() and not asset.alt_text:
            issues.append(ValidationIssue("accessibility", "low", "Missing alt text", "Add descriptive alt text for accessibility"))

        self._check_count += 1
        return issues

    def validate_batch(self, assets: List[MediaAsset], platform: str = "facebook") -> Dict[str, List[ValidationIssue]]:
        """Validate multiple assets."""
        return {asset.file_name or f"asset_{i}": self.validate(asset, platform) for i, asset in enumerate(assets)}

    def validate_platform_limits(self, assets: List[MediaAsset], platform: str) -> List[ValidationIssue]:
        """Check if batch of assets exceeds platform limits."""
        issues: List[ValidationIssue] = []
        limits = self.PLATFORM_LIMITS.get(platform, {})

        max_images = limits.get("max_images", 10)
        images = [a for a in assets if a.is_image()]
        if len(images) > max_images:
            issues.append(ValidationIssue("count", "high", f"Too many images ({len(images)}/{max_images})", f"Reduce to {max_images}"))

        return issues

    @property
    def check_count(self) -> int:
        return self._check_count
