"""API Versions — Track and manage platform API versions."""
from __future__ import annotations
from typing import Any, Dict, Optional


class APIVersion:
    """Version info for a platform API."""

    __slots__ = ("platform", "current_version", "min_supported",
                 "deprecated", "changelog_url")

    def __init__(self, platform: str = "") -> None:
        self.platform = platform
        self.current_version: str = "v1.0"
        self.min_supported: str = "v1.0"
        self.deprecated: bool = False
        self.changelog_url: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform,
            "current_version": self.current_version,
            "min_supported": self.min_supported,
            "deprecated": self.deprecated,
        }


DEFAULT_API_VERSIONS: Dict[str, APIVersion] = {
    "facebook": APIVersion("facebook"),
    "instagram": APIVersion("instagram"),
    "twitter": APIVersion("twitter"),
    "linkedin": APIVersion("linkedin"),
    "youtube": APIVersion("youtube"),
    "tiktok": APIVersion("tiktok"),
}


class APIVersionManager:
    """Manage platform API versions."""

    def __init__(self) -> None:
        self._versions: Dict[str, APIVersion] = dict(DEFAULT_API_VERSIONS)

    def get_version(self, platform: str) -> Optional[APIVersion]:
        return self._versions.get(platform.lower())

    def set_version(self, platform: str, version: APIVersion) -> None:
        self._versions[platform.lower()] = version

    def is_supported(self, platform: str, version: str = "") -> bool:
        ver = self._versions.get(platform.lower())
        if not ver:
            return True
        return not ver.deprecated

    def is_deprecated(self, platform: str) -> bool:
        ver = self._versions.get(platform.lower())
        return ver.deprecated if ver else False

    def get_all_versions(self) -> Dict[str, APIVersion]:
        return dict(self._versions)
