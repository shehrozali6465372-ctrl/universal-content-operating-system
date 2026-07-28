"""BrandProfile — Brand identity for a Pinterest account."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class BrandProfile:
    """Complete brand identity for a Pinterest Business Account."""

    brand_id: str = ""
    account_id: str = ""
    brand_name: str = ""
    brand_voice: str = "professional"  # professional, casual, educational, inspirational, humorous
    brand_tone: str = "consistent"
    brand_colors: Dict[str, str] = field(default_factory=lambda: {
        "primary": "#E60023",
        "secondary": "#000000",
        "accent": "#FFFFFF",
    })
    brand_logo_url: str = ""
    brand_banner_url: str = ""
    brand_fonts: Dict[str, str] = field(default_factory=lambda: {
        "heading": "Helvetica",
        "body": "Arial",
    })
    brand_keywords: List[str] = field(default_factory=list)
    brand_hashtags: List[str] = field(default_factory=list)
    brand_description: str = ""
    brand_guidelines: str = ""
    consistency_score: float = 0.0
    last_reviewed: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "account_id": self.account_id,
            "brand_name": self.brand_name,
            "brand_voice": self.brand_voice,
            "brand_tone": self.brand_tone,
            "brand_colors": self.brand_colors,
            "brand_logo_url": self.brand_logo_url,
            "brand_banner_url": self.brand_banner_url,
            "brand_keywords": self.brand_keywords[:10],
            "brand_hashtags": self.brand_hashtags[:10],
            "consistency_score": round(self.consistency_score, 1),
        }

    @classmethod
    def from_niche(cls, niche: str) -> "BrandProfile":
        """Generate a recommended brand profile from a niche."""
        voice_map = {
            "home decor": "inspirational",
            "beauty": "inspirational",
            "fashion": "inspirational",
            "food": "educational",
            "tech": "professional",
            "fitness": "motivational",
            "travel": "inspirational",
            "finance": "professional",
            "education": "educational",
            "health": "educational",
        }
        color_map = {
            "home decor": {"primary": "#8B7355", "secondary": "#F5F0EB", "accent": "#2F4F4F"},
            "beauty": {"primary": "#FF69B4", "secondary": "#FFF0F5", "accent": "#8B008B"},
            "fashion": {"primary": "#000000", "secondary": "#FFFFFF", "accent": "#FFD700"},
            "food": {"primary": "#FF6347", "secondary": "#FFF8DC", "accent": "#228B22"},
            "tech": {"primary": "#1E90FF", "secondary": "#F0F8FF", "accent": "#32CD32"},
            "fitness": {"primary": "#FF4500", "secondary": "#F5F5F5", "accent": "#006400"},
            "travel": {"primary": "#00CED1", "secondary": "#F0FFFF", "accent": "#FFD700"},
            "finance": {"primary": "#2E8B57", "secondary": "#F5FFFA", "accent": "#1C1C1C"},
            "education": {"primary": "#4169E1", "secondary": "#F8F8FF", "accent": "#FF8C00"},
            "health": {"primary": "#3CB371", "secondary": "#F5FFF5", "accent": "#FF6347"},
        }

        niche_lower = niche.lower().strip()
        voice = voice_map.get(niche_lower, "professional")
        colors = color_map.get(niche_lower, {"primary": "#E60023", "secondary": "#000000", "accent": "#FFFFFF"})

        return cls(
            brand_name=f"{niche.replace(chr(95), chr(32)).title()} Studio",
            brand_voice=voice,
            brand_colors=colors,
            brand_keywords=[niche.replace(chr(95), chr(32))],
        )
