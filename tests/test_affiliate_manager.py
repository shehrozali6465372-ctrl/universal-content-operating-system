"""Comprehensive tests for Layer 23 — Module 6: Affiliate Manager."""
from __future__ import annotations
import time
import pytest

from layers.layer23_website_manager.affiliate_manager.affiliate_manager import (
    AffiliateManager, get_affiliate_manager,
)
from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateNetwork, Merchant, AffiliateProduct, AffiliateClick,
    AffiliateLink, NetworkStatus, ProductStatus, LinkType,
)
from layers.layer23_website_manager.affiliate_manager.exceptions import (
    AffiliateNetworkError, MerchantNotFoundError, ProductNotFoundError,
    BrokenAffiliateLinkError, InvalidCommissionError, ComplianceError,
    RevenueTrackingError, ProductMatchingError, LinkGenerationError,
    InsertionError,
)


# ═══════════════════════════════════════════════════════════════════
# Data Models
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateNetwork:
    def test_default(self):
        n = AffiliateNetwork()
        assert n.status == NetworkStatus.PENDING
        assert n.network_id is not None

    def test_with_values(self):
        n = AffiliateNetwork(network_name="Amazon Associates", country="US",
                               commission_rate=6.0, cookie_days=1)
        assert n.network_name == "Amazon Associates"
        assert n.commission_rate == 6.0
        assert n.is_active is False

    def test_is_active(self):
        n = AffiliateNetwork(status=NetworkStatus.ACTIVE)
        assert n.is_active is True

    def test_to_dict(self):
        n = AffiliateNetwork(network_name="Test Net")
        d = n.to_dict()
        assert d["network_name"] == "Test Net"


class TestMerchant:
    def test_default(self):
        m = Merchant()
        assert m.merchant_id is not None
        assert m.status == NetworkStatus.PENDING

    def test_with_values(self):
        m = Merchant(merchant_name="Nike", category="fashion", commission_rate=5.0)
        assert m.merchant_name == "Nike"
        assert m.commission_rate == 5.0

    def test_to_dict(self):
        m = Merchant(merchant_name="Test Merchant")
        d = m.to_dict()
        assert d["merchant_name"] == "Test Merchant"


class TestAffiliateProduct:
    def test_default(self):
        p = AffiliateProduct()
        assert p.status == ProductStatus.PENDING
        assert p.epc == 0.0

    def test_with_values(self):
        p = AffiliateProduct(product_name="Test Product", price=29.99,
                               rating=4.5, commission_rate=6.0,
                               niche="home_decor")
        assert p.product_name == "Test Product"
        assert p.price == 29.99
        assert p.is_available is False

    def test_is_available(self):
        p = AffiliateProduct(status=ProductStatus.IN_STOCK)
        assert p.is_available is True

    def test_epc(self):
        p = AffiliateProduct(total_clicks=100, total_commission=50.0)
        assert p.epc == 0.5

    def test_epc_zero_clicks(self):
        p = AffiliateProduct()
        assert p.epc == 0.0

    def test_to_dict(self):
        p = AffiliateProduct(product_name="Test")
        d = p.to_dict()
        assert d["product_name"] == "Test"


class TestAffiliateClick:
    def test_default(self):
        c = AffiliateClick()
        assert c.click_id is not None
        assert c.converted is False

    def test_with_values(self):
        c = AffiliateClick(product_id="p1", source="pinterest", sale_amount=50.0, commission=3.0)
        assert c.commission == 3.0

    def test_to_dict(self):
        c = AffiliateClick(product_id="p1")
        d = c.to_dict()
        assert d["product_id"] == "p1"


class TestAffiliateLink:
    def test_default(self):
        l = AffiliateLink()
        assert l.link_type == LinkType.DEEP_LINK
        assert l.is_active is True

    def test_to_dict(self):
        l = AffiliateLink(affiliate_url="https://amzn.to/test")
        d = l.to_dict()
        assert "affiliate_url" in d


# ═══════════════════════════════════════════════════════════════════
# AffiliateNetworkManager
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateNetworkManager:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_register_network(self):
        net = self.am.register_network("Test Network", "US", "key123", 10.0)
        assert net.network_name == "Test Network"
        assert net.status == NetworkStatus.PENDING

    def test_load_presets(self):
        self.am.initialize()
        nets = self.am.get_all_networks()
        assert len(nets) >= 8

    def test_get_network(self):
        net = self.am.register_network("Get Test")
        found = self.am.get_network(net.network_id)
        assert found is not None
        assert found.network_name == "Get Test"

    def test_get_nonexistent_network(self):
        assert self.am.get_network("nonexistent") is None

    def test_activate_network(self):
        net = self.am.register_network("Activate Test")
        assert self.am.activate_network(net.network_id) is True
        assert net.is_active is True

    def test_deactivate_network(self):
        net = self.am.register_network("Deactivate Test")
        self.am.activate_network(net.network_id)
        assert self.am.deactivate_network(net.network_id) is True
        assert net.is_active is False

    def test_activate_nonexistent(self):
        assert self.am.activate_network("nonexistent") is False

    def test_network_stats(self):
        self.am.register_network("Stats Net")
        stats = self.am.networks.get_stats()
        assert stats["total_networks"] >= 1


# ═══════════════════════════════════════════════════════════════════
# MerchantManager
# ═══════════════════════════════════════════════════════════════════

class TestMerchantManager:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_register_merchant(self):
        m = self.am.register_merchant("Test Merchant", commission_rate=5.0, category="tech")
        assert m.merchant_name == "Test Merchant"
        assert m.commission_rate == 5.0

    def test_get_merchant(self):
        m = self.am.register_merchant("Get Merchant")
        found = self.am.get_merchant(m.merchant_id)
        assert found is not None

    def test_get_nonexistent_merchant(self):
        assert self.am.get_merchant("nonexistent") is None

    def test_get_all_merchants(self):
        self.am.register_merchant("M1")
        self.am.register_merchant("M2")
        assert len(self.am.get_all_merchants()) >= 2

    def test_get_merchants_by_category(self):
        self.am.register_merchant("Cat1", category="fashion")
        cats = self.am.merchants.get_merchants_by_category("fashion")
        assert len(cats) >= 1

    def test_delete_merchant(self):
        m = self.am.register_merchant("Delete Me")
        assert self.am.merchants.delete_merchant(m.merchant_id) is True
        assert self.am.get_merchant(m.merchant_id) is None

    def test_merchant_stats(self):
        self.am.register_merchant("Stats")
        stats = self.am.merchants.get_stats()
        assert stats["total_merchants"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ProductDatabase
# ═══════════════════════════════════════════════════════════════════

class TestProductDatabase:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_add_product(self):
        p = self.am.add_product("Test Product", 29.99, "electronics", "tech", 4.5, 6.0)
        assert p.product_name == "Test Product"
        assert p.price == 29.99

    def test_load_presets(self):
        count = self.am.products.load_presets()
        assert count >= 20

    def test_search_by_niche(self):
        self.am.add_product("Bed Frame", 299.99, "furniture", "home_decor", 4.5, 6.0)
        results = self.am.search_products("home_decor")
        assert len(results) >= 1

    def test_search_by_niche_with_rating(self):
        self.am.add_product("Good Product", 50.0, "electronics", "tech", 4.8, 5.0)
        self.am.add_product("Bad Product", 10.0, "electronics", "tech", 2.0, 3.0)
        results = self.am.search_products("tech", min_rating=4.0)
        assert all(p.rating >= 4.0 for p in results)

    def test_get_product(self):
        p = self.am.add_product("Get Product")
        found = self.am.products.get_product(p.product_id)
        assert found is not None

    def test_get_top_products(self):
        self.am.add_product("Top1", rating=5.0, commission_rate=10.0, niche="tech")
        self.am.add_product("Top2", rating=3.0, commission_rate=2.0, niche="tech")
        top = self.am.get_top_products("tech", 1)
        assert len(top) == 1

    def test_update_stats(self):
        p = self.am.add_product("Stats Product")
        assert self.am.products.update_stats(p.product_id, clicks=100, sales=5, commission=25.0) is True
        assert p.total_clicks == 100
        assert p.total_sales == 5

    def test_product_stats(self):
        self.am.add_product("Stats P")
        stats = self.am.products.get_stats()
        assert stats["total_products"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ProductMatcher
# ═══════════════════════════════════════════════════════════════════

class TestProductMatcher:
    def setup_method(self):
        self.am = AffiliateManager()
        self.am.initialize()

    def test_match_product(self):
        products = self.am.search_products("home_decor")
        result = self.am.matcher.match_product("home_decor", "Bedroom Ideas", "bedroom", ["bedroom"], products)
        assert result["product_id"] != ""

    def test_match_no_products(self):
        result = self.am.matcher.match_product("unknown", "Test", "", [], [])
        assert result["product_id"] == ""
        assert result["confidence"] == 0.0

    def test_match_stats(self):
        products = self.am.search_products("tech")
        self.am.matcher.match_product("tech", "Gadgets", "", [], products)
        stats = self.am.matcher.get_stats()
        assert stats["total_matches"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AffiliateLinkManager
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateLinkManager:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_generate_deep_link(self):
        link = self.am.links.generate_deep_link("p1", "https://amazon.com/product", "test123")
        assert link is not None
        assert "tag=test123" in link.affiliate_url
        assert link.link_type == LinkType.DEEP_LINK

    def test_generate_deep_link_invalid_url(self):
        with pytest.raises(LinkGenerationError):
            self.am.links.generate_deep_link("p1", "not-a-url", "test123")

    def test_generate_short_link(self):
        link = self.am.links.generate_short_link("p1", "https://amazon.com/product")
        assert link.short_url.startswith("https://go.affiliate/")

    def test_generate_tracking_link(self):
        link = self.am.links.generate_tracking_link("p1", "https://amazon.com/product", "pinterest")
        assert "utm_source=pinterest" in link.affiliate_url

    def test_get_link(self):
        link = self.am.links.generate_deep_link("p1", "https://example.com", "aid")
        found = self.am.links.get_link(link.link_id)
        assert found is not None

    def test_deactivate_link(self):
        link = self.am.links.generate_deep_link("p1", "https://example.com", "aid")
        assert self.am.links.deactivate_link(link.link_id) is True
        assert link.is_active is False

    def test_record_click(self):
        link = self.am.links.generate_deep_link("p1", "https://example.com", "aid")
        assert self.am.links.record_click(link.link_id) is True
        assert link.total_clicks == 1

    def test_link_stats(self):
        self.am.links.generate_deep_link("p1", "https://example.com", "aid")
        stats = self.am.links.get_stats()
        assert stats["total_links"] >= 1


# ═══════════════════════════════════════════════════════════════════
# LinkValidator
# ═══════════════════════════════════════════════════════════════════

class TestLinkValidator:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_validate_valid_link(self):
        result = self.am.validate_link("https://amazon.com/product?tag=test123")
        assert result["is_valid"] is True
        assert result["score"] >= 90

    def test_validate_empty_link(self):
        result = self.am.validate_link("")
        assert result["is_valid"] is False
        assert len(result["issues"]) > 0

    def test_validate_missing_amazon_tag(self):
        result = self.am.validate_link("https://amazon.com/product")
        assert result["is_valid"] is False

    def test_check_broken(self):
        result = self.am.validator.check_broken("")
        assert result["is_broken"] is True

    def test_validator_stats(self):
        self.am.validate_link("https://example.com")
        stats = self.am.validator.get_stats()
        assert stats["total_validations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AutoLinkInserter
# ═══════════════════════════════════════════════════════════════════

class TestAutoLinkInserter:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_insert_after_first_paragraph(self):
        content = "First paragraph about the product.\n\nSecond paragraph with more details."
        result = self.am.insert_affiliate_link(content, "https://amzn.to/test", "Check Price")
        assert result["modified_length"] > len(content)
        assert "Check Price" in result["modified_content"]

    def test_insert_empty_content(self):
        with pytest.raises(InsertionError):
            self.am.insert_affiliate_link("", "https://example.com")

    def test_insert_empty_url(self):
        with pytest.raises(InsertionError):
            self.am.insert_affiliate_link("Content here", "")

    def test_insert_multiple(self):
        content = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        links = [
            {"url": "https://amzn.to/1", "text": "Link 1"},
            {"url": "https://amzn.to/2", "text": "Link 2"},
        ]
        result = self.am.inserter.insert_multiple(content, links)
        assert result["total_insertions"] == 2

    def test_inserter_stats(self):
        self.am.insert_affiliate_link("Test content.\n\nMore content.", "https://example.com")
        stats = self.am.inserter.get_stats()
        assert stats["total_insertions"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RevenueTracker
# ═══════════════════════════════════════════════════════════════════

class TestRevenueTracker:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_record_click(self):
        click = self.am.record_click("p1", "pinterest")
        assert click.product_id == "p1"
        assert click.source == "pinterest"
        assert click.converted is False

    def test_record_sale(self):
        click = self.am.record_click("p1")
        assert self.am.record_sale(click.click_id, 50.0, 3.0) is True
        assert click.converted is True
        assert click.commission == 3.0

    def test_record_sale_invalid_click(self):
        assert self.am.record_sale("invalid", 50.0, 3.0) is False

    def test_get_revenue_stats(self):
        for _ in range(10):
            c = self.am.record_click("p1")
            self.am.record_sale(c.click_id, 50.0, 3.0)
        stats = self.am.get_revenue_stats(30)
        assert stats["total_clicks"] >= 10
        assert stats["total_sales"] >= 10

    def test_simulate_day(self):
        result = self.am.revenue_tracker.simulate_day("p1", avg_clicks=100, conversion_rate=2.0)
        assert result["clicks"] > 0
        assert result["commission"] > 0

    def test_revenue_stats(self):
        self.am.record_click("p1")
        stats = self.am.revenue_tracker.get_stats()
        assert stats["total_clicks"] >= 1


# ═══════════════════════════════════════════════════════════════════
# OptimizationEngine
# ═══════════════════════════════════════════════════════════════════

class TestOptimizationEngine:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_analyze_product(self):
        p = self.am.add_product("Test Product", 29.99, niche="tech", rating=3.5, commission_rate=3.0)
        p.total_clicks = 100
        result = self.am.analyze_product(p.product_id)
        assert "suggestions" in result
        assert result["suggestion_count"] > 0

    def test_analyze_nonexistent(self):
        result = self.am.analyze_product("nonexistent")
        assert "error" in result

    def test_batch_analyze(self):
        p1 = self.am.add_product("P1", rating=4.5, commission_rate=8.0)
        p2 = self.am.add_product("P2", rating=2.0, commission_rate=2.0)
        results = self.am.optimizer.batch_analyze([p1, p2])
        assert len(results) == 2

    def test_optimizer_stats(self):
        p = self.am.add_product("Opt Stats")
        self.am.optimizer.analyze_product(p)
        stats = self.am.optimizer.get_stats()
        assert stats["total_analyzed"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AffiliateRecommendationEngine
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateRecommendationEngine:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_recommend_better(self):
        p1 = self.am.add_product("Current", rating=3.0, commission_rate=3.0, niche="tech")
        p2 = self.am.add_product("Better", rating=5.0, commission_rate=10.0, niche="tech")
        result = self.am.recommend_better(p1.product_id)
        assert result["recommended"] == "Better"

    def test_recommend_nonexistent(self):
        result = self.am.recommend_better("nonexistent")
        assert "error" in result

    def test_get_top_trending(self):
        p1 = self.am.add_product("T1", rating=5.0, commission_rate=10.0)
        p2 = self.am.add_product("T2", rating=1.0, commission_rate=1.0)
        top = self.am.recommender.get_top_trending([p1, p2], 1)
        assert len(top) == 1
        assert top[0].product_name == "T1"

    def test_recommender_stats(self):
        p1 = self.am.add_product("Rec1", rating=4.0, commission_rate=5.0, niche="tech")
        p2 = self.am.add_product("Rec2", rating=4.5, commission_rate=8.0, niche="tech")
        self.am.recommend_better(p1.product_id)
        stats = self.am.recommender.get_stats()
        assert stats["total_recommendations"] >= 1


# ═══════════════════════════════════════════════════════════════════
# ComplianceManager
# ═══════════════════════════════════════════════════════════════════

class TestComplianceManager:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_check_disclosure_present(self):
        content = "This post contains affiliate links. We may earn a commission."
        result = self.am.check_compliance(content, "website")
        assert result["has_disclosure"] is True

    def test_check_disclosure_missing(self):
        content = "Just some regular content about home decor and bedroom ideas."
        result = self.am.check_compliance(content, "website")
        assert result["has_disclosure"] is False

    def test_generate_disclosure(self):
        disc = self.am.compliance.generate_disclosure("website")
        assert "affiliate" in disc.lower()

    def test_check_pinterest_compliance(self):
        result = self.am.compliance.check_pinterest_compliance(
            "Check out this amazing product! Affiliate link below."
        )
        assert "is_compliant" in result

    def test_compliance_stats(self):
        self.am.check_compliance("test with affiliate", "website")
        stats = self.am.compliance.get_stats()
        assert stats["total_checks"] >= 1


# ═══════════════════════════════════════════════════════════════════
# RevenueAnalytics
# ═══════════════════════════════════════════════════════════════════

class TestRevenueAnalytics:
    def setup_method(self):
        self.am = AffiliateManager()
        self.am.initialize()

    def test_generate_dashboard(self):
        dashboard = self.am.get_revenue_dashboard()
        assert "summary" in dashboard
        assert "top_products" in dashboard
        assert "by_category" in dashboard

    def test_dashboard_summary(self):
        dashboard = self.am.get_revenue_dashboard()
        assert dashboard["summary"]["total_products"] >= 20

    def test_analytics_stats(self):
        self.am.get_revenue_dashboard()
        stats = self.am.revenue_analytics.get_stats()
        assert stats["total_reports"] >= 1


# ═══════════════════════════════════════════════════════════════════
# AffiliateManager Facade — Full Pipeline
# ═══════════════════════════════════════════════════════════════════

class TestAffiliateManagerFacade:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_initialize(self):
        result = self.am.initialize()
        assert result["networks_loaded"] >= 8
        assert result["products_loaded"] >= 20

    def test_full_match_and_link_pipeline(self):
        self.am.initialize()
        result = self.am.match_and_link(
            "home_decor",
            "10 Small Bedroom Ideas That Save Space",
            "Transform your bedroom with these smart storage solutions.",
            ["bedroom", "storage", "organization"],
        )
        assert result["matched"] is True
        assert "product" in result
        assert "affiliate_link" in result
        assert "validation" in result
        assert "disclosure" in result

    def test_match_and_link_no_match(self):
        result = self.am.match_and_link("unknown_niche", "Test", "")
        assert result["matched"] is False

    def test_match_and_link_different_niches(self):
        self.am.initialize()
        for niche in ["home_decor", "fashion", "tech", "food", "beauty"]:
            result = self.am.match_and_link(niche, f"Best {niche} ideas", f"Content about {niche}")
            if result["matched"]:
                assert result["product"]["commission_rate"] > 0

    def test_get_status(self):
        self.am.initialize()
        status = self.am.get_status()
        assert status["module"] == "Affiliate Manager (Layer 23 / Module 6)"
        assert status["version"] == "1.0.0"
        assert "networks" in status
        assert "merchants" in status
        assert "products" in status
        assert "links" in status
        assert "revenue" in status

    def test_status_after_operations(self):
        self.am.initialize()
        self.am.match_and_link("home_decor", "Test")
        self.am.record_click("p1")
        status = self.am.get_status()
        assert status["operations"]["total"] >= 1


# ═══════════════════════════════════════════════════════════════════
# Error Handling
# ═══════════════════════════════════════════════════════════════════

class TestErrorHandling:
    def setup_method(self):
        self.am = AffiliateManager()

    def test_get_nonexistent_network(self):
        assert self.am.get_network("nonexistent") is None

    def test_get_nonexistent_merchant(self):
        assert self.am.get_merchant("nonexistent") is None

    def test_activate_nonexistent_network(self):
        assert self.am.activate_network("nonexistent") is False

    def test_update_invalid_stats(self):
        assert self.am.products.update_stats("nonexistent", 1, 1, 1.0) is False


# ═══════════════════════════════════════════════════════════════════
# Singleton
# ═══════════════════════════════════════════════════════════════════

class TestSingleton:
    def test_get_affiliate_manager(self):
        a1 = get_affiliate_manager()
        a2 = get_affiliate_manager()
        assert a1 is a2


# ═══════════════════════════════════════════════════════════════════
# Exceptions
# ═══════════════════════════════════════════════════════════════════

class TestExceptions:
    def test_all_exceptions_importable(self):
        assert issubclass(AffiliateNetworkError, Exception)
        assert issubclass(MerchantNotFoundError, Exception)
        assert issubclass(ProductNotFoundError, Exception)
        assert issubclass(BrokenAffiliateLinkError, Exception)
        assert issubclass(InvalidCommissionError, Exception)
        assert issubclass(ComplianceError, Exception)
        assert issubclass(RevenueTrackingError, Exception)
        assert issubclass(ProductMatchingError, Exception)
        assert issubclass(LinkGenerationError, Exception)
        assert issubclass(InsertionError, Exception)
