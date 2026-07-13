"""
Metadata Extractor
Layer 2: Research Engine — Module 5

Extracts structured metadata from content:
- Keyword extraction (TF-based)
- Entity extraction (basic NER patterns)
- Category detection
- Sentiment detection (keyword-based)
- Readability scoring
"""

import re
from collections import Counter
from typing import Dict, List, Optional, Tuple

# Common stop words
STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "out", "off", "over",
    "under", "again", "further", "then", "once", "here", "there", "when",
    "where", "why", "how", "all", "each", "every", "both", "few", "more",
    "most", "other", "some", "such", "no", "nor", "not", "only", "own",
    "same", "so", "than", "too", "very", "just", "and", "but", "or",
    "if", "this", "that", "these", "those", "it", "its", "i", "me",
    "my", "we", "our", "you", "your", "he", "she", "they", "them",
}

# Basic entity patterns
ENTITY_PATTERNS: Dict[str, str] = {
    "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "url": r'https?://[^\s<>"]+',
    "phone": r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
    "money": r'\$[\d,]+\.?\d*',
    "percentage": r'\d+\.?\d*%',
    "date": r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
}

# Sentiment keywords
POSITIVE_WORDS = {
    "good", "great", "excellent", "amazing", "wonderful", "best", "love",
    "awesome", "fantastic", "brilliant", "perfect", "success", "win",
    "improve", "benefit", "advantage", "positive", "happy", "free",
}

NEGATIVE_WORDS = {
    "bad", "terrible", "awful", "worst", "hate", "fail", "failure",
    "error", "bug", "problem", "issue", "wrong", "negative", "poor",
    "loss", "risk", "danger", "threat", "concern", "worry", "sad",
}


class MetadataExtractor:
    """Extract structured metadata from content."""

    def __init__(self, top_keywords: int = 15):
        self._top_keywords = top_keywords

    def extract_keywords(self, text: str, top_n: Optional[int] = None) -> List[Tuple[str, int]]:
        """Extract top keywords by frequency."""
        n = top_n or self._top_keywords
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        filtered = [w for w in words if w not in STOP_WORDS]
        return Counter(filtered).most_common(n)

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract basic named entities."""
        entities: Dict[str, List[str]] = {}
        for entity_type, pattern in ENTITY_PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                entities[entity_type] = list(set(matches))[:10]
        return entities

    def detect_category(self, text: str) -> str:
        """Simple category detection by keyword matching."""
        text_lower = text.lower()
        categories = {
            "technology": ["ai", "software", "code", "programming", "data", "algorithm", "tech", "digital"],
            "finance": ["money", "invest", "stock", "crypto", "profit", "revenue", "market", "trading"],
            "health": ["health", "medical", "fitness", "diet", "exercise", "wellness", "mental"],
            "education": ["learn", "course", "teach", "study", "school", "university", "training"],
            "business": ["business", "startup", "company", "marketing", "sales", "brand", "growth"],
            "entertainment": ["movie", "music", "game", "funny", "viral", "celebrity", "show"],
        }
        scores = {}
        for cat, keywords in categories.items():
            scores[cat] = sum(text_lower.count(kw) for kw in keywords)
        if not scores or max(scores.values()) == 0:
            return "general"
        return max(scores, key=scores.get)

    def detect_sentiment(self, text: str) -> str:
        """Simple keyword-based sentiment detection."""
        words = set(text.lower().split())
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        if pos > neg:
            return "positive"
        elif neg > pos:
            return "negative"
        return "neutral"

    def extract_all(self, text: str, title: str = "") -> Dict:
        """Extract all metadata from content."""
        keywords = self.extract_keywords(text)
        entities = self.extract_entities(text)
        category = self.detect_category(text + " " + title)
        sentiment = self.detect_sentiment(text)
        word_count = len(text.split())

        return {
            "keywords": keywords,
            "entities": entities,
            "category": category,
            "sentiment": sentiment,
            "word_count": word_count,
            "has_urls": bool(re.search(r'https?://', text)),
            "has_hashtags": bool(re.search(r'#\w+', text)),
        }
