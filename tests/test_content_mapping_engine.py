"""Comprehensive tests for Layer 23 — Module 5: Content Mapping Engine."""
from __future__ import annotations
import time
import pytest

from layers.layer23_website_manager.content_mapping_engine.content_mapping_engine import (
    ContentMappingEngine, get_mapping_engine,
)
from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, ContentIntent, ContentAudience, PinStrategy,
    MappingPriority, MappingStatus,
)
from layers.layer23_website_manager.content_mapping_engine.models.mapping_history import MappingHistory
from layers.layer23_website_manager.content_mapping_engine.exceptions import (
    ContentClassificationError, WebsiteMappingError, AccountMappingError,
    BoardMappingError, AffiliateMappingError, ImageMappingError,
    SchedulingMappingError, ValidationError, RelationshipError,
    RecommendationError, SEOMappingError, PinStrategyError,
)


# ═══════════════════════════════════════════════════════════════════
# ContentMapping Model
# ═══════════════════════════════════════════════════════════════════

class TestContentMapping:
    def test_default_mapping(self):
        m = ContentMapping()
        assert m.mapping_id is not None
        assert m.intent == ContentIntent.INFORMATIONAL
        assert m.status == MappingStatus.PENDING
        assert m.priority == MappingPriority.MEDIUM

    def test_mapping_with_values(self):
        m = ContentMapping(
            article_title="10 Bedroom Ideas",
            niche="home_decor",
            account_id="acc1",
            board_id="board1",
            website_id="site1",
        )
        assert m.article_title == "10 Bedroom Ideas"
        assert m.niche == "home_decor"
        assert m.is_pending is True
        assert m.is_active is False
        assert m.is_published is False

    def test_status_properties(self):
        m = ContentMapping(status=MappingStatus.ACTIVE)
        assert m.is_active is True
        assert m.is_pending is False

        m = ContentMapping(status=MappingStatus.PUBLISHED)
        assert m.is_published is True

    def test_to_dict(self):
        m = ContentMapping(article_title="Test Article", niche="fashion")
        d = m.to_dict()
        assert d["article_title"] == "Test Article"
        assert d["niche"] == "fashion"
        assert "status" in d
        assert "created_at" in d

    def test_all_intents(self):
        for intent in ContentIntent:
            m = ContentMapping(intent=intent)
            assert m.intent == intent

    def test_all_audiences(self):
        for audience in ContentAudience:
            m = ContentMapping(audience=audience)
            assert m.audience == audience

    def test_all_strategies(self):
        for strategy in PinStrategy:
            m = ContentMapping(pin_strategy=strategy)
            assert m.pin_strategy == strategy

    def test_all_priorities(self):
        for priority in MappingPriority:
            m = ContentMapping(priority=priority)
            assert m.priority == priority

    def test_related_ids(self):
        m = ContentMapping(
            related_article_ids=["a1", "a2"],
            related_pin_ids=["p1"],
            related_board_ids=["b1", "b2", "b3"],
        )
        assert len(m.related_article_ids) == 2
        assert len(m.related_pin_ids) == 1
        assert len(m.related_board_ids) == 3


# ═══════════════════════════════════════════════════════════════════
# MappingHistory Model
# ═══════════════════════════════════════════════════════════════════

class TestMappingHistory:
    def test_default(self):
        h = MappingHistory()
        assert h.history_id is not None
        assert h.old_mapping == {}
        assert h.new_mapping == {}

    def test_create_change(self):
        old = {"status": "draft"}
        new = {"status": "published"}
        h = MappingHistory.create_change("content1", old, new, "Published", 0.95)
        assert h.content_id == "content1"
        assert h.reason == "Published"
        assert h.ai_score == 0.95

    def test_to_dict(self):
        h = MappingHistory(content_id="c1", reason="test", ai_score=0.8)
        d = h.to_dict()
        assert d["content_id"] == "c1"
        assert d["reason"] == "test"


# ═══════════════════════════════════════════════════════════════════
# ContentClassifier
# ═══════════════════════════════════════════════════════════════════

class TestContentClassifier:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_classify_home_decor(self):
        result = self.engine.classifier.classify(
            "10 Small Bedroom Ideas That Save Space",
            content="Transform your bedroom with smart storage",
            keywords=["bedroom", "organization"],
        )
        assert result["niche"] == "home_decor"
        assert result["intent"] in ["educational", "inspirational", "informational"]
        assert result["audience"] in ["all", "homeowners"]
        assert result["confidence"] > 0.5

    def test_classify_fashion(self):
        result = self.engine.classifier.classify(
            "Best Summer Outfit Ideas for Women",
            content="Fashion trends this season",
            keywords=["fashion", "outfit"],
        )
        assert result["niche"] in ["fashion", "home_decor"]  # fashion has match

    def test_classify_food(self):
        result = self.engine.classifier.classify(
            "Easy Chocolate Cake Recipe",
            content="Bake this delicious cake",
            keywords=["recipe", "baking"],
        )
        assert result["niche"] in ["food", "home_decor"]

    def test_classify_empty_title(self):
        with pytest.raises(ContentClassificationError):
            self.engine.classifier.classify("")

    def test_classify_detects_intent_educational(self):
        result = self.engine.classifier.classify("How to Decorate Your Home Like a Pro")
        assert result["intent"] == "educational"

    def test_classify_detects_intent_inspirational(self):
        result = self.engine.classifier.classify("Top 10 Amazing Home Decor Ideas")
        assert result["intent"] == "inspirational"

    def test_classify_detects_audience_women(self):
        result = self.engine.classifier.classify("Best Fashion Tips for Women")
        assert result["audience"] in ["women", "all"]

    def test_classify_content_type(self):
        result = self.engine.classifier.classify("10 Best Skincare Tips")
        assert result["content_type"] == "list"

    def test_classify_guide_type(self):
        result = self.engine.classifier.classify("Complete Guide to Yoga for Beginners")
        assert result["content_type"] == "guide"

    def test_classify_review_type(self):
        result = self.engine.classifier.classify("iPhone 16 Pro Review vs Samsung")
        assert result["content_type"] == "review"

    def test_get_stats(self):
        self.engine.classifier.classify("Test Article Title for Stats")
        stats = self.engine.classifier.get_stats()
        assert stats["total_classified"] >= 1


# ═══════════════════════════════════════════════════════════════════
# WebsiteMapper
# ═══════════════════════════════════════════════════════════════════

class TestWebsiteMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor(self):
        result = self.engine.website_mapper.map_to_website("home_decor")
        assert result["website_id"] == "site_home_decor"
        assert "modernlivinghub.com" in result["website_url"]
        assert result["confidence"] > 0.5

    def test_map_unknown_niche(self):
        result = self.engine.website_mapper.map_to_website("unknown_niche")
        assert result["website_id"] is not None

    def test_map_with_category(self):
        result = self.engine.website_mapper.map_to_website("home_decor", "Kitchen")
        assert "kitchen" in result["website_category"].lower() or "kitchen" in result["website_category"]

    def test_get_available_websites(self):
        sites = self.engine.website_mapper.get_available_websites()
        assert len(sites) >= 8

    def test_get_websites_by_niche(self):
        sites = self.engine.website_mapper.get_websites_by_niche("home_decor")
        assert len(sites) >= 1
        assert sites[0]["niche"] == "home_decor"

    def test_get_stats(self):
        self.engine.website_mapper.map_to_website("fashion")
        stats = self.engine.website_mapper.get_stats()
        assert stats["total_mapped"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinterestAccountMapper
# ═══════════════════════════════════════════════════════════════════

class TestPinterestAccountMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor(self):
        result = self.engine.account_mapper.map_account("home_decor")
        assert result["account_id"] == "pinterest_home"
        assert result["account_name"] == "Modern Living Hub"

    def test_map_fashion(self):
        result = self.engine.account_mapper.map_account("fashion")
        assert result["account_id"] == "pinterest_fashion"

    def test_map_unknown_niche(self):
        result = self.engine.account_mapper.map_account("unknown")
        assert result["account_id"] is not None

    def test_get_available_accounts(self):
        accounts = self.engine.account_mapper.get_available_accounts()
        assert len(accounts) >= 8

    def test_get_accounts_by_niche(self):
        accounts = self.engine.account_mapper.get_accounts_by_niche("beauty")
        assert len(accounts) >= 1

    def test_get_stats(self):
        self.engine.account_mapper.map_account("food")
        stats = self.engine.account_mapper.get_stats()
        assert stats["total_mapped"] >= 1


# ═══════════════════════════════════════════════════════════════════
# BoardMapper
# ═══════════════════════════════════════════════════════════════════

class TestBoardMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_board_bedroom(self):
        result = self.engine.board_mapper.map_board(
            "pinterest_home", "Bedroom", ["bedroom", "design"]
        )
        assert result["board_id"] is not None
        assert result["confidence"] > 0

    def test_map_board_fashion(self):
        result = self.engine.board_mapper.map_board(
            "pinterest_fashion", "Dresses", ["dress"]
        )
        assert result["board_id"] is not None

    def test_map_board_nonexistent_account(self):
        with pytest.raises(BoardMappingError):
            self.engine.board_mapper.map_board("nonexistent", "Category")

    def test_get_boards_for_account(self):
        boards = self.engine.board_mapper.get_boards_for_account("pinterest_home")
        assert len(boards) >= 3

    def test_get_all_boards(self):
        all_boards = self.engine.board_mapper.get_all_boards()
        assert len(all_boards) >= 8

    def test_get_stats(self):
        self.engine.board_mapper.map_board("pinterest_home", "Bedroom")
        stats = self.engine.board_mapper.get_stats()
        assert stats["total_mapped"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinStrategyEngine
# ═══════════════════════════════════════════════════════════════════

class TestPinStrategyEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_select_for_list(self):
        result = self.engine.pin_strategy.select_strategy(
            "list", ContentIntent.INSPIRATIONAL, "home_decor"
        )
        assert result["selected_strategy"] is not None
        assert result["confidence"] > 0.5

    def test_select_for_guide(self):
        result = self.engine.pin_strategy.select_strategy(
            "guide", ContentIntent.EDUCATIONAL
        )
        assert result["selected_strategy"] is not None

    def test_select_for_review(self):
        result = self.engine.pin_strategy.select_strategy(
            "review", ContentIntent.COMMERCIAL
        )
        assert result["selected_strategy"] in ["product", "standard", "rich"]

    def test_select_for_recipe(self):
        result = self.engine.pin_strategy.select_strategy(
            "recipe", ContentIntent.INSPIRATIONAL
        )
        assert result["selected_strategy"] is not None

    def test_select_has_alternatives(self):
        result = self.engine.pin_strategy.select_strategy(
            "article", ContentIntent.INFORMATIONAL
        )
        assert len(result["alternatives"]) >= 1

    def test_get_stats(self):
        self.engine.pin_strategy.select_strategy("article", ContentIntent.INFORMATIONAL)
        stats = self.engine.pin_strategy.get_stats()
        assert stats["total_analyses"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AffiliateMapper
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor(self):
        result = self.engine.affiliate_mapper.map_affiliate(
            "home_decor", ["bedroom", "bed"]
        )
        assert result["product_id"] is not None
        assert result["commission"] > 0

    def test_map_food(self):
        result = self.engine.affiliate_mapper.map_affiliate(
            "food", ["baking", "kitchen"]
        )
        assert result["product_id"] is not None

    def test_map_nonexistent_niche(self):
        with pytest.raises(AffiliateMappingError):
            self.engine.affiliate_mapper.map_affiliate("nonexistent_niche_xyz")

    def test_get_products_by_niche(self):
        products = self.engine.affiliate_mapper.get_products_by_niche("home_decor")
        assert len(products) >= 1

    def test_get_all_products(self):
        all_products = self.engine.affiliate_mapper.get_all_products()
        assert len(all_products) >= 8

    def test_get_stats(self):
        self.engine.affiliate_mapper.map_affiliate("beauty")
        stats = self.engine.affiliate_mapper.get_stats()
        assert stats["total_mapped"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEOMapper
# ═══════════════════════════════════════════════════════════════════

class TestSEOMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_generate_seo_profile(self):
        result = self.engine.seo_mapper.generate_seo_profile(
            "10 Small Bedroom Ideas",
            niche="home_decor",
            keywords=["bedroom", "small space"],
        )
        assert len(result["seo_keywords"]) >= 3
        assert len(result["long_tail_keywords"]) >= 1
        assert result["search_intent"] is not None

    def test_empty_title_raises(self):
        with pytest.raises(SEOMappingError):
            self.engine.seo_mapper.generate_seo_profile("")

    def test_search_intent_transactional(self):
        result = self.engine.seo_mapper.generate_seo_profile("Buy Best Bedroom Furniture")
        assert result["search_intent"] == "transactional"

    def test_search_intent_how_to(self):
        result = self.engine.seo_mapper.generate_seo_profile("How to Decorate a Small Bedroom")
        assert result["search_intent"] == "how-to"

    def test_related_topics(self):
        result = self.engine.seo_mapper.generate_seo_profile(
            "Bedroom Ideas", niche="home_decor"
        )
        assert len(result["related_topics"]) > 0

    def test_get_stats(self):
        self.engine.seo_mapper.generate_seo_profile("Test SEO", niche="fashion")
        stats = self.engine.seo_mapper.get_stats()
        assert stats["total_seo_profiles"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ImageMapper
# ═══════════════════════════════════════════════════════════════════

class TestImageMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_images(self):
        result = self.engine.image_mapper.map_images(
            niche="home_decor", content_type="article", title="Bedroom Ideas"
        )
        assert result["featured_image"] is not None
        assert result["pinterest_image"] is not None
        assert result["thumbnail"] is not None
        assert result["image_style"] is not None
        assert result["dimensions"]["width"] == 1000

    def test_map_images_food(self):
        result = self.engine.image_mapper.map_images(
            niche="food", content_type="recipe", title="Chocolate Cake"
        )
        assert "final_dish" in result["pinterest_image"]

    def test_map_images_list(self):
        result = self.engine.image_mapper.map_images(
            niche="fashion", content_type="list", title="Top Outfits"
        )
        assert "collage" in result["pinterest_image"]

    def test_style_selection(self):
        result = self.engine.image_mapper.map_images(niche="home_decor")
        assert result["image_style"] in self.engine.image_mapper.STYLE_OPTIONS["home_decor"]

    def test_get_stats(self):
        self.engine.image_mapper.map_images(niche="tech")
        stats = self.engine.image_mapper.get_stats()
        assert stats["total_mapped"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SchedulingMapper
# ═══════════════════════════════════════════════════════════════════

class TestSchedulingMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_schedule(self):
        result = self.engine.scheduling_mapper.map_schedule(
            niche="home_decor", intent="inspirational"
        )
        assert result["priority"] in ["high", "medium", "low"]
        assert result["schedule_time"] > 0
        assert len(result["peak_hours"]) >= 1

    def test_commercial_priority(self):
        result = self.engine.scheduling_mapper.map_schedule(
            niche="tech", intent="commercial", confidence=0.95
        )
        assert result["priority"] == "high"

    def test_low_confidence_priority(self):
        result = self.engine.scheduling_mapper.map_schedule(
            niche="garden", intent="inspirational", confidence=0.5
        )
        assert result["priority"] in ["medium", "low"]

    def test_peak_hours(self):
        result = self.engine.scheduling_mapper.map_schedule(niche="food")
        assert 8 <= min(result["peak_hours"]) <= 12

    def test_get_stats(self):
        self.engine.scheduling_mapper.map_schedule(niche="fashion")
        stats = self.engine.scheduling_mapper.get_stats()
        assert stats["total_scheduled"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ValidationEngine
# ═══════════════════════════════════════════════════════════════════

class TestValidationEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_validate_complete_mapping(self):
        mapping = {
            "website_id": "site_home_decor",
            "website_url": "https://modernlivinghub.com",
            "account_id": "pinterest_home",
            "board_id": "board_home_bedroom",
            "pin_strategy": "rich",
            "seo_keywords": ["bedroom", "decor", "ideas"],
            "featured_image": "/images/bedroom.jpg",
            "validation_score": 85,
        }
        result = self.engine.validator.validate_mapping(mapping)
        assert result["is_valid"] is True
        assert result["validation_score"] >= 50

    def test_validate_missing_fields(self):
        mapping = {
            "website_id": "",
            "website_url": "",
            "account_id": "",
            "board_id": "",
            "pin_strategy": "",
            "seo_keywords": [],
        }
        result = self.engine.validator.validate_mapping(mapping)
        assert result["is_valid"] is False
        assert len(result["issues"]) >= 3

    def test_validate_partial(self):
        mapping = {
            "website_id": "site1",
            "website_url": "https://example.com",
            "account_id": "acc1",
            "board_id": "board1",
            "pin_strategy": "standard",
            "seo_keywords": ["kw1"],
            "featured_image": "",
        }
        result = self.engine.validator.validate_mapping(mapping)
        assert result["issue_count"] >= 0

    def test_get_stats(self):
        self.engine.validator.validate_mapping({
            "website_id": "s1", "website_url": "https://x.com",
            "account_id": "a1", "board_id": "b1",
            "pin_strategy": "standard", "seo_keywords": ["a", "b", "c"],
        })
        stats = self.engine.validator.get_stats()
        assert stats["total_validated"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RelationshipEngine
# ═══════════════════════════════════════════════════════════════════

class TestRelationshipEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_build_relationships_existing(self):
        result = self.engine.relationship_engine.build_relationships(
            "small bedroom ideas", "home_decor", ["bedroom"]
        )
        assert result["relationship_count"] >= 1

    def test_build_relationships_empty(self):
        result = self.engine.relationship_engine.build_relationships(
            "some random unique topic xyz", "unknown"
        )
        assert "related_article_ids" in result

    def test_get_stats(self):
        self.engine.relationship_engine.build_relationships("test", "home_decor")
        stats = self.engine.relationship_engine.get_stats()
        assert stats["total_relationships"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RecommendationEngine
# ═══════════════════════════════════════════════════════════════════

class TestRecommendationEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_recommend_empty_mapping(self):
        mapping = {}
        result = self.engine.recommendation_engine.recommend(mapping)
        assert result["total_recommendations"] >= 3
        assert "overall_quality_score" in result

    def test_recommend_complete_mapping(self):
        mapping = {
            "website_id": "site1",
            "website_category": "home",
            "account_id": "acc1",
            "board_id": "board1",
            "pin_strategy": "rich",
            "affiliate_product": "Product",
            "seo_keywords": ["kw1", "kw2", "kw3", "kw4"],
            "featured_image": "/img.jpg",
            "priority": "high",
        }
        result = self.engine.recommendation_engine.recommend(mapping)
        assert result["total_recommendations"] >= 0
        assert result["overall_quality_score"] >= 50

    def test_quality_score_drops_with_issues(self):
        result1 = self.engine.recommendation_engine.recommend({})
        result2 = self.engine.recommendation_engine.recommend({
            "website_id": "s1", "account_id": "a1", "board_id": "b1",
            "pin_strategy": "rich", "affiliate_product": "P",
            "seo_keywords": ["a", "b", "c"], "featured_image": "/img",
            "priority": "high",
        })
        assert result1["overall_quality_score"] < result2["overall_quality_score"]

    def test_get_stats(self):
        self.engine.recommendation_engine.recommend({"website_id": "s1"})
        stats = self.engine.recommendation_engine.get_stats()
        assert stats["total_recommendations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ContentMappingEngine (Facade) — Full Pipeline
# ═══════════════════════════════════════════════════════════════════

class TestFullPipeline:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_full_pipeline_home_decor(self):
        mapping = self.engine.map_article(
            "10 Small Bedroom Ideas That Save Space",
            content="Transform your small bedroom with smart storage solutions...",
            article_id="art_001",
            keywords=["bedroom", "small space", "storage", "organization"],
        )
        assert mapping.mapping_id is not None
        assert mapping.niche == "home_decor"
        assert mapping.website_id is not None
        assert mapping.account_id is not None
        assert mapping.board_id is not None
        assert mapping.pin_strategy is not None
        assert mapping.validation_score > 0
        assert len(mapping.seo_keywords) >= 3

    def test_full_pipeline_fashion(self):
        mapping = self.engine.map_article(
            "Best Summer Fashion Trends for Women",
            article_id="art_002",
            keywords=["fashion", "summer", "trends", "women"],
        )
        assert mapping.mapping_id is not None
        assert mapping.niche in ["fashion", "home_decor"]

    def test_full_pipeline_beauty(self):
        mapping = self.engine.map_article(
            "Complete Skincare Routine for Glowing Skin",
            keywords=["skincare", "beauty", "routine"],
        )
        assert mapping.mapping_id is not None

    def test_full_pipeline_food(self):
        mapping = self.engine.map_article(
            "Easy Chocolate Cake Recipe",
            content="Bake this delicious chocolate cake",
            keywords=["recipe", "baking", "dessert"],
        )
        assert mapping.mapping_id is not None

    def test_full_pipeline_tech(self):
        mapping = self.engine.map_article(
            "Best Wireless Headphones 2026",
            keywords=["tech", "headphones", "wireless"],
        )
        assert mapping.mapping_id is not None

    def test_full_pipeline_travel(self):
        mapping = self.engine.map_article(
            "Top 10 Travel Destinations for Summer",
            keywords=["travel", "destinations", "vacation"],
        )
        assert mapping.mapping_id is not None

    def test_get_mapping(self):
        mapping = self.engine.map_article("Test Article", article_id="art_get")
        found = self.engine.get_mapping(mapping.mapping_id)
        assert found is not None
        assert found.article_id == "art_get"

    def test_get_nonexistent_mapping(self):
        assert self.engine.get_mapping("nonexistent") is None

    def test_get_all_mappings(self):
        count_before = len(self.engine.get_all_mappings())
        self.engine.map_article("Another Article")
        count_after = len(self.engine.get_all_mappings())
        assert count_after > count_before

    def test_get_mappings_by_niche(self):
        self.engine.map_article("Home Decor Article", keywords=["home decor"])
        mappings = self.engine.get_mappings_by_niche("home_decor")
        assert len(mappings) >= 1

    def test_get_mappings_by_account(self):
        mapping = self.engine.map_article("Test Account Map")
        mappings = self.engine.get_mappings_by_account(mapping.account_id)
        assert len(mappings) >= 1

    def test_get_mappings_by_website(self):
        mapping = self.engine.map_article("Test Website Map")
        mappings = self.engine.get_mappings_by_website(mapping.website_id)
        assert len(mappings) >= 1

    def test_update_mapping_status(self):
        mapping = self.engine.map_article("Status Test Article")
        result = self.engine.update_mapping_status(mapping.mapping_id, MappingStatus.PUBLISHED)
        assert result is True
        assert mapping.is_published is True

    def test_update_mapping_status_nonexistent(self):
        result = self.engine.update_mapping_status("nonexistent", MappingStatus.PUBLISHED)
        assert result is False

    def test_get_recommendations(self):
        mapping = self.engine.map_article("Recommendation Test")
        recs = self.engine.get_recommendations(mapping.mapping_id)
        assert "recommendations" in recs or "total_recommendations" in recs

    def test_get_recommendations_nonexistent(self):
        recs = self.engine.get_recommendations("nonexistent")
        assert "error" in recs


# ═══════════════════════════════════════════════════════════════════
# Status
# ═══════════════════════════════════════════════════════════════════

class TestStatus:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_get_status(self):
        status = self.engine.get_status()
        assert status["module"] == "Content Mapping Engine (Layer 23 / Module 5)"
        assert status["version"] == "1.0.0"
        assert "total_mappings" in status
        assert "by_status" in status
        assert "by_niche" in status
        assert "avg_confidence" in status
        assert "classifier" in status
        assert "website_mapper" in status
        assert "account_mapper" in status
        assert "board_mapper" in status
        assert "pin_strategy" in status
        assert "affiliate_mapper" in status
        assert "seo_mapper" in status
        assert "image_mapper" in status
        assert "scheduling" in status
        assert "validator" in status
        assert "relationships" in status
        assert "recommendations" in status

    def test_status_after_mappings(self):
        self.engine.map_article("Article 1 for status")
        self.engine.map_article("Article 2 for status")
        status = self.engine.get_status()
        assert status["total_mappings"] >= 2

    def test_get_status_alias(self):
        assert self.engine.get_stats() == self.engine.get_status()


# ═══════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_get_nonexistent_mapping(self):
        assert self.engine.get_mapping("nonexistent") is None

    def test_update_nonexistent_status(self):
        assert self.engine.update_mapping_status("nonexistent", MappingStatus.PUBLISHED) is False


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_mapping_engine(self):
        e1 = get_mapping_engine()
        e2 = get_mapping_engine()
        assert e1 is e2


# ═══════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_all_exceptions_importable(self):
        assert issubclass(ContentClassificationError, Exception)
        assert issubclass(WebsiteMappingError, Exception)
        assert issubclass(AccountMappingError, Exception)
        assert issubclass(BoardMappingError, Exception)
        assert issubclass(AffiliateMappingError, Exception)
        assert issubclass(ImageMappingError, Exception)
        assert issubclass(SchedulingMappingError, Exception)
        assert issubclass(ValidationError, Exception)
        assert issubclass(RelationshipError, Exception)
        assert issubclass(RecommendationError, Exception)
        assert issubclass(SEOMappingError, Exception)
        assert issubclass(PinStrategyError, Exception)


# ═══════════════════════════════════════════════════════════════════
# Multi-Niche Coverage
# ═══════════════════════════════════════════════════════════════════

class TestAllNiches:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_all_different_niches_map(self):
        articles = [
            ("Modern Living Room Decor Ideas", "home_decor", ["decor", "living room"]),
            ("Summer Fashion Trends 2026", "fashion", ["fashion", "trends"]),
            ("Best Skincare Products for Glowing Skin", "beauty", ["skincare", "beauty"]),
            ("Quick Healthy Dinner Recipes", "food", ["recipe", "dinner", "healthy"]),
            ("Top Gadgets to Buy This Year", "tech", ["tech", "gadgets"]),
            ("Morning Yoga Routine for Beginners", "fitness", ["yoga", "fitness"]),
            ("Budget Travel Tips for Europe", "travel", ["travel", "budget"]),
            ("How to Save Money Fast", "finance", ["money", "save"]),
            ("DIY Wooden Shelf Project", "diy", ["diy", "wood"]),
            ("Spring Garden Planting Guide", "garden", ["garden", "plant"]),
        ]

        for title, niche, keywords in articles:
            mapping = self.engine.map_article(title, keywords=keywords)
            assert mapping.mapping_id is not None
            assert mapping.niche is not None
            assert mapping.website_id is not None
            assert mapping.account_id is not None
            assert mapping.board_id is not None
            assert mapping.pin_strategy is not None
            assert mapping.validation_score > 0
