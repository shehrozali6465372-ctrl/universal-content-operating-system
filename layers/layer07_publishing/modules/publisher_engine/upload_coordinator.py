"""Upload Coordinator — Handle media uploads with progress tracking."""
from __future__ import annotations
from typing import Any, Callable, Dict, List

from layers.layer07_publishing.modules.media_manager.media_asset import MediaAsset


class UploadResult:
    """Result of a single file upload."""

    __slots__ = ("asset_id", "success", "url", "media_id", "error", "duration_ms")

    def __init__(self, asset_id: str = "") -> None:
        self.asset_id = asset_id
        self.success = False
        self.url: str = ""
        self.media_id: str = ""
        self.error: str = ""
        self.duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "asset_id": self.asset_id,
            "success": self.success,
            "url": self.url,
            "media_id": self.media_id,
            "error": self.error,
            "duration_ms": round(self.duration_ms, 2),
        }


class UploadCoordinator:
    """Coordinate media uploads before publishing."""

    def __init__(self) -> None:
        self._upload_count = 0
        self._total_bytes = 0

    def upload_assets(
        self,
        assets: List[MediaAsset],
        uploader: Callable[[MediaAsset], UploadResult],
    ) -> List[UploadResult]:
        results: List[UploadResult] = []
        for asset in assets:
            try:
                result = uploader(asset)
            except Exception as e:
                result = UploadResult(asset.asset_id or asset.file_name)
                result.error = str(e)[:500]
            results.append(result)
            if result.success:
                self._upload_count += 1
                self._total_bytes += asset.size_bytes
        return results

    def validate_assets(self, assets: List[MediaAsset], max_count: int = 10) -> List[str]:
        errors: List[str] = []
        if len(assets) > max_count:
            errors.append(f"Too many assets: {len(assets)} > {max_count}")
        for i, asset in enumerate(assets):
            if not asset.file_path and not asset.file_name:
                errors.append(f"Asset {i}: no file path specified")
        return errors

    def get_upload_summary(self, results: List[UploadResult]) -> Dict[str, Any]:
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        total_ms = sum(r.duration_ms for r in results)
        return {
            "total": len(results),
            "successful": successful,
            "failed": failed,
            "total_duration_ms": round(total_ms, 2),
        }

    @property
    def upload_count(self) -> int:
        return self._upload_count

    @property
    def total_bytes(self) -> int:
        return self._total_bytes
