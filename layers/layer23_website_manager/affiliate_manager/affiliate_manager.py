"""AffiliateManager — Layer 23 / Module 6.

Complete affiliate marketing ecosystem: network management, product matching,
link generation, revenue tracking, optimization, and compliance.

Flow: Content → Product Match → Link Generation → Insertion → Click → Sale → Commission → Analytics
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.affiliate_manager.models.affiliate_models import (
    AffiliateNetwork, Merchant, AffiliateProduct, AffiliateClick,
    AffiliateLink, NetworkStatus, ProductStatus, LinkType,
)
from layers.layer23_website_manager.affiliate_manager.networks.affiliate_network_manager import (
    AffiliateNetworkManager,
)
from layers.layer23_website_manager.affiliate_manager.merchants.merchant_manager import MerchantManager
from layers.layer23_website_manager.affiliate_manager.products.product_database import ProductDatabase
from layers.layer23_website_manager.affiliate_manager.matching.product_matcher import ProductMatcher
from layers.layer23_website_manager.affiliate_manager.links.affiliate_link_manager import AffiliateLinkManager
from layers.layer23_website_manager.affiliate_manager.validation.link_validator import LinkValidator
from layers.layer23_website_manager.affiliate_manager.insertion.auto_link_inserter import AutoLinkInserter
from layers.layer23_website_manager.affiliate_manager.analytics.revenue_tracker import RevenueTracker
from layers.layer23_website_manager.affiliate_manager.analytics.revenue_analytics import RevenueAnalytics
from layers.layer23_website_manager.affiliate_manager.optimization.optimization_engine import OptimizationEngine
from layers.layer23_website_manager.affiliate_manager.optimization.recommendation_engine import (
    AffiliateRecommendationEngine,
)
from layers.layer23_website_manager.affiliate_manager.compliance.compliance_manager import ComplianceManager


class AffiliateManager:
    """Primary facade for Affiliate Manager.

    Full pipeline: Content → Product Match → Link Generation → Insertion → Track → Optimize
    Coordinates 12 sub-modules for end-to-end affiliate monetization.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.networks = AffiliateNetworkManager()
        self.merchants = MerchantManager()
        self.products = ProductDatabase()
        self.matcher = ProductMatcher()
        self.links = AffiliateLinkManager()
        self.validator = LinkValidator()
        self.inserter = AutoLinkInserter()
        self.revenue_tracker = RevenueTracker()
        self.revenue_analytics = RevenueAnalytics()
        self.optimizer = OptimizationEngine()
        self.recommender = AffiliateRecommendationEngine()
        self.compliance = ComplianceManager()

        self._total_operations = 0

    # ─── Initialization ───────────────────────────────────

    def initialize(self) -> Dict[str, Any]:
        """Load presets for networks, merchants, and products."""
        nets = self.networks.load_presets()
        prod_count = self.products.load_presets()
        return {
            "networks_loaded": len(nets),
            "products_loaded": prod_count,
        }

    # ─── Full Pipeline ────────────────────────────────────

    def match_and_link(self, niche: str, article_title: str = "",
                        article_content: str = "",
                        keywords: Optional[List[str]] = None,
                        affiliate_id: str = "universal_ai") -> Dict[str, Any]:
        """Full pipeline: Match product → Generate link → Validate → Return result."""
        if not affiliate_id:
            affiliate_id = "universal_ai"

        # Step 1: Find products by niche
        products = self.products.search_by_niche(niche)

        # Step 2: Match best product
        match = self.matcher.match_product(niche, article_title, article_content,
                                            keywords, products)
        product = match.get("product")

        if not product:
            return {"matched": False, "reason": "No matching product found"}

        # Step 3: Generate affiliate link
        product_url = product.direct_url or f"https://www.amazon.com/dp/{product.product_id}"
        link = self.links.generate_deep_link(product.product_id, product_url, affiliate_id)

        # Step 4: Validate link
        validation = self.validator.validate_link(link.affiliate_url)

        # Step 5: Generate disclosure
        disclosure = self.compliance.generate_disclosure("website")

        result = {
            "matched": True,
            "product": {
                "product_id": product.product_id,
                "product_name": product.product_name,
                "price": product.price,
                "rating": product.rating,
                "commission_rate": product.commission_rate,
            },
            "affiliate_link": {
                "link_id": link.link_id,
                "url": link.affiliate_url,
                "type": link.link_type.value,
            },
            "validation": validation,
            "disclosure": disclosure,
            "confidence": match.get("confidence", 0.0),
        }

        self._log("match_and_link", {"niche": niche, "product": product.product_name})
        return result

    # ─── Network Operations ───────────────────────────────

    def register_network(self, network_name: str, country: str = "US",
                          api_key: str = "", commission_rate: float = 0.0) -> AffiliateNetwork:
        return self.networks.register_network(network_name, country, api_key, commission_rate)

    def get_network(self, network_id: str) -> Optional[AffiliateNetwork]:
        return self.networks.get_network(network_id)

    def get_all_networks(self) -> List[AffiliateNetwork]:
        return self.networks.get_all_networks()

    def activate_network(self, network_id: str) -> bool:
        return self.networks.activate_network(network_id)

    def deactivate_network(self, network_id: str) -> bool:
        return self.networks.deactivate_network(network_id)

    # ─── Merchant Operations ──────────────────────────────

    def register_merchant(self, merchant_name: str, network_id: str = "",
                            commission_rate: float = 0.0,
                            category: str = "") -> Merchant:
        return self.merchants.register_merchant(merchant_name, network_id,
                                                  commission_rate=commission_rate,
                                                  category=category)

    def get_merchant(self, merchant_id: str) -> Optional[Merchant]:
        return self.merchants.get_merchant(merchant_id)

    def get_all_merchants(self) -> List[Merchant]:
        return self.merchants.get_all_merchants()

    # ─── Product Operations ───────────────────────────────

    def add_product(self, product_name: str, price: float = 0.0,
                     category: str = "", niche: str = "",
                     rating: float = 0.0, commission_rate: float = 0.0) -> AffiliateProduct:
        return self.products.add_product(product_name, price, category, niche, rating, commission_rate)

    def search_products(self, niche: str, min_rating: float = 0.0) -> List[AffiliateProduct]:
        return self.products.search_by_niche(niche, min_rating)

    def get_top_products(self, niche: str = "", top_k: int = 5) -> List[AffiliateProduct]:
        return self.products.get_top_products(niche, top_k)

    # ─── Link Operations ──────────────────────────────────

    def generate_link(self, product_id: str, url: str,
                       affiliate_id: str = "universal_ai") -> Optional[AffiliateLink]:
        try:
            return self.links.generate_deep_link(product_id, url, affiliate_id)
        except Exception:
            return None

    def validate_link(self, url: str) -> Dict[str, Any]:
        return self.validator.validate_link(url)

    # ─── Content Insertion ────────────────────────────────

    def insert_affiliate_link(self, content: str, affiliate_url: str,
                                anchor_text: str = "") -> Dict[str, Any]:
        return self.inserter.insert_link(content, affiliate_url, anchor_text)

    def check_compliance(self, content: str, platform: str = "website") -> Dict[str, Any]:
        return self.compliance.check_disclosure(content, platform)

    # ─── Revenue Tracking ─────────────────────────────────

    def record_click(self, product_id: str, source: str = "direct") -> AffiliateClick:
        return self.revenue_tracker.record_click(product_id, source=source)

    def record_sale(self, click_id: str, sale_amount: float,
                     commission: float) -> bool:
        return self.revenue_tracker.record_sale(click_id, sale_amount, commission)

    def get_revenue_stats(self, days: int = 30) -> Dict[str, Any]:
        return self.revenue_tracker.get_revenue_stats(days)

    def get_revenue_dashboard(self) -> Dict[str, Any]:
        return self.revenue_analytics.generate_dashboard(
            self.products.get_all_products(),
            self.merchants.get_all_merchants(),
            self.networks.get_all_networks(),
            self.revenue_tracker.get_stats(),
        )

    # ─── Optimization ─────────────────────────────────────

    def analyze_product(self, product_id: str) -> Dict[str, Any]:
        product = self.products.get_product(product_id)
        if not product:
            return {"error": "Product not found"}
        return self.optimizer.analyze_product(product)

    def recommend_better(self, product_id: str) -> Dict[str, Any]:
        product = self.products.get_product(product_id)
        if not product:
            return {"error": "Product not found"}
        alternatives = self.products.search_by_niche(product.niche)
        return self.recommender.recommend_better_product(product, alternatives)

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        return {
            "module": "Affiliate Manager (Layer 23 / Module 6)",
            "version": "1.0.0",
            "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "networks": self.networks.get_stats(),
            "merchants": self.merchants.get_stats(),
            "products": self.products.get_stats(),
            "links": self.links.get_stats(),
            "revenue": self.revenue_tracker.get_stats(),
            "validator": self.validator.get_stats(),
            "inserter": self.inserter.get_stats(),
            "compliance": self.compliance.get_stats(),
            "optimizer": self.optimizer.get_stats(),
            "recommender": self.recommender.get_stats(),
            "analytics": self.revenue_analytics.get_stats(),
            "matcher": self.matcher.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1


# ─── Singleton ───────────────────────────────────────────────────────────────

_affiliate_manager_instance: Optional[AffiliateManager] = None
_instance_lock = threading.Lock()


def get_affiliate_manager() -> AffiliateManager:
    global _affiliate_manager_instance
    if _affiliate_manager_instance is None:
        with _instance_lock:
            if _affiliate_manager_instance is None:
                _affiliate_manager_instance = AffiliateManager()
    return _affiliate_manager_instance
