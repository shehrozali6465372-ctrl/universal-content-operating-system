"""ImageMapper — Automatically select images: featured, Pinterest, thumbnail."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import ImageMappingError


class ImageMapper:
    """Map appropriate images to content based on niche and content type."""

    STYLE_OPTIONS: Dict[str, List[str]] = {
        "home_decor": ["modern", "minimalist", "cozy", "bright", "warm"],
        "fashion": ["elegant", "trendy", "classic", "edgy", "bohemian"],
        "beauty": ["glamorous", "natural", "fresh", "dewy", "bold"],
        "food": ["appetizing", "bright", "rustic", "fresh", "colorful"],
        "tech": ["sleek", "modern", "minimalist", "futuristic", "clean"],
        "fitness": ["energetic", "motivational", "dynamic", "fresh", "vibrant"],
        "travel": ["breathtaking", "sunny", "adventurous", "serene", "vibrant"],
        "finance": ["professional", "clean", "modern", "minimal", "trustworthy"],
        "diy": ["rustic", "crafty", "warm", "natural", "vibrant"],
        "garden": ["natural", "lush", "bright", "serene", "colorful"],
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []
        self._total_mapped = 0

    def map_images(self, niche: str = "", content_type: str = "article",
                    title: str = "") -> Dict[str, Any]:
        """Select appropriate images for the content."""
        style = self._select_style(niche)
        image_type = self._select_image_type(content_type)

        result = {
            "featured_image": f"/images/{niche or 'general'}/featured_{image_type}.jpg",
            "pinterest_image": f"/images/{niche or 'general'}/pinterest_{image_type}.jpg",
            "thumbnail": f"/images/{niche or 'general'}/thumb_{image_type}.jpg",
            "image_style": style,
            "recommended_format": "vertical_2x3",
            "dimensions": {"width": 1000, "height": 1500},
            "alt_text_template": f"{title or content_type} - {niche or 'general'} inspiration",
            "confidence": 0.82,
        }

        self._mapping_log.append(result)
        self._total_mapped += 1
        return result

    def _select_style(self, niche: str) -> str:
        """Select image style based on niche."""
        styles = self.STYLE_OPTIONS.get(niche, ["clean", "professional"])
        return styles[0]

    def _select_image_type(self, content_type: str) -> str:
        """Select image type based on content format."""
        type_map = {
            "list": "collage",
            "guide": "step_by_step",
            "recipe": "final_dish",
            "review": "product_shot",
            "article": "hero",
        }
        return type_map.get(content_type, "hero")

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mapped": self._total_mapped}
