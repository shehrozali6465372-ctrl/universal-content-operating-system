"""Comprehensive tests for Layer 23 — Module 1: Website Manager."""
from __future__ import annotations
import pytest
import time
import os

from layers.layer23_website_manager.website_manager import WebsiteManager, get_website
from layers.layer23_website_manager.models.website_config import WebsiteConfig
from layers.layer23_website_manager.models.article import Article, ArticleStatus
from layers.layer23_website_manager.models.seo_meta import SEOMetadata
from layers.layer23_website_manager.exceptions import (
    WebsiteConfigError, PublishError, DuplicateArticleError,
    MediaUploadError,
)


# ═══════════════════════════════════════════════════════════════════
# WebsiteConfig
# ═══════════════════════════════════════════════════════════════════

class TestWebsiteConfig:
    def test_default_config(self):
        config = WebsiteConfig()
        assert config.domain == "example.com"
        assert config.site_name == "My Website"
        assert config.language == "en"
        assert config.timezone == "UTC"

    def test_custom_config(self):
        config = WebsiteConfig(
            domain="myblog.com",
            site_name="My AI Blog",
            tagline="AI-Powered Content",
            language="en",
            timezone="America/New_York",
        )
        assert config.domain == "myblog.com"
        assert config.site_name == "My AI Blog"

    def test_to_dict(self):
        config = WebsiteConfig(domain="test.com")
        d = config.to_dict()
        assert d["domain"] == "test.com"
        assert "site_id" in d
        assert "created_at" in d

    def test_from_dict(self):
        config = WebsiteConfig.from_dict({"domain": "restored.com", "site_name": "Restored"})
        assert config.domain == "restored.com"
        assert config.site_name == "Restored"


# ═══════════════════════════════════════════════════════════════════
# Article
# ═══════════════════════════════════════════════════════════════════

class TestArticle:
    def test_create_article(self):
        article = Article(title="Test Article", content="Content here")
        assert article.title == "Test Article"
        assert article.content == "Content here"
        assert article.status == ArticleStatus.DRAFT
        assert article.article_id is not None
        assert article.version == 1

    def test_article_to_dict(self):
        article = Article(title="SEO Article", slug="seo-article")
        d = article.to_dict()
        assert d["title"] == "SEO Article"
        assert d["slug"] == "seo-article"
        assert d["status"] == "draft"

    def test_article_status_published(self):
        article = Article(title="Published", status=ArticleStatus.PUBLISHED)
        assert article.status == ArticleStatus.PUBLISHED


# ═══════════════════════════════════════════════════════════════════
# SEOMetadata
# ═══════════════════════════════════════════════════════════════════

class TestSEOMetadata:
    def test_default_seo(self):
        seo = SEOMetadata()
        assert seo.meta_title == ""
        assert seo.schema_type == "Article"

    def test_from_article(self):
        seo = SEOMetadata.from_article("AI Trends 2025", "An article about AI", "AI")
        assert "AI Trends" in seo.meta_title
        assert seo.focus_keyword == "AI"
        assert len(seo.meta_description) <= 160

    def test_seo_with_site_name(self):
        seo = SEOMetadata.from_article("Test Title", site_name="My Site")
        assert "My Site" in seo.meta_title


# ═══════════════════════════════════════════════════════════════════
# WebsiteManager Integration
# ═══════════════════════════════════════════════════════════════════

class TestWebsiteManager:
    def setup_method(self):
        self.wm = WebsiteManager(domain="testblog.com", site_name="Test Blog")

    def test_initialization(self):
        assert self.wm._config.domain == "testblog.com"
        assert self.wm._config.site_name == "Test Blog"
        assert self.wm.structure is not None
        assert self.wm.publisher is not None
        assert self.wm.seo is not None
        assert self.wm.media is not None
        assert self.wm.health is not None
        assert self.wm.linking is not None

    def test_configure(self):
        self.wm.configure(domain="newdomain.com", site_name="New Site", tagline="New Tagline")
        assert self.wm._config.domain == "newdomain.com"
        assert self.wm._config.site_name == "New Site"
        assert self.wm._config.tagline == "New Tagline"

    def test_create_article(self):
        article = self.wm.create_article("Test Article", "This is test content")
        assert article.title == "Test Article"
        assert article.content == "This is test content"
        assert article.status == ArticleStatus.DRAFT
        assert article.slug is not None
        assert article.article_id is not None
        assert article.meta_title is not None
        assert article.meta_description is not None

    def test_create_article_with_category(self):
        article = self.wm.create_article("Category Test", category="AI")
        assert article.category_id is not None
        cat = self.wm.structure.get_category(article.category_id)
        assert cat is not None

    def test_create_article_published(self):
        article = self.wm.create_article("Published Article", status="published")
        assert article.status == ArticleStatus.PUBLISHED
        assert article.published_at > 0

    def test_create_article_scheduled(self):
        future = time.time() + 3600
        article = self.wm.create_article("Scheduled Article", scheduled_at=future)
        assert article.status == ArticleStatus.SCHEDULED
        assert article.scheduled_at == future

    def test_get_article(self):
        created = self.wm.create_article("Get Test")
        fetched = self.wm.get_article(created.article_id)
        assert fetched is not None
        assert fetched.article_id == created.article_id

    def test_get_article_by_slug(self):
        created = self.wm.create_article("Slug Test")
        fetched = self.wm.get_article_by_slug(created.slug)
        assert fetched is not None
        assert fetched.title == "Slug Test"

    def test_update_article(self):
        article = self.wm.create_article("Update Test", "Original")
        updated = self.wm.update_article(article.article_id, title="Updated Title")
        assert updated is not None
        assert updated.title == "Updated Title"
        assert updated.version == 2

    def test_publish_article(self):
        article = self.wm.create_article("Publish Test")
        published = self.wm.publish_article(article.article_id)
        assert published.status == ArticleStatus.PUBLISHED
        assert published.published_at > 0

    def test_delete_article(self):
        article = self.wm.create_article("Delete Test")
        assert self.wm.delete_article(article.article_id) is True
        assert self.wm.get_article(article.article_id) is None

    def test_get_all_articles(self):
        self.wm.create_article("Article 1")
        self.wm.create_article("Article 2")
        self.wm.create_article("Article 3")
        articles = self.wm.get_all_articles()
        assert len(articles) >= 3

    def test_get_all_articles_by_status(self):
        self.wm.create_article("Draft 1")
        a2 = self.wm.create_article("Publish Me", status="published")
        drafts = self.wm.get_all_articles(status="draft")
        published = self.wm.get_all_articles(status="published")
        assert any(a.article_id == a2.article_id for a in published)
        assert all(a.status == ArticleStatus.DRAFT for a in drafts)

    def test_slug_uniqueness(self):
        a1 = self.wm.create_article("Unique Slug Test")
        a2 = self.wm.create_article("Unique Slug Test")
        assert a1.slug != a2.slug


class TestWebsiteSEO:
    def setup_method(self):
        self.wm = WebsiteManager(domain="seoblog.com", site_name="SEO Blog")

    def test_seo_meta_generated(self):
        article = self.wm.create_article("SEO Test Article", "Content for SEO testing")
        assert "SEO" in article.meta_title
        assert len(article.meta_description) > 0
        assert article.canonical_url.startswith("https://seoblog.com/")

    def test_generate_article_seo(self):
        article = self.wm.create_article("Regenerate SEO")
        meta = self.wm.generate_article_seo(article.article_id)
        assert meta is not None
        assert meta.meta_title is not None
        assert meta.canonical_url is not None

    def test_sitemap_generation(self):
        self.wm.create_article("Sitemap Article 1")
        self.wm.create_article("Sitemap Article 2")
        sitemap = self.wm.generate_sitemap()
        assert "<?xml" in sitemap
        assert "sitemaps.org" in sitemap
        assert "seoblog.com" in sitemap

    def test_robots_txt_generation(self):
        robots = self.wm.generate_robots_txt()
        assert "User-agent: *" in robots
        assert "Allow: /" in robots
        assert "Disallow: /admin/" in robots
        assert "Sitemap:" in robots
        assert "seoblog.com" in robots


class TestWebsiteStructure:
    def setup_method(self):
        self.wm = WebsiteManager(domain="structblog.com")

    def test_add_nav_item(self):
        item = self.wm.structure.add_nav_item("Home", "/")
        assert item.label == "Home"
        assert item.url == "/"
        assert item.item_id is not None

    def test_navigation_order(self):
        self.wm.structure.add_nav_item("Second", "/second", order=2)
        self.wm.structure.add_nav_item("First", "/first", order=1)
        nav = self.wm.structure.get_navigation()
        assert nav[0].label == "First"

    def test_add_category(self):
        cat = self.wm.structure.add_category("AI Research")
        assert cat.name == "AI Research"
        assert cat.slug == "ai-research"

    def test_get_category_by_slug(self):
        self.wm.structure.add_category("Machine Learning")
        cat = self.wm.structure.get_category_by_slug("machine-learning")
        assert cat is not None
        assert cat.name == "Machine Learning"

    def test_static_pages_exist(self):
        pages = self.wm.structure.get_all_pages()
        assert "home" in pages
        assert "about" in pages
        assert "privacy" in pages
        assert "affiliate" in pages


class TestWebsiteMedia:
    def setup_method(self):
        self.wm = WebsiteManager(domain="mediablog.com")

    def test_upload_media(self):
        asset = self.wm.upload_media("photo.jpg", mime_type="image/jpeg", alt_text="A photo")
        assert asset.file_name == "photo.jpg"
        assert asset.alt_text == "A photo"
        assert asset.url == "/media/photo.jpg"

    def test_get_media(self):
        asset = self.wm.upload_media("test.png")
        fetched = self.wm.get_media(asset.asset_id)
        assert fetched is not None
        assert fetched.file_name == "test.png"

    def test_get_all_media(self):
        self.wm.upload_media("img1.jpg")
        self.wm.upload_media("img2.jpg")
        assets = self.wm.get_all_media()
        assert len(assets) >= 2

    def test_invalid_media_type(self):
        with pytest.raises(MediaUploadError):
            self.wm.upload_media("file.pdf", mime_type="application/pdf")

    def test_media_stats(self):
        self.wm.upload_media("stats.jpg")
        stats = self.wm.media.get_stats()
        assert stats["total_assets"] >= 1
        assert "by_type" in stats


class TestWebsiteInternalLinking:
    def setup_method(self):
        self.wm = WebsiteManager(domain="linkblog.com")
        self.articles = []
        for i in range(5):
            a = self.wm.create_article(
                f"Article {i} about AI",
                content=f"This is article {i} about artificial intelligence.",
                tags=["AI", f"tag{i}"],
                category="Tech",
                status="published",
            )
            self.articles.append(a)

    def test_find_related(self):
        article = self.articles[0]
        related = self.wm.generate_related_articles(article.article_id, max_links=3)
        assert len(related) > 0

    def test_related_article_count(self):
        article = self.articles[0]
        related = self.wm.generate_related_articles(article.article_id, max_links=2)
        assert len(related) <= 2


class TestWebsiteHealth:
    def setup_method(self):
        self.wm = WebsiteManager(domain="healthblog.com")

    def test_healthy_site(self):
        self.wm.create_article("Healthy Article", "This is a complete article with enough content.", status="published")
        report = self.wm.check_health()
        assert "overall_score" in report
        assert "health_score" in report

    def test_health_issues_found(self):
        article = Article(title="", content="")  # Missing title and content
        self.wm.publisher._articles[article.article_id] = article
        report = self.wm.check_health()
        assert report["total_issues"] > 0

    def test_site_without_config(self):
        wm = WebsiteManager()  # Default domain
        report = wm.check_health()
        assert len(report["config_issues"]) > 0


class TestWebsiteStatus:
    def setup_method(self):
        self.wm = WebsiteManager(domain="statusblog.com")
        self.wm.create_article("Status Article", "Content", status="published")

    def test_get_status(self):
        status = self.wm.get_status()
        assert status["module"] == "Website Manager (Layer 23 / Module 1)"
        assert status["version"] == "1.0.0"
        assert status["overall"] in ("Healthy", "Degraded")
        assert "configuration" in status
        assert "articles" in status
        assert "media" in status
        assert "seo" in status
        assert "health" in status

    def test_article_stats_in_status(self):
        status = self.wm.get_status()
        assert status["articles"]["total_articles"] >= 1
        assert "published" in status["articles"]["by_status"]


class TestErrorHandling:
    def setup_method(self):
        self.wm = WebsiteManager()

    def test_get_nonexistent_article(self):
        assert self.wm.get_article("nonexistent") is None

    def test_delete_nonexistent_article(self):
        assert self.wm.delete_article("nonexistent") is False

    def test_generate_seo_nonexistent(self):
        meta = self.wm.generate_article_seo("nonexistent")
        assert meta is None

    def test_get_nonexistent_media(self):
        assert self.wm.get_media("nonexistent") is None


class TestSingleton:
    def test_get_website(self):
        wm1 = get_website()
        wm2 = get_website()
        assert wm1 is wm2  # Same instance
