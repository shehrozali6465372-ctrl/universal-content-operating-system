"""BoardMapper — Automatically select the best Pinterest board for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import BoardMappingError


# Simulated board registry per account
BOARD_REGISTRY: Dict[str, List[Dict[str, Any]]] = {
    "pinterest_home": [
        {"id": "board_home_bedroom", "name": "Bedroom Design Ideas", "niche": "home_decor",
         "keywords": ["bedroom", "bed", "sleep", "interior"], "pin_count": 45},
        {"id": "board_home_living", "name": "Living Room Inspirations", "niche": "home_decor",
         "keywords": ["living room", "sofa", "lounge", "interior"], "pin_count": 62},
        {"id": "board_home_kitchen", "name": "Modern Kitchen Ideas", "niche": "home_decor",
         "keywords": ["kitchen", "cooking", "cabinets", "counters"], "pin_count": 38},
        {"id": "board_home_bathroom", "name": "Bathroom Renovations", "niche": "home_decor",
         "keywords": ["bathroom", "shower", "vanity", "tile"], "pin_count": 27},
    ],
    "pinterest_fashion": [
        {"id": "board_fash_dresses", "name": "Stylish Dresses", "niche": "fashion",
         "keywords": ["dress", "outfit", "formal", "casual"], "pin_count": 55},
        {"id": "board_fash_shoes", "name": "Shoe Collection", "niche": "fashion",
         "keywords": ["shoes", "boots", "sneakers", "heels"], "pin_count": 41},
    ],
    "pinterest_beauty": [
        {"id": "board_beauty_skin", "name": "Skincare Routine", "niche": "beauty",
         "keywords": ["skincare", "face", "moisturizer", "serum"], "pin_count": 63},
        {"id": "board_beauty_makeup", "name": "Makeup Tutorials", "niche": "beauty",
         "keywords": ["makeup", "eyes", "lipstick", "foundation"], "pin_count": 48},
    ],
    "pinterest_food": [
        {"id": "board_food_dessert", "name": "Delicious Desserts", "niche": "food",
         "keywords": ["dessert", "cake", "cookie", "sweet"], "pin_count": 72},
        {"id": "board_food_dinner", "name": "Dinner Recipes", "niche": "food",
         "keywords": ["dinner", "chicken", "pasta", "healthy"], "pin_count": 54},
    ],
    "pinterest_tech": [
        {"id": "board_tech_phone", "name": "Smartphone Reviews", "niche": "tech",
         "keywords": ["phone", "smartphone", "mobile", "gadget"], "pin_count": 35},
    ],
    "pinterest_fitness": [
        {"id": "board_fit_workout", "name": "Workout Routines", "niche": "fitness",
         "keywords": ["workout", "exercise", "gym", "training"], "pin_count": 49},
    ],
    "pinterest_travel": [
        {"id": "board_travel_dest", "name": "Travel Destinations", "niche": "travel",
         "keywords": ["destination", "travel", "vacation", "trip"], "pin_count": 67},
    ],
    "pinterest_finance": [
        {"id": "board_fin_save", "name": "Saving Money Tips", "niche": "finance",
         "keywords": ["save", "money", "budget", "finance"], "pin_count": 31},
    ],
    "pinterest_diy": [
        {"id": "board_diy_wood", "name": "Woodworking Projects", "niche": "diy",
         "keywords": ["wood", "diy", "build", "craft"], "pin_count": 44},
    ],
    "pinterest_garden": [
        {"id": "board_garden_plant", "name": "Plant Care Guide", "niche": "garden",
         "keywords": ["plant", "garden", "flower", "grow"], "pin_count": 39},
    ],
}


class BoardMapper:
    """Map content to the best Pinterest board based on topic and keywords."""

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []
        self._total_mapped = 0

    def map_board(self, account_id: str, category: str = "",
                   keywords: Optional[List[str]] = None,
                   topic: str = "") -> Dict[str, Any]:
        """Select the best board for this content within an account."""
        boards = BOARD_REGISTRY.get(account_id, [])
        if not boards:
            raise BoardMappingError(f"No boards found for account: {account_id}")

        keyword_list = [k.lower() for k in (keywords or [])]
        text = f"{category} {topic}".lower()

        # Score each board
        scored = []
        for board in boards:
            score = 0
            board_kws = [k.lower() for k in board["keywords"]]

            for kw in keyword_list:
                if kw in board_kws:
                    score += 3

            for bk in board_kws:
                if bk in text:
                    score += 2

            if category and category.lower() in board["name"].lower():
                score += 2

            scored.append((score, board))

        scored.sort(key=lambda x: x[0], reverse=True)

        best = scored[0][1]
        result = {
            "board_id": best["id"],
            "board_name": best["name"],
            "pin_count": best["pin_count"],
            "match_score": scored[0][0],
            "confidence": min(0.95, 0.5 + scored[0][0] * 0.1),
        }

        self._mapping_log.append(result)
        self._total_mapped += 1
        return result

    def get_boards_for_account(self, account_id: str) -> List[Dict[str, Any]]:
        return BOARD_REGISTRY.get(account_id, [])

    def get_all_boards(self) -> Dict[str, List[Dict[str, Any]]]:
        return dict(BOARD_REGISTRY)

    def get_stats(self) -> Dict[str, Any]:
        total_boards = sum(len(v) for v in BOARD_REGISTRY.values())
        return {
            "total_mapped": self._total_mapped,
            "total_boards": total_boards,
            "accounts_with_boards": len(BOARD_REGISTRY),
        }
