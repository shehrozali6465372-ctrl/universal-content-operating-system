"""
Comprehensive tests for SemanticAnalyzer — Sprint 1

Covers: empty, single sentence, long article, Urdu, English,
mixed, numbers, dates, URLs, emojis, multiple intents,
ambiguous, similarity, confidence, complexity, performance.
"""
import time
from layers.layer03_intelligence.modules.content_understanding.semantic_analyzer import (
    SemanticAnalyzer, SemanticResult,
)


class TestSemanticResult:
    """Tests for the SemanticResult data model."""

    def test_default_values(self):
        r = SemanticResult()
        assert r.topic == ""
        assert r.intent == "unknown"
        assert r.sentiment == "neutral"
        assert r.confidence == 0.0
        assert r.semantic_score == 0.0

    def test_to_dict(self):
        r = SemanticResult()
        r.topic = "AI"
        r.intent = "informative"
        d = r.to_dict()
        assert d["topic"] == "AI"
        assert d["intent"] == "informative"
        assert "sentiment" in d
        assert "semantic_score" in d

    def test_repr(self):
        r = SemanticResult()
        r.topic = "test"
        r.intent = "info"
        assert "test" in repr(r)


class TestSemanticAnalyzerEmpty:
    """Tests for empty / whitespace input."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_empty_string(self):
        r = self.a.analyze("")
        assert r.topic == ""
        assert r.semantic_score == 0.0
        assert r.word_count == 0

    def test_none_like_empty(self):
        r = self.a.analyze("   ")
        assert r.topic == ""

    def test_only_punctuation(self):
        r = self.a.analyze("!!! ??? ...")
        assert r.word_count == 0


class TestSemanticAnalyzerEnglish:
    """Tests for English content."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_single_sentence(self):
        r = self.a.analyze("AI is transforming the technology industry.")
        assert r.topic != ""
        assert r.intent in ("informative", "predictive", "unknown")
        assert r.word_count > 0

    def test_long_article(self):
        text = (
            "Artificial intelligence is revolutionizing how businesses operate. "
            "Machine learning algorithms can now process vast amounts of data "
            "to generate insights that were previously impossible. Companies "
            "like Google and Microsoft are investing billions in AI research. "
            "The future of work will be fundamentally changed by automation "
            "and intelligent systems."
        )
        r = self.a.analyze(text)
        assert r.word_count >= 25
        assert r.sentence_count >= 3
        assert r.semantic_score > 0
        assert r.context in ("technology", "general")

    def test_financial_content(self):
        r = self.a.analyze("Stock market invest money crypto bitcoin profit")
        assert r.context == "finance"

    def test_health_content(self):
        r = self.a.analyze("Regular exercise improves health and wellness fitness")
        assert r.context == "health"

    def test_educational_content(self):
        r = self.a.enriched_analyze if hasattr(self.a, 'enriched_analyze') else self.a.analyze
        r = self.a.analyze("Take this course to learn new skills through training")
        assert r.context == "education"

    def test_career_content(self):
        r = self.a.analyze("Job hiring salary career interview resume employee")
        assert r.context == "career"

    def test_social_content(self):
        r = self.a.analyze("Like share follow comment community friend connect")
        assert r.context == "social"

    def test_numbers_in_text(self):
        r = self.a.analyze("Revenue grew by 25% in Q3 reaching $1.5 million")
        assert len(r.entities) > 0
        assert r.word_count > 0

    def test_dates_in_text(self):
        r = self.a.analyze("The event is scheduled for 2026-07-15 next week")
        date_entities = [e for e in r.entities if e["type"] == "date"]
        assert len(date_entities) > 0

    def test_urls_in_text(self):
        r = self.a.analyze("Visit https://example.com for more details")
        url_entities = [e for e in r.entities if e["type"] == "url"]
        assert len(url_entities) > 0

    def test_hashtags(self):
        r = self.a.analyze("Amazing post #AI #Technology #Innovation")
        hash_entities = [e for e in r.entities if e["type"] == "hashtag"]
        assert len(hash_entities) >= 2

    def test_mentions(self):
        r = self.a.analyze("Thanks @john for the insight")
        mention_entities = [e for e in r.entities if e["type"] == "mention"]
        assert len(mention_entities) >= 1

    def test_person_entities(self):
        r = self.a.analyze("John Smith announced the new product at Facebook")
        people = [e for e in r.entities if e["type"] == "person"]
        orgs = [e for e in r.entities if e["type"] == "organization"]
        assert len(people) >= 1
        assert len(orgs) >= 1

    def test_money_entities(self):
        r = self.a.analyze("The deal is worth $5,000 in initial investment")
        money = [e for e in r.entities if e["type"] == "money"]
        assert len(money) >= 1


class TestSemanticAnalyzerSentiment:
    """Tests for sentiment detection."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_positive_sentiment(self):
        r = self.a.analyze("This is amazing wonderful excellent great fantastic")
        assert r.sentiment == "positive"
        assert r.sentiment_score > 0

    def test_negative_sentiment(self):
        r = self.a.analyze("This is terrible horrible failure broken crisis")
        assert r.sentiment == "negative"
        assert r.sentiment_score < 0

    def test_neutral_sentiment(self):
        r = self.a.analyze("The report was submitted yesterday")
        assert r.sentiment == "neutral"

    def test_mixed_sentiment(self):
        r = self.a.analyze("love amazing wonderful great excellent but terrible")
        assert r.sentiment_score != 0.0


class TestSemanticAnalyzerIntent:
    """Tests for intent classification."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_predictive_intent(self):
        r = self.a.analyze("AI jobs will increase going to boom 2026 mein barhne wali hai")
        assert r.intent in ("predictive", "informative")

    def test_informative_intent(self):
        r = self.a.analyze("How to learn Python tutorial guide tips")
        assert r.intent in ("informative", "educational")

    def test_promotional_intent(self):
        r = self.a.analyze("Buy now limited discount offer sale deal free premium")
        assert r.intent == "promotional"

    def test_engagement_intent(self):
        r = self.a.analyze("What do you think? Share your opinion agree comment")
        assert r.intent == "engagement"

    def test_news_intent(self):
        r = self.a.analyze("Breaking announce launch release update report")
        assert r.intent in ("news", "informative")


class TestSemanticAnalyzerUrdu:
    """Tests for Urdu / Hinglish content."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_urdu_keywords_detected(self):
        r = self.a.analyze("یہ بہترین ٹیکنالوجی ہے technology hai")
        assert r.word_count > 0
        assert r.semantic_score >= 0

    def test_hinglish_content(self):
        r = self.a.analyze("AI ki demand bahut zyada hai aur zabardast growth ho rahi hai")
        assert r.word_count > 0
        assert r.context in ("technology", "career", "general")


class TestSemanticAnalyzerEmojis:
    """Tests for emoji handling."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_emojis_in_text(self):
        r = self.a.analyze("Great post 🔥🔥🔥 Keep it up 👍 #amazing")
        assert r.word_count > 0
        assert r.semantic_score >= 0

    def test_emoji_only(self):
        r = self.a.analyze("🔥🔥🔥👍❤️")
        assert r.word_count == 0


class TestSemanticAnalyzerAmbiguous:
    """Tests for ambiguous or edge-case text."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_single_word(self):
        r = self.a.analyze("Python")
        assert r.topic != ""
        assert r.word_count == 1

    def test_question(self):
        r = self.a.analyze("What is artificial intelligence?")
        assert r.intent in ("informative", "engagement", "unknown")

    def test_all_caps(self):
        r = self.a.analyze("BREAKING NEWS: AI TAKES OVER TECH INDUSTRY")
        assert r.semantic_score >= 0

    def test_very_long_word(self):
        r = self.a.analyze("supercalifragilisticexpialidocious")
        assert r.complexity in ("medium", "high")


class TestSemanticScore:
    """Tests for semantic score computation."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_score_range(self):
        texts = [
            "AI technology software",
            "Buy now discount",
            "Hello",
            "Amazing AI growth in technology sector with innovative solutions",
        ]
        for text in texts:
            r = self.a.analyze(text)
            assert 0.0 <= r.semantic_score <= 100.0, f"Score out of range for: {text}"

    def test_empty_has_zero_score(self):
        assert self.a.semantic_score("") == 0.0

    def test_rich_content_higher_score(self):
        s1 = self.a.semantic_score("AI")
        s2 = self.a.semantic_score(
            "Artificial intelligence is transforming technology with innovative "
            "AI solutions for career growth and education"
        )
        assert s2 >= s1


class TestSemanticSimilarity:
    """Tests for semantic similarity."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_identical_texts(self):
        s = self.a.semantic_similarity("AI technology software", "AI technology software")
        assert s == 1.0

    def test_no_overlap(self):
        s = self.a.semantic_similarity("cats dogs pets", "finance stock market")
        assert s == 0.0

    def test_partial_overlap(self):
        s = self.a.semantic_similarity("AI technology software", "AI technology data")
        assert 0.0 < s < 1.0

    def test_empty_texts(self):
        assert self.a.semantic_similarity("", "hello") == 0.0
        assert self.a.semantic_similarity("hello", "") == 0.0
        assert self.a.semantic_similarity("", "") == 0.0

    def test_case_insensitive(self):
        s = self.a.semantic_similarity("AI Technology", "ai technology")
        assert s == 1.0


class TestConfidence:
    """Tests for confidence scoring."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_rich_text_higher_confidence(self):
        c1 = self.a.analyze("the").confidence
        c2 = self.a.analyze(
            "AI jobs are increasing rapidly with positive growth in technology sector"
        ).confidence
        assert c2 >= c1

    def test_confidence_range(self):
        r = self.a.analyze("This is a test sentence about AI technology")
        assert 0.0 <= r.confidence <= 1.0

    def test_empty_has_zero_confidence(self):
        assert self.a.analyze("").confidence == 0.0


class TestComplexity:
    """Tests for complexity scoring."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_simple_text_low_complexity(self):
        r = self.a.analyze("Hi how are you doing today")
        assert r.complexity in ("low", "medium")

    def test_complex_text_higher_complexity(self):
        r = self.a.analyze(
            "The implementation of sophisticated algorithmic methodologies "
            "necessitates comprehensive understanding of computational "
            "infrastructure optimization"
        )
        assert r.complexity in ("medium", "high")

    def test_complexity_score_range(self):
        r = self.a.analyze("Some text here with various words")
        assert 0.0 <= r.complexity_score <= 1.0


class TestContext:
    """Tests for context detection."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_technology_context(self):
        assert self.a.detect_context("AI software developer code programming") == "technology"

    def test_finance_context(self):
        assert self.a.detect_context("invest money stock crypto profit") == "finance"

    def test_health_context(self):
        assert self.a.detect_context("health medical fitness wellness exercise") == "health"

    def test_education_context(self):
        assert self.a.detect_context("learn course study training knowledge") == "education"

    def test_general_context(self):
        assert self.a.detect_context("random words here") == "general"

    def test_empty_context(self):
        assert self.a.detect_context("") == "general"


class TestPublicAPI:
    """Tests for public API methods."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_analyze_returns_semantic_result(self):
        r = self.a.analyze("AI is great")
        assert isinstance(r, SemanticResult)

    def test_extract_topics(self):
        topics = self.a.extract_topics("AI technology software programming")
        assert len(topics) > 0
        assert all(isinstance(t, str) for t in topics)

    def test_detect_intent(self):
        intent = self.a.detect_intent("How to learn Python")
        assert isinstance(intent, str)
        assert intent in ("informative", "predictive", "promotional",
                          "engagement", "news", "educational",
                          "emotional", "unknown")

    def test_detect_context(self):
        ctx = self.a.detect_context("AI technology software")
        assert isinstance(ctx, str)

    def test_semantic_score(self):
        score = self.a.semantic_score("AI technology is growing")
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_semantic_similarity(self):
        sim = self.a.semantic_similarity("AI tech", "AI technology")
        assert isinstance(sim, float)
        assert 0.0 <= sim <= 1.0


class TestEventBus:
    """Tests for Event Bus integration."""

    def test_publish_events_flag(self):
        a = SemanticAnalyzer(publish_events=True)
        assert a.publish_events is True

    def test_no_publish_by_default(self):
        a = SemanticAnalyzer()
        assert a.publish_events is False

    def test_publish_does_not_break_analysis(self):
        a = SemanticAnalyzer(publish_events=True)
        # Should not raise even if EventBus has issues
        r = a.analyze("AI technology test")
        assert r.semantic_score >= 0


class TestPerformance:
    """Tests for analysis performance."""

    def setup_method(self):
        self.a = SemanticAnalyzer()

    def test_single_analysis_speed(self):
        start = time.time()
        for _ in range(100):
            self.a.analyze("AI technology is transforming the industry with innovation")
        elapsed = time.time() - start
        assert elapsed < 5.0, f"100 analyses took {elapsed:.2f}s"

    def test_similarity_speed(self):
        start = time.time()
        for _ in range(100):
            self.a.semantic_similarity("AI technology software", "AI data technology")
        elapsed = time.time() - start
        assert elapsed < 3.0, f"100 similarities took {elapsed:.2f}s"
