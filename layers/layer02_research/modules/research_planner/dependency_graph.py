"""
Dependency Graph
Layer 2: Research Engine — Module 9

Manages task dependencies:
- Topological sort
- Cycle detection
- Dependency resolution
- Critical path calculation
"""

from collections import defaultdict, deque
from typing import Dict, List, Optional, Set


class DependencyGraph:
    """Directed acyclic graph for task dependencies."""

    def __init__(self):
        self._adjacency: Dict[str, List[str]] = defaultdict(list)
        self._reverse: Dict[str, List[str]] = defaultdict(list)
        self._nodes: Set[str] = set()

    def add_node(self, node_id: str):
        self._nodes.add(node_id)

    def add_edge(self, from_id: str, to_id: str):
        """Add dependency: from_id must complete before to_id."""
        self._nodes.add(from_id)
        self._nodes.add(to_id)
        self._adjacency[from_id].append(to_id)
        self._reverse[to_id].append(from_id)

    def remove_node(self, node_id: str):
        self._nodes.discard(node_id)
        self._adjacency.pop(node_id, None)
        self._reverse.pop(node_id, None)
        for k in list(self._adjacency.keys()):
            self._adjacency[k] = [n for n in self._adjacency[k] if n != node_id]
        for k in list(self._reverse.keys()):
            self._reverse[k] = [n for n in self._reverse[k] if n != node_id]

    def has_cycle(self) -> bool:
        """Detect if the graph has a cycle."""
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.discard(node)
            return False

        for node in self._nodes:
            if node not in visited:
                if dfs(node):
                    return True
        return False

    def topological_sort(self) -> Optional[List[str]]:
        """Topological sort. Returns None if cycle exists."""
        if self.has_cycle():
            return None

        in_degree = {n: 0 for n in self._nodes}
        for node in self._nodes:
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] = in_degree.get(neighbor, 0) + 1

        queue = deque([n for n, d in in_degree.items() if d == 0])
        result = []

        while queue:
            node = queue.popleft()
            result.append(node)
            for neighbor in self._adjacency.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return result if len(result) == len(self._nodes) else None

    def get_ready_nodes(self, completed: Set[str]) -> List[str]:
        """Get nodes whose dependencies are all completed."""
        ready = []
        for node in self._nodes:
            if node in completed:
                continue
            deps = self._reverse.get(node, [])
            if all(d in completed for d in deps):
                ready.append(node)
        return ready

    def get_dependents(self, node_id: str) -> List[str]:
        """Get nodes that depend on this node."""
        return list(self._adjacency.get(node_id, []))

    def get_dependencies(self, node_id: str) -> List[str]:
        """Get nodes this node depends on."""
        return list(self._reverse.get(node_id, []))

    def depth(self, node_id: str) -> int:
        """Get the depth (longest path from root) of a node."""
        deps = self._reverse.get(node_id, [])
        if not deps:
            return 0
        return 1 + max(self.depth(d) for d in deps)

    def size(self) -> int:
        return len(self._nodes)
