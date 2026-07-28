"""BoardSEOManager — Board title optimization, description, keywords, and category."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard
from layers.layer23_website_manager.pinterest_board_manager.exceptions import SEOOptimizationError


class BoardSEOManager:
    """SEO optimization for Pinterest boards — titles, descriptions, keywords, hashtags."""

    def __init__(self) -> None:
        self._optimization_log: List[dict] = []

    def optimize_title(self, board_name: str, niche: str = "",
                        keywords: Optional[List[str]] = None, max_length: int = 100) -> str:
        """Generate an SEO-optimized board title."""
        name = board_name.strip()

        # Add niche context if missing
        if niche and niche.lower().replace(" ", "_") not in name.lower():
            name = f"{name} | {niche.title()} Inspiration"

        # Truncate
        if len(name) > max_length:
            name = name[:max_length].rsplit(" ", 1)[0]

        return name

    def optimize_description(self, description: str, keywords: Optional[List[str]] = None,
                               niche: str = "", max_length: int = 500) -> str:
        """Optimize board description with keywords."""
        desc = description.strip()

        # Append keywords naturally
        if keywords:
            kw_text = ", ".join(keywords[:5])
            if kw_text and kw_text.lower() not in desc.lower():
                desc = f"{desc}\n\nKeywords: {kw_text}"

        # Limit length
        if len(desc) > max_length:
            desc = desc[:max_length].rsplit(".", 1)[0] + "."

        return desc

    def generate_hashtags(self, keywords: Optional[List[str]] = None,
                            niche: str = "", max_tags: int = 10) -> List[str]:
        """Generate relevant hashtags from keywords and niche."""
        tags = set()

        if niche:
            niche_clean = niche.lower().replace(" ", "")
            tags.add(f"#{niche_clean}")
            tags.add(f"#{niche_clean}ideas")

        if keywords:
            for kw in keywords[:8]:
                kw_clean = kw.lower().replace(" ", "")
                if kw_clean:
                    tags.add(f"#{kw_clean}")

        return list(tags)[:max_tags]

    def optimize_keywords(self, keywords: Optional[List[str]], niche: str = "") -> List[str]:
        """Extend keyword list with niche-related terms."""
        result = list(keywords or [])

        niche_keywords = {
            "home_decor": ["home decor", "interior design", "room ideas", "furniture", "decorating"],
            "fashion": ["fashion", "style", "outfit ideas", "trendy", "wardrobe"],
            "beauty": ["beauty", "makeup", "skincare", "cosmetics", "beauty tips"],
            "food": ["food", "recipes", "cooking", "meal ideas", "healthy eating"],
            "fitness": ["fitness", "workout", "exercise", "healthy lifestyle", "wellness"],
            "travel": ["travel", "vacation", "destinations", "travel tips", "adventure"],
            "tech": ["technology", "gadgets", "innovation", "digital", "AI"],
            "finance": ["finance", "money", "investing", "saving", "wealth"],
        }

        niche_key = niche.lower().replace(" ", "_")
        if niche_key in niche_keywords:
            for kw in niche_keywords[niche_key]:
                if kw not in result:
                    result.append(kw)

        return result

    def calculate_seo_score(self, board: PinterestBoard) -> float:
        """Calculate SEO optimization score (0-100) for a board."""
        score = 100.0

        # Title checks
        if not board.board_name:
            score -= 30
        elif len(board.board_name) < 10:
            score -= 10
        elif len(board.board_name) > 100:
            score -= 5

        # Description
        if not board.board_description:
            score -= 25
        elif len(board.board_description) < 50:
            score -= 10

        # Keywords
        if not board.keywords:
            score -= 20
        elif len(board.keywords) < 3:
            score -= 10

        # Hashtags
        if not board.hashtags:
            score -= 10

        # Category
        if not board.category or board.category == "other":
            score -= 5

        board.seo_score = max(0, score)
        return board.seo_score

    def optimize_board(self, board: PinterestBoard) -> Dict[str, Any]:
        """Run full SEO optimization on a board."""
        original_name = board.board_name

        # Optimize title (stored in seo_title, leaves original board_name intact)
        board.seo_title = self.optimize_title(board.board_name, board.niche, board.keywords)

        # Optimize description
        if board.board_description:
            board.board_description = self.optimize_description(
                board.board_description, board.keywords, board.niche
            )

        # Generate hashtags
        if not board.hashtags:
            board.hashtags = self.generate_hashtags(board.keywords, board.niche)

        # Extend keywords
        board.keywords = self.optimize_keywords(board.keywords, board.niche)

        # Calculate score
        score = self.calculate_seo_score(board)

        result = {
            "original_name": original_name,
            "optimized_name": board.board_name,
            "seo_score": score,
            "keyword_count": len(board.keywords),
            "hashtag_count": len(board.hashtags),
            "optimized": True,
        }

        self._optimization_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        return {"total_optimizations": len(self._optimization_log)}
