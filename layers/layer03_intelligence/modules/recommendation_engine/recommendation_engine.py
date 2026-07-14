"""Recommendation Engine — produces actionable topic, content, and posting recommendations."""
from typing import Dict, List

class Recommendation:
    __slots__ = ("rec_type", "title", "description", "confidence", "priority", "metadata")
    def __init__(self, rec_type: str = "", title: str = "", description: str = "", confidence: float = 0.5, priority: str = "MEDIUM"):
        self.rec_type = rec_type
        self.title = title
        self.description = description
        self.confidence = confidence
        self.priority = priority
        self.metadata: Dict = {}
    def to_dict(self) -> dict:
        return {"rec_type": self.rec_type, "title": self.title, "description": self.description,
                "confidence": self.confidence, "priority": self.priority}

class RecommendationEngine:
    def __init__(self):
        self._recommendations: List[Recommendation] = []
    def add(self, rec: Recommendation):
        self._recommendations.append(rec)
    def get_top(self, n: int = 5) -> List[Recommendation]:
        return sorted(self._recommendations, key=lambda r: -r.confidence)[:n]
    def get_by_type(self, rec_type: str) -> List[Recommendation]:
        return [r for r in self._recommendations if r.rec_type == rec_type]
    def get_by_priority(self, priority: str) -> List[Recommendation]:
        return [r for r in self._recommendations if r.priority == priority]
    def count(self) -> int:
        return len(self._recommendations)
    def clear(self):
        self._recommendations.clear()
    def generate_topic_recommendations(self, scored_topics: List[Dict]) -> List[Recommendation]:
        for t in scored_topics:
            name = t.get("topic", t.get("title", "unknown"))
            score = t.get("overall_score", t.get("score", 0))
            priority = "HIGH" if score >= 80 else "MEDIUM" if score >= 50 else "LOW"
            self.add(Recommendation("topic", f"Write about: {name}",
                f"Topic score: {score}", min(1.0, score/100), priority))
        return self.get_top()
    def generate_posting_recommendations(self, best_times: List[str], niche: str = "general") -> List[Recommendation]:
        for time_slot in best_times:
            self.add(Recommendation("posting", f"Post at {time_slot}",
                f"Optimal for {niche} audience", 0.75, "MEDIUM"))
        return self.get_top()
