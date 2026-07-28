"""BoardHealthChecker — Check board health: empty, duplicates, low perf, missing SEO."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard, BoardStatus


class BoardHealthChecker:
    """Monitor board health — empty boards, duplicates, low performance, missing descriptions."""

    def __init__(self) -> None:
        self._check_log: List[dict] = []

    def check_board(self, board: PinterestBoard, all_boards: Optional[List[PinterestBoard]] = None) -> Dict[str, Any]:
        """Check health of a single board. Returns issues and score."""
        issues: List[str] = []

        # Empty check
        if board.is_empty:
            issues.append("Board has no pins")

        # Name check
        if not board.board_name or len(board.board_name.strip()) < 3:
            issues.append("Board name is too short or missing")

        # Description check
        if not board.board_description:
            issues.append("Missing board description")
        elif len(board.board_description) < 50:
            issues.append("Board description too short")

        # SEO check
        if not board.keywords:
            issues.append("No keywords set")
        if not board.hashtags:
            issues.append("No hashtags set")
        if board.seo_score < 50:
            issues.append(f"Low SEO score ({board.seo_score})")

        # Category check
        if not board.category or board.category == "other":
            issues.append("Category not set or default")

        # Duplicate check
        if all_boards:
            for other in all_boards:
                if other.board_id != board.board_id and other.account_id == board.account_id:
                    if other.board_name.lower() == board.board_name.lower():
                        issues.append(f"Duplicate board name: '{board.board_name}'")
                        break

        # Performance check
        if board.total_impressions > 100 and board.engagement_rate < 0.5:
            issues.append(f"Low engagement rate: {board.engagement_rate:.2f}%")

        # Score calculation
        score = 100.0
        penalties = {
            "Board has no pins": 20,
            "Board name is too short or missing": 25,
            "Missing board description": 20,
            "Board description too short": 10,
            "No keywords set": 15,
            "No hashtags set": 10,
            "Low SEO score": 10,
            "Category not set or default": 5,
            "Duplicate board name": 30,
            "Low engagement rate": 15,
        }

        for issue in issues:
            score -= penalties.get(issue, 10)
        score = max(0, min(100, score))

        result = {
            "board_id": board.board_id,
            "board_name": board.board_name,
            "health_score": round(score, 1),
            "status": "healthy" if score >= 70 else "degraded" if score >= 40 else "critical",
            "issues": issues,
            "issue_count": len(issues),
            "checked_at": time.time(),
        }

        self._check_log.append(result)
        return result

    def check_all(self, boards: List[PinterestBoard]) -> Dict[str, Any]:
        """Check health of all boards."""
        results = [self.check_board(b, boards) for b in boards]

        healthy = sum(1 for r in results if r["health_score"] >= 70)
        degraded = sum(1 for r in results if 40 <= r["health_score"] < 70)
        critical = sum(1 for r in results if r["health_score"] < 40)

        return {
            "total_checked": len(results),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "overall_score": round(sum(r["health_score"] for r in results) / max(len(results), 1), 1),
            "all_issues": sum(r["issue_count"] for r in results),
            "checks": results[:50],
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_checks": len(self._check_log),
            "last_check": self._check_log[-1]["checked_at"] if self._check_log else 0,
        }
