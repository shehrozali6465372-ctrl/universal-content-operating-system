"""Decision Graph - Tracks decision dependencies and causal chains."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Set


class DecisionNode:
    """A node in the decision graph."""
    __slots__ = ("node_id", "label", "decision", "confidence", "stage",
                 "timestamp", "metadata", "dependencies")

    def __init__(self, node_id: str = "", label: str = ""):
        self.node_id = node_id
        self.label = label
        self.decision = ""
        self.confidence = 0.0
        self.stage = ""
        self.timestamp = time.time()
        self.metadata: Dict[str, Any] = {}
        self.dependencies: List[str] = []

    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id, "label": self.label,
            "decision": self.decision, "confidence": round(self.confidence, 3),
            "stage": self.stage, "dependencies": list(self.dependencies),
        }


class DecisionEdge:
    """An edge connecting two decision nodes."""
    __slots__ = ("from_node", "to_node", "edge_type", "weight")

    def __init__(self, from_node: str = "", to_node: str = "",
                 edge_type: str = "depends_on", weight: float = 1.0):
        self.from_node = from_node
        self.to_node = to_node
        self.edge_type = edge_type  # depends_on, influences, blocks, enables
        self.weight = weight

    def to_dict(self) -> Dict:
        return {"from": self.from_node, "to": self.to_node,
                "type": self.edge_type, "weight": self.weight}


class DecisionGraph:
    """Tracks decision dependencies and causal chains."""

    def __init__(self) -> None:
        self._nodes: Dict[str, DecisionNode] = {}
        self._edges: List[DecisionEdge] = []

    def add_node(self, node: DecisionNode) -> None:
        self._nodes[node.node_id] = node

    def create_node(self, node_id: str, label: str, decision: str = "",
                    confidence: float = 0.0, stage: str = "",
                    dependencies: Optional[List[str]] = None) -> DecisionNode:
        node = DecisionNode(node_id, label)
        node.decision = decision
        node.confidence = confidence
        node.stage = stage
        node.dependencies = dependencies or []
        self.add_node(node)
        for dep_id in node.dependencies:
            self._edges.append(DecisionEdge(dep_id, node_id, "depends_on"))
        return node

    def add_edge(self, from_id: str, to_id: str, edge_type: str = "depends_on",
                 weight: float = 1.0) -> None:
        self._edges.append(DecisionEdge(from_id, to_id, edge_type, weight))

    def get_node(self, node_id: str) -> Optional[DecisionNode]:
        return self._nodes.get(node_id)

    def get_dependencies(self, node_id: str) -> List[DecisionNode]:
        deps = []
        for edge in self._edges:
            if edge.to_node == node_id and edge.edge_type == "depends_on":
                node = self._nodes.get(edge.from_node)
                if node:
                    deps.append(node)
        return deps

    def get_dependents(self, node_id: str) -> List[DecisionNode]:
        result = []
        for edge in self._edges:
            if edge.from_node == node_id and edge.edge_type == "depends_on":
                node = self._nodes.get(edge.to_node)
                if node:
                    result.append(node)
        return result

    def get_critical_path(self) -> List[DecisionNode]:
        """Get the longest dependency chain (critical path)."""
        if not self._nodes:
            return []
        # Find root nodes (no dependencies)
        roots = [n for n in self._nodes.values() if not n.dependencies]
        if not roots:
            roots = list(self._nodes.values())[:1]

        best_path: List[DecisionNode] = []
        for root in roots:
            path = self._dfs(root.node_id, set())
            if len(path) > len(best_path):
                best_path = path
        return best_path

    def _dfs(self, node_id: str, visited: Set[str]) -> List[DecisionNode]:
        if node_id in visited:
            return []
        visited.add(node_id)
        node = self._nodes.get(node_id)
        if not node:
            return []
        result = [node]
        dependents = self.get_dependents(node_id)
        if dependents:
            longest = max(self._dfs(d.node_id, visited) for d in dependents)
            result.extend(longest)
        return result

    def find_weak_link(self) -> Optional[DecisionNode]:
        """Find the node with lowest confidence on the critical path."""
        path = self.get_critical_path()
        if not path:
            return None
        return min(path, key=lambda n: n.confidence)

    def get_path_confidence(self) -> float:
        """Calculate overall path confidence (product of all node confidences)."""
        path = self.get_critical_path()
        if not path:
            return 0.0
        result = 1.0
        for node in path:
            result *= max(node.confidence, 0.01)
        return result

    def count(self) -> int:
        return len(self._nodes)

    def to_dict(self) -> Dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for e in self._edges],
            "node_count": self.count(),
            "edge_count": len(self._edges),
            "critical_path_confidence": round(self.get_path_confidence(), 3),
        }
