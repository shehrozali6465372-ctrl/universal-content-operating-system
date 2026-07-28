"""Layer 23 — Pinterest Business Platform.

Module 1: Website Manager (v1.0.0)
  Complete website lifecycle management for AI-driven content publishing.

Sub-modules:
  - config: Website identity and brand configuration
  - models: Data classes for articles, SEO, media, structure
  - services: URL management, article publishing, structure management
  - seo: Metadata generation, sitemap, robots.txt, structured data
  - media: Image upload and optimization
  - health: Website health checking and internal linking

Usage:
    from layers.layer23_website_manager import WebsiteManager
    wm = WebsiteManager(domain="mywebsite.com", site_name="My AI Blog")
    wm.create_article("AI Trends 2025", "Content here...")
"""
from __future__ import annotations

from layers.layer23_website_manager.website_manager import WebsiteManager, get_website
from layers.layer23_website_manager.models.website_config import WebsiteConfig
from layers.layer23_website_manager.models.article import Article, ArticleStatus
from layers.layer23_website_manager.pinterest_account_manager.pinterest_account_manager import (
    PinterestAccountManager, get_pinterest_manager,
)

__all__ = [
    "WebsiteManager",
    "get_website",
    "PinterestAccountManager",
    "get_pinterest_manager",
    "WebsiteConfig",
    "Article",
    "ArticleStatus",
]
