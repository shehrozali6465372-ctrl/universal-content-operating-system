"""BoardMappingEngine — Maps articles/topics to the correct Pinterest Account + Board."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard
from layers.layer23_website_manager.pinterest_board_manager.exceptions import BoardMappingError


class BoardMappingEngine:
    """AI-powered mapping: Topic → Account → Board."""

    def __init__(self) -> None:
        self._mapping_log: List[dict] = []

    def find_best_board(self, topic: str, niche: str,
                         boards: List[PinterestBoard]) -> Optional[PinterestBoard]:
        """Find the best board for a given topic using keyword matching."""
        if not boards:
            return None

        topic_lower = topic.lower()
        scored: List[Tuple[float, PinterestBoard]] = []

        for board in boards:
            score = 0.0
            has_text_match = False

            # Name match (highest weight)
            if board.board_name and board.board_name.lower() in topic_lower:
                score += 30
                has_text_match = True
            if topic_lower in (board.board_name or "").lower():
                score += 25
                has_text_match = True

            # Keyword match
            for kw in (board.keywords or []):
                if kw.lower() in topic_lower:
                    score += 10
                    has_text_match = True
                if topic_lower in kw.lower():
                    score += 8
                    has_text_match = True

            # Niche match bonus
            if board.niche and board.niche.lower().replace(" ", "_") == niche.lower().replace(" ", "_"):
                score += 20
                has_text_match = True

            # Only apply bonuses if there's at least some content match
            if has_text_match:
                score += board.seo_score / 10
                if not board.is_empty:
                    score += 5

            scored.append((score, board))

        scored.sort(key=lambda x: x[0], reverse=True)

        if scored and scored[0][0] > 0:
            best = scored[0][1]
            self._mapping_log.append({
                "topic": topic,
                "niche": niche,
                "board_id": best.board_id,
                "board_name": best.board_name,
                "score": round(scored[0][0], 1),
                "timestamp": time.time(),
            })
            return best

        # Fallback: only if niche matches exactly
        if niche:
            fallback = [b for b in boards if b.niche == niche and b.is_active]
            if fallback:
                return fallback[0]
        return None

    def map_article_to_board(self, article_title: str, article_tags: List[str],
                               niche: str, boards: List[PinterestBoard]) -> Dict[str, Any]:
        """Map a full article to the best board."""
        best = self.find_best_board(article_title, niche, boards)

        if not best:
            raise BoardMappingError(f"No suitable board found for topic: {article_title}")

        return {
            "board_id": best.board_id,
            "board_name": best.board_name,
            "account_id": best.account_id,
            "niche": best.niche,
            "mapping_score": self._last_score,
            "matched": True,
        }

    @property
    def _last_score(self) -> float:
        return self._mapping_log[-1]["score"] if self._mapping_log else 0.0

    def get_stats(self) -> Dict[str, Any]:
        return {"total_mappings": len(self._mapping_log)}
