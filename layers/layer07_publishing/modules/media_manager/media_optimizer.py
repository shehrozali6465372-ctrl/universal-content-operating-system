"""Media Optimizer — Optimize media for platform-specific requirements."""
from __future__ import annotations
from typing import Any, Dict, List

from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset


class OptimizationResult:
    """Result of media optimization."""

    __slots__ = ("original_size", "optimized_size", "savings_percent",
                 "changes", "success")

    def __init__(self) -> None:
        self.original_size: int = 0
        self.optimized_size: int = 0
        self.savings_percent: float = 0.0
        self.changes: List[str] = []
        self.success: bool = True

    def to_dict(self) -> dict:
        return {
            "original_size": self.original_size,
            "optimized_size": self.optimized_size,
            "savings_percent": round(self.savings_percent, 1),
            "changes": self.changes,
            "success": self.success,
        }


class MediaOptimizer:
    """Optimize media assets for publishing."""

    # Platform-specific optimal dimensions
    PLATFORM_OPTIMALS: Dict[str, Dict[str, Any]] = {
        "facebook": {"image_width": 1200, "image_height": 630, "aspect_ratio": "1.91:1"},
        "instagram": {"image_width": 1080, "image_height": 1080, "aspect_ratio": "1:1"},
        "twitter": {"image_width": 1200, "image_height": 675, "aspect_ratio": "16:9"},
        "linkedin": {"image_width": 1200, "image_height": 627, "aspect_ratio": "1.91:1"},
        "pinterest": {"image_width": 1000, "image_height": 1500, "aspect_ratio": "2:3"},
    }

    def __init__(self) -> None:
        self._optimize_count = 0

    def optimize(self, asset: MediaAsset, platform: str = "facebook") -> OptimizationResult:
        """Optimize a media asset for a platform."""
        result = OptimizationResult()
        result.original_size = asset.size_bytes

        if asset.is_image():
            self._optimize_image(asset, platform, result)
        elif asset.is_video():
            self._optimize_video(asset, platform, result)

        if result.original_size > 0 and result.optimized_size > 0:
            result.savings_percent = ((result.original_size - result.optimized_size) / result.original_size) * 100

        asset.optimized = True
        self._optimize_count += 1
        return result

    def optimize_batch(self, assets: List[MediaAsset], platform: str = "facebook") -> List[OptimizationResult]:
        return [self.optimize(a, platform) for a in assets]

    def get_optimal_dimensions(self, platform: str) -> Dict[str, Any]:
        return self.PLATFORM_OPTIMALS.get(platform, {})

    def _optimize_image(self, asset: MediaAsset, platform: str, result: OptimizationResult) -> None:
        optimal = self.PLATFORM_OPTIMALS.get(platform, {})
        target_w = optimal.get("image_width", 1200)
        target_h = optimal.get("image_height", 630)

        if asset.width > 0 and asset.height > 0:
            if asset.width != target_w or asset.height != target_h:
                result.changes.append(f"Resize {asset.width}x{asset.height} → {target_w}x{target_h}")
                asset.width = target_w
                asset.height = target_h
                # Simulate size reduction
                result.optimized_size = int(asset.size_bytes * 0.7)
            else:
                result.optimized_size = asset.size_bytes
        else:
            result.optimized_size = asset.size_bytes
            result.changes.append("No dimension info — skipped resize")

    def _optimize_video(self, asset: MediaAsset, platform: str, result: OptimizationResult) -> None:
        # For video, we just estimate compression
        result.optimized_size = int(asset.size_bytes * 0.8)
        result.changes.append("Video compression applied (estimated)")

    def mark_platform_ready(self, asset: MediaAsset, platform: str) -> None:
        asset.platform_ready = True
        asset.metadata["optimized_for"] = platform

