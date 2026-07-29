"""PinImageManager — Manage pin images: validation, optimization, quality, dimensions."""
from __future__ import annotations
import os
import time
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import InvalidImageError


class PinImageManager:
    """Validate, optimize and manage pin images."""

    REQUIRED_WIDTH = 1000
    RECOMMENDED_HEIGHT = 1500
    ASPECT_RATIO = 2 / 3  # Pinterest recommends 2:3
    MAX_SIZE_MB = 20
    ALLOWED_FORMATS = {"jpg", "jpeg", "png", "webp"}

    def __init__(self) -> None:
        self._image_log: List[dict] = []

    def validate_image(self, file_path: str = "", width: int = 0, height: int = 0,
                        format_type: str = "jpg") -> Dict[str, Any]:
        """Validate pin image dimensions, format, and quality."""
        issues: List[str] = []
        score = 100.0

        # Format check
        fmt = format_type.lower().replace("image/", "")
        if fmt not in self.ALLOWED_FORMATS:
            issues.append(f"Unsupported format: {fmt}")
            score -= 30

        # Dimensions
        if width > 0 and height > 0:
            if width < 200 or height < 300:
                issues.append(f"Image too small: {width}x{height}")
                score -= 25

            actual_ratio = width / height
            if abs(actual_ratio - self.ASPECT_RATIO) > 0.1:
                issues.append(f"Aspect ratio {actual_ratio:.2f} != recommended 2:3")
                score -= 15

        # File size
        if file_path and os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            if size_mb > self.MAX_SIZE_MB:
                issues.append(f"File too large: {size_mb:.1f}MB > {self.MAX_SIZE_MB}MB")
                score -= 20

        result = {
            "is_valid": len(issues) == 0,
            "score": max(0, score),
            "issues": issues,
            "width": width,
            "height": height,
            "aspect_ratio": round(width / height, 2) if height > 0 and width > 0 else 0,
        }

        self._image_log.append(result)
        return result

    def recommend_dimensions(self, niche: str = "") -> Dict[str, int]:
        """Recommend optimal pin dimensions for a niche."""
        return {
            "width": self.REQUIRED_WIDTH,
            "height": self.RECOMMENDED_HEIGHT,
            "aspect_ratio": f"2:3",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {"total_validations": len(self._image_log)}
