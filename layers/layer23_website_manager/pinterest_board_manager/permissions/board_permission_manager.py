"""BoardPermissionManager — Control who can edit, publish, or access boards."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard
from layers.layer23_website_manager.pinterest_board_manager.exceptions import BoardPermissionError


class BoardPermissionManager:
    """Granular permission control for boards."""

    PERMISSION_TYPES = ["edit", "publish", "view", "admin", "delete"]

    def __init__(self) -> None:
        self._permission_log: List[dict] = []

    def check_permission(self, board: PinterestBoard, user: str, permission: str) -> bool:
        """Check if a user has specific permission for a board."""
        if permission == "edit":
            return user in board.can_edit
        elif permission == "publish":
            return user in board.can_publish
        elif permission == "view":
            return True  # Public boards visible to all
        elif permission == "admin":
            return "owner" in (board.can_edit if user == "owner" else [])
        elif permission == "delete":
            return user in board.can_edit
        return False

    def require_permission(self, board: PinterestBoard, user: str, permission: str) -> None:
        """Raise exception if permission denied."""
        if not self.check_permission(board, user, permission):
            raise BoardPermissionError(f"User '{user}' lacks '{permission}' permission for board '{board.board_name}'")

    def grant_permission(self, board: PinterestBoard, user: str, permission: str) -> bool:
        """Grant a permission to a user."""
        target_list = []
        if permission == "edit":
            target_list = board.can_edit
        elif permission == "publish":
            target_list = board.can_publish

        if user not in target_list:
            target_list.append(user)
            self._permission_log.append({
                "board_id": board.board_id,
                "user": user,
                "permission": permission,
                "action": "grant",
                "timestamp": time.time(),
            })
            return True
        return False

    def revoke_permission(self, board: PinterestBoard, user: str, permission: str) -> bool:
        """Revoke a permission from a user."""
        target_list = []
        if permission == "edit":
            target_list = board.can_edit
        elif permission == "publish":
            target_list = board.can_publish
        elif permission == "view":
            return True

        if user in target_list:
            target_list.remove(user)
            self._permission_log.append({
                "board_id": board.board_id,
                "user": user,
                "permission": permission,
                "action": "revoke",
                "timestamp": time.time(),
            })
            return True
        return False

    def get_permissions(self, board: PinterestBoard) -> Dict[str, List[str]]:
        return {
            "can_edit": board.can_edit,
            "can_publish": board.can_publish,
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_changes": len(self._permission_log),
            "permission_types": self.PERMISSION_TYPES,
        }
