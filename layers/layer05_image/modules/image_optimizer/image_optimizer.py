"""Image Optimizer — Platform-specific image optimization."""
from __future__ import annotations
from typing import Any, Dict, List


PLATFORM_IMAGE_CONFIG = {
    "facebook": {"max_size_mb": 30, "formats": ["jpg", "png"], "dpi": 72, "compression": "high"},
    "instagram": {"max_size_mb": 30, "formats": ["jpg", "png"], "dpi": 72, "compression": "medium"},
    "twitter": {"max_size_mb": 5, "formats": ["jpg", "png", "gif"], "dpi": 72, "compression": "high"},
    "linkedin": {"max_size_mb": 10, "formats": ["jpg", "png"], "dpi": 72, "compression": "medium"},
    "pinterest": {"max_size_mb": 20, "formats": ["jpg", "png"], "dpi": 72, "compression": "medium"},
    "youtube": {"max_size_mb": 2, "formats": ["jpg", "png"], "dpi": 72, "compression": "high"},
}


class OptimizationResult:
    """Result of image optimization."""
    __slots__ = ("platform", "format", "dimensions", "file_size_estimate",
                 "is_optimal", "recommendations")

    def __init__(self) -> None:
        self.platform = ""
        self.format = "jpg"
        self.dimensions = (1080, 1080)
        self.file_size_estimate = 0.0
        self.is_optimal = True
        self.recommendations: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "format": self.format,
            "dimensions": {"width": self.dimensions[0], "height": self.dimensions[1]},
            "is_optimal": self.is_optimal,
            "recommendations": self.recommendations,
        }


class ImageOptimizer:
    """Optimizes images for platform requirements."""

    def __init__(self) -> None:
        self._opt_count = 0

    def optimize(self, width: int, height: int, platform: str = "facebook") -> OptimizationResult:
        """Get optimization recommendations for an image."""
        result = OptimizationResult()
        result.platform = platform
        config = PLATFORM_IMAGE_CONFIG.get(platform, PLATFORM_IMAGE_CONFIG["facebook"])
        result.format = config["formats"][0]
        result.dimensions = (width, height)

        if width < 600 or height < 600:
            result.is_optimal = False
            result.recommendations.append("Image too small — minimum 600x600 recommended")

        aspect = width / height if height > 0 else 1
        if platform == "instagram" and abs(aspect - 1.0) > 0.2:
            result.recommendations.append("Instagram prefers 1:1 or 4:5 ratio")

        self._opt_count += 1
        return result

    @property
    def optimization_count(self) -> int:
        return self._opt_count
