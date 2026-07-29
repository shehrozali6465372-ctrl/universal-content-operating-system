"""Comprehensive tests for Layer 23 — Module 5: Content Mapping Engine."""
from __future__ import annotations
import time
import pytest

from layers.layer23_website_manager.content_mapping_engine.content_mapping_engine import (
    ContentMappingEngine, get_mapping_engine,
)
from layers.layer23_website_manager.content_mapping_engine.models.content_mapping import (
    ContentMapping, MappingStatus, PinStrategy, Priority, ContentCategory, ContentIntent,
)
from layers.layer23_website_manager.content_mapping_engine.models.mapping_history import MappingHistory
from layers.layer23_website_manager.content_mapping_engine.exceptions import (
    ContentClassificationError, WebsiteMappingError, AccountMappingError,
    BoardMappingError, AffiliateMappingError, ValidationError,
    ImageMappingError, RelationshipError, RecommendationError,
    PinStrategyError, MappingNotFoundError,
)


# ═══════════════════════════════════════════════════════════════════
# ContentMapping Model
# ═══════════════════════════════════════════════════════════════════

class TestContentMapping:
    def test_default_mapping(self):
        m = ContentMapping()
        assert m.status == MappingStatus.PENDING
        assert m.mapping_id is not None
        assert m.priority == Priority.MEDIUM

    def test_mapping_with_values(self):
        m = ContentMapping(
            article_title="10 Bedroom Ideas",
            niche="home_decor",
            category=ContentCategory.HOME_DECOR,
            intent=ContentIntent.INSPIRATIONAL,
            account_id="acc1",
            board_id="board1",
            website_id="site1",
        )
        assert m.article_title == "10 Bedroom Ideas"
        assert m.niche == "home_decor"
        assert m.account_id == "acc1"
        assert m.is_mapped is False
        assert m.is_ready is False

    def test_is_mapped(self):
        m = ContentMapping(status=MappingStatus.MAPPED)
        assert m.is_mapped is True

        m = ContentMapping(status=MappingStatus.VALIDATED)
        assert m.is_mapped is True

        m = ContentMapping(status=MappingStatus.PENDING)
        assert m.is_mapped is False

    def test_is_ready(self):
        m = ContentMapping(
            is_validated=True, account_id="a1", board_id="b1", website_id="w1"
        )
        assert m.is_ready is True

        m.is_validated = False
        assert m.is_ready is False

    def test_to_dict(self):
        m = ContentMapping(article_title="Test Article", niche="fashion")
        d = m.to_dict()
        assert d["article_title"] == "Test Article"
        assert d["niche"] == "fashion"
        assert "mapping_id" in d
        assert "created_at" in d


# ═══════════════════════════════════════════════════════════════════
# MappingHistory Model
# ═══════════════════════════════════════════════════════════════════

class TestMappingHistory:
    def test_default(self):
        h = MappingHistory()
        assert h.history_id is not None
        assert h.change_type == ""
        assert h.ai_score == 0.0

    def test_with_values(self):
        h = MappingHistory(
            mapping_id="m1",
            change_type="auto",
            change_reason="Initial mapping",
            ai_score=0.85,
        )
        assert h.mapping_id == "m1"
        assert h.change_type == "auto"
        assert h.ai_score == 0.85

    def test_to_dict(self):
        h = MappingHistory(mapping_id="m1", change_type="auto")
        d = h.to_dict()
        assert d["mapping_id"] == "m1"
        assert "created_at" in d


# ═══════════════════════════════════════════════════════════════════
# ContentClassifier
# ═══════════════════════════════════════════════════════════════════

class TestContentClassifier:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_classify_home_decor(self):
        result = self.engine.classify(
            "10 Small Bedroom Ideas That Save Space",
            "Transform your bedroom with smart storage",
            ["bedroom", "decor"],
        )
        assert result["niche"] == "home_decor"
        assert "category" in result
        assert result["confidence"] > 0

    def test_classify_fashion(self):
        result = self.engine.classify(
            "Best Summer Outfits for Women",
            "Stay stylish with these trendy fashion ideas",
            ["fashion", "outfit"],
        )
        assert result["niche"] == "fashion"

    def test_classify_food(self):
        result = self.engine.classify(
            "Quick 30-Minute Dinner Recipes",
            "Easy cooking recipes for busy weeknights",
        )
        assert result["niche"] == "food"

    def test_classify_tech(self):
        result = self.engine.classify(
            "Best Budget Smartphones 2026",
            "Tech gadgets and phone reviews",
        )
        assert result["niche"] == "tech"

    def test_classify_fitness(self):
        result = self.engine.classify(
            "30-Day Fitness Challenge for Beginners",
            "Workout routines and exercise tips",
        )
        assert result["niche"] == "fitness"

    def test_classify_travel(self):
        result = self.engine.classify(
            "Top Travel Destinations for 2026",
            "Vacation ideas and travel tips",
        )
        assert result["niche"] == "travel"

    def test_classify_finance(self):
        result = self.engine.classify(
            "Passive Income Ideas for Beginners",
            "Money management and investing tips",
        )
        assert result["niche"] == "finance"

    def test_classify_diy(self):
        result = self.engine.classify(
            "DIY Woodworking Projects for Beginners",
            "Handmade woodworking and craft projects",
        )
        assert result["niche"] == "diy"

    def test_classify_intent_educational(self):
        result = self.engine.classify("How to Decorate Your Home")
        assert result["intent"] == "educational"

    def test_classify_intent_inspirational(self):
        result = self.engine.classify("Best Home Decor Ideas")
        assert result["intent"] == "inspirational"

    def test_classify_intent_commercial(self):
        result = self.engine.classify("Best Affordable Furniture to Buy Online - Shop Now")
        assert result["intent"] in ("commercial", "inspirational")

    def test_classify_audience(self):
        result = self.engine.classify("Bedroom Decor Ideas")
        assert result["audience"] is not None

    def test_classify_content_type(self):
        result = self.engine.classify("How to Organize Your Closet")
        assert result["content_type"] == "tutorial"

    def test_classify_empty_title(self):
        with pytest.raises(ContentClassificationError):
            self.engine.classify("", "")

    def test_classify_general(self):
        result = self.engine.classify("Some random content without keywords")
        assert result["niche"] in ("general", "diy")

    def test_classify_stats(self):
        self.engine.classify("Test Article", "Content here")
        stats = self.engine.classifier.get_stats()
        assert stats["total_classified"] >= 1


# ═══════════════════════════════════════════════════════════════════
# WebsiteMapper
# ═══════════════════════════════════════════════════════════════════

class TestWebsiteMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor_website(self):
        result = self.engine.map_website("home_decor")
        assert result["id"] == "site_hd1"
        assert result["confidence"] > 0

    def test_map_fashion_website(self):
        result = self.engine.map_website("fashion")
        assert result["id"] == "site_fa1"

    def test_map_unknown_niche(self):
        result = self.engine.map_website("unknown_niche")
        assert result["id"] == ""
        assert result["confidence"] == 0.0

    def test_preferred_website(self):
        result = self.engine.map_website("home_decor", preferred="site_hd2")
        assert result["id"] == "site_hd2"

    def test_get_available_websites(self):
        sites = self.engine.website_mapper.get_available_websites("home_decor")
        assert len(sites) > 0

    def test_get_available_empty(self):
        sites = self.engine.website_mapper.get_available_websites("nonexistent")
        assert len(sites) == 0

    def test_website_stats(self):
        self.engine.map_website("home_decor")
        stats = self.engine.website_mapper.get_stats()
        assert stats["total_mappings"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinterestAccountMapper
# ═══════════════════════════════════════════════════════════════════

class TestPinterestAccountMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor_account(self):
        result = self.engine.map_account("home_decor")
        assert result["id"] is not None
        assert result["name"] == "Modern Living Hub"

    def test_map_fashion_account(self):
        result = self.engine.map_account("fashion")
        assert result["name"] == "Style Vault"

    def test_map_unknown_niche(self):
        result = self.engine.map_account("unknown")
        assert result["id"] == ""
        assert result["confidence"] == 0.0

    def test_preferred_account(self):
        result = self.engine.map_account("home_decor", preferred="acc_hd2")
        assert result["id"] == "acc_hd2"

    def test_get_available_accounts(self):
        accounts = self.engine.account_mapper.get_available_accounts("home_decor")
        assert len(accounts) >= 2

    def test_accounts_by_niche(self):
        by_niche = self.engine.account_mapper.get_accounts_by_niche()
        assert "home_decor" in by_niche
        assert "fashion" in by_niche

    def test_account_stats(self):
        self.engine.map_account("food")
        stats = self.engine.account_mapper.get_stats()
        assert stats["total_mappings"] >= 1


# ═══════════════════════════════════════════════════════════════════
# BoardMapper
# ═══════════════════════════════════════════════════════════════════

class TestBoardMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor_board(self):
        result = self.engine.map_board("home_decor")
        assert result["id"] is not None

    def test_map_board_with_topic(self):
        result = self.engine.map_board("home_decor", "Bedroom")
        assert "Bedroom" in result["name"]

    def test_map_unknown_niche(self):
        result = self.engine.map_board("unknown")
        assert result["id"] == ""
        assert result["confidence"] == 0.0

    def test_preferred_board(self):
        result = self.engine.map_board("home_decor", preferred="board_hd3")
        assert result["id"] == "board_hd3"

    def test_get_available_boards(self):
        boards = self.engine.board_mapper.get_available_boards("home_decor")
        assert len(boards) >= 3

    def test_boards_by_niche(self):
        by_niche = self.engine.board_mapper.get_boards_by_niche()
        assert "home_decor" in by_niche

    def test_board_stats(self):
        self.engine.map_board("food")
        stats = self.engine.board_mapper.get_stats()
        assert stats["total_mappings"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinStrategyEngine
# ═══════════════════════════════════════════════════════════════════

class TestPinStrategyEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_standard_strategy(self):
        result = self.engine.select_strategy("home_decor", "informational", "article")
        assert result["strategy"] in ("standard", "idea_pin", "rich_pin")

    def test_idea_pin_for_educational(self):
        result = self.engine.select_strategy("beauty", "educational", "tutorial")
        assert result["strategy"] == "idea_pin"

    def test_carousel_for_listicle(self):
        result = self.engine.select_strategy("home_decor", "educational", "listicle")
        assert result["strategy"] == "standard"

    def test_product_pin_for_commercial(self):
        result = self.engine.select_strategy("tech", "commercial", "review")
        assert result["strategy"] == "product_pin"

    def test_rich_pin_for_travel(self):
        result = self.engine.select_strategy("travel", "inspirational", "article")
        assert result["strategy"] == "rich_pin"

    def test_strategy_stats(self):
        self.engine.select_strategy("tech", "educational", "tutorial")
        stats = self.engine.pin_strategy.get_stats()
        assert stats["total_strategies"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AffiliateMapper
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor_affiliate(self):
        result = self.engine.map_affiliate("home_decor")
        assert result["product"] is not None
        assert result["url"] is not None

    def test_map_fashion_affiliate(self):
        result = self.engine.map_affiliate("fashion")
        assert result["product"] == "Casual Blazer"

    def test_map_unknown_niche(self):
        result = self.engine.map_affiliate("unknown")
        assert result["product"] == ""
        assert result["confidence"] == 0.0

    def test_get_available_products(self):
        products = self.engine.affiliate_mapper.get_available_products("home_decor")
        assert len(products) > 0

    def test_affiliate_stats(self):
        self.engine.map_affiliate("tech")
        stats = self.engine.affiliate_mapper.get_stats()
        assert stats["total_mappings"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SEOMapper
# ═══════════════════════════════════════════════════════════════════

class TestSEOMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_generate_seo_home_decor(self):
        result = self.engine.generate_seo("home_decor", "inspirational")
        assert len(result["keywords"]) > 0
        assert len(result["long_tail_keywords"]) > 0
        assert len(result["related_topics"]) > 0

    def test_generate_seo_tech(self):
        result = self.engine.generate_seo("tech", "commercial")
        assert "tech gadgets" in result["keywords"]
        assert result["search_intent"] is not None

    def test_generate_seo_food(self):
        result = self.engine.generate_seo("food", "educational")
        assert "easy recipes" in result["keywords"]

    def test_generate_seo_with_title(self):
        result = self.engine.generate_seo("home_decor", "inspirational", "Modern Bedroom Ideas")
        assert any("bedroom" in kw for kw in result["keywords"])

    def test_seo_stats(self):
        self.engine.generate_seo("fashion", "informational")
        stats = self.engine.seo_mapper.get_stats()
        assert stats["total_profiles"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ImageMapper
# ═══════════════════════════════════════════════════════════════════

class TestImageMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_map_home_decor_images(self):
        result = self.engine.map_images("home_decor")
        assert result["featured_image_style"] == "bright_well_lit"
        assert result["pin_image_orientation"] == "vertical"

    def test_map_fashion_images(self):
        result = self.engine.map_images("fashion")
        assert result["featured_image_style"] == "clean_minimal"

    def test_map_tutorial_images(self):
        result = self.engine.map_images("diy", "tutorial")
        assert result.get("needs_step_images") is True

    def test_image_stats(self):
        self.engine.map_images("travel")
        stats = self.engine.image_mapper.get_stats()
        assert stats["total_mappings"] >= 1


# ═══════════════════════════════════════════════════════════════════
# SchedulingMapper
# ═══════════════════════════════════════════════════════════════════

class TestSchedulingMapper:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_schedule_high_confidence(self):
        result = self.engine.schedule("home_decor", "commercial", 0.9)
        assert result["priority"] == "high"
        assert result["suggested_publish_time"] > 0

    def test_schedule_medium_confidence(self):
        result = self.engine.schedule("home_decor", "informational", 0.7)
        assert result["priority"] == "medium"

    def test_schedule_low_confidence(self):
        result = self.engine.schedule("home_decor", "informational", 0.3)
        assert result["priority"] == "low"

    def test_schedule_queue_delay(self):
        result = self.engine.scheduling_mapper.schedule("home_decor", "informational", 0.9, existing_queue=10)
        assert result["priority"] == "low"

    def test_schedule_stats(self):
        self.engine.schedule("tech", "educational", 0.8)
        stats = self.engine.scheduling_mapper.get_stats()
        assert stats["total_scheduled"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ValidationEngine
# ═══════════════════════════════════════════════════════════════════

class TestValidationEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_validate_complete_mapping(self):
        m = ContentMapping(
            article_title="Test",
            website_id="w1",
            website_url="https://example.com",
            account_id="a1",
            account_name="Test Account",
            board_id="b1",
            board_name="Test Board",
            niche="home_decor",
            category=ContentCategory.HOME_DECOR,
            seo_keywords=["kw1", "kw2"],
            pin_strategy=PinStrategy.STANDARD,
            featured_image="style1",
            affiliate_url="https://amzn.to/test",
        )
        result = self.engine.validator.validate_mapping(m)
        assert result["is_validated"] is True
        assert result["validation_score"] >= 80

    def test_validate_incomplete_mapping(self):
        m = ContentMapping(article_title="Incomplete")
        result = self.engine.validator.validate_mapping(m)
        assert result["is_validated"] is False
        assert len(result["issues"]) > 0

    def test_validate_and_get_mapping(self):
        m = self.engine.map_content("Test Title", "Test content")
        result = self.engine.validate(m.mapping_id)
        assert "validation_score" in result

    def test_validate_nonexistent(self):
        result = self.engine.validate("nonexistent")
        assert "error" in result

    def test_validation_stats(self):
        m = ContentMapping(article_title="Stats Test")
        self.engine.validator.validate_mapping(m)
        stats = self.engine.validator.get_stats()
        assert stats["total_validations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RelationshipEngine
# ═══════════════════════════════════════════════════════════════════

class TestRelationshipEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_build_relationships(self):
        m = self.engine.map_content("Bedroom Ideas", "Content about bedrooms")
        result = self.engine.build_relationships(m.mapping_id)
        assert len(result["related_articles"]) > 0
        assert len(result["related_pins"]) > 0
        assert len(result["related_boards"]) > 0

    def test_build_nonexistent(self):
        result = self.engine.build_relationships("nonexistent")
        assert "error" in result

    def test_relationship_stats(self):
        m = self.engine.map_content("Test", "Test content")
        self.engine.build_relationships(m.mapping_id)
        stats = self.engine.relationship_engine.get_stats()
        assert stats["total_relationships"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RecommendationEngine
# ═══════════════════════════════════════════════════════════════════

class TestRecommendationEngine:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_recommend(self):
        m = self.engine.map_content("Test Article", "Some content")
        result = self.engine.recommend(m.mapping_id)
        assert "recommendations" in result

    def test_recommend_nonexistent(self):
        result = self.engine.recommend("nonexistent")
        assert "error" in result

    def test_recommendation_stats(self):
        m = self.engine.map_content("Rec Test", "Content")
        self.engine.recommend(m.mapping_id)
        stats = self.engine.recommendation_engine.get_stats()
        assert stats["total_recommendations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ContentMappingEngine (Facade — Full Pipeline)
# ═══════════════════════════════════════════════════════════════════

class TestContentMappingEngineFacade:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_full_mapping_pipeline(self):
        m = self.engine.map_content(
            article_title="10 Small Bedroom Ideas That Save Space",
            article_content="Transform your small bedroom with smart storage solutions...",
            article_id="art_001",
            keywords=["bedroom", "small space", "storage"],
        )
        assert m is not None
        assert m.mapping_id is not None
        assert m.article_id == "art_001"
        assert m.niche == "home_decor"
        assert m.website_id is not None
        assert m.account_id is not None
        assert m.board_id is not None
        assert m.pin_strategy is not None
        assert m.seo_keywords is not None
        assert m.priority is not None
        assert m.is_validated is not None

    def test_multiple_niches(self):
        niches = [
            ("Fashion Trends 2026", "fashion"),
            ("Healthy Recipes", "food"),
            ("Tech Gadgets", "tech"),
            ("Travel Destinations", "travel"),
            ("Fitness Tips", "fitness"),
        ]
        for title, expected_niche in niches:
            m = self.engine.map_content(title, f"Content about {title}")
            assert m.niche == expected_niche, f"{title}: expected {expected_niche}, got {m.niche}"

    def test_get_mapping(self):
        m = self.engine.map_content("Get Me", "Content")
        found = self.engine.get_mapping(m.mapping_id)
        assert found is not None
        assert found.article_title == "Get Me"

    def test_get_nonexistent_mapping(self):
        assert self.engine.get_mapping("nonexistent") is None

    def test_get_mappings_by_niche(self):
        self.engine.map_content("Bedroom Ideas", "Content", keywords=["bedroom"])
        found = self.engine.get_mappings_by_niche("home_decor")
        assert len(found) >= 1

    def test_get_mappings_by_account(self):
        m = self.engine.map_content("Account Test", "Content")
        found = self.engine.get_mappings_by_account(m.account_id)
        assert len(found) >= 1

    def test_get_all_mappings(self):
        count_before = len(self.engine.get_all_mappings())
        self.engine.map_content("All Test", "Content")
        assert len(self.engine.get_all_mappings()) >= count_before + 1

    def test_delete_mapping(self):
        m = self.engine.map_content("Delete Me", "Content")
        assert self.engine.delete_mapping(m.mapping_id) is True
        assert self.engine.get_mapping(m.mapping_id) is None

    def test_delete_nonexistent(self):
        assert self.engine.delete_mapping("nonexistent") is False


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
        assert "mappings" in status
        assert "classifier" in status
        assert "website_mapper" in status
        assert "account_mapper" in status
        assert "board_mapper" in status
        assert "pin_strategy" in status
        assert "affiliate_mapper" in status
        assert "seo_mapper" in status
        assert "image_mapper" in status
        assert "scheduling_mapper" in status
        assert "validator" in status
        assert "relationship_engine" in status
        assert "recommendation_engine" in status

    def test_status_after_mapping(self):
        self.engine.map_content("Status Test", "Content")
        status = self.engine.get_status()
        assert status["mappings"]["total"] >= 1


# ═══════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def setup_method(self):
        self.engine = ContentMappingEngine()

    def test_get_nonexistent(self):
        assert self.engine.get_mapping("nonexistent") is None

    def test_delete_nonexistent(self):
        assert self.engine.delete_mapping("nonexistent") is False

    def test_classify_empty(self):
        with pytest.raises(ContentClassificationError):
            self.engine.classify("", "")


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
        assert issubclass(ValidationError, Exception)
        assert issubclass(RelationshipError, Exception)
        assert issubclass(RecommendationError, Exception)
        assert issubclass(PinStrategyError, Exception)
        assert issubclass(MappingNotFoundError, Exception)
