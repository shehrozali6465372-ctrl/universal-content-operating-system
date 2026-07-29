"""StructuredDataManager — Generate Schema.org structured data: Article, Product, FAQ, etc."""
from __future__ import annotations
import json
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.models.seo_models import ContentType
from layers.layer23_website_manager.seo_richpins_manager.exceptions import SchemaError


class StructuredDataManager:
    """Generate Schema.org JSON-LD structured data for multiple content types."""

    def __init__(self) -> None:
        self._schema_log: List[dict] = []

    def generate_article_schema(self, title: str, description: str = "",
                                  author: str = "AI Blog", site_name: str = "",
                                  url: str = "", date_published: str = "",
                                  image_url: str = "",
                                  keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate Article schema.org JSON-LD."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description[:200] if description else "",
            "author": {"@type": "Person", "name": author},
            "publisher": {"@type": "Organization", "name": site_name or "AI Blog"},
            "url": url,
            "datePublished": date_published,
            "image": image_url,
            "keywords": ", ".join(keywords[:5]) if keywords else "",
        }

        result = {
            "schema_type": "Article",
            "schema_json": json.dumps(schema, indent=2),
            "schema_data": schema,
        }

        self._schema_log.append(result)
        return result

    def generate_product_schema(self, name: str, description: str = "",
                                  price: str = "", currency: str = "USD",
                                  availability: str = "InStock",
                                  brand: str = "", url: str = "",
                                  rating: float = 0.0) -> Dict[str, Any]:
        """Generate Product schema.org JSON-LD."""
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": name,
            "description": description[:200] if description else "",
            "offers": {
                "@type": "Offer",
                "price": price,
                "priceCurrency": currency,
                "availability": f"https://schema.org/{availability}",
            },
            "brand": {"@type": "Brand", "name": brand or "Store"},
            "url": url,
        }
        if rating > 0:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": rating,
                "bestRating": 5,
            }

        result = {
            "schema_type": "Product",
            "schema_json": json.dumps(schema, indent=2),
            "schema_data": schema,
        }

        self._schema_log.append(result)
        return result

    def generate_faq_schema(self, faqs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate FAQ schema from Q&A pairs."""
        schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q["question"],
                 "acceptedAnswer": {"@type": "Answer", "text": q["answer"]}}
                for q in faqs
            ],
        }

        result = {
            "schema_type": "FAQ",
            "schema_json": json.dumps(schema, indent=2),
            "schema_data": schema,
        }

        self._schema_log.append(result)
        return result

    def generate_breadcrumb_schema(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """Generate BreadcrumbList schema."""
        schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "name": item["name"], "item": item.get("url", "")}
                for i, item in enumerate(items)
            ],
        }

        result = {
            "schema_type": "BreadcrumbList",
            "schema_json": json.dumps(schema, indent=2),
            "schema_data": schema,
        }

        self._schema_log.append(result)
        return result

    def get_stats(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for entry in self._schema_log:
            t = entry["schema_type"]
            by_type[t] = by_type.get(t, 0) + 1
        return {"total_schemas": len(self._schema_log), "by_type": by_type}
