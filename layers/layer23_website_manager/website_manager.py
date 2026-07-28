"""WebsiteManager — Universal AI Content Operating System Layer 23.

Manages website lifecycle: configuration, structure, content publishing,
SEO, media, internal linking, and health monitoring.

Module 1 of Layer 23 — Pinterest Business Platform (v1.0.0)
"""
from __future__ import annotations
import time
import os
import json
import threading
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.models.website_config import WebsiteConfig
from layers.layer23_website_manager.models.article import Article, ArticleStatus
from layers.layer23_website_manager.models.seo_meta import SEOMetadata
from layers.layer23_website_manager.models.media_asset import MediaAsset
from layers.layer23_website_manager.services.url_manager import URLManager
from layers.layer23_website_manager.services.publisher import Publisher
from layers.layer23_website_manager.services.site_structure_manager import SiteStructureManager
from layers.layer23_website_manager.seo.seo_manager import SEOManager
from layers.layer23_website_manager.media.media_manager import MediaManager
from layers.layer23_website_manager.health.website_health import (
    WebsiteHealthChecker, InternalLinkManager,
)
from layers.layer23_website_manager.exceptions import (
    WebsiteConfigError, PublishError,
)


class WebsiteManager:
    """Primary facade for Website Management Platform.

    Coordinates all sub-modules: config, structure, publishing, SEO,
    media, internal linking, and health.
    """

    def __init__(self, domain: str = "example.com", site_name: str = "My Website",
                 storage_dir: str = "") -> None:
        # Core configuration
        self._config = WebsiteConfig(domain=domain, site_name=site_name)
        self._lock = threading.RLock()
        self._start_time = time.time()

        # Sub-modules
        self.structure = SiteStructureManager()
        self.url_manager = URLManager(domain=domain)
        self.publisher = Publisher(storage_dir=os.path.join(storage_dir, "articles"))
        self.seo = SEOManager(site_name=site_name, domain=domain)
        self.media = MediaManager(storage_dir=os.path.join(storage_dir, "media"))
        self.health = WebsiteHealthChecker()
        self.linking = InternalLinkManager()

        # Stats
        self._total_operations = 0
        self._total_errors = 0
        self._operation_log: List[dict] = []

    # ─── Configuration ─────────────────────────────────────

    def configure(self, domain: str = "", site_name: str = "",
                  tagline: str = "", logo_url: str = "", favicon_url: str = "",
                  theme: str = "", language: str = "", timezone: str = "",
                  brand_color_primary: str = "", brand_color_secondary: str = "",
                  meta_description: str = "") -> WebsiteConfig:
        """Update website configuration."""
        with self._lock:
            if domain:
                self._config.domain = domain
                self.url_manager.configure(domain=domain)
                self.seo.configure(domain=domain)
            if site_name:
                self._config.site_name = site_name
                self.seo.configure(site_name=site_name)
            if tagline:
                self._config.tagline = tagline
            if logo_url:
                self._config.logo_url = logo_url
            if favicon_url:
                self._config.favicon_url = favicon_url
            if theme:
                self._config.theme = theme
            if language:
                self._config.language = language
            if timezone:
                self._config.timezone = timezone
            if brand_color_primary:
                self._config.brand_color_primary = brand_color_primary
            if brand_color_secondary:
                self._config.brand_color_secondary = brand_color_secondary
            if meta_description:
                self._config.meta_description = meta_description

            self._config.updated_at = time.time()
            self._log_operation("configure", {"domain": domain or self._config.domain})

        return self._config

    def get_config(self) -> WebsiteConfig:
        """Get current website configuration."""
        return self._config

    # ─── Article Operations ────────────────────────────────

    def create_article(self, title: str, content: str = "", category: str = "",
                       tags: Optional[List[str]] = None, author: str = "Admin",
                       featured_image: str = "",
                       meta_title: str = "", meta_description: str = "",
                       status: str = "draft", scheduled_at: float = 0.0) -> Article:
        """Create a new article with optional SEO metadata."""
        # Generate slug
        slug = self.url_manager.generate_slug(title)
        slug = self.url_manager.register_slug(slug, title)

        # Map status string
        article_status = ArticleStatus(status) if status in (
            "draft", "scheduled", "published"
        ) else ArticleStatus.DRAFT

        # Get or create category
        category_id = ""
        cat = self.structure.get_category_by_slug(category.lower().replace(" ", "-"))
        if not cat and category:
            cat = self.structure.add_category(category)
            category_id = cat.category_id
        elif cat:
            category_id = cat.category_id

        # Create article
        article = Article(
            title=title,
            content=content,
            slug=slug,
            category_id=category_id,
            tags=tags or [],
            author=author,
            status=article_status,
            featured_image=featured_image,
            meta_title=meta_title or self.seo.generate_meta(title, content[:200]).meta_title,
            meta_description=meta_description or self.seo.generate_meta(title, content[:200]).meta_description,
        )

        # Schedule if needed
        if scheduled_at > 0:
            article.status = ArticleStatus.SCHEDULED
            article.scheduled_at = scheduled_at

        # Publish immediately if requested
        if status == "published":
            article.status = ArticleStatus.PUBLISHED
            article.published_at = time.time()

        with self._lock:
            self.publisher._articles[article.article_id] = article
        self._log_operation("create_article", {"title": title, "slug": slug})

        # Generate SEO metadata
        self._generate_article_seo(article)

        # Add to sitemap
        article_url = self.url_manager.build_article_url(slug)
        self.seo.add_sitemap_url(
            loc=article_url,
            changefreq="weekly",
            priority=0.7 if article.status == ArticleStatus.PUBLISHED else 0.3,
        )

        return article

    def get_article(self, article_id: str) -> Optional[Article]:
        return self.publisher.get_article(article_id)

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        return self.publisher.get_article_by_slug(slug)

    def update_article(self, article_id: str, **kwargs) -> Optional[Article]:
        with self._lock:
            result = self.publisher.update_article(article_id, **kwargs)
            if result:
                self._log_operation("update_article", {"article_id": article_id})
        return result

    def delete_article(self, article_id: str) -> bool:
        with self._lock:
            result = self.publisher.delete_article(article_id)
            if result:
                self._log_operation("delete_article", {"article_id": article_id})
        return result

    def publish_article(self, article_id: str) -> Article:
        article = self.publisher.publish_article(article_id)
        self._log_operation("publish_article", {"article_id": article_id})
        return article

    def get_all_articles(self, status: str = "", category: str = "") -> List[Article]:
        status_filter = ArticleStatus(status) if status else None
        return self.publisher.get_all_articles(status=status_filter, category_id=category)

    # ─── SEO Generation ────────────────────────────────────

    def _generate_article_seo(self, article: Article) -> None:
        """Generate and set SEO metadata for an article."""
        meta = self.seo.generate_meta(
            title=article.title,
            excerpt=article.excerpt or article.content[:200],
            keywords=article.tags,
            og_image=article.featured_image,
        )
        article.meta_title = meta.meta_title
        article.meta_description = meta.meta_description
        article.og_title = meta.og_title
        article.og_description = meta.og_description
        article.og_image = meta.og_image
        article.canonical_url = self.url_manager.build_canonical_url(article.slug)

        # Generate structured data
        self.seo.generate_article_schema(
            title=article.title,
            description=article.excerpt or article.content[:200],
            url=article.canonical_url,
            author=article.author,
        )

    def generate_article_seo(self, article_id: str) -> Optional[SEOMetadata]:
        """Regenerate SEO metadata for an article."""
        article = self.publisher.get_article(article_id)
        if not article:
            return None
        self._generate_article_seo(article)
        meta = SEOMetadata(
            meta_title=article.meta_title,
            meta_description=article.meta_description,
            og_title=article.og_title,
            og_description=article.og_description,
            og_image=article.og_image,
            canonical_url=article.canonical_url,
        )
        return meta

    # ─── Media ─────────────────────────────────────────────

    def upload_media(self, file_name: str, file_path: str = "",
                     mime_type: str = "image/jpeg", alt_text: str = "",
                     is_featured: bool = False) -> MediaAsset:
        return self.media.upload(file_name, file_path, mime_type, alt_text, is_featured=is_featured)

    def get_media(self, asset_id: str) -> Optional[MediaAsset]:
        return self.media.get_asset(asset_id)

    def get_all_media(self) -> List[MediaAsset]:
        return self.media.get_all_assets()

    # ─── Internal Linking ──────────────────────────────────

    def generate_related_articles(self, article_id: str, max_links: int = 5) -> List[Article]:
        article = self.publisher.get_article(article_id)
        if not article:
            return []
        all_articles = self.publisher.get_all_articles()
        return self.linking.find_related_articles(article, all_articles, max_links)

    def apply_internal_links(self, article_id: str, max_links: int = 3) -> Optional[str]:
        """Auto-generate internal links in article content."""
        article = self.publisher.get_article(article_id)
        if not article or not article.content:
            return None
        all_articles = self.publisher.get_all_articles(
            status=ArticleStatus.PUBLISHED
        )
        new_content = self.linking.generate_internal_links(
            article.content, all_articles, max_links
        )
        article.content = new_content
        return new_content

    # ─── Health ────────────────────────────────────────────

    def check_health(self) -> Dict[str, Any]:
        """Run comprehensive website health check."""
        all_articles = self.publisher.get_all_articles()
        report = self.health.generate_report(all_articles)

        # Add config check
        config_issues = []
        if not self._config.domain or self._config.domain == "example.com":
            config_issues.append("Domain not configured")
        if not self._config.site_name or self._config.site_name == "My Website":
            config_issues.append("Site name is default")

        report["config_issues"] = config_issues
        report["config_score"] = max(0, 100 - len(config_issues) * 20)
        report["overall_score"] = (report["health_score"] + report["config_score"]) // 2

        return report

    # ─── Sitemap & Robots ──────────────────────────────────

    def generate_sitemap(self) -> str:
        """Generate and return XML sitemap."""
        return self.seo.generate_sitemap_xml()

    def generate_robots_txt(self) -> str:
        """Generate and return robots.txt."""
        sitemap_url = self.url_manager.build_url("sitemap.xml")
        return self.seo.generate_robots_txt(sitemap_url)

    def add_sitemap_entry(self, slug: str, changefreq: str = "weekly",
                           priority: float = 0.5) -> None:
        url = self.url_manager.build_url(slug)
        self.seo.add_sitemap_url(url, changefreq=changefreq, priority=priority)

    # ─── System Status ─────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get complete website manager status."""
        article_stats = self.publisher.get_stats()
        media_stats = self.media.get_stats()
        health_report = self.check_health()

        return {
            "module": "Website Manager (Layer 23 / Module 1)",
            "version": "1.0.0",
            "overall": "Healthy" if health_report["overall_score"] >= 70 else "Degraded",
            "uptime_seconds": round(time.time() - self._start_time, 1),
            "configuration": self._config.to_dict(),
            "articles": article_stats,
            "media": media_stats,
            "seo": self.seo.to_dict(),
            "url_manager": self.url_manager.to_dict(),
            "health": {
                "overall_score": health_report["overall_score"],
                "content_health": health_report["health_score"],
                "config_health": health_report["config_score"],
                "issues": health_report["total_issues"],
            },
            "operations": {
                "total": self._total_operations,
                "errors": self._total_errors,
            },
        }

    def to_dict(self) -> Dict[str, Any]:
        return self.get_status()

    # ─── Internal ──────────────────────────────────────────

    def _log_operation(self, operation: str, details: dict) -> None:
        """Log an operation for audit."""
        with self._lock:
            self._total_operations += 1
            self._operation_log.append({
                "operation": operation,
                "details": details,
                "timestamp": time.time(),
            })

    def get_operation_log(self, limit: int = 50) -> List[dict]:
        """Get operation history."""
        return self._operation_log[-limit:]


# ─── Singleton Access ───────────────────────────────────────────────────────

_website_instance: Optional[WebsiteManager] = None
_instance_lock = threading.Lock()


def get_website(domain: str = "example.com", site_name: str = "My Website") -> WebsiteManager:
    """Get or create the singleton WebsiteManager instance."""
    global _website_instance
    if _website_instance is None:
        with _instance_lock:
            if _website_instance is None:
                storage = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "website")
                _website_instance = WebsiteManager(
                    domain=domain,
                    site_name=site_name,
                    storage_dir=storage,
                )
    return _website_instance
