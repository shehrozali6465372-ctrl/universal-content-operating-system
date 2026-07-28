"""BoardNode — Hierarchical board tree structure."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class BoardNode:
    """A node in the board hierarchy tree."""

    board_id: str
    board_name: str
    niche: str = ""
    children: List["BoardNode"] = field(default_factory=list)
    parent_id: Optional[str] = None
    depth: int = 0
    pin_count: int = 0
    is_active: bool = True

    def add_child(self, child: "BoardNode") -> None:
        child.parent_id = self.board_id
        child.depth = self.depth + 1
        self.children.append(child)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "board_id": self.board_id,
            "board_name": self.board_name,
            "niche": self.niche,
            "depth": self.depth,
            "pin_count": self.pin_count,
            "is_active": self.is_active,
            "children": [c.to_dict() for c in self.children],
        }

    def total_pins_recursive(self) -> int:
        return self.pin_count + sum(c.total_pins_recursive() for c in self.children)

    def flatten(self) -> List["BoardNode"]:
        """Flatten tree to list."""
        result = [self]
        for child in self.children:
            result.extend(child.flatten())
        return result
