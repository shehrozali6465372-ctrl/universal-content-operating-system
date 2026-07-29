"""BoardMapper — Automatically choose the best Pinterest board for content."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.content_mapping_engine.exceptions import BoardMappingError


class BoardMapper:
    """Map content to the most relevant Pinterest board by topic, keywords, and performance."""

    # Predefined boards by niche
    NICHE_BOARDS: Dict[str, List[Dict[str, Any]]] = {
        "home_decor": [
            {"id": "board_hd1", "name": "Bedroom Design Ideas", "pins": 120, "followers": 5000},
            {"id": "board_hd2", "name": "Modern Kitchen Inspiration", "pins": 85, "followers": 3200},
            {"id": "board_hd3", "name": "Living Room Decor", "pins": 95, "followers": 4100},
            {"id": "board_hd4", "name": "Bathroom Renovations", "pins": 60, "followers": 2100},
            {"id": "board_hd5", "name": "Home Organization", "pins": 45, "followers": 1800},
        ],
        "fashion": [
            {"id": "board_fa1", "name": "Trendy Outfits", "pins": 200, "followers": 8000},
            {"id": "board_fa2", "name": "Accessories Guide", "pins": 75, "followers": 2500},
        ],
        "beauty": [
            {"id": "board_be1", "name": "Skincare Routine", "pins": 150, "followers": 6000},
            {"id": "board_be2", "name": "Makeup Tutorials", "pins": 110, "followers": 4500},
        ],
        "food": [
            {"id": "board_fo1", "name": "Quick Recipes", "pins": 180, "followers": 7000},
            {"id": "board_fo2", "name": "Healthy Eating", "pins": 90, "followers": 3500},
        ],
        "tech": [
            {"id": "board_te1", "name": "Tech Gadgets", "pins": 130, "followers": 4000},
        ],
        "fitness": [
            {"id": "board_fi1", "name": "Workout Routines", "pins": 160, "followers": 5500},
        ],
        "travel": [
            {"id": "board_tr1", "name": "Travel Destinations", "pins": 220, "followers": 9000},
        ],
        "finance": [
            {"id": "board_fn1", "name": "Money Tips", "pins": 100, "followers": 3000},
        ],
        "diy": [
            {"id": "board_di1", "name": "DIY Home Projects", "pins": 140, "followers": 5000},
        ],
    }

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def map_board(self, niche: str, topic: str = "", preferred_board: str = "") -> Dict[str, Any]:
        """Map content to the best board for given niche and topic."""
        boards = self.NICHE_BOARDS.get(niche, [])

        if not boards:
            return {"id": "", "name": "", "confidence": 0.0}

        # Check preferred board
        if preferred_board:
            for b in boards:
                if b["id"] == preferred_board or b["name"] == preferred_board:
                    result = {**b, "confidence": 1.0}
                    self._mapping_log.append(result)
                    return result

        # Try topic match
        if topic:
            topic_lower = topic.lower()
            for b in boards:
                if any(w in b["name"].lower() for w in topic_lower.split()):
                    result = {**b, "confidence": 0.9}
                    self._mapping_log.append(result)
                    return result

        # Default to first board
        result = {**boards[0], "confidence": 0.7}
        self._mapping_log.append(result)
        return result

    def get_available_boards(self, niche: str) -> List[Dict[str, Any]]:
        return self.NICHE_BOARDS.get(niche, [])

    def get_boards_by_niche(self) -> Dict[str, List[Dict[str, Any]]]:
        return self.NICHE_BOARDS

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
