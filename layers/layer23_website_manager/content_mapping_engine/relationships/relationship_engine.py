"""RelationshipEngine — Build content relationships: related articles, pins, boards."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import RelationshipError


# Related content registry (simulated)
RELATED_CONTENT: Dict[str, Dict[str, Any]] = {
    "small_bedroom": {
        "article_ids": ["art_bedroom_1", "art_bedroom_2", "art_bedroom_3"],
        "pin_ids": ["pin_bed_1", "pin_bed_2", "pin_bed_3", "pin_bed_4"],
        "board_ids": ["board_home_bedroom", "board_home_small_spaces"],
    },
    "kitchen_remodel": {
        "article_ids": ["art_kitchen_1", "art_kitchen_2", "art_kitchen_4"],
        "pin_ids": ["pin_kitchen_1", "pin_kitchen_2", "pin_kitchen_3"],
        "board_ids": ["board_home_kitchen", "board_home_renovation"],
    },
    "skincare_routine": {
        "article_ids": ["art_skin_1", "art_skin_2"],
        "pin_ids": ["pin_skin_1", "pin_skin_2", "pin_skin_3"],
        "board_ids": ["board_beauty_skin", "board_beauty_tips"],
    },
}


class RelationshipEngine:
    """Build content relationships for cross-linking and discovery."""

    def __init__(self) -> None:
        self._relationship_log: List[dict] = []
        self._total_built = 0

    def build_relationships(self, topic: str, niche: str = "",
                              keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Find related articles, pins, and boards for this content."""
        # Find relationship set by keyword matching
        rel_key = self._find_relationship_key(topic, keywords or [])
        related = RELATED_CONTENT.get(rel_key)

        if not related:
            # Generate empty relationships
            related = {"article_ids": [], "pin_ids": [], "board_ids": []}

        result = {
            "related_article_ids": related.get("article_ids", []),
            "related_pin_ids": related.get("pin_ids", []),
            "related_board_ids": related.get("board_ids", []),
            "relationship_count": (
                len(related.get("article_ids", [])) +
                len(related.get("pin_ids", [])) +
                len(related.get("board_ids", []))
            ),
        }

        self._relationship_log.append(result)
        self._total_built += 1
        return result

    def _find_relationship_key(self, topic: str, keywords: List[str]) -> str:
        """Find best matching relationship key from topic/keywords."""
        text = f"{topic} {' '.join(keywords)}".lower()

        for key in RELATED_CONTENT:
            if key.replace("_", " ") in text or key in text:
                return key

        # Partial match
        words = set(text.split())
        best_key = None
        best_score = 0
        for key in RELATED_CONTENT:
            key_words = set(key.split("_"))
            overlap = len(words & key_words)
            if overlap > best_score:
                best_score = overlap
                best_key = key

        return best_key or "small_bedroom"

    def get_stats(self) -> Dict[str, Any]:
        return {"total_relationships": self._total_built}
