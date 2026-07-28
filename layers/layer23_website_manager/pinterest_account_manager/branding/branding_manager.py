"""BrandingManager — Brand colors, logo, banner, voice, and consistency."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_account_manager.models.brand_profile import BrandProfile
from layers.layer23_website_manager.pinterest_account_manager.exceptions import BrandingError


class BrandingManager:
    """Manage brand identity for all Pinterest accounts."""

    def __init__(self) -> None:
        self._profiles: Dict[str, BrandProfile] = {}
        self._synced = 0

    def create_profile(self, account_id: str, brand_name: str,
                        brand_voice: str = "professional",
                        brand_colors: Optional[Dict[str, str]] = None,
                        logo_url: str = "", banner_url: str = "",
                        keywords: Optional[List[str]] = None) -> BrandProfile:
        """Create a brand profile for an account."""
        profile = BrandProfile(
            account_id=account_id,
            brand_name=brand_name,
            brand_voice=brand_voice,
            brand_colors=brand_colors or {"primary": "#E60023", "secondary": "#000000", "accent": "#FFFFFF"},
            brand_logo_url=logo_url,
            brand_banner_url=banner_url,
            brand_keywords=keywords or [],
        )
        self._profiles[account_id] = profile
        return profile

    def create_from_niche(self, account_id: str, niche: str) -> BrandProfile:
        """Create a brand profile automatically from niche."""
        profile = BrandProfile.from_niche(niche)
        profile.account_id = account_id
        self._profiles[account_id] = profile
        return profile

    def get_profile(self, account_id: str) -> Optional[BrandProfile]:
        """Get brand profile for an account."""
        return self._profiles.get(account_id)

    def update_profile(self, account_id: str, **kwargs) -> Optional[BrandProfile]:
        """Update brand profile fields."""
        profile = self._profiles.get(account_id)
        if not profile:
            return None

        allowed = {"brand_name", "brand_voice", "brand_tone", "brand_colors",
                    "brand_logo_url", "brand_banner_url", "brand_fonts",
                    "brand_keywords", "brand_hashtags", "brand_description",
                    "brand_guidelines"}

        for key, value in kwargs.items():
            if key in allowed:
                setattr(profile, key, value)

        profile.last_reviewed = time.time()
        return profile

    def calculate_consistency(self, account_id: str, has_logo: bool = True,
                                has_banner: bool = True, has_keywords: bool = True) -> float:
        """Calculate brand consistency score (0-100)."""
        score = 100.0
        if not has_logo:
            score -= 25
        if not has_banner:
            score -= 15
        if not has_keywords:
            score -= 20
        if not has_keywords:
            score -= 10
        # Voice default reduces score
        profile = self._profiles.get(account_id)
        if profile and profile.brand_voice == "professional":
            score -= 5

        score = max(0, min(100, score))
        return score

    def sync_branding(self, account_id: str) -> Dict[str, Any]:
        """Apply branding settings to account (simulated sync)."""
        profile = self._profiles.get(account_id)
        if not profile:
            raise BrandingError(f"No brand profile for account {account_id}")

        self._synced += 1
        return {
            "account_id": account_id,
            "synced_at": time.time(),
            "status": "synced",
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_profiles": len(self._profiles),
            "total_synced": self._synced,
            "profiles": [p.to_dict() for p in self._profiles.values()],
        }
