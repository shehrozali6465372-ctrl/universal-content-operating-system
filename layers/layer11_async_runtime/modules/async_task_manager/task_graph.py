"""TaskGraph — DAG for task dependencies."""
from __future__ import annotations
from typing import Any, Dict, List, Set

class TaskGraph:
    def __init__(self):
        self._adj: Dict[str, List[str]] = {}
        self._reverse: Dict[str, List[str]] = {}
    def add_edge(self, from_id: str, to_id: str) -> None:
        self._adj.setdefault(from_id, []).append(to_id)
        self._reverse.setdefault(to_id, []).append(from_id)
    def get_dependencies(self, task_id: str) -> List[str]:
        return self._reverse.get(task_id, [])
    def get_dependents(self, task_id: str) -> List[str]:
        return self._adj.get(task_id, [])
    def get_ready_tasks(self, completed: Set[str]) -> List[str]:
        ready = []
        for tid in set(list(self._adj.keys()) + list(self._reverse.keys())):
            if tid not in completed and all(d in completed for d in self.get_dependencies(tid)):
                ready.append(tid)
        return ready
    def has_cycle(self) -> bool:
        visited, stack = set(), set()
        def dfs(node):
            visited.add(node)
            stack.add(node)
            for n in self._adj.get(node, []):
                if n not in visited:
                    if dfs(n): return True
                elif n in stack: return True
            stack.discard(node)
            return False
        return any(dfs(n) for n in set(list(self._adj.keys()) + list(self._reverse.keys())) if n not in visited)
    def get_stats(self) -> Dict[str, Any]:
        return {"nodes": len(set(list(self._adj.keys()) + list(self._reverse.keys()))), "edges": sum(len(v) for v in self._adj.values())}
