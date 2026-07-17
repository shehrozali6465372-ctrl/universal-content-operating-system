"""Media Policies — Platform-specific media requirements and restrictions."""
from __future__ import annotations
from typing import Any, Dict, List, Set


class MediaPolicy:
    """Media policy for a specific platform."""

    __slots__ = ("platform", "supported_image_formats", "supported_video_formats",
                 "max_image_size_mb", "max_video_size_mb", "min_image_width",
                 "min_image_height", "aspect_ratios")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.supported_image_formats: Set[str] = {"jpg", "jpeg", "png", "gif"}
        self.supported_video_formats: Set[str] = {"mp4", "mov"}
        self.max_image_size_mb: float = 8.0
        self.max_video_size_mb: float = 230.0
        self.min_image_width: int = 600
        self.min_image_height: int = 600
        self.aspect_ratios: List[str] = ["1:1", "4:5", "16:9"]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "supported_image_formats": list(self.supported_image_formats),
            "supported_video_formats": list(self.supported_video_formats),
            "max_image_size_mb": self.max_image_size_mb,
            "max_video_size_mb": self.max_video_size_mb,
        }


DEFAULT_MEDIA_POLICIES: Dict[str, MediaPolicy] = {
    "facebook": MediaPolicy("facebook"),
    "instagram": MediaPolicy("instagram"),
    "twitter": MediaPolicy("twitter"),
    "linkedin": MediaPolicy("linkedin"),
    "youtube": MediaPolicy("youtube"),
    "tiktok": MediaPolicy("tiktok"),
}


class MediaPolicies:
    """Centralized media policies for all platforms."""

    def __init__(self) -> None:
        self._policies: Dict[str, MediaPolicy] = dict(DEFAULT_MEDIA_POLICIES)

    def get_policy(self, platform: str) -> MediaPolicy:
        return self._policies.get(platform.lower(), MediaPolicy(platform))

    def check_image_format(self, platform: str, file_ext: str) -> bool:
        policy = self.get_policy(platform)
        return file_ext.lower() in policy.supported_image_formats

    def check_video_format(self, platform: str, file_ext: str) -> bool:
        policy = self.get_policy(platform)
        return file_ext.lower() in policy.supported_video_formats

    def check_image_size(self, platform: str, size_mb: float) -> bool:
        policy = self.get_policy(platform)
        return size_mb <= policy.max_image_size_mb

    def check_video_size(self, platform: str, size_mb: float) -> bool:
        policy = self.get_policy(platform)
        return size_mb <= policy.max_video_size_mb

    def get_all_policies(self) -> Dict[str, MediaPolicy]:
        return dict(self._policies)
