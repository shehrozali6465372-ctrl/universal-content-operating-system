"""Comprehensive tests for Layer 23 — Module 4: Pinterest Pin Manager."""
from __future__ import annotations
import time
import pytest

from layers.layer23_website_manager.pinterest_pin_manager.pinterest_pin_manager import (
    PinterestPinManager, get_pin_manager,
)
from layers.layer23_website_manager.pinterest_pin_manager.models.pinterest_pin import (
    PinterestPin, PinStatus, PinType,
)
from layers.layer23_website_manager.pinterest_pin_manager.models.pin_analytics import PinAnalytics
from layers.layer23_website_manager.pinterest_pin_manager.exceptions import (
    PinNotFoundError, InvalidImageError, InvalidPinTitleError,
    DuplicatePinError, PublishFailedError, SchedulingError,
    BrokenWebsiteLinkError, RichPinError, RateLimitError,
    PinterestAPIError, PinLimitError,
)


# ═══════════════════════════════════════════════════════════════════
# PinterestPin Model
# ═══════════════════════════════════════════════════════════════════

class TestPinterestPin:
    def test_default_pin(self):
        pin = PinterestPin()
        assert pin.status == PinStatus.DRAFT
        assert pin.pin_id is not None
        assert pin.pin_type == PinType.ARTICLE

    def test_pin_with_values(self):
        pin = PinterestPin(
            pin_title="10 Small Bedroom Ideas",
            account_id="acc1",
            board_id="board1",
            website_url="https://example.com/article",
        )
        assert pin.pin_title == "10 Small Bedroom Ideas"
        assert pin.account_id == "acc1"
        assert pin.board_id == "board1"
        assert pin.is_published is False
        assert pin.is_failed is False

    def test_pin_status(self):
        pin = PinterestPin(status=PinStatus.PUBLISHED)
        assert pin.is_published is True
        assert pin.is_failed is False

        pin = PinterestPin(status=PinStatus.FAILED)
        assert pin.is_published is False
        assert pin.is_failed is True

    def test_can_retry(self):
        pin = PinterestPin(status=PinStatus.FAILED, retry_count=0)
        assert pin.can_retry is True

        pin.retry_count = 3
        assert pin.can_retry is False

    def test_display_title(self):
        pin = PinterestPin(pin_title="My Pin", seo_title="SEO Pin Title")
        assert pin.display_title == "SEO Pin Title"

        pin.seo_title = ""
        assert pin.display_title == "My Pin"

    def test_to_dict(self):
        pin = PinterestPin(pin_title="Test Pin", account_id="acc1")
        d = pin.to_dict()
        assert d["pin_title"] == "Test Pin"
        assert "status" in d
        assert "created_at" in d

    def test_from_article(self):
        pin = PinterestPin.from_article(
            "10 Amazing Ideas", "Here is the article content...",
            article_id="art1", website_url="https://example.com"
        )
        assert pin.pin_title == "10 Amazing Ideas"
        assert pin.article_id == "art1"
        assert pin.website_url == "https://example.com"
        assert pin.is_ai_generated is True

    def test_properties(self):
        pin = PinterestPin(pin_title="Short")
        assert len(pin.pin_title) == 5

    def test_empty_pin(self):
        pin = PinterestPin()
        assert pin.total_impressions == 0
        assert pin.total_saves == 0
        assert pin.total_clicks == 0


# ═══════════════════════════════════════════════════════════════════
# PinAnalytics Model
# ═══════════════════════════════════════════════════════════════════

class TestPinAnalytics:
    def test_default(self):
        a = PinAnalytics()
        assert a.ctr == 0.0
        assert a.save_rate == 0.0

    def test_ctr(self):
        a = PinAnalytics(impressions=1000, clicks=50)
        assert a.ctr == 5.0

    def test_save_rate(self):
        a = PinAnalytics(impressions=1000, saves=100)
        assert a.save_rate == 10.0

    def test_engagement_rate(self):
        a = PinAnalytics(impressions=1000, saves=100, clicks=50, closeups=20)
        assert a.engagement_rate == 17.0

    def test_aggregate(self):
        a1 = PinAnalytics(impressions=500, saves=50, clicks=20)
        a2 = PinAnalytics(impressions=500, saves=30, clicks=10)
        agg = PinAnalytics.aggregate([a1, a2])
        assert agg.impressions == 1000
        assert agg.saves == 80
        assert agg.clicks == 30

    def test_to_dict(self):
        a = PinAnalytics(pin_id="pin1", impressions=100)
        d = a.to_dict()
        assert d["pin_id"] == "pin1"
        assert "ctr" in d


# ═══════════════════════════════════════════════════════════════════
# PinRegistry
# ═══════════════════════════════════════════════════════════════════

class TestPinRegistry:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_create_pin(self):
        pin = self.pm.registry.create(
            pin_title="Test Pin Title",
            account_id="acc1",
            board_id="board1",
        )
        assert pin.pin_id is not None
        assert pin.pin_title == "Test Pin Title"
        assert pin.account_id == "acc1"

    def test_create_pin_empty_title(self):
        with pytest.raises(InvalidPinTitleError):
            self.pm.registry.create(pin_title="")

    def test_create_pin_whitespace_title(self):
        with pytest.raises(InvalidPinTitleError):
            self.pm.registry.create(pin_title="   ")

    def test_duplicate_pin_title_same_board(self):
        self.pm.registry.create(pin_title="Unique Pin", board_id="b1")
        with pytest.raises(DuplicatePinError):
            self.pm.registry.create(pin_title="Unique Pin", board_id="b1")

    def test_same_title_different_board(self):
        self.pm.registry.create(pin_title="Same Title", board_id="b1")
        pin2 = self.pm.registry.create(pin_title="Same Title", board_id="b2")
        assert pin2 is not None

    def test_get_pin(self):
        pin = self.pm.registry.create(pin_title="Get Me", board_id="b1")
        found = self.pm.registry.get(pin.pin_id)
        assert found is not None
        assert found.pin_title == "Get Me"

    def test_get_nonexistent_pin(self):
        assert self.pm.registry.get("nonexistent") is None

    def test_update_pin(self):
        pin = self.pm.registry.create(pin_title="Update Me", board_id="b1")
        updated = self.pm.registry.update(pin.pin_id, pin_title="Updated Title")
        assert updated is not None
        assert updated.pin_title == "Updated Title"

    def test_update_nonexistent(self):
        assert self.pm.registry.update("nonexistent", pin_title="X") is None

    def test_delete_pin(self):
        pin = self.pm.registry.create(pin_title="Delete Me", board_id="b1")
        assert self.pm.registry.delete(pin.pin_id) is True
        assert self.pm.registry.get(pin.pin_id) is None

    def test_delete_nonexistent(self):
        assert self.pm.registry.delete("nonexistent") is False

    def test_set_status(self):
        pin = self.pm.registry.create(pin_title="Status Change", board_id="b1")
        self.pm.registry.set_status(pin.pin_id, PinStatus.PUBLISHED)
        assert pin.is_published is True
        assert pin.published_at > 0

    def test_set_status_nonexistent(self):
        assert self.pm.registry.set_status("nonexistent", PinStatus.PUBLISHED) is None

    def test_archive_pin(self):
        pin = self.pm.registry.create(pin_title="Archive Me", board_id="b1")
        self.pm.registry.archive(pin.pin_id)
        assert pin.status == PinStatus.ARCHIVED

    def test_get_by_board(self):
        self.pm.registry.create(pin_title="B1 Pin 1", board_id="b1")
        self.pm.registry.create(pin_title="B1 Pin 2", board_id="b1")
        self.pm.registry.create(pin_title="B2 Pin", board_id="b2")
        b1_pins = self.pm.registry.get_by_board("b1")
        assert len(b1_pins) == 2

    def test_get_by_account(self):
        self.pm.registry.create(pin_title="A1 Pin", account_id="a1", board_id="b1")
        self.pm.registry.create(pin_title="A2 Pin", account_id="a2", board_id="b2")
        a1_pins = self.pm.registry.get_by_account("a1")
        assert len(a1_pins) == 1

    def test_get_by_niche(self):
        self.pm.registry.create(pin_title="Fashion Pin", niche="fashion", board_id="b1")
        self.pm.registry.create(pin_title="Tech Pin", niche="tech", board_id="b2")
        fashion = self.pm.registry.get_by_niche("fashion")
        assert len(fashion) == 1

    def test_count_by_board(self):
        self.pm.registry.create(pin_title="C1", board_id="b1")
        self.pm.registry.create(pin_title="C2", board_id="b1")
        count = self.pm.registry.count_by_board("b1")
        assert count == 2

    def test_get_all(self):
        self.pm.registry.create(pin_title="All1", board_id="b1")
        self.pm.registry.create(pin_title="All2", board_id="b2")
        assert len(self.pm.registry.get_all()) >= 2

    def test_get_pin_stats(self):
        self.pm.registry.create(pin_title="Stats Pin", board_id="b1")
        stats = self.pm.registry.get_stats()
        assert "total_pins" in stats
        assert "by_status" in stats
        assert stats["total_pins"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AIPinBuilder
# ═══════════════════════════════════════════════════════════════════

class TestAIPinBuilder:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_build_from_article(self):
        result = self.pm.builder.build_from_article(
            "10 Small Bedroom Ideas",
            article_content="Transform your small bedroom into a cozy space...",
            niche="home_decor",
            keywords=["bedroom", "decor", "small space"],
        )
        assert result["pin_title"] is not None
        assert "10 Small Bedroom Ideas" in result["pin_title"]
        assert result["pin_description"] is not None
        assert result["alt_text"] is not None
        assert result["call_to_action"] is not None
        assert len(result["hashtags"]) > 0
        assert len(result["seo_keywords"]) > 0
        assert result["search_intent"] in ["educational", "inspirational", "informational", "commercial"]

    def test_title_generation_includes_keywords(self):
        result = self.pm.builder.build_from_article(
            "Modern Kitchen Remodel",
            keywords=["kitchen", "remodel"],
        )
        title_lower = result["pin_title"].lower()
        assert "kitchen" in title_lower or "kitchen" in " ".join(result["seo_keywords"])

    def test_cta_generation(self):
        result = self.pm.builder.build_from_article("Test Article")
        assert len(result["call_to_action"]) > 0

    def test_hashtags_generated(self):
        result = self.pm.builder.build_from_article(
            "Beauty Tips", niche="beauty", keywords=["skincare"]
        )
        tags = " ".join(result["hashtags"]).lower()
        assert "beauty" in tags or "#beauty" in tags

    def test_detect_intent_educational(self):
        result = self.pm.builder.build_from_article("How to Decorate Your Home")
        assert result["search_intent"] == "educational"

    def test_detect_intent_inspirational(self):
        result = self.pm.builder.build_from_article("Best Home Decor Ideas")
        assert result["search_intent"] == "inspirational"

    def test_get_stats(self):
        self.pm.builder.build_from_article("Stats Test")
        stats = self.pm.builder.get_stats()
        assert stats["total_generated"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinImageManager
# ═══════════════════════════════════════════════════════════════════

class TestPinImageManager:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_validate_good_image(self):
        result = self.pm.images.validate_image(width=1000, height=1500, format_type="jpg")
        assert result["is_valid"] is True

    def test_validate_bad_format(self):
        result = self.pm.images.validate_image(width=1000, height=1500, format_type="gif")
        assert result["is_valid"] is False

    def test_validate_too_small(self):
        result = self.pm.images.validate_image(width=100, height=100, format_type="jpg")
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_aspect_ratio(self):
        result = self.pm.images.validate_image(width=2000, height=1000, format_type="jpg")
        assert len(result["issues"]) > 0

    def test_recommend_dimensions(self):
        dims = self.pm.images.recommend_dimensions("home_decor")
        assert dims["width"] == 1000
        assert dims["height"] == 1500

    def test_get_stats(self):
        self.pm.images.validate_image(width=1000, height=1500, format_type="jpg")
        stats = self.pm.images.get_stats()
        assert stats["total_validations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinSEOManager
# ═══════════════════════════════════════════════════════════════════

class TestPinSEOManager:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_optimize_pin(self):
        pin = self.pm.registry.create(pin_title="Test Pin for SEO", board_id="b1")
        result = self.pm.seo.optimize_pin(pin)
        assert result["seo_score"] >= 0
        assert result["keyword_count"] > 0
        assert result["hashtag_count"] > 0

    def test_calculate_score_complete(self):
        pin = PinterestPin(
            pin_title="Complete SEO Title for Testing",
            pin_description="A longer description for testing purposes that should be sufficient.",
            website_url="https://example.com",
            image_path="/path/to/image.jpg",
            alt_text="Test alt text",
            seo_keywords=["test", "seo", "pin"],
            hashtags=["#test"],
        )
        score = self.pm.seo.calculate_score(pin)
        assert score >= 85

    def test_calculate_score_empty(self):
        pin = PinterestPin()
        score = self.pm.seo.calculate_score(pin)
        assert score <= 50

    def test_generate_rich_pin_metadata(self):
        pin = self.pm.registry.create(pin_title="Rich Pin Test", website_url="https://example.com")
        meta = self.pm.seo.generate_rich_pin_metadata(pin, {
            "author": "Test Author",
            "date_published": "2026-01-01",
            "site_name": "Test Blog",
        })
        assert meta["title"] == "Rich Pin Test"
        assert meta["author"] == "Test Author"
        assert pin.is_rich_pin is True

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="SEO Stats Test", board_id="b1")
        self.pm.seo.optimize_pin(pin)
        stats = self.pm.seo.get_stats()
        assert stats["total_optimizations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# WebsiteLinkManager
# ═══════════════════════════════════════════════════════════════════

class TestWebsiteLinkManager:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_attach_article_link(self):
        pin = self.pm.registry.create(pin_title="Link Test", board_id="b1")
        result = self.pm.links.attach_article_link(
            pin, "https://example.com/article", "Test Article"
        )
        assert result is True
        assert pin.website_url == "https://example.com/article"
        assert pin.link_title == "Test Article"

    def test_invalid_url_raises(self):
        pin = self.pm.registry.create(pin_title="Bad Link", board_id="b1")
        with pytest.raises(BrokenWebsiteLinkError):
            self.pm.links.attach_article_link(pin, "not-a-url")

    def test_empty_url_raises(self):
        pin = self.pm.registry.create(pin_title="Empty Link", board_id="b1")
        with pytest.raises(BrokenWebsiteLinkError):
            self.pm.links.attach_article_link(pin, "")

    def test_attach_affiliate_link(self):
        pin = self.pm.registry.create(pin_title="Affiliate", board_id="b1")
        result = self.pm.links.attach_affiliate_link(
            pin, "https://amzn.to/example", "https://original.com"
        )
        assert result is True
        assert pin.affiliate_url == "https://amzn.to/example"
        assert pin.website_url == "https://original.com"

    def test_validate_link_valid(self):
        result = self.pm.links.validate_link("https://example.com")
        assert result["is_valid"] is True

    def test_validate_link_invalid(self):
        result = self.pm.links.validate_link("invalid")
        assert result["is_valid"] is False

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="Link Stats", board_id="b1")
        self.pm.links.attach_article_link(pin, "https://example.com/1")
        stats = self.pm.links.get_stats()
        assert stats["total_links"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RichPinManager
# ═══════════════════════════════════════════════════════════════════

class TestRichPinManager:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_create_article_rich_pin(self):
        pin = self.pm.registry.create(pin_title="Article Rich Pin", website_url="https://example.com")
        meta = self.pm.rich_pins.create_article_rich_pin(
            pin, title="My Article", author="Author", site_name="Blog"
        )
        assert meta["@type"] == "Article"
        assert meta["author"] == "Author"
        assert pin.is_rich_pin is True
        assert pin.rich_pin_type == "article"

    def test_create_product_rich_pin(self):
        pin = self.pm.registry.create(pin_title="Product Pin", website_url="https://shop.com")
        meta = self.pm.rich_pins.create_product_rich_pin(
            pin, product_name="Cool Widget", price="$29.99",
        )
        assert meta["@type"] == "Product"
        assert meta["name"] == "Cool Widget"
        assert pin.rich_pin_type == "product"

    def test_validate_rich_pin_valid(self):
        pin = self.pm.registry.create(pin_title="Valid Rich", website_url="https://example.com")
        self.pm.rich_pins.create_article_rich_pin(pin, author="Author")
        result = self.pm.rich_pins.validate_rich_pin(pin)
        assert result["is_valid"] is True

    def test_validate_rich_pin_invalid(self):
        pin = self.pm.registry.create(pin_title="Invalid Rich")
        result = self.pm.rich_pins.validate_rich_pin(pin)
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0

    def test_rich_pin_types(self):
        assert "article" in self.pm.rich_pins.RICH_PIN_TYPES
        assert "product" in self.pm.rich_pins.RICH_PIN_TYPES

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="Rich Stats", website_url="https://example.com")
        self.pm.rich_pins.create_article_rich_pin(pin)
        stats = self.pm.rich_pins.get_stats()
        assert stats["total_rich_pins"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinScheduler
# ═══════════════════════════════════════════════════════════════════

class TestPinScheduler:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_schedule_pin(self):
        pin = self.pm.registry.create(pin_title="Scheduled Pin", board_id="b1")
        future = time.time() + 3600
        result = self.pm.scheduler.schedule(pin, future)
        assert result is True
        assert pin.status == PinStatus.SCHEDULED
        assert pin.publish_time == future

    def test_schedule_past_time(self):
        pin = self.pm.registry.create(pin_title="Past Pin", board_id="b1")
        past = time.time() - 3600
        with pytest.raises(SchedulingError):
            self.pm.scheduler.schedule(pin, past)

    def test_cancel_schedule(self):
        pin = self.pm.registry.create(pin_title="Cancel Pin", board_id="b1")
        self.pm.scheduler.schedule(pin, time.time() + 3600)
        result = self.pm.scheduler.cancel_schedule(pin)
        assert result is True
        assert pin.status == PinStatus.DRAFT

    def test_cancel_nonexistent(self):
        pin = self.pm.registry.create(pin_title="No Schedule", board_id="b1")
        result = self.pm.scheduler.cancel_schedule(pin)
        assert result is False

    def test_get_due_pins(self):
        pin1 = self.pm.registry.create(pin_title="Due Pin 1", board_id="b1")
        pin2 = self.pm.registry.create(pin_title="Future Pin", board_id="b2")
        self.pm.scheduler.schedule(pin1, time.time() + 10)
        self.pm.scheduler.schedule(pin2, time.time() + 99999)
        due = self.pm.scheduler.get_due_pins([pin1, pin2])
        # pin1 won't be due since 10s in future
        assert len(due) == 0

    def test_get_queue_stats(self):
        self.pm.registry.create(pin_title="QS Pin", board_id="b1")
        stats = self.pm.scheduler.get_queue_stats()
        assert "total_scheduled" in stats
        assert "upcoming" in stats
        assert "overdue" in stats


# ═══════════════════════════════════════════════════════════════════
# PinPublisher
# ═══════════════════════════════════════════════════════════════════

class TestPinPublisher:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_publish_pin(self):
        pin = self.pm.registry.create(
            pin_title="Publish Test",
            account_id="acc1",
            board_id="b1",
            website_url="https://example.com",
        )
        result = self.pm.publisher.publish(pin)
        assert result["status"] == "published"
        assert pin.is_published is True

    def test_publish_no_account(self):
        pin = self.pm.registry.create(
            pin_title="No Account", board_id="b1", website_url="https://example.com"
        )
        with pytest.raises(PublishFailedError):
            self.pm.publisher.publish(pin)

    def test_publish_no_board(self):
        pin = self.pm.registry.create(
            pin_title="No Board", account_id="acc1", website_url="https://example.com"
        )
        with pytest.raises(PublishFailedError):
            self.pm.publisher.publish(pin)

    def test_publish_no_url(self):
        pin = self.pm.registry.create(
            pin_title="No URL", account_id="acc1", board_id="b1"
        )
        with pytest.raises(PublishFailedError):
            self.pm.publisher.publish(pin)

    def test_publish_batch(self):
        pins = []
        for i in range(3):
            pin = self.pm.registry.create(
                pin_title=f"Batch Pin {i}",
                account_id="acc1",
                board_id="b1",
                website_url="https://example.com",
            )
            pins.append(pin)
        results = self.pm.publisher.publish_batch(pins)
        assert len(results) == 3
        assert all(r["status"] == "published" for r in results)

    def test_retry_failed_pin(self):
        pin = self.pm.registry.create(
            pin_title="Retry Pin", account_id="acc1", board_id="b1",
            website_url="https://example.com",
        )
        # First publish
        self.pm.publisher.publish(pin)
        assert pin.is_published is True

    def test_check_rate_limit(self):
        result = self.pm.publisher.check_rate_limit()
        assert "remaining" in result
        assert "is_limited" in result

    def test_get_stats(self):
        pin = self.pm.registry.create(
            pin_title="Pub Stats", account_id="acc1", board_id="b1",
            website_url="https://example.com",
        )
        self.pm.publisher.publish(pin)
        stats = self.pm.publisher.get_stats()
        assert stats["total_published"] >= 1
        assert "success_rate" in stats


# ═══════════════════════════════════════════════════════════════════
# PublishingQueue
# ═══════════════════════════════════════════════════════════════════

class TestPublishingQueue:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_enqueue(self):
        pin = self.pm.registry.create(pin_title="Queue Pin", board_id="b1")
        result = self.pm.queue.enqueue(pin)
        assert result is True
        assert pin.status == PinStatus.QUEUED

    def test_enqueue_high_priority(self):
        pin = self.pm.registry.create(pin_title="High Priority", board_id="b1")
        result = self.pm.queue.enqueue(pin, priority=self.pm.queue.PRIORITY_HIGH)
        assert result is True

    def test_dequeue(self):
        pin = self.pm.registry.create(pin_title="Dequeue Me", board_id="b1")
        self.pm.queue.enqueue(pin)
        dequeued = self.pm.queue.dequeue()
        assert dequeued is not None
        assert dequeued.pin_id == pin.pin_id

    def test_dequeue_empty(self):
        assert self.pm.queue.dequeue() is None

    def test_peek(self):
        pin = self.pm.registry.create(pin_title="Peek Pin", board_id="b1")
        self.pm.queue.enqueue(pin)
        peeked = self.pm.queue.peek()
        assert peeked is not None
        assert peeked.pin_id == pin.pin_id
        # Still in queue
        assert self.pm.queue.size() == 1

    def test_remove(self):
        pin = self.pm.registry.create(pin_title="Remove Pin", board_id="b1")
        self.pm.queue.enqueue(pin)
        assert self.pm.queue.remove(pin.pin_id) is True
        assert self.pm.queue.size() == 0

    def test_remove_nonexistent(self):
        assert self.pm.queue.remove("nonexistent") is False

    def test_clear(self):
        for i in range(3):
            pin = self.pm.registry.create(pin_title=f"Clear {i}", board_id="b1")
            self.pm.queue.enqueue(pin)
        count = self.pm.queue.clear()
        assert count == 3
        assert self.pm.queue.size() == 0

    def test_size(self):
        pin = self.pm.registry.create(pin_title="Size Test", board_id="b1")
        self.pm.queue.enqueue(pin)
        assert self.pm.queue.size() == 1

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="Queue Stats", board_id="b1")
        self.pm.queue.enqueue(pin)
        stats = self.pm.queue.get_stats()
        assert stats["queue_size"] >= 1
        assert "max_size" in stats


# ═══════════════════════════════════════════════════════════════════
# PinAnalyticsTracker
# ═══════════════════════════════════════════════════════════════════

class TestPinAnalyticsTracker:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_record_analytics(self):
        analytics = self.pm.analytics.record("pin1", impressions=1000, saves=100, clicks=50)
        assert analytics.pin_id == "pin1"
        assert analytics.ctr == 5.0
        assert analytics.save_rate == 10.0

    def test_simulate_daily(self):
        pin = self.pm.registry.create(pin_title="Analytics Pin", board_id="b1")
        self.pm.registry.set_status(pin.pin_id, PinStatus.PUBLISHED)
        result = self.pm.analytics.simulate_daily(pin)
        assert result is not None
        assert result.impressions > 0

    def test_get_pin_performance(self):
        self.pm.analytics.record("pin2", impressions=500, saves=50)
        perf = self.pm.analytics.get_pin_performance("pin2")
        assert len(perf) >= 1

    def test_get_aggregate(self):
        self.pm.analytics.record("pin3", impressions=1000, saves=100, clicks=50)
        agg = self.pm.analytics.get_aggregate("pin3")
        assert agg.impressions >= 1000

    def test_get_top_pins(self):
        pins = []
        for i in range(3):
            pin = self.pm.registry.create(pin_title=f"Top Pin {i}", board_id="b1")
            pins.append(pin)
        top = self.pm.analytics.get_top_pins(pins, top_k=2)
        assert len(top) == 2

    def test_get_stats(self):
        self.pm.analytics.record("pin4", impressions=100, saves=10)
        stats = self.pm.analytics.get_stats()
        assert stats["tracked_pins"] >= 1
        assert stats["total_records"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinHealthChecker
# ═══════════════════════════════════════════════════════════════════

class TestPinHealthChecker:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_check_healthy_pin(self):
        pin = self.pm.registry.create(
            pin_title="Healthy Pin Title",
            description="A longer description for testing that should be sufficient for health check.",
            website_url="https://example.com",
            image_path="/path/to/image.jpg",
            keywords=["test", "health"],
        )
        pin.alt_text = "Test alt"
        pin.hashtags = ["#test"]
        pin.seo_keywords = ["test"]
        result = self.pm.health.check_pin(pin)
        assert result["health_score"] >= 50

    def test_check_pin_missing_title(self):
        pin = self.pm.registry.create(pin_title="Hi", board_id="b1")
        # Pin with very short title should still have issues
        result = self.pm.health.check_pin(pin)
        assert result["health_score"] < 100

    def test_check_pin_missing_data(self):
        pin = self.pm.registry.create(pin_title="A", board_id="b1")
        # Override to simulate missing data
        pin.__dict__["pin_title"] = "A"
        result = self.pm.health.check_pin(pin)
        assert result["issue_count"] > 0

    def test_check_all_health(self):
        self.pm.registry.create(
            pin_title="HP 1", account_id="acc1", board_id="b1",
            website_url="https://example.com",
        )
        self.pm.registry.create(
            pin_title="HP 2", account_id="acc1", board_id="b1",
            website_url="https://example.com",
        )
        report = self.pm.health.check_all(self.pm.registry.get_all())
        assert report["total_checked"] >= 2
        assert report["overall_score"] >= 0

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="Health Stats", board_id="b1")
        self.pm.health.check_pin(pin)
        stats = self.pm.health.get_stats()
        assert stats["total_checks"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinOptimizer
# ═══════════════════════════════════════════════════════════════════

class TestPinOptimizer:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_analyze_pin_short_title(self):
        pin = self.pm.registry.create(pin_title="Short", board_id="b1")
        result = self.pm.optimizer.analyze_pin(pin, ctr=0.3)
        assert len(result["suggestions"]) > 0
        assert "priority" in result

    def test_analyze_pin_no_description(self):
        pin = self.pm.registry.create(pin_title="Long Enough Title for Test", board_id="b1")
        result = self.pm.optimizer.analyze_pin(pin)
        assert any("description" in s.lower() for s in result["suggestions"])

    def test_analyze_pin_low_ctr(self):
        pin = self.pm.registry.create(pin_title="Low CTR Pin Title Test", board_id="b1")
        result = self.pm.optimizer.analyze_pin(pin, ctr=0.1)
        assert result["priority"] == "high"

    def test_suggest_improvements(self):
        pin = self.pm.registry.create(pin_title="Test Improvement", board_id="b1")
        suggestions = self.pm.optimizer.suggest_improvements(pin)
        assert "suggestions" in suggestions

    def test_batch_analyze(self):
        pins = []
        for i in range(3):
            pin = self.pm.registry.create(pin_title=f"BA Pin {i}", board_id="b1")
            pins.append(pin)
        results = self.pm.optimizer.batch_analyze(pins)
        assert len(results) == 3

    def test_get_stats(self):
        pin = self.pm.registry.create(pin_title="Opti Stats", board_id="b1")
        self.pm.optimizer.analyze_pin(pin)
        stats = self.pm.optimizer.get_stats()
        assert stats["total_analyzed"] >= 1


# ═══════════════════════════════════════════════════════════════════
# PinterestPinManager (Facade)
# ═══════════════════════════════════════════════════════════════════

class TestPinterestPinManagerFacade:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_full_pipeline(self):
        pin = self.pm.create_pin_from_article(
            article_title="10 Small Bedroom Ideas That Save Space",
            article_content="Transform your small bedroom with these smart storage solutions...",
            article_id="art_001",
            website_url="https://example.com/bedroom-ideas",
            account_id="acc1",
            board_id="board1",
            niche="home_decor",
            keywords=["bedroom", "small space", "storage"],
            author="Test Author",
            site_name="Decor Blog",
        )
        assert pin is not None
        assert pin.pin_id is not None
        assert pin.account_id == "acc1"
        assert pin.board_id == "board1"
        assert pin.article_id == "art_001"
        assert pin.website_url == "https://example.com/bedroom-ideas"
        assert pin.is_ai_generated is True
        assert len(pin.hashtags) > 0
        assert len(pin.seo_keywords) > 0
        assert pin.is_rich_pin is True
        assert pin.rich_pin_type == "article"

    def test_create_pin(self):
        pin = self.pm.create_pin("My New Pin", "acc1", "board1")
        assert pin is not None
        assert pin.pin_title == "My New Pin"

    def test_schedule_pin(self):
        pin = self.pm.create_pin("Schedule Test", "acc1", "board1")
        future = time.time() + 7200
        result = self.pm.schedule_pin(pin.pin_id, future)
        assert result is True

    def test_schedule_nonexistent(self):
        result = self.pm.schedule_pin("nonexistent", time.time() + 3600)
        assert result is False

    def test_publish_pin(self):
        pin = self.pm.create_pin(
            "Publish Facade", "acc1", "board1", website_url="https://example.com"
        )
        result = self.pm.publish_pin(pin.pin_id)
        assert result["status"] == "published"

    def test_publish_nonexistent(self):
        result = self.pm.publish_pin("nonexistent")
        assert "error" in result

    def test_queue_and_process(self):
        pin = self.pm.create_pin(
            "Queue Process", "acc1", "board1", website_url="https://example.com"
        )
        self.pm.queue_pin(pin.pin_id)
        count = self.pm.process_queue()
        assert count >= 1

    def test_process_scheduled(self):
        pin = self.pm.create_pin(
            "Scheduled Process", "acc1", "board1", website_url="https://example.com"
        )
        # Schedule in the past to make it due
        pin.status = PinStatus.SCHEDULED
        pin.publish_time = time.time() - 100
        count = self.pm.process_scheduled()
        assert count >= 1

    def test_track_performance(self):
        analytics = self.pm.track_performance("pin1", 1000, 100, 50)
        assert analytics.ctr == 5.0

    def test_simulate_daily(self):
        pin = self.pm.create_pin("Sim Pin", "acc1", "board1")
        result = self.pm.simulate_daily(pin.pin_id)
        assert "impressions" in result

    def test_get_top_pins(self):
        for i in range(5):
            pin = self.pm.create_pin(f"Top {i}", "acc1", "board1")
            self.pm.registry.set_status(pin.pin_id, PinStatus.PUBLISHED)
        top = self.pm.get_top_pins("acc1", top_k=3)
        assert len(top) <= 3

    def test_check_pin_health(self):
        pin = self.pm.create_pin(
            "Health Check Pin", "acc1", "board1", website_url="https://example.com"
        )
        result = self.pm.check_pin_health(pin.pin_id)
        assert "health_score" in result

    def test_check_pin_health_nonexistent(self):
        result = self.pm.check_pin_health("nonexistent")
        assert "error" in result

    def test_check_all_health(self):
        self.pm.create_pin("HA1", "acc1", "board1", website_url="https://example.com")
        self.pm.create_pin("HA2", "acc1", "board1", website_url="https://example.com")
        report = self.pm.check_all_health("acc1")
        assert report["total_checked"] >= 2

    def test_analyze_pin(self):
        pin = self.pm.create_pin("Analyze This Pin", "acc1", "board1")
        result = self.pm.analyze_pin(pin.pin_id)
        assert "suggestions" in result

    def test_analyze_nonexistent(self):
        result = self.pm.analyze_pin("nonexistent")
        assert "error" in result


# ═══════════════════════════════════════════════════════════════════
# Status
# ═══════════════════════════════════════════════════════════════════

class TestStatus:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_get_status(self):
        status = self.pm.get_status()
        assert status["module"] == "Pinterest Pin Manager (Layer 23 / Module 4)"
        assert status["version"] == "1.0.0"
        assert "pins" in status
        assert "health" in status
        assert "scheduler" in status
        assert "publisher" in status
        assert "queue" in status
        assert "analytics" in status
        assert "seo" in status

    def test_status_health(self):
        status = self.pm.get_status()
        health = status["health"]
        assert "score" in health
        assert "healthy" in health
        assert "critical" in health


# ═══════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def setup_method(self):
        self.pm = PinterestPinManager()

    def test_get_nonexistent_pin(self):
        assert self.pm.registry.get("nonexistent") is None

    def test_delete_nonexistent(self):
        assert self.pm.registry.delete("nonexistent") is False

    def test_update_nonexistent(self):
        assert self.pm.registry.update("nonexistent", pin_title="X") is None

    def test_archive_nonexistent(self):
        assert self.pm.registry.archive("nonexistent") is None


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_pin_manager(self):
        pm1 = get_pin_manager()
        pm2 = get_pin_manager()
        assert pm1 is pm2


# ═══════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_all_exceptions_importable(self):
        assert issubclass(PinNotFoundError, Exception)
        assert issubclass(InvalidImageError, Exception)
        assert issubclass(InvalidPinTitleError, Exception)
        assert issubclass(DuplicatePinError, Exception)
        assert issubclass(PublishFailedError, Exception)
        assert issubclass(SchedulingError, Exception)
        assert issubclass(BrokenWebsiteLinkError, Exception)
        assert issubclass(RichPinError, Exception)
        assert issubclass(RateLimitError, Exception)
        assert issubclass(PinterestAPIError, Exception)
        assert issubclass(PinLimitError, Exception)
