"""Comprehensive tests for Layer 23 — Module 7: SEO & Rich Pins Manager."""
from __future__ import annotations
import time
import pytest
import json

from layers.layer23_website_manager.seo_richpins_manager.seo_richpins_manager import (
    SEORichPinsManager, get_seo_manager,
)
from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import (
    SEOProfile, SEOAnalytics, SEOScore, ContentType,
)
from layers.layer23_website_manager.seo_richpins_manager.exceptions import (
    KeywordGenerationError, MetaGenerationError, RichPinError,
    SchemaError, SitemapError, RobotsError, SEOValidationError,
    DuplicateMetadataError, OpenGraphError, TwitterCardError,
)


# ═══════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════

class TestSEOProfile:
    def test_default(self):
        p = SEOProfile()
        assert p.profile_id is not None
        assert p.seo_score == 0.0
        assert p.is_optimized is False

    def test_with_values(self):
        p = SEOProfile(article_title="Test Article", seo_score=85.0)
        assert p.is_optimized is True

    def test_is_optimized(self):
        p = SEOProfile(seo_score=70)
        assert p.is_optimized is True
        p.seo_score = 60
        assert p.is_optimized is False

    def test_to_dict(self):
        p = SEOProfile(article_title="Test")
        d = p.to_dict()
        assert d["article_title"] == "Test"
        assert "seo_score" in d


class TestSEOAnalytics:
    def test_default(self):
        a = SEOAnalytics()
        assert a.total_traffic == 0

    def test_google_metrics(self):
        a = SEOAnalytics(google_impressions=1000, google_clicks=50)
        assert a.total_traffic == 50

    def test_total_traffic(self):
        a = SEOAnalytics(google_clicks=30, pinterest_clicks=20)
        assert a.total_traffic == 50

    def test_to_dict(self):
        a = SEOAnalytics(article_id="a1")
        d = a.to_dict()
        assert d["article_id"] == "a1"


class TestSEOScore:
    def test_default(self):
        s = SEOScore()
        assert s.total == 0.0
        d = s.to_dict()
        assert "keyword_score" in d


# ═══════════════════════════════════════════════════════════════════
# KeywordEngine
# ═══════════════════════════════════════════════════════════════════

class TestKeywordEngine:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_home_decor(self):
        r = self.sm.generate_keywords("home_decor", "Bedroom Ideas", "Decor content")
        assert r["primary_keyword"] is not None
        assert len(r["secondary_keywords"]) > 0
        assert len(r["long_tail_keywords"]) > 0
        assert len(r["lsi_keywords"]) > 0

    def test_generate_tech(self):
        r = self.sm.generate_keywords("tech", "Gadget Review")
        assert r["primary_keyword"] == "tech reviews"

    def test_generate_beauty(self):
        r = self.sm.generate_keywords("beauty", "Skincare Tips")
        assert "skincare" in r["secondary_keywords"][0] or "skincare" in " ".join(r["secondary_keywords"]).lower()

    def test_intent_educational(self):
        r = self.sm.generate_keywords("home_decor", "How to Decorate")
        assert r["search_intent"] == "educational"

    def test_intent_inspirational(self):
        r = self.sm.generate_keywords("fashion", "Best Outfit Ideas")
        assert r["search_intent"] == "inspirational"

    def test_keyword_stats(self):
        self.sm.generate_keywords("food", "Recipe")
        stats = self.sm.keywords.get_stats()
        assert stats["total_generations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# MetaManager
# ═══════════════════════════════════════════════════════════════════

class TestMetaManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_meta(self):
        r = self.sm.generate_meta("10 Bedroom Ideas", "bedroom ideas", "Transform your bedroom", "Decor Blog")
        assert r["seo_title"] is not None
        assert len(r["meta_description"]) <= 160
        assert r["robots_meta"] == "index, follow"

    def test_title_with_keyword(self):
        r = self.sm.generate_meta("Test", "test keyword")
        assert "test keyword" in r["seo_title"].lower()

    def test_empty_title_raises(self):
        with pytest.raises(MetaGenerationError):
            self.sm.generate_meta("")

    def test_meta_description_length(self):
        long_desc = "X" * 300
        r = self.sm.generate_meta("Title", desc=long_desc)
        assert len(r["meta_description"]) <= 160

    def test_meta_stats(self):
        self.sm.generate_meta("Stats Test")
        stats = self.sm.meta.get_stats()
        assert stats["total_generated"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinterestSEOManager
# ═══════════════════════════════════════════════════════════════════

class TestPinterestSEOManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_optimize_pin(self):
        r = self.sm.optimize_pin_seo("Small Bedroom Ideas", "home_decor", "bedroom decor", "Decor content")
        assert r["pin_seo_title"] is not None
        assert len(r["pinterest_hashtags"]) > 0
        assert len(r["pinterest_keywords"]) > 0

    def test_hashtags_generated(self):
        r = self.sm.optimize_pin_seo("Beauty Tips", "beauty")
        tags = " ".join(r["pinterest_hashtags"]).lower()
        assert "#beauty" in tags or "#beautyideas" in tags

    def test_pinterest_stats(self):
        self.sm.optimize_pin_seo("Test Pin", "tech")
        stats = self.sm.pinterest_seo.get_stats()
        assert stats["total_optimizations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RichPinsManager
# ═══════════════════════════════════════════════════════════════════

class TestRichPinsManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_create_article_rich_pin(self):
        r = self.sm.create_rich_pin("Test Article", "Description", "Author", "Blog", "https://example.com")
        assert r["is_rich_pin"] is True
        assert r["rich_pin_type"] == "article"

    def test_empty_title_raises(self):
        with pytest.raises(RichPinError):
            self.sm.rich_pins.create_article_rich_pin("")

    def test_validate_rich_pin(self):
        result = self.sm.rich_pins.validate_rich_pin({"headline": "Test", "url": "https://example.com", "description": "Desc"})
        assert result["is_valid"] is True

    def test_rich_pin_stats(self):
        self.sm.create_rich_pin("Stats")
        stats = self.sm.rich_pins.get_stats()
        assert stats["total_rich_pins"] >= 1


# ═══════════════════════════════════════════════════════════════════
# OpenGraphManager
# ═══════════════════════════════════════════════════════════════════

class TestOpenGraphManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_og(self):
        r = self.sm.generate_og("Test Title", "Test desc", "https://img.com/1.jpg", "https://example.com")
        assert r["og:title"] == "Test Title"
        assert r["og:type"] == "article"

    def test_empty_title_raises(self):
        with pytest.raises(OpenGraphError):
            self.sm.generate_og("")

    def test_og_stats(self):
        self.sm.generate_og("OG Test")
        stats = self.sm.opengraph.get_stats()
        assert stats["total_og_tags"] >= 1


# ═══════════════════════════════════════════════════════════════════
# TwitterCardManager
# ═══════════════════════════════════════════════════════════════════

class TestTwitterCardManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_twitter(self):
        r = self.sm.generate_twitter("Twitter Title", "Twitter desc", "https://img.com/tw.jpg")
        assert r["twitter:title"] == "Twitter Title"
        assert r["twitter:card"] == "summary_large_image"

    def test_empty_title_raises(self):
        with pytest.raises(TwitterCardError):
            self.sm.generate_twitter("")

    def test_twitter_stats(self):
        self.sm.generate_twitter("TW Test")
        stats = self.sm.twitter.get_stats()
        assert stats["total_cards"] >= 1


# ═══════════════════════════════════════════════════════════════════
# StructuredDataManager
# ═══════════════════════════════════════════════════════════════════

class TestStructuredDataManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_article_schema(self):
        r = self.sm.generate_article_schema("Article Title", "Description", "Author", "Blog", "https://example.com")
        assert r["schema_type"] == "Article"
        assert json.loads(r["schema_json"])["@type"] == "Article"

    def test_generate_product_schema(self):
        r = self.sm.schema.generate_product_schema("Product Name", "Desc", "29.99", rating=4.5)
        assert r["schema_type"] == "Product"
        assert "aggregateRating" in r["schema_data"]

    def test_generate_faq_schema(self):
        faqs = [{"question": "Q1?", "answer": "A1"}, {"question": "Q2?", "answer": "A2"}]
        r = self.sm.schema.generate_faq_schema(faqs)
        assert r["schema_type"] == "FAQ"
        assert len(r["schema_data"]["mainEntity"]) == 2

    def test_generate_breadcrumb(self):
        items = [{"name": "Home", "url": "/"}, {"name": "Category", "url": "/cat"}]
        r = self.sm.schema.generate_breadcrumb_schema(items)
        assert r["schema_type"] == "BreadcrumbList"

    def test_schema_stats(self):
        self.sm.generate_article_schema("Schema Test")
        stats = self.sm.schema.get_stats()
        assert stats["total_schemas"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SitemapManager
# ═══════════════════════════════════════════════════════════════════

class TestSitemapManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_sitemap(self):
        articles = [{"url": "https://example.com/a1", "slug": "a1", "updated_at": "2026-01-01"}]
        sitemap = self.sm.generate_sitemap(articles, "https://example.com")
        assert "<urlset" in sitemap
        assert "https://example.com/a1" in sitemap

    def test_empty_articles_raises(self):
        with pytest.raises(SitemapError):
            self.sm.sitemap.generate_article_sitemap([])

    def test_generate_sitemap_index(self):
        sitemaps = [{"url": "https://example.com/sitemap1.xml"}, {"url": "https://example.com/sitemap2.xml"}]
        index = self.sm.sitemap.generate_sitemap_index(sitemaps)
        assert "<sitemapindex" in index

    def test_sitemap_stats(self):
        self.sm.generate_sitemap([{"url": "https://example.com/test"}])
        stats = self.sm.sitemap.get_stats()
        assert stats["total_sitemaps"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RobotsManager
# ═══════════════════════════════════════════════════════════════════

class TestRobotsManager:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_generate_robots(self):
        robots = self.sm.generate_robots("https://example.com/sitemap.xml")
        assert "User-agent: *" in robots
        assert "Sitemap:" in robots

    def test_restrict_ai_bots(self):
        robots = self.sm.generate_robots("https://example.com/sitemap.xml", restrict_ai=True)
        assert "GPTBot" in robots or "CCBot" in robots

    def test_restricted_paths(self):
        robots = self.sm.robots.generate_robots_txt("https://example.com/sitemap.xml",
                                                      restricted_paths=["/admin", "/private"])
        assert "/admin" in robots

    def test_robots_stats(self):
        self.sm.generate_robots("https://example.com/sitemap.xml")
        stats = self.sm.robots.get_stats()
        assert stats["total_robots"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEOValidator
# ═══════════════════════════════════════════════════════════════════

class TestSEOValidator:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_validate_complete_profile(self):
        profile = self.sm.optimize_article("Title", "Content", "tech", "a1")
        result = self.sm.validate_seo(profile.profile_id)
        assert result["seo_score"] >= 70
        assert result["is_valid"] is True

    def test_validate_nonexistent(self):
        result = self.sm.validate_seo("nonexistent")
        assert "error" in result

    def test_validator_stats(self):
        p = self.sm.optimize_article("V Test", "Content", "food", "a2")
        self.sm.validate_seo(p.profile_id)
        stats = self.sm.validator.get_stats()
        assert stats["total_validations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEOOptimizer
# ═══════════════════════════════════════════════════════════════════

class TestSEOOptimizer:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_analyze_good_profile(self):
        p = self.sm.optimize_article("Good SEO Title Here", "Content", "tech", "a3")
        result = self.sm.analyze_seo(p.profile_id)
        assert "suggestions" in result
        assert result["priority"] in ("low", "medium", "high")

    def test_analyze_nonexistent(self):
        result = self.sm.analyze_seo("nonexistent")
        assert "error" in result

    def test_optimizer_stats(self):
        p = self.sm.optimize_article("O Test", "Content", "fashion", "a4")
        self.sm.analyze_seo(p.profile_id)
        stats = self.sm.optimizer.get_stats()
        assert stats["total_analyzed"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEOAnalytics
# ═══════════════════════════════════════════════════════════════════

class TestSEOAnalytics:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_record_analytics(self):
        a = self.sm.record_analytics("a1", google_impressions=1000, google_clicks=50)
        assert a.google_impressions == 1000
        assert a.google_ctr > 0

    def test_simulate_analytics(self):
        a = self.sm.analytics.simulate_analytics("a2", seo_score=80.0)
        assert a.seo_score == 80.0
        assert a.google_impressions > 0

    def test_get_article_performance(self):
        self.sm.record_analytics("a3", 500, 25)
        perf = self.sm.analytics.get_article_performance("a3")
        assert perf["total_impressions"] >= 500

    def test_generate_report(self):
        self.sm.record_analytics("a4", 1000, 50)
        report = self.sm.generate_seo_report()
        assert "total_impressions" in report
        assert "total_clicks" in report

    def test_analytics_stats(self):
        self.sm.record_analytics("a5", 100, 5)
        stats = self.sm.analytics.get_stats()
        assert stats["total_records"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEORichPinsManager Facade — Full Pipeline
# ═══════════════════════════════════════════════════════════════════

class TestSEORichPinsManagerFacade:
    def setup_method(self):
        self.sm = SEORichPinsManager()

    def test_full_optimization_pipeline(self):
        profile = self.sm.optimize_article(
            article_title="10 Small Bedroom Ideas That Save Space",
            article_content="Transform your bedroom with smart storage solutions...",
            niche="home_decor",
            article_id="art_001",
            site_name="Decor Blog",
            url="https://decorblog.com/bedroom-ideas",
            image_url="https://decorblog.com/img/bedroom.jpg",
            author="AI Writer",
        )
        assert profile is not None
        assert profile.primary_keyword is not None
        assert profile.seo_title is not None
        assert profile.meta_description is not None
        assert profile.og_title is not None
        assert profile.twitter_title is not None
        assert profile.has_schema is True
        assert profile.is_rich_pin is True
        assert profile.is_optimized is True
        assert profile.seo_score >= 80

    def test_multiple_niches(self):
        for niche in ["home_decor", "fashion", "tech", "food", "travel"]:
            p = self.sm.optimize_article(f"Best {niche} Ideas", f"Content about {niche}", niche)
            assert p.is_optimized is True

    def test_get_profile(self):
        p = self.sm.optimize_article("Get Profile", "Content", "tech", "a10")
        found = self.sm.get_profile(p.profile_id)
        assert found is not None

    def test_get_all_profiles(self):
        count = len(self.sm.get_all_profiles())
        self.sm.optimize_article("All Test", "Content", "fashion", "a11")
        assert len(self.sm.get_all_profiles()) >= count + 1

    def test_get_status(self):
        self.sm.optimize_article("Status Test", "Content", "food", "a12")
        status = self.sm.get_status()
        assert status["module"] == "SEO & Rich Pins Manager (Layer 23 / Module 7)"
        assert status["version"] == "1.0.0"
        assert status["profiles"]["total"] >= 1


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_seo_manager(self):
        s1 = get_seo_manager()
        s2 = get_seo_manager()
        assert s1 is s2


# ═══════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_all_importable(self):
        assert issubclass(KeywordGenerationError, Exception)
        assert issubclass(MetaGenerationError, Exception)
        assert issubclass(RichPinError, Exception)
        assert issubclass(SchemaError, Exception)
        assert issubclass(SitemapError, Exception)
        assert issubclass(RobotsError, Exception)
        assert issubclass(SEOValidationError, Exception)
        assert issubclass(DuplicateMetadataError, Exception)
        assert issubclass(OpenGraphError, Exception)
        assert issubclass(TwitterCardError, Exception)
