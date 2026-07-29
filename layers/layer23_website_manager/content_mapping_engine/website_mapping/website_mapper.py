"""WebsiteMapper — Automatically choose website, category, and subcategory for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.exceptions import WebsiteMappingError


class WebsiteMapper:
    """Map content to the correct website, category, and subcategory."""

    # Predefined websites by niche
    NICHE_WEBSITES: Dict[str, List[Dict[str, str]]] = {
        "home_decor": [
            {"id": "site_hd1", "name": "Modern Living Hub", "domain": "modernlivinghub.com"},
            {"id": "site_hd2", "name": "Home Decor Daily", "domain": "homedecordaily.com"},
        ],
        "fashion": [
            {"id": "site_fa1", "name": "Style Vault", "domain": "stylevault.com"},
        ],
        "beauty": [
            {"id": "site_be1", "name": "Beauty Bloom Studio", "domain": "beautybloom.com"},
        ],
        "food": [
            {"id": "site_fo1", "name": "Tasty Kitchen", "domain": "tastykitchen.com"},
        ],
        "tech": [
            {"id": "site_te1", "name": "Tech Trends", "domain": "techtrends.com"},
        ],
        "fitness": [
            {"id": "site_fi1", "name": "Fit Life", "domain": "fitlife.com"},
        ],
        "travel": [
            {"id": "site_tr1", "name": "Wanderlust", "domain": "wanderlust.com"},
        ],
        "finance": [
            {"id": "site_fn1", "name": "Money Smart", "domain": "moneysmart.com"},
        ],
        "diy": [
            {"id": "site_di1", "name": "DIY Crafts Hub", "domain": "diycraftshub.com"},
        ],
    }

    CATEGORY_MAP: Dict[str, List[str]] = {
        "home_decor": ["bedroom", "kitchen", "living_room", "bathroom", "organization"],
        "fashion": ["women", "men", "accessories", "seasonal"],
        "beauty": ["skincare", "makeup", "hair_care", "nail_art"],
        "food": ["breakfast", "dinner", "dessert", "healthy", "baking"],
        "tech": ["gadgets", "software", "AI", "mobile"],
        "fitness": ["workout", "yoga", "nutrition", "weight_loss"],
        "travel": ["destinations", "tips", "budget_travel", "adventure"],
        "finance": ["investing", "saving", "crypto", "passive_income"],
        "diy": ["home_diy", "crafts", "recycling", "woodworking"],
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def map_website(self, niche: str, category: str = "",
                     preferred_website: str = "") -> Dict[str, Any]:
        """Map content to the best website."""
        websites = self.NICHE_WEBSITES.get(niche, [])

        if not websites:
            return {"id": "", "name": "", "domain": "", "confidence": 0.0}

        # Use preferred website if valid
        if preferred_website:
            for ws in websites:
                if ws["id"] == preferred_website or ws["name"] == preferred_website:
                    result = {**ws, "confidence": 1.0}
                    self._mapping_log.append(result)
                    return result

        website = websites[0]
        result = {**website, "confidence": 0.9}
        self._mapping_log.append(result)
        return result

    def map_category(self, niche: str, title: str = "") -> Dict[str, Any]:
        """Map content to the best category and subcategory."""
        categories = self.CATEGORY_MAP.get(niche, ["general"])
        primary = categories[0] if categories else "general"
        subcategory = ""

        # Try to detect subcategory from title
        if title:
            title_lower = title.lower()
            for cat in categories:
                if cat.replace("_", " ") in title_lower:
                    primary = cat
                    subcategory = ""
                    break

        result = {
            "category": primary,
            "subcategory": subcategory or "general",
            "available_categories": categories,
        }
        self._mapping_log.append(result)
        return result

    def get_available_websites(self, niche: str) -> List[Dict[str, str]]:
        return self.NICHE_WEBSITES.get(niche, [])

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
