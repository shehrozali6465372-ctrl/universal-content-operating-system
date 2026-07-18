"""TaskPriority — Priority levels for tasks."""
from __future__ import annotations
CRITICAL=0; HIGH=1; NORMAL=2; LOW=3; BACKGROUND=4
class Priority:
    def __init__(self, level: int=2): self.level = level
    def __lt__(self, other): return self.level < other.level
    def __repr__(self): return f"Priority({self.level})"
