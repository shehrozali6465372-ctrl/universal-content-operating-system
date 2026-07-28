"""SEOManager — SEO metadata, structured data, sitemap, and robots.txt generation."""
from __future__ import annotations
import time
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional
from xml.sax.saxutils import escape

from layers.layer23_website_manager.models.seo_meta import SEOMetadata
from layers.layer23_website_manager.exceptions import SEOValidationError


class SEOManager:
    """Complete SEO management — metadata, sitemap, robots.txt, structured data."""

    def __init__(self, site_name: str = "My Website", domain: str = "example.com") -> None:
        self._site_name = site_name
        self._domain = domain
        self._protocol = "https"
        self._meta_defaults = SEOMetadata()
        self._sitemap_urls: List[dict] = []
        self._structured_data: Dict[str, dict] = {}

    # ─── Metadata Generation ───────────────────────────────

    def generate_meta(self, title: str, excerpt: str = "",
                      focus_keyword: str = "", keywords: Optional[List[str]] = None,
                      og_image: str = "") -> SEOMetadata:
        """Generate complete SEO metadata for content."""
        tagline = self._meta_defaults.meta_description or self._site_name

        meta_title = f"{title[:55]} — {self._site_name}" if len(f"{title} — {self._site_name}") <= 60 else title[:60]
        meta_desc = excerpt[:155] if len(excerpt) > 155 else (excerpt or tagline)

        return SEOMetadata(
            meta_title=meta_title,
            meta_description=meta_desc,
            focus_keyword=focus_keyword,
            keywords=keywords or [focus_keyword] if focus_keyword else [],
            og_title=title[:95],
            og_description=meta_desc,
            og_image=og_image or self._meta_defaults.og_image,
            twitter_title=title[:70],
            twitter_description=meta_desc,
            twitter_image=og_image or self._meta_defaults.og_image,
            canonical_url=f"{self._protocol}://{self._domain}/",
        )

    def validate_meta(self, meta: SEOMetadata) -> List[str]:
        """Validate SEO metadata and return list of issues."""
        issues = []

        if not meta.meta_title:
            issues.append("Meta title is empty")
        elif len(meta.meta_title) > 60:
            issues.append(f"Meta title too long ({len(meta.meta_title)} > 60 chars)")

        if not meta.meta_description:
            issues.append("Meta description is empty")
        elif len(meta.meta_description) > 160:
            issues.append(f"Meta description too long ({len(meta.meta_description)} > 160 chars)")

        if not meta.focus_keyword:
            issues.append("No focus keyword set")

        return issues

    # ─── Open Graph ────────────────────────────────────────

    def generate_og_tags(self, title: str, description: str, url: str,
                         image: str = "", type_: str = "article") -> Dict[str, str]:
        """Generate Open Graph meta tags."""
        return {
            "og:title": title[:95],
            "og:description": description[:200],
            "og:url": url,
            "og:image": image or self._meta_defaults.og_image,
            "og:type": type_,
            "og:site_name": self._site_name,
        }

    # ─── Structured Data ───────────────────────────────────

    def generate_article_schema(self, title: str, description: str, url: str,
                                 author: str = "Admin", date_published: str = "",
                                 image: str = "") -> dict:
        """Generate JSON-LD structured data for Article."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": {"@type": "Person", "name": author},
            "publisher": {
                "@type": "Organization",
                "name": self._site_name,
            },
            "url": url,
            "mainEntityOfPage": url,
        }
        if date_published:
            schema["datePublished"] = date_published
        if image:
            schema["image"] = image

        schema_id = url.rstrip("/").split("/")[-1] or "home"
        self._structured_data[schema_id] = schema
        return schema

    def generate_website_schema(self) -> dict:
        """Generate Website schema."""
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": self._site_name,
            "url": f"{self._protocol}://{self._domain}/",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{self._protocol}://{self._domain}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string",
            },
        }

    def get_structured_data(self, key: str = "") -> dict:
        """Get structured data by key or all."""
        if key:
            return self._structured_data.get(key, {})
        return self._structured_data

    # ─── XML Sitemap ───────────────────────────────────────

    def add_sitemap_url(self, loc: str, lastmod: Optional[float] = None,
                        changefreq: str = "weekly", priority: float = 0.5) -> dict:
        """Add URL to sitemap."""
        entry = {
            "loc": loc,
            "lastmod": lastmod or time.time(),
            "changefreq": changefreq,
            "priority": priority,
        }
        self._sitemap_urls.append(entry)
        return entry

    def generate_sitemap_xml(self) -> str:
        """Generate complete XML sitemap."""
        urlset = ET.Element("urlset")
        urlset.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

        for entry in self._sitemap_urls:
            url_el = ET.SubElement(urlset, "url")
            loc_el = ET.SubElement(url_el, "loc")
            loc_el.text = escape(entry["loc"])

            if entry.get("lastmod"):
                lastmod_el = ET.SubElement(url_el, "lastmod")
                import datetime
                dt = datetime.datetime.fromtimestamp(entry["lastmod"], tz=datetime.timezone.utc)
                lastmod_el.text = dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

            changefreq_el = ET.SubElement(url_el, "changefreq")
            changefreq_el.text = entry.get("changefreq", "weekly")

            priority_el = ET.SubElement(url_el, "priority")
            priority_el.text = str(entry.get("priority", 0.5))

        return ET.tostring(urlset, encoding="unicode", xml_declaration=True)

    def get_sitemap_urls(self) -> List[dict]:
        """Get all sitemap URLs."""
        return list(self._sitemap_urls)

    def clear_sitemap(self) -> None:
        """Clear all sitemap entries."""
        self._sitemap_urls.clear()

    # ─── Robots.txt ────────────────────────────────────────

    def generate_robots_txt(self, sitemap_url: str = "",
                            additional_rules: Optional[List[str]] = None) -> str:
        """Generate robots.txt content."""
        lines = ["User-agent: *", "Allow: /"]

        # Disallow admin paths
        lines.extend([
            "Disallow: /admin/",
            "Disallow: /api/",
            "Disallow: /_internal/",
            "Disallow: /private/",
        ])

        if additional_rules:
            lines.extend(additional_rules)

        # Sitemap
        url = sitemap_url or f"{self._protocol}://{self._domain}/sitemap.xml"
        lines.append(f"\nSitemap: {url}")

        return "\n".join(lines)

    # ─── Configuration ─────────────────────────────────────

    def configure(self, site_name: str = "", domain: str = "") -> None:
        """Update SEO configuration."""
        if site_name:
            self._site_name = site_name
        if domain:
            self._domain = domain

    def to_dict(self) -> Dict[str, Any]:
        return {
            "site_name": self._site_name,
            "domain": self._domain,
            "sitemap_urls": len(self._sitemap_urls),
            "structured_data_entries": len(self._structured_data),
            "meta_defaults": self._meta_defaults.to_dict(),
        }
