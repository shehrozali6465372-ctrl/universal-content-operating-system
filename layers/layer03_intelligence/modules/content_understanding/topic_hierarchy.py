"""
Topic Hierarchy — Sprint 3 (v3.0)

Organizes topics into parent-child trees for better understanding.
"""

from __future__ import annotations
from typing import Dict, List, Optional


class TopicNode:
    """A node in the topic hierarchy."""

    __slots__ = ("name", "parent", "children", "aliases", "depth")

    def __init__(self, name: str, parent: str = "", aliases: Optional[List[str]] = None, depth: int = 0):
        self.name = name
        self.parent = parent
        self.children: List[str] = []
        self.aliases = aliases or []
        self.depth = depth

    def to_dict(self) -> Dict:
        return {"name": self.name, "parent": self.parent,
                "children": list(self.children), "depth": self.depth}


# Build hierarchy programmatically to avoid dict syntax issues
def _build_default_hierarchy() -> Dict:
    """Build the default topic hierarchy."""
    h = {}

    # Technology
    h["technology"] = {"parent": "", "aliases": ["tech"], "children": {
        "artificial_intelligence": {"parent": "technology", "aliases": ["ai", "ml", "machine_learning"], "children": {
            "natural_language_processing": {"parent": "artificial_intelligence", "aliases": ["nlp"], "children": {}},
            "computer_vision": {"parent": "artificial_intelligence", "aliases": ["cv"], "children": {}},
            "llm": {"parent": "artificial_intelligence", "aliases": ["large_language_model", "gpt", "claude"], "children": {}},
        }},
        "programming": {"parent": "technology", "aliases": ["coding", "development"], "children": {
            "web_development": {"parent": "programming", "aliases": ["web"], "children": {}},
            "mobile_development": {"parent": "programming", "aliases": ["mobile"], "children": {}},
            "data_science": {"parent": "programming", "aliases": ["analytics"], "children": {}},
        }},
        "cloud_computing": {"parent": "technology", "aliases": ["cloud", "aws", "azure"], "children": {}},
        "cybersecurity": {"parent": "technology", "aliases": ["security", "infosec"], "children": {}},
        "blockchain": {"parent": "technology", "aliases": ["crypto", "web3"], "children": {}},
    }}

    # Finance
    h["finance"] = {"parent": "", "aliases": ["financial"], "children": {
        "investing": {"parent": "finance", "aliases": ["investment"], "children": {
            "stock_market": {"parent": "investing", "aliases": ["stocks", "equities"], "children": {}},
            "cryptocurrency": {"parent": "investing", "aliases": ["crypto"], "children": {}},
        }},
        "banking": {"parent": "finance", "aliases": ["bank"], "children": {}},
        "personal_finance": {"parent": "finance", "aliases": ["money_management"], "children": {}},
    }}

    # Health
    h["health"] = {"parent": "", "aliases": ["healthcare"], "children": {
        "fitness": {"parent": "health", "aliases": ["exercise", "workout"], "children": {}},
        "nutrition": {"parent": "health", "aliases": ["diet", "food"], "children": {}},
        "mental_health": {"parent": "health", "aliases": ["wellness", "mindfulness"], "children": {}},
        "medicine": {"parent": "health", "aliases": ["medical", "clinical"], "children": {}},
    }}

    # Education
    h["education"] = {"parent": "", "aliases": ["learning"], "children": {
        "online_learning": {"parent": "education", "aliases": ["elearning", "mooc"], "children": {}},
        "skills_training": {"parent": "education", "aliases": ["training"], "children": {}},
        "academic": {"parent": "education", "aliases": ["research", "university"], "children": {}},
    }}

    # Career
    h["career"] = {"parent": "", "aliases": ["jobs"], "children": {
        "job_search": {"parent": "career", "aliases": ["hiring", "recruitment"], "children": {}},
        "professional_development": {"parent": "career", "aliases": ["growth"], "children": {}},
        "entrepreneurship": {"parent": "career", "aliases": ["startup", "business"], "children": {}},
    }}

    # Social Media
    h["social_media"] = {"parent": "", "aliases": ["social"], "children": {
        "content_creation": {"parent": "social_media", "aliases": ["content"], "children": {}},
        "community_management": {"parent": "social_media", "aliases": ["community"], "children": {}},
    }}

    return h


_DEFAULT_HIERARCHY = _build_default_hierarchy()


class TopicHierarchy:
    """Manages a hierarchical topic taxonomy."""

    def __init__(self, custom_hierarchy: Optional[Dict] = None) -> None:
        self._nodes: Dict[str, TopicNode] = {}
        self._alias_map: Dict[str, str] = {}
        hierarchy = custom_hierarchy or _DEFAULT_HIERARCHY
        self._build(hierarchy, parent="", depth=0)

    def classify(self, topic: str) -> TopicNode:
        lower = topic.lower().strip().replace(" ", "_")
        if lower in self._nodes:
            return self._nodes[lower]
        canonical = self._alias_map.get(lower, "")
        if canonical and canonical in self._nodes:
            return self._nodes[canonical]
        for name, node in self._nodes.items():
            if lower in name or name in lower:
                return node
        return TopicNode(name=topic, parent="", depth=0)

    def get_parent(self, topic: str) -> str:
        return self.classify(topic).parent

    def get_children(self, topic: str) -> List[str]:
        return list(self.classify(topic).children)

    def get_siblings(self, topic: str) -> List[str]:
        node = self.classify(topic)
        if not node.parent:
            return []
        parent_node = self._nodes.get(node.parent)
        if not parent_node:
            return []
        return [c for c in parent_node.children if c != node.name]

    def get_ancestors(self, topic: str) -> List[str]:
        ancestors = []
        current = self.classify(topic).parent
        while current and current in self._nodes:
            ancestors.append(current)
            current = self._nodes[current].parent
        return ancestors

    def get_hierarchy(self) -> Dict:
        roots = [n for n in self._nodes.values() if not n.parent]
        return {r.name: self._subtree(r.name) for r in roots}

    def search(self, query: str) -> List[TopicNode]:
        q = query.lower()
        return [n for n in self._nodes.values() if q in n.name or q in " ".join(n.aliases)]

    def get_all_topics(self) -> List[str]:
        return list(self._nodes.keys())

    def get_depth(self, topic: str) -> int:
        return self.classify(topic).depth

    def _build(self, data: Dict, parent: str, depth: int) -> None:
        for name, info in data.items():
            node = TopicNode(name=name, parent=parent, aliases=info.get("aliases", []), depth=depth)
            self._nodes[name] = node
            self._alias_map[name] = name
            for alias in node.aliases:
                self._alias_map[alias.lower()] = name
            if parent and parent in self._nodes:
                self._nodes[parent].children.append(name)
            children = info.get("children", {})
            if isinstance(children, dict) and children:
                self._build(children, parent=name, depth=depth + 1)

    def _subtree(self, name: str) -> Dict:
        node = self._nodes.get(name)
        if not node:
            return {}
        result = {"name": node.name, "aliases": node.aliases}
        if node.children:
            result["children"] = {c: self._subtree(c) for c in node.children}
        return result
