"""
Semantic Analyzer — Sprint 1 (v1.0)

Production-grade semantic analysis of text content.

Public API:
    analyze(text) -> SemanticResult
    extract_topics(text) -> List[str]
    detect_intent(text) -> str
    detect_context(text) -> str
    semantic_score(text) -> float
    semantic_similarity(text_a, text_b) -> float

Features:
    - Topic detection from text
    - Intent classification (informative, promotional, etc.)
    - Context extraction (setting, domain, audience)
    - Sentiment analysis (positive, negative, neutral)
    - Complexity scoring (reading level)
    - Confidence scoring
    - Mixed Urdu/English support (basic)
    - Event Bus integration on analysis completion

Version: 1.0.0
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple

from layers.shared.models.event import Event, EventType


# ─────────────────────────────────────────────────────────────────────
# Intent lexicons
# ─────────────────────────────────────────────────────────────────────
_INTENT_LEXICON: Dict[str, List[str]] = {
    "predictive": ["will", "going to", "expect", "forecast", "predict",
                    "展望", "ہوگا", "ہونے والا", "والا ہے", "预计", "soon"],
    "informative": ["how", "what", "guide", "learn", "explain", "tutorial",
                     "tip", "kya", "kaise", "کیا", "کیسے", "سیکھیں"],
    "promotional": ["buy", "discount", "offer", "sale", "deal", "free",
                     "premium", "limited", "خریدیں", "آفر"],
    "engagement": ["question", "poll", "guess", "think", "opinion",
                    "agree", "comment", "share", "سوچیں", "رائے"],
    "news": ["breaking", "announce", "launch", "release", "update",
             "report", "develop", "خبر", "اعلان"],
    "educational": ["course", "learn", "study", "research", "teach",
                     "training", "skill", "نصاب", "مشق"],
    "emotional": ["love", "feel", "heart", "amazing", "beautiful",
                   "touching", "پیار", "خوبصورت"],
}

# ─────────────────────────────────────────────────────────────────────
# Sentiment lexicons (lightweight, no external lib)
# ─────────────────────────────────────────────────────────────────────
_POSITIVE_WORDS: Set[str] = {
    "good", "great", "excellent", "amazing", "wonderful", "fantastic",
    "awesome", "best", "love", "happy", "success", "win", "positive",
    "improve", "growth", "increase", "boost", "opportunity", "innovative",
    "powerful", "effective", "brilliant", "perfect", "beautiful",
    # Urdu / Hinglish
    "اچھا", "بہترین", "خوبصورت", "کامیاب", "پیار", "خوشی", "فائدہ",
    "best", "zabardast", "achha", "kamyab", "khush",
}
_NEGATIVE_WORDS: Set[str] = {
    "bad", "poor", "terrible", "horrible", "worst", "fail", "failure",
    "problem", "issue", "error", "loss", "decline", "decrease", "risk",
    "danger", "threat", "concern", "worse", "negative", "difficult",
    "crisis", "bug", "broken",
    # Urdu / Hinglish
    "خراب", "ناقص", "ناکام", "مشکل", "خطرناک", "نقصان", "کمزور",
    "kharab", "nakam", "mushkil", "khatarnak",
}

# ─────────────────────────────────────────────────────────────────────
# Context keywords
# ─────────────────────────────────────────────────────────────────────
_CONTEXT_KEYWORDS: Dict[str, List[str]] = {
    "technology": ["ai", "software", "tech", "digital", "data", "code",
                   "programming", "developer", "algorithm", "machine",
                   "ٹیکنالوجی", "سوفٹویئر"],
    "finance": ["invest", "money", "stock", "crypto", "finance", "bank",
                "revenue", "profit", "budget", "market",
                "مالیات", "سرمایہ", "پیسہ"],
    "health": ["health", "medical", "fitness", "wellness", "diet", "doctor",
               "disease", "treatment", "exercise",
               "صحت", "طبی", "ورزش"],
    "education": ["learn", "course", "study", "skill", "training", "school",
                  "university", "teach", "knowledge", "student",
                  "تعلیم", "سکھیں"],
    "career": ["job", "career", "hiring", "salary", "interview", "resume",
               "hire", "employee", "work", "profession",
               "ملازمت", "کیریئر", "نوکری"],
    "social": ["post", "share", "follow", "like", "comment", "community",
               "friend", "connect", "network",
               "سوشل", "کمیونٹی"],
}

# ─────────────────────────────────────────────────────────────────────
# Complexity indicators
# ─────────────────────────────────────────────────────────────────────
_LONG_WORDS_THRESHOLD = 6     # avg chars per word → high complexity
_LONG_SENTENCE_THRESHOLD = 20  # words per sentence → high complexity


# ─────────────────────────────────────────────────────────────────────
# Public Result Model
# ─────────────────────────────────────────────────────────────────────
class SemanticResult:
    """Result of semantic analysis on a piece of text.

    Attributes:
        topic: Primary detected topic phrase.
        topics: All detected topic phrases (ranked by relevance).
        intent: Primary intent category.
        intent_confidence: Confidence in intent classification (0.0–1.0).
        entities: Extracted entities (people, orgs, dates, numbers).
        sentiment: Sentiment label (positive / negative / neutral).
        sentiment_score: Numeric sentiment (−1.0 to +1.0).
        context: Primary context domain (technology, finance, etc.).
        confidence: Overall analysis confidence (0.0–1.0).
        complexity: Reading complexity level (low / medium / high).
        complexity_score: Numeric complexity (0.0–1.0).
        semantic_score: Composite quality/relevance score (0.0–100.0).
        word_count: Total words in input.
        sentence_count: Total sentences in input.
    """

    __slots__ = (
        "topic", "topics", "intent", "intent_confidence",
        "entities", "sentiment", "sentiment_score",
        "context", "confidence", "complexity", "complexity_score",
        "semantic_score", "word_count", "sentence_count",
    )

    def __init__(self) -> None:
        self.topic: str = ""
        self.topics: List[str] = []
        self.intent: str = "unknown"
        self.intent_confidence: float = 0.0
        self.entities: List[Dict[str, str]] = []
        self.sentiment: str = "neutral"
        self.sentiment_score: float = 0.0
        self.context: str = "general"
        self.confidence: float = 0.0
        self.complexity: str = "medium"
        self.complexity_score: float = 0.5
        self.semantic_score: float = 0.0
        self.word_count: int = 0
        self.sentence_count: int = 0

    def to_dict(self) -> Dict:
        return {
            "topic": self.topic,
            "topics": list(self.topics),
            "intent": self.intent,
            "intent_confidence": round(self.intent_confidence, 3),
            "entities": list(self.entities),
            "sentiment": self.sentiment,
            "sentiment_score": round(self.sentiment_score, 3),
            "context": self.context,
            "confidence": round(self.confidence, 3),
            "complexity": self.complexity,
            "complexity_score": round(self.complexity_score, 3),
            "semantic_score": round(self.semantic_score, 2),
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
        }

    def __repr__(self) -> str:
        return (
            f"SemanticResult(topic='{self.topic}', intent='{self.intent}', "
            f"sentiment='{self.sentiment}', score={self.semantic_score:.1f})"
        )


# ─────────────────────────────────────────────────────────────────────
# Semantic Analyzer
# ─────────────────────────────────────────────────────────────────────
class SemanticAnalyzer:
    """Production-grade semantic analyzer for text content.

    Analyzes text for topics, intent, sentiment, context, complexity,
    and produces a composite semantic score.

    Usage::

        analyzer = SemanticAnalyzer()
        result = analyzer.analyze("AI jobs are booming in 2026")
        print(result.topic, result.sentiment, result.semantic_score)
    """

    def __init__(self, publish_events: bool = False) -> None:
        """
        Args:
            publish_events: If True, publish SEMANTIC_ANALYZED event to
                            the global EventBus after each analysis.
        """
        self.publish_events = publish_events

    # ── Public API ───────────────────────────────────────────────────

    def analyze(self, text: str) -> SemanticResult:
        """Run full semantic analysis on *text*.

        Returns a :class:`SemanticResult` with all fields populated.
        """
        result = SemanticResult()

        if not text or not text.strip():
            return result

        clean = text.strip()
        words = self._tokenize(clean)
        sentences = self._split_sentences(clean)

        result.word_count = len(words)
        result.sentence_count = len(sentences)

        # 1. Topics
        result.topics = self.extract_topics(clean)
        result.topic = result.topics[0] if result.topics else ""

        # 2. Intent
        result.intent, result.intent_confidence = self._classify_intent(clean)

        # 3. Entities (basic)
        result.entities = self._extract_entities(clean)

        # 4. Sentiment
        result.sentiment, result.sentiment_score = self._analyze_sentiment(words)

        # 5. Context
        result.context = self.detect_context(clean)

        # 6. Complexity
        result.complexity, result.complexity_score = self._score_complexity(words, sentences)

        # 7. Semantic score (composite)
        result.semantic_score = self._compute_semantic_score(result)

        # 8. Overall confidence
        result.confidence = self._compute_confidence(result)

        # 9. Event Bus integration
        if self.publish_events:
            self._publish_event(result)

        return result

    def extract_topics(self, text: str) -> List[str]:
        """Extract ranked topic phrases from *text*.

        Returns a list of topic strings ordered by relevance.
        """
        if not text or not text.strip():
            return []

        words = self._tokenize(text)
        if not words:
            return []

        # Score words by TF × length bonus
        freq: Dict[str, int] = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1

        total = len(words)
        scored: List[Tuple[str, float]] = []
        for word, count in freq.items():
            tf = count / total
            length_bonus = min(1.5, len(word) / 5.0)
            scored.append((word, tf * length_bonus))

        scored.sort(key=lambda x: -x[1])

        # Also extract bigrams
        bigrams = self._extract_bigrams(words, freq, total)

        topics = [w for w, _ in scored[:5]]
        topics.extend(bigrams[:3])

        return list(dict.fromkeys(topics))  # deduplicate, preserve order

    def detect_intent(self, text: str) -> str:
        """Detect the primary intent of *text*.

        Returns one of: predictive, informative, promotional, engagement,
        news, educational, emotional, unknown.
        """
        intent, _ = self._classify_intent(text)
        return intent

    def detect_context(self, text: str) -> str:
        """Detect the domain context of *text*.

        Returns one of: technology, finance, health, education, career,
        social, general.
        """
        if not text:
            return "general"

        words = set(self._tokenize(text))
        scores: Dict[str, int] = {}

        for context, keywords in _CONTEXT_KEYWORDS.items():
            matches = words.intersection(set(keywords))
            if matches:
                scores[context] = len(matches)

        if not scores:
            return "general"

        return max(scores, key=scores.get)

    def semantic_score(self, text: str) -> float:
        """Compute composite semantic score (0.0–100.0) for *text*."""
        result = self.analyze(text)
        return result.semantic_score

    def semantic_similarity(self, text_a: str, text_b: str) -> float:
        """Compute keyword-overlap similarity between two texts.

        Returns a value between 0.0 (no overlap) and 1.0 (identical words).
        """
        if not text_a or not text_b:
            return 0.0

        words_a = set(self._tokenize(text_a))
        words_b = set(self._tokenize(text_b))

        if not words_a and not words_b:
            return 0.0

        intersection = words_a & words_b
        union = words_a | words_b

        return round(len(intersection) / max(len(union), 1), 3)

    # ── Private helpers ──────────────────────────────────────────────

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into lowercase meaningful words."""
        stop = {"the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "shall", "can",
                "to", "of", "in", "for", "on", "with", "at", "by", "from",
                "as", "into", "through", "during", "before", "after",
                "above", "below", "between", "out", "off", "over", "under",
                "again", "further", "then", "once", "here", "there",
                "when", "where", "why", "how", "all", "both", "each",
                "few", "more", "most", "other", "some", "such", "no",
                "nor", "not", "only", "own", "same", "so", "than",
                "too", "very", "just", "because", "but", "and", "or",
                "if", "while", "that", "this", "it", "its", "he", "she",
                "they", "them", "we", "you", "i", "me", "my", "your",
                "his", "her", "our", "their", "what", "which", "who",
                "whom", "these", "those", "am", "about", "up", "down",
                "also", "like", "well", "much", "many", "even", "still",
                "really", "quite", "right", "now", "new", "one", "two",
                "get", "got", "make", "made", "go", "going", "come",
                "came", "see", "know", "take", "want", "give", "use",
                "find", "tell", "ask", "work", "seem", "feel", "try",
                "leave", "call", "need", "become", "keep", "let",
                "begin", "show", "hear", "play", "run", "move",
                "live", "believe", "bring", "happen", "must",
                "ka", "ki", "ke", "hai", "ho", "ko", "se", "ne",
                "mein", "par", "ya", "aur", "to", "bhi", "kya",
                "kab", "kaise", "kyun", "ye", "wo", "yeh", "woh",
                "hum", "tum", "main", "mera", "tera", "uska"}

        tokens = re.findall(r"[a-zA-Z0-9\u0600-\u06FF]+", text.lower())
        return [t for t in tokens if len(t) >= 2 and t not in stop]

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        parts = re.split(r'[.!?؟\n]+', text)
        return [s.strip() for s in parts if s.strip()]

    def _extract_bigrams(self, words: List[str], freq: Dict[str, int],
                         total: int) -> List[str]:
        """Extract meaningful bigrams."""
        bigram_counts: Dict[str, int] = {}
        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            bigram_counts[bg] = bigram_counts.get(bg, 0) + 1

        scored = [(bg, count / max(total, 1)) for bg, count in bigram_counts.items()
                  if count >= 2]
        scored.sort(key=lambda x: -x[1])
        return [bg for bg, _ in scored[:5]]

    def _classify_intent(self, text: str) -> Tuple[str, float]:
        """Classify intent and return (label, confidence)."""
        words = set(self._tokenize(text))
        text_lower = text.lower()

        scores: Dict[str, float] = {}
        for intent, keywords in _INTENT_LEXICON.items():
            # Direct word match
            direct = len(words.intersection(set(keywords)))
            # Substring match (for multi-word patterns)
            substr = sum(1 for kw in keywords if kw in text_lower)
            total_matches = max(direct, substr)
            if total_matches > 0:
                scores[intent] = total_matches / len(keywords)

        if not scores:
            return "unknown", 0.0

        best = max(scores, key=scores.get)
        confidence = min(0.95, scores[best] + 0.3)
        return best, round(confidence, 3)

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        """Extract basic entities (names, orgs, dates, numbers, URLs)."""
        entities: List[Dict[str, str]] = []
        seen: Set[str] = set()

        patterns: List[Tuple[str, str]] = [
            ("url", r"https?://[^\s]+"),
            ("email", r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b"),
            ("date", r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b"),
            ("date", r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\w*\s+\d{1,2},?\s+\d{4}\b"),
            ("money", r"\$[\d,]+(?:\.\d{2})?"),
            ("number", r"\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b"),
            ("number", r"\b\d+(?:\.\d+)?%?\b"),
            ("hashtag", r"#[a-zA-Z0-9_]+"),
            ("mention", r"@[a-zA-Z0-9_]+"),
            ("person", r"\b[A-Z][a-z]+ [A-Z][a-z]+\b"),
            ("organization", r"\b(?:Facebook|Google|Microsoft|Apple|Amazon|OpenAI|Tesla|Meta|Samsung|Netflix|Twitter)\b"),
        ]

        for etype, pattern in patterns:
            for match in re.finditer(pattern, text):
                val = match.group()
                key = f"{val.lower()}:{etype}"
                if key not in seen:
                    seen.add(key)
                    entities.append({"text": val, "type": etype})

        return entities

    def _analyze_sentiment(self, words: List[str]) -> Tuple[str, float]:
        """Analyze sentiment from word list.

        Returns (label, score) where score is in [-1.0, +1.0].
        """
        if not words:
            return "neutral", 0.0

        pos = len(set(words) & _POSITIVE_WORDS)
        neg = len(set(words) & _NEGATIVE_WORDS)
        total = pos + neg

        if total == 0:
            return "neutral", 0.0

        score = (pos - neg) / total
        score = max(-1.0, min(1.0, score))

        if score > 0.1:
            label = "positive"
        elif score < -0.1:
            label = "negative"
        else:
            label = "neutral"

        return label, round(score, 3)

    def _score_complexity(self, words: List[str],
                          sentences: List[str]) -> Tuple[str, float]:
        """Score text complexity (0.0 = simple, 1.0 = complex)."""
        if not words:
            return "low", 0.0

        avg_word_len = sum(len(w) for w in words) / len(words)
        avg_sentence_len = len(words) / max(len(sentences), 1)

        # Normalize to 0–1
        word_score = min(1.0, max(0.0, (avg_word_len - 3) / (_LONG_WORDS_THRESHOLD - 3)))
        sent_score = min(1.0, max(0.0, (avg_sentence_len - 5) / (_LONG_SENTENCE_THRESHOLD - 5)))

        combined = word_score * 0.5 + sent_score * 0.5

        if combined < 0.33:
            level = "low"
        elif combined < 0.66:
            level = "medium"
        else:
            level = "high"

        return level, round(combined, 3)

    def _compute_semantic_score(self, r: SemanticResult) -> float:
        """Compute composite semantic score (0–100)."""
        components: List[float] = []

        # Topic relevance (has topics = good)
        if r.topics:
            components.append(min(30.0, len(r.topics) * 6.0))

        # Intent clarity
        components.append(r.intent_confidence * 25.0)

        # Sentiment strength (stronger = more engaging)
        components.append(abs(r.sentiment_score) * 15.0)

        # Context relevance (specific > general)
        components.append(10.0 if r.context != "general" else 5.0)

        # Entity richness
        components.append(min(10.0, len(r.entities) * 2.0))

        # Word count bonus (50–500 words ideal)
        if 10 <= r.word_count <= 500:
            components.append(10.0)
        elif r.word_count > 0:
            components.append(5.0)

        return round(sum(components), 2)

    def _compute_confidence(self, r: SemanticResult) -> float:
        """Compute overall analysis confidence."""
        signals = []

        if r.topics:
            signals.append(0.8)
        if r.intent != "unknown":
            signals.append(r.intent_confidence)
        if r.sentiment != "neutral":
            signals.append(0.7)
        if r.context != "general":
            signals.append(0.75)
        if r.entities:
            signals.append(0.7)
        if r.word_count >= 3:
            signals.append(0.6)

        if not signals:
            return 0.0

        return round(sum(signals) / len(signals), 3)

    def _publish_event(self, result: SemanticResult) -> None:
        """Publish analysis completion event to the global EventBus."""
        try:
            from layers.shared.event_bus.event_bus import EventBus
            bus = EventBus()
            bus.publish(Event(
                event_type=EventType.TOPIC_SCORED,
                source="layer03.content_understanding.semantic_analyzer",
                data={
                    "topic": result.topic,
                    "intent": result.intent,
                    "sentiment": result.sentiment,
                    "context": result.context,
                    "semantic_score": result.semantic_score,
                    "confidence": result.confidence,
                },
            ))
        except Exception:
            pass  # Never break analysis due to event publishing
