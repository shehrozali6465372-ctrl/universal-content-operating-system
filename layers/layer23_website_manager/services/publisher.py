"""Publisher — Article lifecycle management (CRUD + scheduling)."""
from __future__ import annotations
import time
import json
import threading
import os
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.models.article import Article, ArticleStatus
from layers.layer23_website_manager.exceptions import (
    PublishError, DuplicateArticleError, WebsiteNotFoundError,
)


class Publisher:
    """Manage article lifecycle — create, read, update, delete, schedule, publish."""

    def __init__(self, storage_dir: str = "") -> None:
        self._articles: Dict[str, Article] = {}
        self._lock = threading.Lock()
        self._storage_dir = storage_dir
        self._total_published = 0
        self._total_errors = 0
        self._publish_log: List[dict] = []

        # Load existing articles
        if storage_dir:
            self._load_from_disk()

    # ─── CRUD Operations ───────────────────────────────────

    def create_article(self, title: str, content: str = "", slug: str = "",
                       category_id: str = "", tags: Optional[List[str]] = None,
                       author: str = "Admin", status: ArticleStatus = ArticleStatus.DRAFT) -> Article:
        """Create a new article."""
        article = Article(
            title=title,
            content=content,
            slug=slug or self._generate_slug(title),
            category_id=category_id,
            tags=tags or [],
            author=author,
            status=status,
        )

        with self._lock:
            if article.slug in [a.slug for a in self._articles.values()]:
                raise DuplicateArticleError(f"Article with slug '{article.slug}' already exists")
            self._articles[article.article_id] = article

        return article

    def get_article(self, article_id: str) -> Optional[Article]:
        """Get article by ID."""
        return self._articles.get(article_id)

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        """Get article by slug."""
        for article in self._articles.values():
            if article.slug == slug:
                return article
        return None

    def update_article(self, article_id: str, **kwargs) -> Optional[Article]:
        """Update article fields. Returns updated article or None."""
        article = self._articles.get(article_id)
        if not article:
            return None

        allowed_fields = {
            "title", "content", "slug", "excerpt", "category_id", "tags",
            "featured_image", "author", "meta_title", "meta_description",
            "og_title", "og_description", "og_image", "canonical_url",
            "is_indexable", "scheduled_at", "related_article_ids",
            "internal_links",
        }

        with self._lock:
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(article, key, value)
            article.updated_at = time.time()
            article.version += 1

        return article

    def delete_article(self, article_id: str) -> bool:
        """Delete an article."""
        with self._lock:
            if article_id in self._articles:
                del self._articles[article_id]
                return True
        return False

    def get_all_articles(self, status: Optional[ArticleStatus] = None,
                         category_id: str = "") -> List[Article]:
        """Get all articles, optionally filtered."""
        articles = list(self._articles.values())

        if status:
            articles = [a for a in articles if a.status == status]
        if category_id:
            articles = [a for a in articles if a.category_id == category_id]

        return sorted(articles, key=lambda a: a.created_at, reverse=True)

    # ─── Publishing ────────────────────────────────────────

    def publish_article(self, article_id: str) -> Article:
        """Publish a draft or scheduled article."""
        article = self.get_article(article_id)
        if not article:
            raise WebsiteNotFoundError(f"Article {article_id} not found")

        if article.status == ArticleStatus.PUBLISHED:
            article.status = ArticleStatus.UPDATED
            article.version += 1
        else:
            article.status = ArticleStatus.PUBLISHED
            article.published_at = time.time()

        article.updated_at = time.time()

        with self._lock:
            self._total_published += 1
            self._publish_log.append({
                "article_id": article_id,
                "title": article.title,
                "slug": article.slug,
                "action": "publish",
                "timestamp": time.time(),
            })

        return article

    def draft_article(self, article_id: str) -> Article:
        """Move article back to draft."""
        article = self.get_article(article_id)
        if article:
            article.status = ArticleStatus.DRAFT
            article.updated_at = time.time()
        return article

    def schedule_article(self, article_id: str, publish_at: float) -> Article:
        """Schedule article for future publication."""
        article = self.get_article(article_id)
        if article:
            article.status = ArticleStatus.SCHEDULED
            article.scheduled_at = publish_at
            article.updated_at = time.time()
        return article

    # ─── Scheduling ────────────────────────────────────────

    def get_due_articles(self) -> List[Article]:
        """Get articles that are due for publishing."""
        now = time.time()
        due = []
        for article in self._articles.values():
            if article.status == ArticleStatus.SCHEDULED and 0 < article.scheduled_at <= now:
                due.append(article)
        return due

    def process_scheduled(self) -> int:
        """Publish all due scheduled articles. Returns count."""
        count = 0
        for article in self.get_due_articles():
            try:
                self.publish_article(article.article_id)
                count += 1
            except Exception:
                with self._lock:
                    self._total_errors += 1
        return count

    # ─── Stats ─────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics."""
        statuses = {}
        for article in self._articles.values():
            s = article.status.value
            statuses[s] = statuses.get(s, 0) + 1

        return {
            "total_articles": len(self._articles),
            "by_status": statuses,
            "total_published": self._total_published,
            "total_errors": self._total_errors,
            "scheduled_due": len(self.get_due_articles()),
        }

    # ─── Helpers ───────────────────────────────────────────

    @staticmethod
    def _generate_slug(title: str) -> str:
        """Basic slug generation from title."""
        import re
        slug = title.lower().strip()
        slug = re.sub(r"[^a-z0-9\s-]", "", slug)
        slug = re.sub(r"[\s]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")[:80] or "untitled"

    def _load_from_disk(self) -> None:
        """Load articles from disk storage."""
        path = os.path.join(self._storage_dir, "articles.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for item in data:
                    article = Article(**item)
                    self._articles[article.article_id] = article
            except Exception:
                pass

    def save_to_disk(self) -> None:
        """Save articles to disk storage."""
        if not self._storage_dir:
            return
        os.makedirs(self._storage_dir, exist_ok=True)
        path = os.path.join(self._storage_dir, "articles.json")
        with open(path, "w") as f:
            json.dump([a.to_dict() for a in self._articles.values()], f, indent=2)
