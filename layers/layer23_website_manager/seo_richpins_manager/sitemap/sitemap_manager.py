"""SitemapManager — Generate XML sitemaps: articles, images, categories."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import SitemapError


class SitemapManager:
    """Generate XML sitemaps for articles, images, categories."""

    def __init__(self) -> None:
        self._sitemap_log: List[dict] = []

    def generate_article_sitemap(self, articles: List[Dict[str, Any]],
                                   base_url: str = "https://example.com") -> str:
        """Generate XML sitemap for articles."""
        if not articles:
            raise SitemapError("No articles to generate sitemap")

        urls = []
        for article in articles:
            url = article.get("url", f"{base_url}/{article.get('slug', 'article')}")
            lastmod = article.get("updated_at", time.strftime("%Y-%m-%d"))
            urls.append(f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{article.get('changefreq', 'weekly')}</changefreq>
    <priority>{article.get('priority', 0.7)}</priority>
  </url>""")

        sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  {"".join(urls)}
</urlset>"""

        self._sitemap_log.append({"type": "article", "count": len(articles)})
        return sitemap

    def generate_sitemap_index(self, sitemaps: List[Dict[str, str]]) -> str:
        """Generate sitemap index file."""
        entries = []
        for sm in sitemaps:
            entries.append(f"""
  <sitemap>
    <loc>{sm['url']}</loc>
    <lastmod>{sm.get('lastmod', time.strftime('%Y-%m-%d'))}</lastmod>
  </sitemap>""")

        index = f"""<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  {"".join(entries)}
</sitemapindex>"""

        self._sitemap_log.append({"type": "index", "count": len(sitemaps)})
        return index

    def get_stats(self) -> Dict[str, Any]:
        articles = sum(1 for e in self._sitemap_log if e["type"] == "article")
        indexes = sum(1 for e in self._sitemap_log if e["type"] == "index")
        return {"total_sitemaps": len(self._sitemap_log), "article_sitemaps": articles, "indexes": indexes}
