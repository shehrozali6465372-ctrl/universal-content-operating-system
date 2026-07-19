"""DependencyGraph — tracks and resolves inter-layer dependencies."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Set
from collections import deque


class DependencyNode:
    __slots__ = ("node_id", "dependencies", "dependents", "metadata")

    def __init__(self, node_id: str) -> None:
        self.node_id = node_id
        self.dependencies: Set[str] = set()
        self.dependents: Set[str] = set()
        self.metadata: Dict[str, Any] = {}

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "dependencies": sorted(self.dependencies),
                "dependents": sorted(self.dependents)}


class DependencyGraph:
    def __init__(self) -> None:
        self._nodes: Dict[str, DependencyNode] = {}

    def add_node(self, node_id: str) -> DependencyNode:
        if node_id not in self._nodes:
            self._nodes[node_id] = DependencyNode(node_id)
        return self._nodes[node_id]

    def remove_node(self, node_id: str) -> bool:
        if node_id not in self._nodes:
            return False
        node = self._nodes[node_id]
        for dep in node.dependencies:
            if dep in self._nodes:
                self._nodes[dep].dependents.discard(node_id)
        for dep in node.dependents:
            if dep in self._nodes:
                self._nodes[dep].dependencies.discard(node_id)
        del self._nodes[node_id]
        return True

    def add_dependency(self, node_id: str, depends_on: str) -> None:
        self.add_node(node_id)
        self.add_node(depends_on)
        self._nodes[node_id].dependencies.add(depends_on)
        self._nodes[depends_on].dependents.add(node_id)

    def get_dependencies(self, node_id: str) -> Set[str]:
        node = self._nodes.get(node_id)
        return node.dependencies.copy() if node else set()

    def get_all_dependencies(self, node_id: str) -> Set[str]:
        visited: Set[str] = set()
        queue = deque(self._nodes[node_id].dependencies) if node_id in self._nodes else deque()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            if current in self._nodes:
                queue.extend(self._nodes[current].dependencies - visited)
        return visited

    def topological_sort(self) -> List[str]:
        in_degree: Dict[str, int] = {n: 0 for n in self._nodes}
        for node in self._nodes.values():
            for dep in node.dependencies:
                if dep in in_degree:
                    in_degree[node.node_id] += 1
        queue = deque([n for n, d in in_degree.items() if d == 0])
        result: List[str] = []
        while queue:
            current = queue.popleft()
            result.append(current)
            for dependent in self._nodes[current].dependents:
                if dependent in in_degree:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        return result

    def has_cycle(self) -> bool:
        return len(self.topological_sort()) != len(self._nodes)

    def get_roots(self) -> List[str]:
        return [n for n, node in self._nodes.items() if not node.dependencies]

    def get_leaves(self) -> List[str]:
        return [n for n, node in self._nodes.items() if not node.dependents]

    def get_node(self, node_id: str) -> Optional[DependencyNode]:
        return self._nodes.get(node_id)

    def list_nodes(self) -> List[Dict[str, Any]]:
        return [n.to_dict() for n in self._nodes.values()]

    def count(self) -> int:
        return len(self._nodes)

    def validate(self) -> Dict[str, Any]:
        cycle = self.has_cycle()
        return {"valid": not cycle, "node_count": len(self._nodes),
                "has_cycle": cycle, "roots": self.get_roots(),
                "leaves": self.get_leaves()}
