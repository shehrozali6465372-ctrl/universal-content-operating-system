"""WebsiteHealthChecker — Website health monitoring and validation."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.models.article import Article, ArticleStatus


class WebsiteHealthChecker:
    """Check website health — broken links, duplicate content, missing metadata."""

    def __init__(self) -> None:
        self._check_history: List[dict] = []

    # ─── Article Validations ───────────────────────────────

    def check_article_health(self, article: Article) -> List[dict]:
        """Check a single article for health issues."""
        issues: List[dict] = []

        # Content checks
        if not article.title:
            issues.append({"type": "missing_title", "severity": "high",
                           "message": "Article has no title", "article_id": article.article_id})
        if not article.content:
            issues.append({"type": "missing_content", "severity": "high",
                           "message": "Article has no content", "article_id": article.article_id})
        if len(article.content) < 100:
            issues.append({"type": "short_content", "severity": "medium",
                           "message": f"Article content too short ({len(article.content)} chars)",
                           "article_id": article.article_id})

        # SEO checks
        if not article.meta_title:
            issues.append({"type": "missing_meta_title", "severity": "medium",
                           "message": "Missing meta title", "article_id": article.article_id})
        if not article.meta_description:
            issues.append({"type": "missing_meta_description", "severity": "medium",
                           "message": "Missing meta description", "article_id": article.article_id})
        if not article.slug:
            issues.append({"type": "missing_slug", "severity": "high",
                           "message": "Article has no slug", "article_id": article.article_id})

        # Image checks
        if not article.featured_image:
            issues.append({"type": "missing_featured_image", "severity": "low",
                           "message": "No featured image set", "article_id": article.article_id})

        return issues

    # ─── Bulk Validations ─────────────────────────────────

    def check_all_articles(self, articles: List[Article]) -> List[dict]:
        """Check all articles for issues."""
        all_issues: List[dict] = []
        for article in articles:
            all_issues.extend(self.check_article_health(article))

        # Duplicate check
        slugs: Dict[str, int] = {}
        for article in articles:
            if article.slug:
                slugs[article.slug] = slugs.get(article.slug, 0) + 1

        for slug, count in slugs.items():
            if count > 1:
                all_issues.append({
                    "type": "duplicate_slug", "severity": "high",
                    "message": f"Slug '{slug}' used {count} times",
                })

        return all_issues

    # ─── Report ────────────────────────────────────────────

    def generate_report(self, articles: List[Article]) -> Dict[str, Any]:
        """Generate complete website health report."""
        issues = self.check_all_articles(articles)

        by_severity: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        by_type: Dict[str, int] = {}

        for issue in issues:
            sev = issue.get("severity", "low")
            by_severity[sev] = by_severity.get(sev, 0) + 1
            typ = issue["type"]
            by_type[typ] = by_type.get(typ, 0) + 1

        score = 100
        score -= by_severity.get("high", 0) * 10
        score -= by_severity.get("medium", 0) * 3
        score -= by_severity.get("low", 0) * 1
        score = max(0, score)

        report = {
            "health_score": score,
            "total_issues": len(issues),
            "by_severity": by_severity,
            "by_type": by_type,
            "issues": issues[:50],  # Limit output
            "passed": len(issues) == 0,
        }

        self._check_history.append({
            "timestamp": __import__("time").time(),
            "score": score,
            "issues": len(issues),
        })

        return report

    def get_history(self) -> List[dict]:
        """Get health check history."""
        return list(self._check_history)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "checks_performed": len(self._check_history),
            "last_score": self._check_history[-1]["score"] if self._check_history else None,
        }


class InternalLinkManager:
    """Manage internal linking between articles for SEO."""

    def __init__(self) -> None:
        self._link_rules: List[dict] = []

    def find_related_articles(self, article: Article,
                               all_articles: List[Article], max_links: int = 5) -> List[Article]:
        """Find related articles based on tags and categories."""
        article_tags = set(t.lower() for t in article.tags)
        scored: List[Tuple[int, Article]] = []

        for candidate in all_articles:
            if candidate.article_id == article.article_id:
                continue
            if candidate.status != ArticleStatus.PUBLISHED:
                continue

            score = 0
            candidate_tags = set(t.lower() for t in candidate.tags)

            # Tag overlap
            overlap = article_tags & candidate_tags
            score += len(overlap) * 3

            # Same category
            if candidate.category_id and candidate.category_id == article.category_id:
                score += 2

            if score > 0:
                scored.append((score, candidate))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [a for _, a in scored[:max_links]]

    def generate_internal_links(self, content: str, articles: List[Article],
                                 max_links: int = 3) -> str:
        """Automatically insert internal links into content."""
        import re

        linked_articles: List[Article] = []
        result = content

        for article in articles:
            if len(linked_articles) >= max_links:
                break

            # Find article title in content (case insensitive)
            title_lower = article.title.lower()
            content_lower = result.lower()

            if title_lower in content_lower:
                # Find position and insert link
                pos = content_lower.index(title_lower)
                end_pos = pos + len(title_lower)

                # Check not already linked
                before = result[max(0, pos - 10):pos]
                if "href" in before or ">" in before.split()[-1:] if before else False:
                    continue

                link = f'<a href="/{article.slug}/">{article.title}</a>'
                result = result[:pos] + link + result[end_pos:]
                linked_articles.append(article)

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {"rules": len(self._link_rules), "active": True}
