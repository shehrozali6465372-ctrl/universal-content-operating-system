"""AffiliateMapper — Automatically detect and attach affiliate products to content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import AffiliateMappingError


# Simulated affiliate product registry per niche
AFFILIATE_PRODUCTS: Dict[str, List[Dict[str, Any]]] = {
    "home_decor": [
        {"id": "aff_bed_frame", "name": "Modern Bed Frame", "price": "$299",
         "commission": 8.0, "url": "https://amzn.to/bedframe", "keywords": ["bed", "bedroom", "frame"]},
        {"id": "aff_sofa", "name": "Luxury Sofa Set", "price": "$899",
         "commission": 6.0, "url": "https://amzn.to/sofa", "keywords": ["sofa", "living room", "furniture"]},
        {"id": "aff_lamp", "name": "Designer Floor Lamp", "price": "$79",
         "commission": 10.0, "url": "https://amzn.to/lamp", "keywords": ["lamp", "lighting", "decor"]},
    ],
    "fashion": [
        {"id": "aff_dress", "name": "Elegant Evening Dress", "price": "$89",
         "commission": 12.0, "url": "https://amzn.to/dress", "keywords": ["dress", "evening", "formal"]},
    ],
    "beauty": [
        {"id": "aff_serum", "name": "Vitamin C Serum", "price": "$34",
         "commission": 15.0, "url": "https://amzn.to/serum", "keywords": ["serum", "skincare", "face"]},
    ],
    "food": [
        {"id": "aff_mixer", "name": "Stand Mixer Pro", "price": "$249",
         "commission": 7.0, "url": "https://amzn.to/mixer", "keywords": ["mixer", "baking", "kitchen"]},
    ],
    "tech": [
        {"id": "aff_headphone", "name": "Noise Cancelling Headphones", "price": "$149",
         "commission": 5.0, "url": "https://amzn.to/headphone", "keywords": ["headphone", "audio", "music"]},
    ],
    "fitness": [
        {"id": "aff_yoga_mat", "name": "Premium Yoga Mat", "price": "$49",
         "commission": 10.0, "url": "https://amzn.to/yogamat", "keywords": ["yoga", "mat", "exercise"]},
    ],
    "travel": [
        {"id": "aff_luggage", "name": "Smart Luggage Set", "price": "$199",
         "commission": 8.0, "url": "https://amzn.to/luggage", "keywords": ["luggage", "travel", "bag"]},
    ],
    "finance": [
        {"id": "aff_ledger", "name": "Budget Planner", "price": "$24",
         "commission": 20.0, "url": "https://amzn.to/ledger", "keywords": ["budget", "planner", "finance"]},
    ],
    "diy": [
        {"id": "aff_drill", "name": "Cordless Drill Kit", "price": "$79",
         "commission": 6.0, "url": "https://amzn.to/drill", "keywords": ["drill", "tool", "diy"]},
    ],
    "garden": [
        {"id": "aff_pot", "name": "Self-Watering Plant Pot", "price": "$39",
         "commission": 12.0, "url": "https://amzn.to/pot", "keywords": ["pot", "plant", "garden"]},
    ],
}


class AffiliateMapper:
    """Map content to the best affiliate product based on niche and keywords."""

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []
        self._total_mapped = 0

    def map_affiliate(self, niche: str, keywords: Optional[List[str]] = None,
                       topic: str = "") -> Dict[str, Any]:
        """Select the best affiliate product for this content."""
        products = AFFILIATE_PRODUCTS.get(niche, [])
        if not products:
            raise AffiliateMappingError(f"No affiliate products for niche: {niche}")

        keyword_list = [k.lower() for k in (keywords or [])]
        text = topic.lower()

        # Score products by keyword relevance
        scored = []
        for product in products:
            score = 0
            prod_kws = [k.lower() for k in product["keywords"]]

            for kw in keyword_list:
                if kw in prod_kws:
                    score += 3
            for pk in prod_kws:
                if pk in text:
                    score += 2
            # Bonus for high commission
            score += product["commission"] / 10

            scored.append((score, product))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]

        result = {
            "product_id": best["id"],
            "product_name": best["name"],
            "price": best["price"],
            "commission": best["commission"],
            "affiliate_url": best["url"],
            "confidence": min(0.95, 0.4 + scored[0][0] * 0.1),
        }

        self._mapping_log.append(result)
        self._total_mapped += 1
        return result

    def get_products_by_niche(self, niche: str) -> List[Dict[str, Any]]:
        return AFFILIATE_PRODUCTS.get(niche, [])

    def get_all_products(self) -> Dict[str, List[Dict[str, Any]]]:
        return dict(AFFILIATE_PRODUCTS)

    def get_stats(self) -> Dict[str, Any]:
        total_products = sum(len(v) for v in AFFILIATE_PRODUCTS.values())
        return {
            "total_mapped": self._total_mapped,
            "total_products": total_products,
            "niches_covered": len(AFFILIATE_PRODUCTS),
        }
