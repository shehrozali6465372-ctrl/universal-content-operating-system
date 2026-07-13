"""
Interest Mapper
Layer 2: Research Engine — Module 4

Maps and clusters audience interests:
- Interest categorization
- Interest overlap detection
- Interest-to-content mapping
- Interest scoring (relevance, popularity, competition)
- Interest hierarchy
"""

from typing import Dict, List, Optional


# Interest hierarchy: parent → children
INTEREST_HIERARCHY: Dict[str, List[str]] = {
    "technology": ["ai", "python", "web dev", "mobile", "cloud", "cybersecurity", "blockchain"],
    "finance": ["investing", "crypto", "personal finance", "stocks", "forex", "real estate"],
    "health": ["fitness", "nutrition", "mental health", "yoga", "diet", "sleep"],
    "business": ["marketing", "sales", "leadership", "startup", "ecommerce", "freelancing"],
    "lifestyle": ["travel", "fashion", "cooking", "home decor", "minimalism", "parenting"],
    "education": ["online courses", "skills", "certification", "languages", "coding"],
    "entertainment": ["movies", "music", "gaming", "books", "podcasts"],
    "motivation": ["productivity", "self-improvement", "mindset", "habits", "goals"],
}

# Reverse lookup: child → parent
_CHILD_TO_PARENT: Dict[str, str] = {}
for parent, children in INTEREST_HIERARCHY.items():
    for child in children:
        _CHILD_TO_PARENT[child] = parent


class InterestNode:
    """A single scored interest."""

    __slots__ = ("name", "category", "relevance_score", "popularity_score",
                 "competition_score", "composite_score", "related")

    def __init__(self, name: str, category: str = "general",
                 relevance_score: float = 5.0, popularity_score: float = 5.0,
                 competition_score: float = 5.0):
        self.name = name.lower()
        self.category = category
        self.relevance_score = max(0.0, min(10.0, relevance_score))
        self.popularity_score = max(0.0, min(10.0, popularity_score))
        self.competition_score = max(0.0, min(10.0, competition_score))
        self.related: List[str] = []
        self.composite_score = round(
            (self.relevance_score * 0.4 +
             self.popularity_score * 0.35 +
             (10.0 - self.competition_score) * 0.25),
            2,
        )

    def to_dict(self) -> dict:
        return {
            "name": self.name, "category": self.category,
            "relevance_score": self.relevance_score,
            "popularity_score": self.popularity_score,
            "competition_score": self.competition_score,
            "composite_score": self.composite_score,
            "related": self.related,
        }


class InterestMapper:
    """Map, cluster, and score audience interests."""

    def __init__(self):
        self._interests: Dict[str, InterestNode] = {}
        self._clusters: Dict[str, List[str]] = {}

    def add_interest(
        self,
        name: str,
        category: str = "general",
        relevance_score: float = 5.0,
        popularity_score: float = 5.0,
        competition_score: float = 5.0,
    ) -> InterestNode:
        """Add or update an interest."""
        node = InterestNode(name, category, relevance_score, popularity_score, competition_score)
        # Auto-detect category from hierarchy
        if category == "general" and name.lower() in _CHILD_TO_PARENT:
            node.category = _CHILD_TO_PARENT[name.lower()]

        # Set related interests
        parent = _CHILD_TO_PARENT.get(name.lower())
        if parent and parent in INTEREST_HIERARCHY:
            node.related = [c for c in INTEREST_HIERARCHY[parent] if c != name.lower()]

        self._interests[node.name] = node
        return node

    def get_interest(self, name: str) -> Optional[InterestNode]:
        return self._interests.get(name.lower())

    def remove_interest(self, name: str) -> bool:
        if name.lower() in self._interests:
            del self._interests[name.lower()]
            return True
        return False

    def list_interests(self) -> List[InterestNode]:
        return list(self._interests.values())

    def get_top_interests(self, count: int = 10) -> List[InterestNode]:
        """Get top interests by composite score."""
        return sorted(self._interests.values(), key=lambda n: n.composite_score, reverse=True)[:count]

    def get_by_category(self, category: str) -> List[InterestNode]:
        return [n for n in self._interests.values() if n.category == category]

    def cluster_interests(self) -> Dict[str, List[str]]:
        """Group interests by category."""
        self._clusters.clear()
        for node in self._interests.values():
            cat = node.category
            if cat not in self._clusters:
                self._clusters[cat] = []
            self._clusters[cat].append(node.name)
        return dict(self._clusters)

    def find_related(self, name: str, max_results: int = 5) -> List[str]:
        """Find interests related to a given interest."""
        node = self._interests.get(name.lower())
        if not node:
            return []

        related = set(node.related)
        # Also check parent's other children
        parent = _CHILD_TO_PARENT.get(name.lower())
        if parent and parent in INTEREST_HIERARCHY:
            for child in INTEREST_HIERARCHY[parent]:
                if child != name.lower():
                    related.add(child)

        return list(related)[:max_results]

    def compute_overlap(self, interests_a: List[str], interests_b: List[str]) -> float:
        """Compute interest overlap ratio between two sets (0.0 to 1.0)."""
        set_a = set(i.lower() for i in interests_a)
        set_b = set(i.lower() for i in interests_b)
        if not set_a or not set_b:
            return 0.0
        intersection = set_a & set_b
        union = set_a | set_b
        return round(len(intersection) / len(union), 3) if union else 0.0

    def score_content_fit(self, content_topics: List[str], audience_interests: List[str]) -> float:
        """Score how well content topics match audience interests (0-10)."""
        if not content_topics or not audience_interests:
            return 0.0

        match_count = 0
        for topic in content_topics:
            topic_lower = topic.lower()
            for interest in audience_interests:
                interest_lower = interest.lower()
                if topic_lower == interest_lower or topic_lower in interest_lower or interest_lower in topic_lower:
                    match_count += 1
                    break
                # Check parent-child relationship
                topic_parent = _CHILD_TO_PARENT.get(topic_lower)
                interest_parent = _CHILD_TO_PARENT.get(interest_lower)
                if topic_parent and topic_parent == interest_parent:
                    match_count += 1
                    break

        return round(min(10.0, (match_count / len(content_topics)) * 10), 2)

    def suggest_content_topics(self, audience_interests: List[str], count: int = 10) -> List[str]:
        """Suggest content topics based on audience interests."""
        suggestions = set()
        for interest in audience_interests:
            node = self._interests.get(interest.lower())
            if node:
                suggestions.update(node.related)
            parent = _CHILD_TO_PARENT.get(interest.lower())
            if parent and parent in INTEREST_HIERARCHY:
                suggestions.update(INTEREST_HIERARCHY[parent])
            suggestions.add(interest)

        suggestions -= set(i.lower() for i in audience_interests)
        return sorted(suggestions)[:count]
