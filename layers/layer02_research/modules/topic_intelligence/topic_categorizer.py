"""
Topic Categorizer
Layer 2: Research Engine — Module 2

Intelligent topic categorization and clustering:
- Auto-categorization by keyword matching
- Topic clustering (group related topics)
- Niche detection from keywords
- Content type suggestions
"""

from collections import defaultdict
from typing import Dict, List
from layers.layer02_research.modules.topic_intelligence.topic_entry import TopicEntry


# Keyword → Niche mapping for auto-categorization
NICHE_KEYWORDS: Dict[str, List[str]] = {
    "finance": [
        "investment", "stock", "crypto", "bitcoin", "trading", "money",
        "budget", "savings", "forex", "mutual fund", "nft", "wallet",
        "finance", "financial", "wealth", "income", "profit",
    ],
    "technology": [
        "ai", "machine learning", "python", "coding", "software",
        "app", "startup", "tech", "robot", "blockchain", "saas",
        "api", "cloud", "data", "algorithm", "digital",
    ],
    "health": [
        "diet", "nutrition", "vitamin", "exercise", "mental health",
        "wellness", "medical", "doctor", "yoga", "meditation",
        "sleep", "immune", "health", "healthy", "disease",
    ],
    "lifestyle": [
        "fashion", "beauty", "home", "decor", "minimalism",
        "daily routine", "morning", "self care", "aesthetic",
        "lifestyle", "living", "style", "trend",
    ],
    "education": [
        "learn", "course", "tutorial", "study", "skill",
        "book", "knowledge", "class", "training", "certification",
        "degree", "university", "teaching", "education",
    ],
    "entertainment": [
        "movie", "music", "game", "funny", "meme", "viral",
        "celebrity", "news", "show", "series", "podcast",
        "entertainment", "content", "video", "stream",
    ],
    "business": [
        "startup", "entrepreneur", "business", "marketing",
        "sales", "brand", "strategy", "leadership", "management",
        "ecommerce", "customer", "revenue", "growth", "hustle",
    ],
    "ai": [
        "artificial intelligence", "chatgpt", "gpt", "llm",
        "openai", "deep learning", "neural", "automation",
        "prompt", "agent", "copilot", "generative ai",
    ],
    "crypto": [
        "bitcoin", "ethereum", "defi", "token", "blockchain",
        "web3", "nft", "altcoin", "mining", "staking",
        "crypto", "coin", "binance", "wallet",
    ],
    "fitness": [
        "workout", "gym", "muscle", "weight loss", "cardio",
        "protein", "bodybuilding", "running", "strength",
        "fitness", "training", "abs", "lean",
    ],
    "cooking": [
        "recipe", "cook", "food", "kitchen", "bake",
        "meal", "ingredient", "chef", "cuisine", "dish",
        "cooking", "restaurant", "taste", "flavor",
    ],
    "travel": [
        "travel", "trip", "destination", "hotel", "flight",
        "adventure", "backpacking", "vacation", "tourism",
        "country", "city", "beach", "mountain", "explore",
    ],
    "parenting": [
        "parent", "baby", "child", "kid", "family",
        "school", "toddler", "pregnancy", "motherhood",
        "fatherhood", "parenting", "education", "toy",
    ],
    "motivation": [
        "motivation", "inspire", "goal", "mindset",
        "success", "hustle", "grind", "discipline",
        "believe", "dream", "growth", "mindset",
    ],
}


# Topic → Content type suggestions
CONTENT_TYPE_MAP: Dict[str, List[str]] = {
    "finance": ["carousel", "infographic", "short_video", "text_post"],
    "technology": ["tutorial", "thread", "infographic", "video"],
    "health": ["infographic", "short_video", "checklist", "carousel"],
    "lifestyle": ["photo", "reel", "story", "carousel"],
    "education": ["tutorial", "thread", "carousel", "infographic"],
    "entertainment": ["meme", "video", "reel", "story"],
    "business": ["carousel", "infographic", "text_post", "video"],
    "ai": ["tutorial", "demo_video", "thread", "infographic"],
    "crypto": ["infographic", "news_post", "carousel", "thread"],
    "fitness": ["video", "workout_reel", "transformation", "carousel"],
    "cooking": ["recipe_video", "reel", "photo", "carousel"],
    "travel": ["photo", "reel", "vlog", "carousel"],
    "parenting": ["text_post", "story", "photo", "carousel"],
    "motivation": ["quote_image", "text_post", "reel", "story"],
}


class TopicCategorizer:
    """Categorize and cluster Facebook topics."""

    def __init__(self):
        self._niche_keywords: Dict[str, List[str]] = dict(NICHE_KEYWORDS)
        self._clusters: Dict[str, List[str]] = {}
        self._cluster_counter = 0

    def detect_niche(self, keywords: List[str]) -> str:
        """Auto-detect niche from a list of keywords."""
        scores: Dict[str, int] = defaultdict(int)
        normalized = [k.lower().strip() for k in keywords]

        for niche, niche_kws in self._niche_keywords.items():
            for kw in normalized:
                for niche_kw in niche_kws:
                    if kw == niche_kw or niche_kw in kw or kw in niche_kw:
                        scores[niche] += 1

        if not scores:
            return "general"
        return max(scores, key=scores.get)

    def suggest_content_type(self, niche: str) -> List[str]:
        """Suggest content types for a niche."""
        return list(CONTENT_TYPE_MAP.get(niche, ["text_post", "photo"]))

    def auto_categorize(self, topic: TopicEntry) -> TopicEntry:
        """Auto-categorize a topic based on its keywords."""
        if not topic.keywords:
            return topic
        detected_niche = self.detect_niche(topic.keywords)
        if topic.niche == "general" and detected_niche != "general":
            topic.niche = detected_niche
        return topic

    def batch_categorize(self, topics: List[TopicEntry]) -> List[TopicEntry]:
        """Categorize a batch of topics."""
        for topic in topics:
            self.auto_categorize(topic)
        return topics

    def cluster_topics(self, topics: List[TopicEntry]) -> Dict[str, List[str]]:
        """Group related topics into clusters based on shared keywords/niches."""
        self._clusters.clear()
        niche_groups: Dict[str, List[str]] = defaultdict(list)

        for topic in topics:
            niche_groups[topic.niche].append(topic.topic_id)

        for niche, topic_ids in niche_groups.items():
            if len(topic_ids) >= 2:
                self._cluster_counter += 1
                cluster_name = f"cluster_{niche}_{self._cluster_counter}"
                self._clusters[cluster_name] = topic_ids

        return dict(self._clusters)

    def find_related(self, topic: TopicEntry, all_topics: List[TopicEntry], max_results: int = 5) -> List[str]:
        """Find related topic IDs based on keyword overlap."""
        topic_words = set(kw.lower() for kw in topic.keywords)
        if not topic_words:
            topic_words = {topic.niche}

        scores = []
        for other in all_topics:
            if other.topic_id == topic.topic_id:
                continue
            other_words = set(kw.lower() for kw in other.keywords)
            if not other_words:
                other_words = {other.niche}
            overlap = len(topic_words & other_words)
            if overlap > 0:
                scores.append((other.topic_id, overlap))

        scores.sort(key=lambda x: x[1], reverse=True)
        return [tid for tid, _ in scores[:max_results]]

    def get_niche_stats(self, topics: List[TopicEntry]) -> Dict[str, Dict]:
        """Get statistics per niche."""
        stats: Dict[str, Dict] = {}
        niche_topics: Dict[str, List[TopicEntry]] = defaultdict(list)
        for t in topics:
            niche_topics[t.niche].append(t)

        for niche, group in niche_topics.items():
            avg_composite = sum(t.composite_score for t in group) / len(group)
            avg_engagement = sum(t.engagement_score for t in group) / len(group)
            stats[niche] = {
                "count": len(group),
                "avg_composite": round(avg_composite, 2),
                "avg_engagement": round(avg_engagement, 2),
                "top_topic": max(group, key=lambda t: t.composite_score).name,
            }
        return stats
