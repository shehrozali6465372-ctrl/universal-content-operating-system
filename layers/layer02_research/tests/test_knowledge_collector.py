"""
Tests for Knowledge Collector Module
Layer 2: Research Engine — Module 5

Run: python -m pytest layers/layer02_research/tests/test_knowledge_collector.py -v
"""

import pytest
from datetime import datetime, timezone, timedelta

from layers.layer02_research.shared.confidence_engine import ConfidenceEngine, ConfidenceResult
from layers.layer02_research.modules.knowledge_collector.knowledge_entry import KnowledgeEntry
from layers.layer02_research.modules.knowledge_collector.source_registry import SourceRegistry
from layers.layer02_research.modules.knowledge_collector.content_cleaner import ContentCleaner
from layers.layer02_research.modules.knowledge_collector.deduplicator import Deduplicator
from layers.layer02_research.modules.knowledge_collector.metadata_extractor import MetadataExtractor
from layers.layer02_research.modules.knowledge_collector.cache_manager import KnowledgeCache
from layers.layer02_research.modules.knowledge_collector.knowledge_collector_manager import KnowledgeCollectorManager
from layers.layer02_research.modules.knowledge_collector.exceptions import (
    EntryNotFoundError,
)


# ═══════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════

@pytest.fixture
def manager(tmp_path):
    return KnowledgeCollectorManager(storage_path=str(tmp_path / "kb.json"))


@pytest.fixture
def manager_with_entries(manager):
    """Manager with pre-populated knowledge entries."""
    entries = [
        ("AI Jobs Boom", "AI is transforming the job market rapidly", "tech_news", "ai"),
        ("Crypto Update", "Bitcoin reaches new highs in 2026", "finance_daily", "finance"),
        ("Python Tips", "10 Python tips for beginners", "code_blog", "technology"),
        ("Health News", "New study on mental health benefits", "health_org", "health"),
        ("Marketing Guide", "Social media marketing strategies 2026", "marketing_hub", "business"),
    ]
    for title, content_data, source, cat in entries:
        manager.collect(
            title=title, content=content_data, source=source, category=cat,
        )
    return manager


# ═══════════════════════════════════════════
# Test 1: Confidence Engine (Shared)
# ═══════════════════════════════════════════

class TestConfidenceEngine:
    def test_calculate_basic(self):
        ce = ConfidenceEngine()
        result = ce.calculate({"data_quality": 0.8, "freshness": 0.7})
        assert result.confidence > 0
        assert result.risk_level in ConfidenceResult.RISK_LEVELS

    def test_calculate_high_confidence(self):
        ce = ConfidenceEngine()
        result = ce.calculate({
            "data_quality": 0.95, "source_reliability": 0.9,
            "sample_size": 0.8, "consistency": 0.85,
            "freshness": 0.9, "diversity": 0.8, "corroboration": 0.9,
        })
        assert result.confidence >= 0.8
        assert result.risk_level in ("VERY_LOW", "LOW")

    def test_calculate_low_confidence(self):
        ce = ConfidenceEngine()
        result = ce.calculate({"data_quality": 0.1, "freshness": 0.1})
        assert result.confidence < 0.5
        assert result.risk_level in ("HIGH", "CRITICAL")

    def test_calculate_with_evidence(self):
        ce = ConfidenceEngine()
        result = ce.calculate(
            {"data_quality": 0.8},
            evidence=["Trend score high", "Multiple sources"],
        )
        assert len(result.evidence) == 2

    def test_calculate_risk_override(self):
        ce = ConfidenceEngine()
        result = ce.calculate({"data_quality": 0.9}, risk_override="LOW")
        assert result.risk_level == "LOW"

    def test_aggregate(self):
        ce = ConfidenceEngine()
        r1 = ConfidenceResult(confidence=0.8, risk_level="LOW")
        r2 = ConfidenceResult(confidence=0.6, risk_level="MEDIUM")
        agg = ce.aggregate([r1, r2])
        assert 0.6 <= agg.confidence <= 0.8

    def test_aggregate_empty(self):
        ce = ConfidenceEngine()
        agg = ce.aggregate([])
        assert agg.confidence == 0.0
        assert agg.risk_level == "CRITICAL"

    def test_from_evidence(self):
        ce = ConfidenceEngine()
        result = ce.from_evidence(["Evidence 1", "Evidence 2", "Evidence 3", "Evidence 4"])
        assert result.confidence > 0.5
        assert len(result.evidence) == 4

    def test_from_evidence_empty(self):
        ce = ConfidenceEngine()
        result = ce.from_evidence([])
        assert result.confidence < 0.2

    def test_compare(self):
        ce = ConfidenceEngine()
        a = ConfidenceResult(confidence=0.8)
        b = ConfidenceResult(confidence=0.6)
        assert ce.compare(a, b) == "A"
        assert ce.compare(b, a) == "B"
        assert ce.compare(a, ConfidenceResult(confidence=0.8)) == "EQUAL"

    def test_is_trustworthy(self):
        r = ConfidenceResult(confidence=0.8, risk_level="LOW")
        assert r.is_trustworthy() is True
        r2 = ConfidenceResult(confidence=0.3, risk_level="HIGH")
        assert r2.is_trustworthy() is False

    def test_result_to_dict(self):
        r = ConfidenceResult(confidence=0.9, reasons=["strong data"], evidence=["ev1"])
        d = r.to_dict()
        assert d["confidence"] == 0.9
        assert "strong data" in d["reasons"]

    def test_result_add_reason_and_evidence(self):
        r = ConfidenceResult()
        r.add_reason("reason1")
        r.add_evidence("ev1")
        assert "reason1" in r.reasons
        assert "ev1" in r.evidence

    def test_result_str(self):
        r = ConfidenceResult(confidence=0.85, risk_level="LOW")
        s = str(r)
        assert "0.85" in s


# ═══════════════════════════════════════════
# Test 2: Knowledge Entry
# ═══════════════════════════════════════════

class TestKnowledgeEntry:
    def test_create_entry(self):
        e = KnowledgeEntry(title="Test", content="Some content here")
        assert e.title == "Test"
        assert e.word_count == 3
        assert e.status == "active"

    def test_composite_score(self):
        e = KnowledgeEntry("T", credibility_score=8.0, freshness_score=7.0, relevance_score=9.0)
        assert e.composite_score > 0

    def test_is_expired(self):
        e = KnowledgeEntry("T", expires_in_hours=0)
        assert e.is_expired() is True

    def test_not_expired(self):
        e = KnowledgeEntry("T", expires_in_hours=100)
        assert e.is_expired() is False

    def test_is_trustworthy(self):
        e = KnowledgeEntry("T", credibility_score=7.0)
        assert e.is_trustworthy() is True

    def test_not_trustworthy_low_cred(self):
        e = KnowledgeEntry("T", credibility_score=0.3)
        assert e.is_trustworthy() is False

    def test_not_trustworthy_duplicate(self):
        e = KnowledgeEntry("T", credibility_score=8.0)
        e.is_duplicate = True
        assert e.is_trustworthy() is False

    def test_to_dict(self):
        e = KnowledgeEntry("T", source="web", category="ai")
        d = e.to_dict()
        assert d["title"] == "T"
        assert d["source"] == "web"

    def test_from_dict(self):
        d = {"title": "R", "source": "api", "content": "hello world"}
        e = KnowledgeEntry.from_dict(d)
        assert e.title == "R"
        assert e.source == "api"

    def test_from_dict_preserves_id(self):
        d = {"title": "X", "entry_id": "custom_id", "content": "test"}
        e = KnowledgeEntry.from_dict(d)
        assert e.entry_id == "custom_id"

    def test_content_hash(self):
        e1 = KnowledgeEntry("T", content="same content")
        e2 = KnowledgeEntry("T", content="same content")
        assert e1.content_hash == e2.content_hash

    def test_different_content_different_hash(self):
        e1 = KnowledgeEntry("T", content="content A")
        e2 = KnowledgeEntry("T", content="content B")
        assert e1.content_hash != e2.content_hash

    def test_get_age_hours(self):
        e = KnowledgeEntry("T")
        age = e.get_age_hours()
        assert age >= 0


# ═══════════════════════════════════════════
# Test 3: Source Registry
# ═══════════════════════════════════════════

class TestSourceRegistry:
    def test_register_source(self):
        sr = SourceRegistry()
        src = sr.register("TechCrunch", source_type="web", reliability=0.9)
        assert src.name == "TechCrunch"
        assert src.reliability == 0.9

    def test_unregister(self):
        sr = SourceRegistry()
        src = sr.register("Temp")
        assert sr.unregister(src.source_id) is True
        assert sr.get(src.source_id) is None

    def test_get_by_name(self):
        sr = SourceRegistry()
        sr.register("MySource")
        found = sr.get_by_name("mysource")
        assert found is not None

    def test_list_sources(self):
        sr = SourceRegistry()
        sr.register("A", source_type="web")
        sr.register("B", source_type="rss")
        assert len(sr.list_sources()) == 2

    def test_list_by_type(self):
        sr = SourceRegistry()
        sr.register("A", source_type="web")
        sr.register("B", source_type="rss")
        sr.register("C", source_type="web")
        assert len(sr.list_sources(source_type="web")) == 2

    def test_get_top_sources(self):
        sr = SourceRegistry()
        sr.register("Low", reliability=0.3)
        sr.register("High", reliability=0.95)
        top = sr.get_top_sources(1)
        assert top[0].name == "High"

    def test_deactivate_activate(self):
        sr = SourceRegistry()
        src = sr.register("Test")
        assert sr.deactivate(src.source_id) is True
        assert len(sr.list_sources(active_only=True)) == 0
        assert sr.activate(src.source_id) is True
        assert len(sr.list_sources(active_only=True)) == 1

    def test_health_report(self):
        sr = SourceRegistry()
        sr.register("A")
        sr.register("B")
        report = sr.health_report()
        assert len(report) == 2

    def test_get_by_category(self):
        sr = SourceRegistry()
        sr.register("A", category="ai")
        sr.register("B", category="finance")
        ai_sources = sr.get_by_category("ai")
        assert len(ai_sources) == 1

    def test_source_health(self):
        sr = SourceRegistry()
        src = sr.register("Test")
        src.fetch_count = 10
        src.error_count = 1
        h = src.health()
        assert h["success_rate"] == 0.9


# ═══════════════════════════════════════════
# Test 4: Content Cleaner
# ═══════════════════════════════════════════

class TestContentCleaner:
    def test_clean_html(self):
        result = ContentCleaner.clean_html("<p>Hello <b>world</b></p>")
        assert "Hello" in result
        assert "<p>" not in result

    def test_clean_html_entities(self):
        result = ContentCleaner.clean_html("A &amp; B &lt; C")
        assert "&amp;" not in result
        assert "A & B" in result

    def test_normalize_whitespace(self):
        result = ContentCleaner.normalize_whitespace("  Hello   world  ")
        assert result == "Hello world"

    def test_clean_full(self):
        result = ContentCleaner.clean("<div>  Hello   world  </div>")
        assert "Hello world" in result
        assert "<div>" not in result

    def test_truncate(self):
        long_text = " ".join(["word"] * 100)
        result = ContentCleaner.truncate(long_text, max_words=10)
        assert len(result.split()) <= 11  # 10 words + "..."

    def test_truncate_short(self):
        short = "Hello world"
        assert ContentCleaner.truncate(short, 10) == short

    def test_extractive_summary(self):
        text = "First sentence. Second sentence. Third sentence. Fourth."
        summary = ContentCleaner.extractive_summary(text, sentence_count=2)
        assert "First" in summary
        assert "Second" in summary

    def test_detect_language_english(self):
        assert ContentCleaner.detect_language("The quick brown fox jumps over the lazy dog") == "en"

    def test_detect_language_empty(self):
        assert ContentCleaner.detect_language("") == "unknown"

    def test_extract_urls(self):
        text = "Visit https://example.com and http://test.org"
        urls = ContentCleaner.extract_urls(text)
        assert len(urls) == 2

    def test_extract_hashtags(self):
        text = "Great post #AI #Python #Coding"
        tags = ContentCleaner.extract_hashtags(text)
        assert "#AI" in tags

    def test_extract_mentions(self):
        text = "Thanks @user1 and @user2"
        mentions = ContentCleaner.extract_mentions(text)
        assert "@user1" in mentions

    def test_remove_special_chars(self):
        text = "Hello! @World# $%^&*()"
        result = ContentCleaner.remove_special_chars(text, keep_basic=False)
        assert "!" not in result or "$" not in result


# ═══════════════════════════════════════════
# Test 5: Deduplicator
# ═══════════════════════════════════════════

class TestDeduplicator:
    def test_exact_match(self):
        dd = Deduplicator()
        e1 = KnowledgeEntry("Same Title", content="identical content here")
        e2 = KnowledgeEntry("Same Title", content="identical content here")
        dd.register(e1)
        dup = dd.check_exact(e2)
        assert dup is not None

    def test_no_match(self):
        dd = Deduplicator()
        e1 = KnowledgeEntry("T", content="content A")
        e2 = KnowledgeEntry("T2", content="content B completely different")
        dd.register(e1)
        assert dd.check_exact(e2) is None

    def test_find_duplicates(self):
        dd = Deduplicator()
        e1 = KnowledgeEntry("Same", content="same content")
        e2 = KnowledgeEntry("Same", content="same content")
        e3 = KnowledgeEntry("Different", content="different content here xyz")
        dups = dd.find_duplicates([e1, e2, e3])
        assert len(dups) == 1

    def test_mark_duplicates(self):
        dd = Deduplicator()
        e1 = KnowledgeEntry("Same", content="same content")
        e2 = KnowledgeEntry("Same", content="same content")
        count = dd.mark_duplicates([e1, e2])
        assert count == 1
        assert e2.is_duplicate is True
        assert e2.duplicate_of == e1.entry_id

    def test_similarity_score(self):
        dd = Deduplicator()
        score = dd.similarity_score("hello world foo baz", "hello world bar baz")
        assert score >= 0.5

    def test_similarity_score_empty(self):
        dd = Deduplicator()
        assert dd.similarity_score("", "hello") == 0.0
        assert dd.similarity_score("", "") == 0.0

    def test_find_similar(self):
        dd = Deduplicator(similarity_threshold=0.3)
        target = KnowledgeEntry("T", content="AI jobs are booming in technology sector")
        similar = KnowledgeEntry("S", content="AI jobs are growing in the tech sector rapidly")
        different = KnowledgeEntry("D", content="Cooking recipes for beginners on a budget")
        results = dd.find_similar(target, [similar, different])
        assert len(results) >= 1

    def test_fuzzy_dedup(self):
        dd = Deduplicator(similarity_threshold=0.8)
        e1 = KnowledgeEntry("T1", content="exact duplicate of this content")
        e2 = KnowledgeEntry("T2", content="exact duplicate of this content")
        e3 = KnowledgeEntry("T3", content="completely different text here")
        count = dd.fuzzy_dedup([e1, e2, e3])
        assert count == 1

    def test_get_stats(self):
        dd = Deduplicator()
        e = KnowledgeEntry("T", content="test")
        dd.register(e)
        stats = dd.get_stats()
        assert stats["total_hashes_indexed"] == 1

    def test_clear(self):
        dd = Deduplicator()
        e = KnowledgeEntry("T", content="test")
        dd.register(e)
        dd.clear()
        assert dd.get_stats()["total_hashes_indexed"] == 0


# ═══════════════════════════════════════════
# Test 6: Metadata Extractor
# ═══════════════════════════════════════════

class TestMetadataExtractor:
    def test_extract_keywords(self):
        me = MetadataExtractor()
        keywords = me.extract_keywords("AI is transforming technology business machine learning algorithms")
        assert len(keywords) > 0

    def test_extract_keywords_stop_words_filtered(self):
        me = MetadataExtractor()
        keywords = me.extract_keywords("the the the is is is AI python coding")
        kw_names = [kw[0] for kw in keywords]
        assert "the" not in kw_names
        assert "is" not in kw_names

    def test_extract_entities(self):
        me = MetadataExtractor()
        text = "Contact us at test@example.com for more info. Price is $99.99"
        entities = me.extract_entities(text)
        assert "email" in entities
        assert "money" in entities

    def test_detect_category_technology(self):
        me = MetadataExtractor()
        cat = me.detect_category("AI software programming algorithm machine learning")
        assert cat == "technology"

    def test_detect_category_finance(self):
        me = MetadataExtractor()
        cat = me.detect_category("stock market trading investment profit revenue")
        assert cat == "finance"

    def test_detect_category_general(self):
        me = MetadataExtractor()
        cat = me.detect_category("random text with no category signals")
        assert cat == "general"

    def test_detect_sentiment_positive(self):
        me = MetadataExtractor()
        assert me.detect_sentiment("This is a great and amazing article") == "positive"

    def test_detect_sentiment_negative(self):
        me = MetadataExtractor()
        assert me.detect_sentiment("This is a terrible failure and loss") == "negative"

    def test_detect_sentiment_neutral(self):
        me = MetadataExtractor()
        assert me.detect_sentiment("The weather is cloudy today") == "neutral"

    def test_extract_all(self):
        me = MetadataExtractor()
        result = me.extract_all("AI technology software coding", title="Tech Article")
        assert "keywords" in result
        assert "category" in result
        assert "sentiment" in result
        assert "word_count" in result


# ═══════════════════════════════════════════
# Test 7: Cache Manager
# ═══════════════════════════════════════════

class TestCacheManager:
    def test_put_and_get(self):
        cache = KnowledgeCache(max_size=100)
        cache.put("key1", {"data": "value"})
        result = cache.get("key1")
        assert result == {"data": "value"}

    def test_get_miss(self):
        cache = KnowledgeCache()
        assert cache.get("missing") is None

    def test_lru_eviction(self):
        cache = KnowledgeCache(max_size=2)
        cache.put("a", {"v": 1})
        cache.put("b", {"v": 2})
        cache.put("c", {"v": 3})
        assert cache.size() == 2
        assert cache.get("a") is None  # Evicted

    def test_lru_access_keeps_alive(self):
        cache = KnowledgeCache(max_size=2)
        cache.put("a", {"v": 1})
        cache.put("b", {"v": 2})
        cache.get("a")  # Access "a" → moves to end
        cache.put("c", {"v": 3})
        assert cache.get("a") is not None  # Still there
        assert cache.get("b") is None  # "b" evicted

    def test_delete(self):
        cache = KnowledgeCache()
        cache.put("key", {"v": 1})
        assert cache.delete("key") is True
        assert cache.get("key") is None

    def test_exists(self):
        cache = KnowledgeCache()
        cache.put("key", {"v": 1})
        assert cache.exists("key") is True
        assert cache.exists("nope") is False

    def test_cleanup_expired(self):
        cache = KnowledgeCache(default_ttl=0)
        cache.put("a", {"v": 1})
        removed = cache.cleanup()
        assert removed == 1

    def test_stats(self):
        cache = KnowledgeCache()
        cache.put("a", {"v": 1})
        cache.get("a")
        cache.get("missing")
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5

    def test_clear(self):
        cache = KnowledgeCache()
        cache.put("a", {"v": 1})
        cache.clear()
        assert cache.size() == 0


# ═══════════════════════════════════════════
# Test 8: Manager CRUD
# ═══════════════════════════════════════════

class TestManagerCRUD:
    def test_collect(self, manager):
        entry = manager.collect(title="Test", content="Hello world", source="web")
        assert entry.title == "Test"
        assert entry.status == "active"

    def test_collect_with_pipeline(self, manager):
        entry = manager.collect(
            title="<b>AI News</b>", content="  Great article about AI  ",
            source="web", category="technology",
        )
        assert "<b>" not in entry.title
        assert entry.word_count > 0

    def test_get_entry(self, manager):
        e = manager.collect(title="GetMe", content="content")
        found = manager.get_entry(e.entry_id)
        assert found.title == "GetMe"

    def test_get_not_found(self, manager):
        with pytest.raises(EntryNotFoundError):
            manager.get_entry("ghost")

    def test_update_entry(self, manager):
        e = manager.collect(title="Update", content="old content")
        manager.update_entry(e.entry_id, title="Updated")
        updated = manager.get_entry(e.entry_id)
        assert updated.title == "Updated"

    def test_delete_entry(self, manager):
        e = manager.collect(title="Delete", content="content")
        assert manager.delete_entry(e.entry_id) is True

    def test_delete_not_found(self, manager):
        with pytest.raises(EntryNotFoundError):
            manager.delete_entry("ghost")

    def test_list_entries(self, manager):
        manager.collect(title="A", content="content a", source="web")
        manager.collect(title="B", content="content b", source="rss")
        assert len(manager.list_entries()) == 2

    def test_list_by_source(self, manager):
        manager.collect(title="A", content="c", source="web")
        manager.collect(title="B", content="c", source="rss")
        assert len(manager.list_entries(source="web")) == 1

    def test_list_by_category(self, manager):
        manager.collect(title="A", content="c", category="ai")
        manager.collect(title="B", content="c", category="finance")
        assert len(manager.list_entries(category="ai")) == 1


# ═══════════════════════════════════════════
# Test 9: Manager Intelligence
# ═══════════════════════════════════════════

class TestManagerIntelligence:
    def test_deduplicate(self, manager):
        manager.collect(title="Same", content="identical content here")
        manager.collect(title="Same", content="identical content here")
        count = manager.deduplicate()
        assert count >= 1

    def test_get_top_entries(self, manager_with_entries):
        top = manager_with_entries.get_top_entries(3)
        assert len(top) == 3
        assert top[0].composite_score >= top[-1].composite_score

    def test_search_by_keyword(self, manager_with_entries):
        results = manager_with_entries.search_by_keyword("AI")
        assert len(results) > 0

    def test_search_by_category(self, manager_with_entries):
        results = manager_with_entries.search_by_category("technology")
        assert len(results) > 0

    def test_cleanup_expired(self, manager):
        e = manager.collect(title="Exp", content="content")
        e.expires_at = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
        removed = manager.cleanup_expired()
        assert removed >= 1

    def test_build_evidence(self, manager_with_entries):
        result = manager_with_entries.build_evidence()
        assert result.confidence > 0
        assert len(result.evidence) > 0

    def test_build_evidence_empty(self, manager):
        result = manager.build_evidence()
        assert result.confidence < 0.2

    def test_cache_integration(self, manager):
        e = manager.collect(title="Cache", content="content test")
        # First get → from storage
        manager.get_entry(e.entry_id)
        # Second get → from cache
        cached = manager.get_entry(e.entry_id)
        assert cached.title == "Cache"


# ═══════════════════════════════════════════
# Test 10: Persistence & Health
# ═══════════════════════════════════════════

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        path = tmp_path / "persist.json"
        m1 = KnowledgeCollectorManager(storage_path=str(path))
        m1.collect(title="Persist", content="data")
        m2 = KnowledgeCollectorManager(storage_path=str(path))
        assert len(m2.list_entries()) == 1

    def test_no_storage(self):
        m = KnowledgeCollectorManager()
        m.collect(title="NoStorage", content="data")
        assert len(m.list_entries()) == 1

    def test_corrupt_file(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid json")
        m = KnowledgeCollectorManager(storage_path=str(path))
        assert len(m.list_entries()) == 0

    def test_health_check_empty(self, manager):
        h = manager.health_check()
        assert h["total_entries"] == 0
        assert h["sources_registered"] == 0

    def test_health_check_with_data(self, manager_with_entries):
        h = manager_with_entries.health_check()
        assert h["total_entries"] == 5
        assert h["active"] == 5


# ═══════════════════════════════════════════
# Test 11: Edge Cases
# ═══════════════════════════════════════════

class TestEdgeCases:
    def test_collect_empty_content(self, manager):
        e = manager.collect(title="Empty", content="")
        assert e.word_count == 0

    def test_collect_large_content(self, manager):
        large = "word " * 10000
        e = manager.collect(title="Large", content=large)
        assert e.word_count == 10000

    def test_many_entries_performance(self, manager):
        for i in range(100):
            manager.collect(title=f"Entry_{i}", content=f"Content for entry {i}", source="test")
        assert len(manager.list_entries()) == 100

    def test_concurrent_access(self, manager):
        import threading
        errors = []

        def collect(i):
            try:
                manager.collect(title=f"Thread_{i}", content=f"Content {i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=collect, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(manager.list_entries()) == 20

    def test_content_hash_deterministic(self):
        e1 = KnowledgeEntry("T", content="deterministic content")
        e2 = KnowledgeEntry("T", content="deterministic content")
        assert e1.content_hash == e2.content_hash

    def test_confidence_engine_custom_weights(self):
        ce = ConfidenceEngine(weights={"data_quality": 1.0})
        result = ce.calculate({"data_quality": 0.9})
        assert result.confidence >= 0.8
