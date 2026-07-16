"""Media Manager — Core orchestrator for media management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset
from layers.layer07_publishing.modules.media_manager.media_validator import MediaValidator, ValidationIssue
from layers.layer07_publishing.modules.media_manager.media_optimizer import MediaOptimizer, OptimizationResult


class MediaManager:
    """Orchestrate media validation, optimization, and preparation."""

    def __init__(
        self,
        validator: Optional[MediaValidator] = None,
        optimizer: Optional[MediaOptimizer] = None,
    ) -> None:
        self.validator = validator or MediaValidator()
        self.optimizer = optimizer or MediaOptimizer()
        self._assets: Dict[str, MediaAsset] = {}
        self._checksums: Dict[str, str] = {}
        self._manage_count = 0

    def add_asset(self, asset: MediaAsset) -> str:
        """Add a media asset, compute checksum for dedup."""
        asset.compute_checksum()
        if not asset.asset_id:
            asset.asset_id = f"media_{asset.checksum[:8]}"
        self._assets[asset.asset_id] = asset
        self._checksums[asset.checksum] = asset.asset_id
        self._manage_count += 1
        return asset.asset_id

    def add_image(self, file_path: str, alt_text: str = "", width: int = 0, height: int = 0) -> MediaAsset:
        """Convenience: add an image asset."""
        asset = MediaAsset(file_path, media_type="image")
        asset.alt_text = alt_text
        asset.width = width
        asset.height = height
        asset.format = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        self.add_asset(asset)
        return asset

    def add_video(self, file_path: str, duration: float = 0.0) -> MediaAsset:
        asset = MediaAsset(file_path, media_type="video")
        asset.duration_seconds = duration
        asset.format = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        self.add_asset(asset)
        return asset

    def add_document(self, file_path: str) -> MediaAsset:
        asset = MediaAsset(file_path, media_type="document")
        asset.format = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
        self.add_asset(asset)
        return asset

    def validate(self, asset_id: str, platform: str = "facebook") -> List[ValidationIssue]:
        asset = self._assets.get(asset_id)
        if not asset:
            return [ValidationIssue("asset", "critical", f"Asset {asset_id} not found", "Add asset first")]
        return self.validator.validate(asset, platform)

    def optimize(self, asset_id: str, platform: str = "facebook") -> Optional[OptimizationResult]:
        asset = self._assets.get(asset_id)
        if not asset:
            return None
        result = self.optimizer.optimize(asset, platform)
        self.optimizer.mark_platform_ready(asset, platform)
        return result

    def prepare_for_platform(self, asset_id: str, platform: str) -> Dict[str, Any]:
        """Validate + optimize + mark ready for platform."""
        asset = self._assets.get(asset_id)
        if not asset:
            return {"error": f"Asset {asset_id} not found"}

        issues = self.validator.validate(asset, platform)
        opt_result = self.optimizer.optimize(asset, platform)
        self.optimizer.mark_platform_ready(asset, platform)

        return {
            "asset_id": asset_id,
            "platform": platform,
            "valid": len([i for i in issues if i.severity in ("high", "critical")]) == 0,
            "issues": [i.to_dict() for i in issues],
            "optimization": opt_result.to_dict(),
            "platform_ready": asset.platform_ready,
        }

    def find_duplicate(self, asset_id: str) -> Optional[str]:
        asset = self._assets.get(asset_id)
        if not asset or not asset.checksum:
            return None
        for aid, existing in self._assets.items():
            if aid != asset_id and existing.checksum == asset.checksum:
                return aid
        return None

    def get_asset(self, asset_id: str) -> Optional[MediaAsset]:
        return self._assets.get(asset_id)

    def list_assets(self) -> List[MediaAsset]:
        return list(self._assets.values())

    def remove_asset(self, asset_id: str) -> bool:
        return self._assets.pop(asset_id, None) is not None

    def get_statistics(self) -> Dict[str, Any]:
        assets = list(self._assets.values())
        return {
            "total_assets": len(assets),
            "images": sum(1 for a in assets if a.is_image()),
            "videos": sum(1 for a in assets if a.is_video()),
            "documents": sum(1 for a in assets if a.is_document()),
            "optimized": sum(1 for a in assets if a.optimized),
            "platform_ready": sum(1 for a in assets if a.platform_ready),
            "total_size_bytes": sum(a.size_bytes for a in assets),
        }

    @property
    def manage_count(self) -> int:
        return self._manage_count
