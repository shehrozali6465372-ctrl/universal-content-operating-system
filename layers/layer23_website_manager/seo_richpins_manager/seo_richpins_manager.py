"""SEORichPinsManager — Layer 23 / Module 7.

SEO & Rich Pins intelligence for maximum organic traffic from Google and Pinterest.

Flow: Article → Keywords → Meta → Pinterest SEO → Rich Pins → Open Graph → Twitter → Schema → Sitemap → Validate
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import (
    SEOProfile, SEOAnalytics as SEOAnalyticsModel, SEOScore, ContentType,
)
from layers.layer23_website_manager.seo_richpins_manager.keywords.keyword_engine import KeywordEngine
from layers.layer23_website_manager.seo_richpins_manager.metadata.meta_manager import MetaManager
from layers.layer23_website_manager.seo_richpins_manager.pinterest.pinterest_seo_manager import PinterestSEOManager
from layers.layer23_website_manager.seo_richpins_manager.richpins.rich_pins_manager import RichPinsManager
from layers.layer23_website_manager.seo_richpins_manager.opengraph.open_graph_manager import OpenGraphManager
from layers.layer23_website_manager.seo_richpins_manager.twitter.twitter_card_manager import TwitterCardManager
from layers.layer23_website_manager.seo_richpins_manager.schema.structured_data_manager import StructuredDataManager
from layers.layer23_website_manager.seo_richpins_manager.sitemap.sitemap_manager import SitemapManager
from layers.layer23_website_manager.seo_richpins_manager.robots.robots_manager import RobotsManager
from layers.layer23_website_manager.seo_richpins_manager.validation.seo_validator import SEOValidator
from layers.layer23_website_manager.seo_richpins_manager.optimization.seo_optimizer import SEOOptimizer
from layers.layer23_website_manager.seo_richpins_manager.analytics.seo_analytics import SEOAnalytics


class SEORichPinsManager:
    """Primary facade for SEO & Rich Pins Manager.

    Full pipeline: Keywords → Meta → Pinterest SEO → Rich Pins → OG → Twitter → Schema → Sitemap → Validate
    Coordinates 12 sub-modules for complete SEO optimization.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.keywords = KeywordEngine()
        self.meta = MetaManager()
        self.pinterest_seo = PinterestSEOManager()
        self.rich_pins = RichPinsManager()
        self.opengraph = OpenGraphManager()
        self.twitter = TwitterCardManager()
        self.schema = StructuredDataManager()
        self.sitemap = SitemapManager()
        self.robots = RobotsManager()
        self.validator = SEOValidator()
        self.optimizer = SEOOptimizer()
        self.analytics = SEOAnalytics()

        # Storage
        self._profiles: Dict[str, SEOProfile] = {}
        self._total_operations = 0

    # ─── Full Pipeline ────────────────────────────────────

    def optimize_article(self, article_title: str, article_content: str = "",
                          niche: str = "", article_id: str = "",
                          site_name: str = "AI Blog",
                          url: str = "", image_url: str = "",
                          author: str = "AI Blog") -> SEOProfile:
        """Full SEO pipeline: Keywords → Meta → Pinterest SEO → Rich Pins → OG → Twitter → Schema."""
        profile = SEOProfile(
            article_id=article_id,
            article_title=article_title,
        )

        # Step 1: Keywords
        kw_data = self.keywords.generate_keywords(niche, article_title, article_content)
        profile.primary_keyword = kw_data["primary_keyword"]
        profile.secondary_keywords = kw_data["secondary_keywords"]
        profile.long_tail_keywords = kw_data["long_tail_keywords"]
        profile.lsi_keywords = kw_data["lsi_keywords"]
        profile.search_intent = kw_data["search_intent"]

        # Step 2: Meta
        meta_data = self.meta.generate_meta(article_title, profile.primary_keyword,
                                              article_content, site_name, url)
        profile.seo_title = meta_data["seo_title"]
        profile.meta_description = meta_data["meta_description"]
        profile.canonical_url = meta_data["canonical_url"]
        profile.robots_meta = meta_data["robots_meta"]

        # Step 3: Pinterest SEO
        pin_data = self.pinterest_seo.optimize_pin(article_title, niche, profile.primary_keyword, article_content)
        profile.pin_seo_title = pin_data["pin_seo_title"]
        profile.pin_description = pin_data["pin_description"]
        profile.pinterest_keywords = pin_data["pinterest_keywords"]
        profile.pinterest_hashtags = pin_data["pinterest_hashtags"]

        # Step 4: Rich Pins
        rich_data = self.rich_pins.create_article_rich_pin(
            article_title, article_content, author, site_name, url, "", image_url,
        )
        profile.rich_pin_type = rich_data["rich_pin_type"]
        profile.rich_pin_data = rich_data["rich_pin_data"]
        profile.is_rich_pin = True

        # Step 5: Open Graph
        og_data = self.opengraph.generate_og_tags(article_title, article_content,
                                                    image_url, url, "article", site_name)
        profile.og_title = og_data["og:title"]
        profile.og_description = og_data["og:description"]
        profile.og_image = og_data["og:image"]
        profile.og_url = og_data["og:url"]
        profile.og_type = og_data["og:type"]

        # Step 6: Twitter Card
        tw_data = self.twitter.generate_twitter_card(article_title, article_content, image_url)
        profile.twitter_title = tw_data["twitter:title"]
        profile.twitter_description = tw_data["twitter:description"]
        profile.twitter_image = tw_data["twitter:image"]
        profile.twitter_card_type = tw_data["twitter:card"]

        # Step 7: Schema
        schema_data = self.schema.generate_article_schema(
            article_title, article_content, author, site_name, url, "", image_url,
            profile.secondary_keywords,
        )
        profile.schema_type = ContentType.ARTICLE
        profile.schema_data = schema_data["schema_data"]
        profile.has_schema = True

        # Calculate SEO score
        profile.seo_score = self._calculate_score(profile)

        # Store profile
        self._profiles[profile.profile_id] = profile
        self._log("optimize_article", {"article": article_title})

        return profile

    def _calculate_score(self, profile: SEOProfile) -> float:
        """Calculate overall SEO score (0-100)."""
        score = 100.0
        if not profile.primary_keyword: score -= 10
        if not profile.secondary_keywords: score -= 5
        if not profile.seo_title: score -= 15
        if not profile.meta_description: score -= 10
        if not profile.canonical_url: score -= 10
        if not profile.pinterest_hashtags: score -= 5
        if not profile.has_schema: score -= 10
        if not profile.og_title: score -= 5
        if not profile.twitter_title: score -= 5
        if not profile.internal_links: score -= 5
        return max(0, score)

    # ─── Individual Operations ────────────────────────────

    def generate_keywords(self, niche: str, title: str = "", content: str = "") -> Dict[str, Any]:
        return self.keywords.generate_keywords(niche, title, content)

    def generate_meta(self, title: str, keyword: str = "", desc: str = "",
                       site_name: str = "AI Blog") -> Dict[str, Any]:
        return self.meta.generate_meta(title, keyword, desc, site_name)

    def optimize_pin_seo(self, title: str, niche: str = "",
                          keyword: str = "", desc: str = "") -> Dict[str, Any]:
        return self.pinterest_seo.optimize_pin(title, niche, keyword, desc)

    def create_rich_pin(self, title: str, desc: str = "", author: str = "",
                         site_name: str = "", url: str = "") -> Dict[str, Any]:
        return self.rich_pins.create_article_rich_pin(title, desc, author, site_name, url)

    def generate_og(self, title: str, desc: str = "", image: str = "",
                     url: str = "", og_type: str = "article") -> Dict[str, Any]:
        return self.opengraph.generate_og_tags(title, desc, image, url, og_type)

    def generate_twitter(self, title: str, desc: str = "", image: str = "") -> Dict[str, Any]:
        return self.twitter.generate_twitter_card(title, desc, image)

    def generate_article_schema(self, title: str, desc: str = "", author: str = "",
                                  site_name: str = "", url: str = "",
                                  keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        return self.schema.generate_article_schema(title, desc, author, site_name, url,
                                                     keywords=keywords)

    def generate_sitemap(self, articles: List[Dict[str, Any]], base_url: str = "") -> str:
        return self.sitemap.generate_article_sitemap(articles, base_url)

    def generate_robots(self, sitemap_url: str = "", restrict_ai: bool = False) -> str:
        return self.robots.generate_robots_txt(sitemap_url, restrict_ai_bots=restrict_ai)

    def validate_seo(self, profile_id: str) -> Dict[str, Any]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return {"error": "Profile not found"}
        return self.validator.validate_profile(profile)

    def analyze_seo(self, profile_id: str) -> Dict[str, Any]:
        profile = self._profiles.get(profile_id)
        if not profile:
            return {"error": "Profile not found"}
        return self.optimizer.analyze(profile)

    def record_analytics(self, article_id: str, google_impressions: int = 0,
                          google_clicks: int = 0) -> SEOAnalyticsModel:
        return self.analytics.record(article_id, google_impressions, google_clicks)

    def generate_seo_report(self) -> Dict[str, Any]:
        return self.analytics.generate_report()

    def get_profile(self, profile_id: str) -> Optional[SEOProfile]:
        return self._profiles.get(profile_id)

    def get_all_profiles(self) -> List[SEOProfile]:
        return list(self._profiles.values())

    # ─── Status ───────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        optimized = sum(1 for p in self._profiles.values() if p.is_optimized)
        avg_score = sum(p.seo_score for p in self._profiles.values()) / max(len(self._profiles), 1)

        return {
            "module": "SEO & Rich Pins Manager (Layer 23 / Module 7)",
            "version": "1.0.0",
            "overall": "Healthy",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "profiles": {
                "total": len(self._profiles),
                "optimized": optimized,
                "avg_seo_score": round(avg_score, 1),
            },
            "keywords": self.keywords.get_stats(),
            "meta": self.meta.get_stats(),
            "pinterest_seo": self.pinterest_seo.get_stats(),
            "rich_pins": self.rich_pins.get_stats(),
            "opengraph": self.opengraph.get_stats(),
            "twitter": self.twitter.get_stats(),
            "schema": self.schema.get_stats(),
            "sitemap": self.sitemap.get_stats(),
            "robots": self.robots.get_stats(),
            "validator": self.validator.get_stats(),
            "optimizer": self.optimizer.get_stats(),
            "analytics": self.analytics.get_stats(),
            "operations": {"total": self._total_operations},
        }

    def _log(self, operation: str, details: dict) -> None:
        with self._lock:
            self._total_operations += 1


# ─── Singleton ───────────────────────────────────────────────────────────────

_seo_manager_instance: Optional[SEORichPinsManager] = None
_instance_lock = threading.Lock()


def get_seo_manager() -> SEORichPinsManager:
    global _seo_manager_instance
    if _seo_manager_instance is None:
        with _instance_lock:
            if _seo_manager_instance is None:
                _seo_manager_instance = SEORichPinsManager()
    return _seo_manager_instance
