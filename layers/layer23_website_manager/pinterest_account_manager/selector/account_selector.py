"""AccountSelector — AI-powered Pinterest account selection by niche/topic.

Matches content topics to the best Pinterest Business Account based on:
- Niche alignment (primary)
- Health status
- Brand consistency
- Posting frequency
- Historical performance
"""
from __future__ import annotations
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.exceptions import SelectionError


class AccountSelector:
    """AI-powered account selection — matches topic to best Pinterest account."""

    # Predefined niche-to-account mappings for AI matching
    NICHE_KEYWORDS: Dict[str, List[str]] = {
        "home_decor": ["home", "decor", "interior", "furniture", "diy", "renovation", "living room", "bedroom"],
        "fashion": ["fashion", "style", "outfit", "clothing", "accessories", "trendy", "wardrobe"],
        "beauty": ["beauty", "makeup", "skincare", "cosmetics", "nail", "hair", "glam"],
        "food": ["recipe", "cooking", "food", "baking", "kitchen", "delicious", "meal prep"],
        "fitness": ["fitness", "workout", "exercise", "gym", "yoga", "health", "weight loss"],
        "travel": ["travel", "vacation", "destination", "wanderlust", "adventure", "trip", "explore"],
        "tech": ["tech", "technology", "ai", "software", "gadget", "digital", "programming"],
        "finance": ["finance", "money", "invest", "saving", "budget", "wealth", "passive income"],
        "education": ["education", "learning", "study", "course", "skill", "knowledge", "academic"],
        "health": ["wellness", "health", "mental health", "self care", "mindfulness", "meditation"],
    }

    def __init__(self) -> None:
        self._selection_log: List[dict] = []
        self._total_selections = 0

    def select(self, topic: str, accounts: List[PinterestAccount],
                niche: str = "", prefer_healthy: bool = True) -> PinterestAccount:
        """Select the best Pinterest account for a given topic.

        Args:
            topic: Content topic (e.g., "Modern Home Office Design")
            accounts: Available Pinterest accounts
            niche: Preferred niche (optional)
            prefer_healthy: Only consider healthy accounts

        Returns:
            Best matching PinterestAccount

        Raises:
            SelectionError: If no suitable account found
        """
        # Filter healthy accounts
        candidates = [a for a in accounts if a.status == AccountStatus.ACTIVE]
        if prefer_healthy:
            candidates = [a for a in candidates if a.is_healthy]

        if not candidates:
            raise SelectionError("No suitable Pinterest account available")

        # Score each candidate
        scored: List[Tuple[float, PinterestAccount]] = []
        topic_lower = topic.lower()

        for acc in candidates:
            score = 0.0

            # Niche match (0-50 points)
            niche_scores = self._score_niche_match(topic_lower, acc.niche)
            score += niche_scores * 50

            # Explicit niche preference (bonus 20)
            if niche and acc.niche.lower() == niche.lower():
                score += 20

            # Health bonus
            score += acc.health_score / 10  # Up to 10 points

            # Brand consistency bonus
            if acc.brand_consistency_score > 0:
                score += acc.brand_consistency_score / 10  # Up to 10 points

            # Engagement bonus
            score += min(acc.engagement_rate / 2, 5)

            # Random factor (0-5) for variety
            score += random.uniform(0, 5)

            scored.append((score, acc))

        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1]

        self._selection_log.append({
            "topic": topic,
            "selected": best.account_name or best.username,
            "niche": best.niche,
            "score": round(scored[0][0], 1),
            "timestamp": time.time(),
        })
        self._total_selections += 1

        return best

    def select_multi(self, topics: List[str], accounts: List[PinterestAccount],
                      prefer_healthy: bool = True) -> Dict[str, PinterestAccount]:
        """Select accounts for multiple topics."""
        result: Dict[str, PinterestAccount] = {}
        used_ids: set = set()

        for topic in topics:
            # Prefer unused accounts for variety
            available = [a for a in accounts if a.account_id not in used_ids]
            if not available:
                available = accounts

            try:
                selected = self.select(topic, available, prefer_healthy=prefer_healthy)
                result[topic] = selected
                used_ids.add(selected.account_id)
            except SelectionError:
                # Fallback to any healthy account
                healthy = [a for a in accounts if a.is_healthy and a.status == AccountStatus.ACTIVE]
                if healthy:
                    result[topic] = healthy[0]
                    used_ids.add(healthy[0].account_id)

        return result

    def _score_niche_match(self, topic: str, account_niche: str) -> float:
        """Score how well a topic matches an account's niche (0.0-1.0)."""
        niche_key = account_niche.lower().replace(" ", "_")
        keywords = self.NICHE_KEYWORDS.get(niche_key, [])

        if not keywords:
            return 0.3  # Default match for unknown niches

        matches = sum(1 for kw in keywords if kw in topic)
        max_possible = min(len(keywords), 5)
        return min(matches / max_possible, 1.0)

    def get_selection_history(self, limit: int = 20) -> List[dict]:
        return self._selection_log[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_selections": self._total_selections,
            "recent_selections": self._selection_log[-5:] if self._selection_log else [],
        }
