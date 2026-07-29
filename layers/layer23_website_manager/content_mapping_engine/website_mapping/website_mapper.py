"""WebsiteMapper — Automatically select correct website and category for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import WebsiteMappingError


# Simulated website registry
WEBSITE_REGISTRY: Dict[str, Dict[str, Any]] = {
    "site_home_decor": {
        "id": "site_home_decor",
        "name": "Modern Living Hub",
        "domain": "modernlivinghub.com",
        "niche": "home_decor",
        "categories": ["Bedroom", "Living Room", "Kitchen", "Bathroom", "Garden"],
    },
    "site_fashion": {
        "id": "site_fashion",
        "name": "Style Vault",
        "domain": "stylevault.com",
        "niche": "fashion",
        "categories": ["Dresses", "Shoes", "Bags", "Accessories"],
    },
    "site_beauty": {
        "id": "site_beauty",
        "name": "Beauty Bloom Studio",
        "domain": "beautybloomstudio.com",
        "niche": "beauty",
        "categories": ["Skincare", "Makeup", "Hair Care", "Nails"],
    },
    "site_food": {
        "id": "site_food",
        "name": "Tasty Kitchen",
        "domain": "tastykitchen.com",
        "niche": "food",
        "categories": ["Desserts", "Main Course", "Breakfast", "Drinks"],
    },
    "site_tech": {
        "id": "site_tech",
        "name": "Gadget Flow",
        "domain": "gadgetflow.com",
        "niche": "tech",
        "categories": ["Smartphones", "Laptops", "Audio", "Gaming"],
    },
    "site_fitness": {
        "id": "site_fitness",
        "name": "Fit Life Hub",
        "domain": "fitlifehub.com",
        "niche": "fitness",
        "categories": ["Workouts", "Yoga", "Nutrition", "Equipment"],
    },
    "site_travel": {
        "id": "site_travel",
        "name": "Wanderlust Diaries",
        "domain": "wanderlustdiaries.com",
        "niche": "travel",
        "categories": ["Destinations", "Hotels", "Tips", "Adventure"],
    },
    "site_finance": {
        "id": "site_finance",
        "name": "Wealth Wise",
        "domain": "wealthwise.com",
        "niche": "finance",
        "categories": ["Saving", "Investing", "Budgeting", "Retirement"],
    },
    "site_diy": {
        "id": "site_diy",
        "name": "DIY Crafts Master",
        "domain": "diycraftsmaster.com",
        "niche": "diy",
        "categories": ["Woodworking", "Sewing", "Painting", "Recycling"],
    },
    "site_garden": {
        "id": "site_garden",
        "name": "Garden Paradise",
        "domain": "gardenparadise.com",
        "niche": "garden",
        "categories": ["Plants", "Flowers", "Landscaping", "Vegetables"],
    },
}


class WebsiteMapper:
    """Map content to correct website and category."""

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []
        self._total_mapped = 0

    def map_to_website(self, niche: str, category: str = "",
                        topic: str = "") -> Dict[str, Any]:
        """Select the best website for this content."""
        # Find websites matching niche
        candidates = [w for w in WEBSITE_REGISTRY.values() if w["niche"] == niche]

        if not candidates:
            # Default to first available
            candidates = list(WEBSITE_REGISTRY.values())

        if not candidates:
            raise WebsiteMappingError(f"No website found for niche: {niche}")

        # Pick best match
        website = candidates[0]
        mapped_category = self._map_category(website, category)

        result = {
            "website_id": website["id"],
            "website_name": website["name"],
            "website_url": f"https://{website['domain']}",
            "website_category": mapped_category,
            "confidence": 0.85,
        }

        self._mapping_log.append(result)
        self._total_mapped += 1
        return result

    def _map_category(self, website: Dict[str, Any], category: str) -> str:
        """Map article category to website category."""
        if not category:
            return website["categories"][0]

        cat_lower = category.lower()
        for wc in website["categories"]:
            if wc.lower() in cat_lower or cat_lower in wc.lower():
                return wc

        return website["categories"][0]

    def get_available_websites(self) -> List[Dict[str, Any]]:
        return list(WEBSITE_REGISTRY.values())

    def get_websites_by_niche(self, niche: str) -> List[Dict[str, Any]]:
        return [w for w in WEBSITE_REGISTRY.values() if w["niche"] == niche]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_mapped": self._total_mapped,
            "available_websites": len(WEBSITE_REGISTRY),
        }
