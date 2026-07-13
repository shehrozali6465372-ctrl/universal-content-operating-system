"""
Tests for Trend Discovery Module
Layer 2: Research Engine — Module 1

Run: python -m pytest layers/layer02_research/tests/test_trend_discovery.py -v
"""

import json
import pytest
from datetime import datetime, timezone, timedelta

from layers.layer02_research.modules.trend_discovery.trend_manager import TrendManager, TrendSource
from layers.layer02_research.modules.trend_discovery.trend_entry import TrendEntry
from layers.layer02_research.modules.trend_discovery.exceptions import (
    TrendSourceError, TrendNotFoundError, InvalidSourceError,
)


@pytest.fixture
def tm(tmp_path):
    return TrendManager(storage_path=str(tmp_path / "trends.json"))


@pytest.fixture
def tm_with_source(tm):
    """TrendManager with a mock source registered."""
    def mock_fetch(category="general", limit=20):
        return [
            TrendEntry("AI in Finance", category="finance", source="mock",
                       virality_score=8.0, relevance_score=7.5, freshness_score=9.0,
                       volume=5000, direction="rising"),
            TrendEntry("Crypto News", category="finance", source="mock",
                       virality_score=6.0, relevance_score=5.0, freshness_score=7.0,
                       volume=3000, direction="stable"),
            TrendEntry("React Tips", category="tech", source="mock",
                       virality_score=7.0, relevance_score=8.0, freshness_score=6.0,
                       volume=4000, direction="rising"),
        ]

    tm.register_source("mock_source", fetch_fn=mock_fetch, reliability=0.9)
    return tm


# ── Test 1: Trend Entry ────────────────────

class TestTrendEntry:
    def test_create_trend(self):
        t = TrendEntry("AI Trends", category="tech", source="manual",
                       virality_score=7.0, relevance_score=8.0, freshness_score=6.0)
        assert t.keyword == "AI Trends"
        assert t.category == "tech"
        assert t.source == "manual"
        assert t.composite_score > 0

    def test_composite_score_calculation(self):
        t = TrendEntry("Test", virality_score=10.0, relevance_score=10.0, freshness_score=10.0)
        assert t.composite_score == 10.0

    def test_score_clamping(self):
        t = TrendEntry("Test", virality_score=15.0, relevance_score=-5.0)
        assert t.virality_score == 10.0
        assert t.relevance_score == 0.0

    def test_to_dict(self):
        t = TrendEntry("Test", category="cat", source="src")
        d = t.to_dict()
        assert d["keyword"] == "Test"
        assert d["category"] == "cat"
        assert "composite_score" in d
        assert "discovered_at" in d

    def test_from_dict(self):
        d = {"keyword": "K", "category": "C", "source": "S",
             "virality_score": 5.0, "relevance_score": 6.0, "freshness_score": 7.0}
        t = TrendEntry.from_dict(d)
        assert t.keyword == "K"
        assert t.virality_score == 5.0

    def test_direction_validation(self):
        t = TrendEntry("Test", direction="invalid")
        assert t.direction == "stable"

    def test_related_keywords(self):
        t = TrendEntry("Test", related_keywords=["AI", "ML", "DL"])
        assert len(t.related_keywords) == 3

    def test_expiry(self):
        t = TrendEntry("Test", expires_in_hours=0)
        assert t.is_expired() is True


# ── Test 2: Add / Get / Delete ─────────────

class TestTrendCRUD:
    def test_add_trend(self, tm):
        t = tm.add_trend("AI Trends", category="tech")
        assert t.keyword == "AI Trends"
        assert tm.exists("AI Trends")

    def test_get_trend(self, tm):
        t = tm.add_trend("Test", category="tech")
        found = tm.get_trend(t.trend_id)
        assert found.keyword == "Test"

    def test_get_nonexistent_raises(self, tm):
        with pytest.raises(TrendNotFoundError):
            tm.get_trend("no_such_trend")

    def test_delete_trend(self, tm):
        t = tm.add_trend("Delete Me")
        assert tm.delete_trend(t.trend_id) is True
        assert not tm.exists("Delete Me")

    def test_delete_nonexistent_raises(self, tm):
        with pytest.raises(TrendNotFoundError):
            tm.delete_trend("nope")

    def test_exists(self, tm):
        tm.add_trend("Exists")
        assert tm.exists("Exists") is True
        assert tm.exists("Not Here") is False


# ── Test 3: Source Management ───────────────

class TestSources:
    def test_register_source(self, tm):
        source = tm.register_source("test_src", reliability=0.9)
        assert source.name == "test_src"
        assert source.reliability == 0.9

    def test_unregister_source(self, tm):
        tm.register_source("to_remove")
        assert tm.unregister_source("to_remove") is True
        assert tm.unregister_source("nonexistent") is False

    def test_list_sources(self, tm):
        tm.register_source("s1")
        tm.register_source("s2")
        sources = tm.list_sources()
        assert len(sources) == 2

    def test_source_health(self, tm):
        tm.register_source("health_src")
        sources = tm.list_sources()
        assert sources[0]["name"] == "health_src"
        assert sources[0]["fetch_count"] == 0


# ── Test 4: Discovery ──────────────────────

class TestDiscovery:
    def test_discover_from_source(self, tm_with_source):
        trends = tm_with_source.discover()
        assert len(trends) == 3

    def test_discover_all_sources(self, tm_with_source):
        trends = tm_with_source.discover()
        assert len(trends) == 3

    def test_discover_stores_trends(self, tm_with_source):
        tm_with_source.discover()
        stats = tm_with_source.stats()
        assert stats["total_trends"] == 3

    def test_discover_no_sources(self, tm):
        trends = tm.discover()
        assert len(trends) == 0

    def test_discover_source_error(self, tm):
        def failing_fetch(**kwargs):
            raise RuntimeError("API down")

        tm.register_source("failing", fetch_fn=failing_fetch)
        trends = tm.discover()
        assert len(trends) == 0  # Should handle error gracefully


# ── Test 5: Queries & Filtering ────────────

class TestQueries:
    def test_get_trends_filtered(self, tm_with_source):
        tm_with_source.discover()
        finance = tm_with_source.get_trends(category="finance")
        assert len(finance) == 2
        assert all(t["category"] == "finance" for t in finance)

    def test_top_trends(self, tm_with_source):
        tm_with_source.discover()
        top = tm_with_source.top_trends(category="finance", limit=2)
        assert len(top) == 2
        assert top[0]["composite_score"] >= top[1]["composite_score"]

    def test_rising_trends(self, tm_with_source):
        tm_with_source.discover()
        rising = tm_with_source.rising_trends(category="tech")
        assert len(rising) > 0
        assert all(t["direction"] == "rising" for t in rising)

    def test_min_score_filter(self, tm_with_source):
        tm_with_source.discover()
        high = tm_with_source.get_trends(min_score=7.0)
        assert all(t["composite_score"] >= 7.0 for t in high)

    def test_search(self, tm_with_source):
        tm_with_source.discover()
        results = tm_with_source.search("AI")
        assert len(results) >= 1
        assert any("AI" in t["keyword"] for t in results)

    def test_search_by_related(self, tm):
        tm.add_trend("Finance Tips", related_keywords=["stock market", "investing"])
        results = tm.add_trend("Investing 101", related_keywords=["stocks"])
        results = tm.search("stock market")
        assert len(results) >= 1


# ── Test 6: Comparison ──────────────────────

class TestComparison:
    def test_compare_snapshots(self, tm_with_source):
        tm_with_source.discover()
        snap_a = tm_with_source.get_trends()

        tm_with_source.add_trend("New Trend", source="manual")
        snap_b = tm_with_source.get_trends()

        diff = tm_with_source.compare_snapshots(snap_a, snap_b)
        assert len(diff["new"]) == 1
        assert len(diff["removed"]) == 0
        assert len(diff["common"]) == 3


# ── Test 7: Expiration ──────────────────────

class TestExpiration:
    def test_cleanup_expired(self, tm):
        tm.add_trend("Expired", expires_in_hours=0)
        tm.add_trend("Fresh", expires_in_hours=72)
        removed = tm.cleanup_expired()
        assert removed == 1
        assert not tm.exists("Expired")
        assert tm.exists("Fresh")

    def test_expired_excluded_by_default(self, tm):
        tm.add_trend("Expired", expires_in_hours=0)
        tm.add_trend("Fresh", expires_in_hours=72)
        trends = tm.get_trends()
        assert len(trends) == 1
        assert trends[0]["keyword"] == "Fresh"

    def test_include_expired(self, tm):
        tm.add_trend("Expired", expires_in_hours=0)
        trends = tm.get_trends(include_expired=True)
        assert len(trends) == 1


# ── Test 8: Persistence ────────────────────

class TestPersistence:
    def test_save_and_load(self, tmp_path):
        path = str(tmp_path / "trends.json")
        tm1 = TrendManager(storage_path=path)
        tm1.add_trend("Persistent Trend", category="finance")
        tm1.save()

        tm2 = TrendManager(storage_path=path)
        assert tm2.exists("Persistent Trend")

    def test_load_nonexistent(self, tmp_path):
        tm = TrendManager(storage_path=str(tmp_path / "nope.json"))
        assert tm.stats()["total_trends"] == 0

    def test_save_custom_path(self, tmp_path):
        tm = TrendManager()
        tm.add_trend("Custom")
        tm.save(str(tmp_path / "custom.json"))
        assert (tmp_path / "custom.json").exists()


# ── Test 9: History ────────────────────────

class TestHistory:
    def test_history_recorded(self, tm):
        tm.add_trend("Historical")
        history = tm.get_history()
        assert len(history) >= 1
        assert history[-1]["action"] == "add"

    def test_history_limit(self, tm):
        for i in range(10):
            tm.add_trend(f"Trend {i}")
        history = tm.get_history(limit=3)
        assert len(history) == 3


# ── Test 10: Stats ─────────────────────────

class TestStats:
    def test_stats(self, tm_with_source):
        tm_with_source.discover()
        stats = tm_with_source.stats()
        assert stats["total_trends"] == 3
        assert stats["active"] == 3
        assert stats["expired"] == 0
        assert "finance" in stats["categories"]
        assert "mock" in stats["sources"]

    def test_stats_empty(self, tm):
        stats = tm.stats()
        assert stats["total_trends"] == 0


# ── Test 11: Health Check ──────────────────

class TestHealthCheck:
    def test_health_no_trends(self, tm):
        report = tm.health_check()
        assert report["overall"] == "WARN"

    def test_health_with_data(self, tm_with_source):
        tm_with_source.discover()
        report = tm_with_source.health_check()
        assert report["overall"] == "PASS"
        assert "trends" in report["checks"]
        assert "sources" in report["checks"]

    def test_health_expired_warns(self, tm):
        tm.add_trend("Expired", expires_in_hours=0)
        report = tm.health_check()
        assert report["overall"] == "WARN"
