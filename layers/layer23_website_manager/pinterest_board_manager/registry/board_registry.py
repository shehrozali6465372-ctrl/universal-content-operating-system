"""BoardRegistry — CRUD for Pinterest boards across all accounts."""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import (
    PinterestBoard, BoardStatus,
)
from layers.layer23_website_manager.pinterest_board_manager.exceptions import (
    BoardNotFoundError, DuplicateBoardError, BoardLimitError, InvalidBoardNameError,
)


class BoardRegistry:
    """Register, update, delete, archive, restore boards with multi-account support."""

    def __init__(self, max_boards_per_account: int = 50) -> None:
        self._boards: Dict[str, PinterestBoard] = {}
        self._lock = threading.Lock()
        self._max_boards_per_account = max_boards_per_account
        self._total_created = 0

    def create(self, account_id: str, board_name: str,
                description: str = "", niche: str = "", category: str = "other",
                keywords: Optional[List[str]] = None,
                parent_board_id: Optional[str] = None) -> PinterestBoard:
        """Create a new board under an account."""
        if not board_name or not board_name.strip():
            raise InvalidBoardNameError("Board name cannot be empty")

        # Check duplicate (compare against original board_name and seo_title)
        for board in self._boards.values():
            if board.account_id == account_id:
                if board.board_name.lower() == board_name.lower():
                    raise DuplicateBoardError(f"Board '{board_name}' already exists for this account")
                if board.seo_title and board.seo_title.lower() == board_name.lower():
                    raise DuplicateBoardError(f"Board '{board_name}' already exists (seo_title) for this account")

        # Check limit
        account_boards = [b for b in self._boards.values() if b.account_id == account_id]
        if len(account_boards) >= self._max_boards_per_account:
            raise BoardLimitError(f"Account board limit reached: {self._max_boards_per_account}")

        board = PinterestBoard(
            account_id=account_id,
            board_name=board_name,
            board_description=description,
            niche=niche or self._detect_niche(board_name),
            category=category,
            keywords=keywords or [],
            parent_board_id=parent_board_id,
            status=BoardStatus.ACTIVE,
        )

        # Set depth based on parent
        if parent_board_id:
            parent = self._boards.get(parent_board_id)
            if parent:
                board.board_depth = parent.board_depth + 1

        with self._lock:
            self._boards[board.board_id] = board
            self._total_created += 1

        return board

    def get(self, board_id: str) -> Optional[PinterestBoard]:
        return self._boards.get(board_id)

    def get_by_name(self, account_id: str, board_name: str) -> Optional[PinterestBoard]:
        for board in self._boards.values():
            if board.account_id == account_id and board.board_name.lower() == board_name.lower():
                return board
        return None

    def update(self, board_id: str, **kwargs) -> Optional[PinterestBoard]:
        board = self._boards.get(board_id)
        if not board:
            return None

        allowed = {"board_name", "board_description", "niche", "category",
                    "keywords", "search_terms", "hashtags", "seo_title",
                    "seo_description", "parent_board_id", "sort_order",
                    "can_edit", "can_publish"}

        with self._lock:
            for key, value in kwargs.items():
                if key in allowed:
                    setattr(board, key, value)
            board.updated_at = time.time()

        return board

    def delete(self, board_id: str) -> bool:
        with self._lock:
            return self._boards.pop(board_id, None) is not None

    def archive(self, board_id: str) -> bool:
        board = self._boards.get(board_id)
        if not board:
            return False
        with self._lock:
            board.status = BoardStatus.ARCHIVED
            board.is_archived = True
            board.updated_at = time.time()
        return True

    def restore(self, board_id: str) -> bool:
        board = self._boards.get(board_id)
        if not board:
            return False
        with self._lock:
            board.status = BoardStatus.ACTIVE
            board.is_archived = False
            board.updated_at = time.time()
        return True

    def get_by_account(self, account_id: str, include_archived: bool = False) -> List[PinterestBoard]:
        boards = [b for b in self._boards.values() if b.account_id == account_id]
        if not include_archived:
            boards = [b for b in boards if not b.is_archived]
        return sorted(boards, key=lambda b: (b.board_depth, b.sort_order, b.board_name))

    def get_by_niche(self, niche: str) -> List[PinterestBoard]:
        return [b for b in self._boards.values() if b.niche.lower() == niche.lower() and not b.is_archived]

    def get_all(self, status: Optional[BoardStatus] = None) -> List[PinterestBoard]:
        boards = list(self._boards.values())
        if status:
            boards = [b for b in boards if b.status == status]
        return sorted(boards, key=lambda b: b.created_at, reverse=True)

    def count_by_account(self, account_id: str) -> int:
        return sum(1 for b in self._boards.values() if b.account_id == account_id)

    def get_stats(self) -> Dict[str, Any]:
        by_status: Dict[str, int] = {}
        by_niche: Dict[str, int] = {}
        total_pins = 0

        for b in self._boards.values():
            by_status[b.status.value] = by_status.get(b.status.value, 0) + 1
            by_niche[b.niche or "uncategorized"] = by_niche.get(b.niche or "uncategorized", 0) + 1
            total_pins += b.pin_count

        return {
            "total_boards": len(self._boards),
            "max_per_account": self._max_boards_per_account,
            "by_status": by_status,
            "by_niche": by_niche,
            "total_pins": total_pins,
            "total_created": self._total_created,
            "empty_boards": sum(1 for b in self._boards.values() if b.is_empty),
        }

    @staticmethod
    def _detect_niche(board_name: str) -> str:
        """Detect niche from board name using keywords."""
        niche_keywords = {
            "home decor": ["home", "decor", "interior", "furniture", "room", "kitchen", "bedroom", "bathroom", "living"],
            "fashion": ["fashion", "style", "outfit", "clothing", "wardrobe", "accessory"],
            "beauty": ["beauty", "makeup", "skincare", "cosmetic", "hair", "nail", "glam"],
            "food": ["food", "recipe", "cooking", "baking", "kitchen", "delicious", "meal"],
            "fitness": ["fitness", "workout", "exercise", "gym", "yoga", "health", "wellness"],
            "travel": ["travel", "vacation", "destination", "trip", "adventure", "wanderlust"],
            "tech": ["tech", "technology", "ai", "gadget", "software", "digital"],
            "finance": ["finance", "money", "invest", "saving", "budget", "wealth"],
            "education": ["education", "learning", "study", "course", "skill", "knowledge"],
            "DIY": ["diy", "craft", "homemade", "tutorial", "how to"],
        }

        name_lower = board_name.lower()
        for niche, keywords in niche_keywords.items():
            if any(kw in name_lower for kw in keywords):
                return niche
        return "other"
