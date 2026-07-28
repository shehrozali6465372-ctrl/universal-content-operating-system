"""BoardAnalyticsTracker — Track impressions, saves, clicks, engagement per board."""
from __future__ import annotations
import time
import random
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.board_performance import BoardPerformance
from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard


class BoardAnalyticsTracker:
    """Track and analyze board performance metrics."""

    def __init__(self) -> None:
        self._performances: Dict[str, List[BoardPerformance]] = {}
        self._tracking_log: List[dict] = []

    def record_performance(self, board_id: str, impressions: int = 0,
                            saves: int = 0, clicks: int = 0,
                            closeups: int = 0) -> BoardPerformance:
        """Record a daily performance snapshot for a board."""
        perf = BoardPerformance(
            board_id=board_id,
            impressions=impressions,
            saves=saves,
            clicks=clicks,
            closeups=closeups,
            engagement=saves + clicks + closeups,
        )

        if board_id not in self._performances:
            self._performances[board_id] = []
        self._performances[board_id].append(perf)

        self._tracking_log.append({
            "board_id": board_id,
            "impressions": impressions,
            "engagement": perf.engagement_rate,
            "timestamp": time.time(),
        })

        return perf

    def simulate_daily(self, board: PinterestBoard) -> BoardPerformance:
        """Simulate a day of performance data (for testing)."""
        impressions = random.randint(100, 10000)
        saves = random.randint(5, int(impressions * 0.15))
        clicks = random.randint(3, int(impressions * 0.08))
        closeups = random.randint(1, int(impressions * 0.05))

        # Update board totals
        board.total_impressions += impressions
        board.total_saves += saves
        board.total_clicks += clicks
        board.engagement_rate = board.total_saves / max(board.total_impressions, 1) * 100

        return self.record_performance(board.board_id, impressions, saves, clicks, closeups)

    def get_board_performance(self, board_id: str, days: int = 30) -> List[BoardPerformance]:
        """Get recent performance data for a board."""
        performances = self._performances.get(board_id, [])
        cutoff = time.time() - (days * 86400)
        return [p for p in performances if p.date >= cutoff]

    def get_aggregate(self, board_id: str, days: int = 30) -> BoardPerformance:
        """Get aggregate performance for a board over a period."""
        recent = self.get_board_performance(board_id, days)
        return BoardPerformance.aggregate(recent)

    def get_top_boards(self, boards: List[PinterestBoard], top_k: int = 5) -> List[PinterestBoard]:
        """Get top performing boards by engagement rate."""
        sorted_boards = sorted(boards, key=lambda b: b.engagement_rate, reverse=True)
        return sorted_boards[:top_k]

    def get_stats(self) -> Dict[str, Any]:
        return {
            "tracked_boards": len(self._performances),
            "total_records": sum(len(p) for p in self._performances.values()),
            "tracking_events": len(self._tracking_log),
        }
