"""ImageMapper — Automatically choose featured image, pin image, thumbnail, and style."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.exceptions import ImageMappingError


class ImageMapper:
    """Map content to the best images — featured, pin, thumbnail, infographic."""

    NICHE_STYLES: Dict[str, Dict[str, Any]] = {
        "home_decor": {"style": "bright_well_lit", "orientation": "vertical", "vibe": "warm"},
        "fashion": {"style": "clean_minimal", "orientation": "vertical", "vibe": "modern"},
        "beauty": {"style": "soft_glam", "orientation": "vertical", "vibe": "elegant"},
        "food": {"style": "bright_appetizing", "orientation": "square", "vibe": "fresh"},
        "tech": {"style": "sleek_modern", "orientation": "horizontal", "vibe": "professional"},
        "fitness": {"style": "energetic", "orientation": "vertical", "vibe": "motivational"},
        "travel": {"style": "vibrant", "orientation": "horizontal", "vibe": "adventurous"},
        "finance": {"style": "clean_professional", "orientation": "horizontal", "vibe": "trustworthy"},
        "diy": {"style": "bright_step_by_step", "orientation": "vertical", "vibe": "creative"},
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def map_images(self, niche: str, content_type: str = "article") -> Dict[str, Any]:
        """Choose optimal image types and styles for content."""
        style_info = self.NICHE_STYLES.get(niche, {
            "style": "clean", "orientation": "vertical", "vibe": "neutral",
        })

        result = {
            "featured_image_style": style_info["style"],
            "pin_image_orientation": style_info["orientation"],
            "thumbnail_style": style_info["style"],
            "image_vibe": style_info["vibe"],
            "needs_infographic": content_type in ("listicle", "tutorial", "recipe"),
            "recommended_width": 1000,
            "recommended_height": 1500,
        }

        if content_type == "tutorial":
            result["needs_step_images"] = True
            result["image_count"] = 5

        self._mapping_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
