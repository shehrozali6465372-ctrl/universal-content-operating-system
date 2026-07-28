"""BoardHierarchyManager — Main boards, sub-boards, hierarchy tree management."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.pinterest_board_manager.models.pinterest_board import PinterestBoard
from layers.layer23_website_manager.pinterest_board_manager.models.board_hierarchy import BoardNode


class BoardHierarchyManager:
    """Manage board hierarchy — parent/child relationships, tree structure."""

    def __init__(self) -> None:
        self._hierarchy_log: List[dict] = []

    def build_tree(self, boards: List[PinterestBoard], root_niche: str = "") -> List[BoardNode]:
        """Build a hierarchical tree from a flat list of boards."""
        board_map = {b.board_id: b for b in boards}
        children_map: Dict[str, List[PinterestBoard]] = {}

        # Group children by parent
        for b in boards:
            pid = b.parent_board_id or "root"
            if pid not in children_map:
                children_map[pid] = []
            children_map[pid].append(b)

        # Find roots (no parent or parent not in list)
        root_boards = [b for b in boards if not b.parent_board_id or b.parent_board_id not in board_map]
        if root_niche:
            root_boards = [b for b in root_boards if b.niche == root_niche]

        # Build tree recursively
        trees = []
        for root in sorted(root_boards, key=lambda b: b.sort_order):
            node = self._build_node(root, children_map)
            trees.append(node)

        return trees

    def _build_node(self, board: PinterestBoard, children_map: Dict[str, List]) -> BoardNode:
        """Recursively build a tree node."""
        node = BoardNode(
            board_id=board.board_id,
            board_name=board.board_name,
            niche=board.niche,
            parent_id=board.parent_board_id,
            depth=board.board_depth,
            pin_count=board.pin_count,
            is_active=board.is_active,
        )

        children = children_map.get(board.board_id, [])
        for child in sorted(children, key=lambda b: b.sort_order):
            child_node = self._build_node(child, children_map)
            node.add_child(child_node)

        return node

    def set_parent(self, board: PinterestBoard, parent_board: Optional[PinterestBoard]) -> bool:
        """Set or remove a parent board."""
        board.parent_board_id = parent_board.board_id if parent_board else None
        board.board_depth = (parent_board.board_depth + 1) if parent_board else 0

        self._hierarchy_log.append({
            "board_id": board.board_id,
            "new_parent": parent_board.board_name if parent_board else None,
        })
        return True

    def get_children(self, board_id: str, boards: List[PinterestBoard]) -> List[PinterestBoard]:
        """Get all direct children of a board."""
        return [b for b in boards if b.parent_board_id == board_id]

    def get_descendants(self, board_id: str, boards: List[PinterestBoard]) -> List[PinterestBoard]:
        """Get all descendants (children + grandchildren) of a board."""
        result = []
        children = self.get_children(board_id, boards)
        for child in children:
            result.append(child)
            result.extend(self.get_descendants(child.board_id, boards))
        return result

    def get_siblings(self, board: PinterestBoard, boards: List[PinterestBoard]) -> List[PinterestBoard]:
        """Get all sibling boards (same parent)."""
        return [b for b in boards if b.parent_board_id == board.parent_board_id and b.board_id != board.board_id]

    def flatten_tree(self, trees: List[BoardNode]) -> List[BoardNode]:
        """Flatten tree(s) to a single sorted list."""
        nodes = []
        for tree in trees:
            nodes.extend(tree.flatten())
        return nodes

    def get_stats(self) -> Dict[str, Any]:
        return {"hierarchy_changes": len(self._hierarchy_log)}
