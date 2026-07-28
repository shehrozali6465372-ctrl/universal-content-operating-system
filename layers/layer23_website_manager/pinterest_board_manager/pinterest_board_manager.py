"""PinterestBoardManager — Layer 23 / Module 3.

Complete Pinterest Board lifecycle management:
- Board Registry, AI Creation, SEO, Niche Mapping
- Hierarchy, Analytics, Health, Recommendations, Permissions
- Multi-account support (10 default, 61+ scalable)

Version: 1.0.0
"""
from __future__ import annotations
import time
import os
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import (
    PinterestBoard, BoardStatus,
)
from layers.layer23_website_manager.pinterest_board_manager.models.board_hierarchy import BoardNode
from layers.layer23_website_manager.pinterest_board_manager.registry.board_registry import BoardRegistry
from layers.layer23_website_manager.pinterest_board_manager.creation.board_creator import BoardCreator
from layers.layer23_website_manager.pinterest_board_manager.seo.board_seo_manager import BoardSEOManager
from layers.layer23_website_manager.pinterest_board_manager.mapping.board_mapping_engine import BoardMappingEngine
from layers.layer23_website_manager.pinterest_board_manager.hierarchy.board_hierarchy_manager import BoardHierarchyManager
from layers.layer23_website_manager.pinterest_board_manager.analytics.board_analytics import BoardAnalyticsTracker
from layers.layer23_website_manager.pinterest_board_manager.health.board_health import BoardHealthChecker
from layers.layer23_website_manager.pinterest_board_manager.recommendation.board_recommendation import BoardRecommendationEngine
from layers.layer23_website_manager.pinterest_board_manager.permissions.board_permission_manager import BoardPermissionManager
from layers.layer23_website_manager.pinterest_board_manager.exceptions import (
    BoardNotFoundError, DuplicateBoardError, BoardLimitError,
)


class PinterestBoardManager:
    """Primary facade for Pinterest Board Management.

    Coordinates: registry, creation, SEO, mapping, hierarchy,
    analytics, health, recommendations, and permissions.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.registry = BoardRegistry(max_boards_per_account=50)
        self.creator = BoardCreator()
        self.seo = BoardSEOManager()
        self.mapping = BoardMappingEngine()
        self.hierarchy = BoardHierarchyManager()
        self.analytics = BoardAnalyticsTracker()
        self.health = BoardHealthChecker()
        self.recommendation = BoardRecommendationEngine()
        self.permissions = BoardPermissionManager()

        # Stats
        self._total_operations = 0

    # ─── Board CRUD ───────────────────────────────────────

    def create_board(self, account_id: str, board_name: str,
                      description: str = "", niche: str = "", category: str = "other",
                      keywords: Optional[List[str]] = None,
                      parent_board_id: Optional[str] = None,
                      ai_generated: bool = False) -> PinterestBoard:
        """Create a new board."""
        board = self.registry.create(
            account_id=account_id,
            board_name=board_name,
            description=description,
            niche=niche,
            category=category,
            keywords=keywords,
            parent_board_id=parent_board_id,
        )
        if ai_generated:
            board.is_ai_created = True

        # Auto-SEO
        self.seo.optimize_board(board)

        self._log("create_board", {"account_id": account_id, "board_name": board_name})
        return board

    def create_board_ai(self, account_id: str, keyword: str,
                         niche: str = "", category: str = "other") -> PinterestBoard:
        """AI-powered board creation — auto names, describes, and optimizes."""
        suggestion = self.creator.create_board_suggestion(keyword, niche, category)
        return self.create_board(
            account_id=account_id,
            board_name=suggestion["board_name"],
            description=suggestion["description"],
            niche=suggestion["niche"],
            category=category,
            keywords=suggestion["keywords"],
            ai_generated=True,
        )

    def get_board(self, board_id: str) -> Optional[PinterestBoard]:
        return self.registry.get(board_id)

    def update_board(self, board_id: str, **kwargs) -> Optional[PinterestBoard]:
        result = self.registry.update(board_id, **kwargs)
        if result:
            self._log("update_board", {"board_id": board_id})
        return result

    def delete_board(self, board_id: str) -> bool:
        result = self.registry.delete(board_id)
        if result:
            self._log("delete_board", {"board_id": board_id})
        return result

    def archive_board(self, board_id: str) -> bool:
        return self.registry.archive(board_id)

    def restore_board(self, board_id: str) -> bool:
        return self.registry.restore(board_id)

    # ─── Account Links ────────────────────────────────────

    def get_boards_for_account(self, account_id: str) -> List[PinterestBoard]:
        return self.registry.get_by_account(account_id)

    def get_boards_by_niche(self, niche: str) -> List[PinterestBoard]:
        return self.registry.get_by_niche(niche)

    def get_all_boards(self) -> List[PinterestBoard]:
        return self.registry.get_all()

    # ─── SEO ──────────────────────────────────────────────

    def optimize_board_seo(self, board_id: str) -> Optional[Dict[str, Any]]:
        board = self.registry.get(board_id)
        if not board:
            return None
        return self.seo.optimize_board(board)

    def recalculate_seo_scores(self, account_id: str = "") -> int:
        """Recalculate SEO scores for all boards (or one account)."""
        boards = self.registry.get_by_account(account_id) if account_id else self.registry.get_all()
        count = 0
        for board in boards:
            self.seo.calculate_seo_score(board)
            count += 1
        return count

    # ─── Mapping ──────────────────────────────────────────

    def map_topic_to_board(self, topic: str, niche: str,
                            account_ids: Optional[List[str]] = None) -> Optional[PinterestBoard]:
        """Find the best board for a topic across accounts."""
        if account_ids:
            boards = []
            for aid in account_ids:
                boards.extend(self.registry.get_by_account(aid))
        else:
            boards = self.registry.get_all(status=BoardStatus.ACTIVE)
        return self.mapping.find_best_board(topic, niche, boards)

    # ─── Hierarchy ────────────────────────────────────────

    def get_board_tree(self, account_id: str) -> List[BoardNode]:
        boards = self.registry.get_by_account(account_id)
        return self.hierarchy.build_tree(boards)

    def set_board_parent(self, board_id: str, parent_board_id: Optional[str]) -> bool:
        board = self.registry.get(board_id)
        parent = self.registry.get(parent_board_id) if parent_board_id else None
        return self.hierarchy.set_parent(board, parent)

    # ─── Analytics ────────────────────────────────────────

    def record_performance(self, board_id: str, impressions: int = 0,
                            saves: int = 0, clicks: int = 0) -> dict:
        perf = self.analytics.record_performance(board_id, impressions, saves, clicks)
        # Update board totals
        board = self.registry.get(board_id)
        if board:
            board.total_impressions += impressions
            board.total_saves += saves
            board.total_clicks += clicks
        return perf.to_dict()

    def simulate_daily_performance(self, board_id: str) -> dict:
        board = self.registry.get(board_id)
        if not board:
            return {}
        perf = self.analytics.simulate_daily(board)
        return perf.to_dict()

    def get_top_boards(self, account_id: str, top_k: int = 5) -> List[PinterestBoard]:
        boards = self.registry.get_by_account(account_id)
        return self.analytics.get_top_boards(boards, top_k)

    # ─── Health ───────────────────────────────────────────

    def check_board_health(self, board_id: str) -> Dict[str, Any]:
        board = self.registry.get(board_id)
        if not board:
            return {"error": "Board not found"}
        all_boards = self.registry.get_all()
        return self.health.check_board(board, all_boards)

    def check_all_health(self, account_id: str = "") -> Dict[str, Any]:
        boards = self.registry.get_by_account(account_id) if account_id else self.registry.get_all()
        return self.health.check_all(boards)

    # ─── Recommendations ──────────────────────────────────

    def recommend_new_boards(self, niche: str, account_id: str = "") -> List[Dict[str, Any]]:
        existing = self.registry.get_by_niche(niche) if not account_id else self.registry.get_by_account(account_id)
        return self.recommendation.recommend_boards(niche, existing)

    def detect_board_gaps(self, niche: str, account_id: str = "") -> List[Dict[str, Any]]:
        existing = self.registry.get_by_niche(niche) if not account_id else self.registry.get_by_account(account_id)
        return self.recommendation.detect_gaps(niche, existing)

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive Pinterest Board Manager status."""
        registry_stats = self.registry.get_stats()
        health_report = self.check_all_health()

        return {
            "module": "Pinterest Board Manager (Layer 23 / Module 3)",
            "version": "1.0.0",
            "overall": "Healthy" if health_report["overall_score"] >= 70 else "Degraded",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "boards": registry_stats,
            "health": {
                "overall_score": health_report["overall_score"],
                "healthy": health_report["healthy"],
                "degraded": health_report["degraded"],
                "critical": health_report["critical"],
                "issues": health_report["all_issues"],
            },
            "seo": self.seo.get_stats(),
            "analytics": self.analytics.get_stats(),
            "mapping": self.mapping.get_stats(),
            "recommendations": self.recommendation.get_stats(),
            "permissions": self.permissions.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1


# ─── Singleton ───────────────────────────────────────────────────────────────

_board_manager_instance: Optional[PinterestBoardManager] = None
_instance_lock = threading.Lock()


def get_board_manager() -> PinterestBoardManager:
    global _board_manager_instance
    if _board_manager_instance is None:
        with _instance_lock:
            if _board_manager_instance is None:
                _board_manager_instance = PinterestBoardManager()
    return _board_manager_instance
