"""
Content Analyzer
Main orchestrator for Module 1: Content Understanding.

Combines topic extraction, intent detection, entity recognition,
and keyword analysis into a unified content understanding result.
"""

from typing import Dict, List

from layers.layer03_intelligence.modules.content_understanding.topic_extractor import TopicExtractor
from layers.layer03_intelligence.modules.content_understanding.intent_detector import IntentDetector, IntentResult
from layers.layer03_intelligence.modules.content_understanding.entity_recognizer import EntityRecognizer, Entity
from layers.layer03_intelligence.modules.content_understanding.keyword_analyzer import KeywordAnalyzer, KeywordAnalysis


class ContentUnderstanding:
    """Complete understanding of a piece of content."""

    __slots__ = (
        "text", "topics", "multi_word_topics", "intent",
        "entities", "keyword_analysis", "domain",
        "overall_score",
    )

    def __init__(self, text: str = "", domain: str = "general"):
        self.text = text
        self.topics: List[Dict] = []
        self.multi_word_topics: List[Dict] = []
        self.intent = IntentResult()
        self.entities: List[Entity] = []
        self.keyword_analysis = KeywordAnalysis()
        self.domain = domain
        self.overall_score = 0.0

    def to_dict(self) -> dict:
        return {
            "text_length": len(self.text),
            "topics": self.topics[:5],
            "multi_word_topics": self.multi_word_topics[:5],
            "intent": self.intent.to_dict(),
            "entities": [e.to_dict() for e in self.entities],
            "keyword_analysis": self.keyword_analysis.to_dict(),
            "domain": self.domain,
            "overall_score": self.overall_score,
        }


class ContentAnalyzer:
    """Main content understanding engine."""

    def __init__(self):
        self.topic_extractor = TopicExtractor()
        self.intent_detector = IntentDetector()
        self.entity_recognizer = EntityRecognizer()
        self.keyword_analyzer = KeywordAnalyzer()

    def analyze(self, text: str, domain: str = "general") -> ContentUnderstanding:
        """Full content analysis."""
        result = ContentUnderstanding(text, domain)

        if not text.strip():
            return result

        # Run all analysis components
        result.topics = self.topic_extractor.extract(text)
        result.multi_word_topics = self.topic_extractor.extract_multi_word(text)
        result.intent = self.intent_detector.detect(text)
        result.entities = self.entity_recognizer.recognize(text)
        result.keyword_analysis = self.keyword_analyzer.analyze(text, domain)

        # Calculate overall score
        scores = []
        if result.topics:
            scores.append(result.topics[0]["score"] * 10)
        if result.intent.confidence > 0:
            scores.append(result.intent.confidence * 10)
        if result.keyword_analysis.score > 0:
            scores.append(min(10.0, result.keyword_analysis.score))
        if result.entities:
            scores.append(min(10.0, len(result.entities) * 2.0))

        result.overall_score = round(sum(scores) / max(len(scores), 1), 3) if scores else 0.0
        return result

    def analyze_batch(self, texts: List[str], domain: str = "general") -> List[ContentUnderstanding]:
        """Analyze multiple texts."""
        return [self.analyze(t, domain) for t in texts]

    def compare(self, text_a: str, text_b: str, domain: str = "general") -> Dict:
        """Compare two pieces of content."""
        a = self.analyze(text_a, domain)
        b = self.analyze(text_b, domain)

        return {
            "text_a": {"score": a.overall_score, "intent": a.intent.primary_intent},
            "text_b": {"score": b.overall_score, "intent": b.intent.primary_intent},
            "similarity": self._keyword_overlap(a, b),
        }

    def _keyword_overlap(self, a: ContentUnderstanding, b: ContentUnderstanding) -> float:
        """Calculate keyword overlap between two analyses."""
        kw_a = set(k["keyword"] for k in a.keyword_analysis.keywords)
        kw_b = set(k["keyword"] for k in b.keyword_analysis.keywords)
        if not kw_a and not kw_b:
            return 0.0
        intersection = kw_a & kw_b
        union = kw_a | kw_b
        return round(len(intersection) / max(len(union), 1), 3)
