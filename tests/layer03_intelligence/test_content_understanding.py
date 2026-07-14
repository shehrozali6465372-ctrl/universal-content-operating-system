"""Tests for Module 1: Content Understanding."""
from layers.layer03_intelligence.modules.content_understanding.topic_extractor import TopicExtractor
from layers.layer03_intelligence.modules.content_understanding.intent_detector import IntentDetector
from layers.layer03_intelligence.modules.content_understanding.entity_recognizer import EntityRecognizer
from layers.layer03_intelligence.modules.content_understanding.keyword_analyzer import KeywordAnalyzer
from layers.layer03_intelligence.modules.content_understanding.content_analyzer import ContentAnalyzer


class TestTopicExtractor:
    def setup_method(self): self.te = TopicExtractor()
    def test_extract(self):
        topics = self.te.extract("AI artificial intelligence is changing the world of technology")
        assert len(topics) > 0
        assert any(t["topic"] in ("ai", "artificial", "intelligence", "changing", "world", "technology") for t in topics)
    def test_extract_empty(self):
        assert self.te.extract("") == []
    def test_extract_stop_words_filtered(self):
        topics = self.te.extract("the the the is is are are")
        assert len(topics) == 0
    def test_multi_word(self):
        phrases = self.te.extract_multi_word("artificial intelligence is changing artificial intelligence")
        assert len(phrases) > 0
    def test_max_topics(self):
        te = TopicExtractor(max_topics=3)
        topics = te.extract("one two three four five six seven eight nine ten")
        assert len(topics) <= 3


class TestIntentDetector:
    def setup_method(self): self.id = IntentDetector()
    def test_detect_informative(self):
        r = self.id.detect("How to learn Python programming guide")
        assert r.primary_intent == "informative"
    def test_detect_promotional(self):
        r = self.id.detect("Buy now discount offer limited sale premium")
        assert r.primary_intent == "promotional"
    def test_detect_engagement(self):
        r = self.id.detect("What do you think? Share your opinion")
        assert r.primary_intent == "engagement"
    def test_detect_batch(self):
        results = self.id.detect_batch(["Buy now", "How to learn", "What do you think"])
        assert len(results) == 3
    def test_dominant_intent(self):
        r = self.id.get_dominant_intent(["Buy now", "Buy sale", "How to guide"])
        assert r.primary_intent == "promotional"
    def test_add_pattern(self):
        self.id.add_pattern("custom", ["alpha", "beta", "gamma"])
        r = self.id.detect("alpha beta gamma")
        assert "custom" in r.all_intents


class TestEntityRecognizer:
    def setup_method(self): self.er = EntityRecognizer()
    def test_recognize_person(self):
        entities = self.er.recognize("John Smith went to New York")
        types = [e.entity_type for e in entities]
        assert "person" in types
    def test_recognize_org(self):
        entities = self.er.recognize("Facebook announced new features")
        types = [e.entity_type for e in entities]
        assert "organization" in types
    def test_recognize_url(self):
        entities = self.er.recognize("Visit https://example.com for info")
        assert any(e.entity_type == "url" for e in entities)
    def test_recognize_hashtag(self):
        entities = self.er.recognize("Trending #AI #Tech")
        assert any(e.entity_type == "hashtag" for e in entities)
    def test_recognize_batch(self):
        entities = self.er.recognize("John Smith at Facebook #AI")
        assert len(entities) >= 2
    def test_get_entity_types(self):
        types = self.er.get_entity_types("Facebook and Google compete")
        assert "organization" in types
    def test_extract_all_text(self):
        texts = self.er.extract_all_text("Facebook Google Microsoft", "organization")
        assert "Facebook" in texts


class TestKeywordAnalyzer:
    def setup_method(self): self.ka = KeywordAnalyzer()
    def test_analyze(self):
        r = self.ka.analyze("AI artificial intelligence technology software data")
        assert r.score > 0
        assert len(r.primary_keywords) > 0
    def test_analyze_domain(self):
        r = self.ka.analyze("invest money stock crypto finance", "finance")
        assert r.score > 0
    def test_analyze_empty(self):
        r = self.ka.analyze("")
        assert r.score == 0
    def test_common_keywords(self):
        common = self.ka.get_common_keywords(["AI is great", "AI technology", "AI data"])
        assert len(common) > 0
    def test_add_domain(self):
        self.ka.add_domain("custom", {"test": 2.0})
        r = self.ka.analyze("test test test", "custom")
        assert r.score > 0


class TestContentAnalyzer:
    def setup_method(self): self.ca = ContentAnalyzer()
    def test_analyze(self):
        r = self.ca.analyze("AI jobs are increasing rapidly #AI @John")
        assert r.overall_score > 0
        assert len(r.topics) > 0
        assert r.intent.primary_intent != ""
    def test_analyze_empty(self):
        r = self.ca.analyze("")
        assert r.overall_score == 0
    def test_analyze_batch(self):
        results = self.ca.analyze_batch(["AI technology", "Finance invest"])
        assert len(results) == 2
    def test_compare(self):
        r = self.ca.compare("AI technology software", "AI technology data")
        assert "similarity" in r
        assert r["similarity"] > 0
    def test_to_dict(self):
        r = self.ca.analyze("AI technology")
        d = r.to_dict()
        assert "topics" in d
        assert "intent" in d
