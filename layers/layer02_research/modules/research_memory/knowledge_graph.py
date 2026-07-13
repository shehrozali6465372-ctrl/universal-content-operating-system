"""
Knowledge Graph
Layer 2: Research Engine — Module 7

Graph-based knowledge representation:
- Entity nodes
- Relationship edges
- Path finding
- Neighborhood queries
- Graph statistics
"""

from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple


class GraphNode:
    """A node in the knowledge graph."""

    __slots__ = ("node_id", "node_type", "label", "properties", "weight")

    def __init__(self, node_id: str, node_type: str = "entity", label: str = "", weight: float = 1.0):
        self.node_id = node_id
        self.node_type = node_type
        self.label = label or node_id
        self.properties: Dict = {}
        self.weight = max(0.0, min(10.0, weight))

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id, "node_type": self.node_type,
            "label": self.label, "weight": self.weight,
            "properties": self.properties,
        }


class GraphEdge:
    """An edge in the knowledge graph."""

    __slots__ = ("source_id", "target_id", "relation", "weight", "properties")

    def __init__(self, source_id: str, target_id: str, relation: str = "related_to", weight: float = 1.0):
        self.source_id = source_id
        self.target_id = target_id
        self.relation = relation
        self.weight = max(0.0, min(10.0, weight))
        self.properties: Dict = {}

    def to_dict(self) -> dict:
        return {
            "source": self.source_id, "target": self.target_id,
            "relation": self.relation, "weight": self.weight,
        }


class KnowledgeGraph:
    """Graph-based knowledge storage and traversal."""

    def __init__(self):
        self._nodes: Dict[str, GraphNode] = {}
        self._edges: Dict[str, List[GraphEdge]] = defaultdict(list)
        self._reverse_edges: Dict[str, List[GraphEdge]] = defaultdict(list)

    def add_node(self, node_id: str, node_type: str = "entity", label: str = "", weight: float = 1.0) -> GraphNode:
        if node_id not in self._nodes:
            self._nodes[node_id] = GraphNode(node_id, node_type, label, weight)
        return self._nodes[node_id]

    def add_edge(self, source_id: str, target_id: str, relation: str = "related_to", weight: float = 1.0) -> GraphEdge:
        # Auto-create nodes
        if source_id not in self._nodes:
            self.add_node(source_id)
        if target_id not in self._nodes:
            self.add_node(target_id)
        edge = GraphEdge(source_id, target_id, relation, weight)
        self._edges[source_id].append(edge)
        self._reverse_edges[target_id].append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Tuple[str, str]]:
        """Get neighbor node IDs and their relation types."""
        neighbors = []
        if direction in ("out", "both"):
            for edge in self._edges.get(node_id, []):
                neighbors.append((edge.target_id, edge.relation))
        if direction in ("in", "both"):
            for edge in self._reverse_edges.get(node_id, []):
                neighbors.append((edge.source_id, edge.relation))
        return neighbors

    def find_path(self, start_id: str, end_id: str, max_depth: int = 5) -> Optional[List[str]]:
        """BFS shortest path between two nodes."""
        if start_id == end_id:
            return [start_id]
        visited = {start_id}
        queue = deque([(start_id, [start_id])])
        while queue:
            current, path = queue.popleft()
            if len(path) > max_depth:
                continue
            for neighbor_id, _ in self.get_neighbors(current, "out"):
                if neighbor_id == end_id:
                    return path + [neighbor_id]
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append((neighbor_id, path + [neighbor_id]))
        return None

    def get_subgraph(self, center_id: str, depth: int = 2) -> Dict[str, any]:
        """Get a subgraph around a center node."""
        visited = {center_id}
        nodes = {center_id: self._nodes[center_id].to_dict()} if center_id in self._nodes else {}
        edges = []

        current_level = [center_id]
        for _ in range(depth):
            next_level = []
            for nid in current_level:
                for edge in self._edges.get(nid, []):
                    if edge.target_id not in visited:
                        visited.add(edge.target_id)
                        next_level.append(edge.target_id)
                        if edge.target_id in self._nodes:
                            nodes[edge.target_id] = self._nodes[edge.target_id].to_dict()
                        edges.append(edge.to_dict())
            current_level = next_level

        return {"nodes": nodes, "edges": edges}

    def find_related(self, node_id: str, relation: Optional[str] = None, max_results: int = 10) -> List[str]:
        """Find related nodes optionally filtered by relation."""
        neighbors = self.get_neighbors(node_id, "out")
        if relation:
            neighbors = [(nid, rel) for nid, rel in neighbors if rel == relation]
        return [nid for nid, _ in neighbors[:max_results]]

    def get_nodes_by_type(self, node_type: str) -> List[GraphNode]:
        return [n for n in self._nodes.values() if n.node_type == node_type]

    def stats(self) -> dict:
        edge_types = defaultdict(int)
        for edges in self._edges.values():
            for e in edges:
                edge_types[e.relation] += 1
        return {
            "total_nodes": len(self._nodes),
            "total_edges": sum(len(edges) for edges in self._edges.values()),
            "node_types": len(set(n.node_type for n in self._nodes.values())),
            "edge_types": dict(edge_types),
        }

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self._nodes.values()],
            "edges": [e.to_dict() for edges in self._edges.values() for e in edges],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeGraph":
        graph = cls()
        for nd in data.get("nodes", []):
            graph.add_node(nd["node_id"], nd.get("node_type", "entity"), nd.get("label", ""), nd.get("weight", 1.0))
        for ed in data.get("edges", []):
            graph.add_edge(ed["source"], ed["target"], ed.get("relation", "related_to"), ed.get("weight", 1.0))
        return graph
