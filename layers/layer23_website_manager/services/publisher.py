"""Publisher — Article lifecycle management (CRUD + scheduling)."""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.models.article import Article, ArticleStatus
from layers.layer23_website_manager.exceptions import DuplicateArticleError, PublishError, WebsiteNotFoundError


class Publisher:
    """Manage article lifecycle with durable atomic disk persistence."""

    def __init__(self, storage_dir: str = "") -> None:
        self._articles: Dict[str, Article] = {}
        self._lock = threading.RLock()
        self._storage_dir = storage_dir
        self._total_published = 0
        self._total_errors = 0
        self._publish_log: List[dict] = []
        if storage_dir:
            self._load_from_disk()

    def create_article(self, title: str, content: str = "", slug: str = "",
                       category_id: str = "", tags: Optional[List[str]] = None,
                       author: str = "Admin", status: ArticleStatus = ArticleStatus.DRAFT) -> Article:
        article = Article(title=title, content=content, slug=slug or self._generate_slug(title),
                          category_id=category_id, tags=tags or [], author=author, status=status)
        return self.save_article(article)

    def save_article(self, article: Article) -> Article:
        with self._lock:
            for existing in self._articles.values():
                if existing.article_id != article.article_id and existing.slug == article.slug:
                    raise DuplicateArticleError(f"Article with slug '{article.slug}' already exists")
            self._articles[article.article_id] = article
            self._persist_locked()
        return article

    def get_article(self, article_id: str) -> Optional[Article]:
        with self._lock:
            return self._articles.get(article_id)

    def get_article_by_slug(self, slug: str) -> Optional[Article]:
        with self._lock:
            return next((a for a in self._articles.values() if a.slug == slug), None)

    def update_article(self, article_id: str, **kwargs) -> Optional[Article]:
        article = self.get_article(article_id)
        if not article:
            return None
        allowed_fields = {"title", "content", "slug", "excerpt", "category_id", "tags",
                          "featured_image", "author", "meta_title", "meta_description",
                          "og_title", "og_description", "og_image", "canonical_url",
                          "is_indexable", "scheduled_at", "related_article_ids", "internal_links"}
        with self._lock:
            old_slug = article.slug
            for key, value in kwargs.items():
                if key in allowed_fields:
                    setattr(article, key, value)
            if article.slug != old_slug and any(
                other.article_id != article.article_id and other.slug == article.slug
                for other in self._articles.values()
            ):
                article.slug = old_slug
                raise DuplicateArticleError(f"Article with slug '{old_slug}' already exists")
            article.updated_at = time.time()
            article.version += 1
            self._persist_locked()
        return article

    def delete_article(self, article_id: str) -> bool:
        with self._lock:
            if article_id not in self._articles:
                return False
            del self._articles[article_id]
            self._persist_locked()
            return True

    def publish_article(self, article_id: str) -> Article:
        article = self.get_article(article_id)
        if not article:
            raise WebsiteNotFoundError(f"Article {article_id} not found")
        with self._lock:
            if article.status == ArticleStatus.PUBLISHED:
                article.status = ArticleStatus.UPDATED
                article.version += 1
            else:
                article.status = ArticleStatus.PUBLISHED
                article.published_at = time.time()
            article.updated_at = time.time()
            self._total_published += 1
            self._publish_log.append({"article_id": article_id, "title": article.title,
                                      "slug": article.slug, "action": "publish", "timestamp": time.time()})
            self._persist_locked()
        return article

    def draft_article(self, article_id: str) -> Optional[Article]:
        article = self.get_article(article_id)
        if article:
            with self._lock:
                article.status = ArticleStatus.DRAFT
                article.updated_at = time.time()
                self._persist_locked()
        return article

    def schedule_article(self, article_id: str, publish_at: float) -> Optional[Article]:
        article = self.get_article(article_id)
        if article:
            with self._lock:
                article.status = ArticleStatus.SCHEDULED
                article.scheduled_at = publish_at
                article.updated_at = time.time()
                self._persist_locked()
        return article

    def get_due_articles(self) -> List[Article]:
        now = time.time()
        with self._lock:
            return [a for a in self._articles.values()
                    if a.status == ArticleStatus.SCHEDULED and 0 < a.scheduled_at <= now]

    def process_scheduled(self) -> int:
        count = 0
        for article in self.get_due_articles():
            try:
                self.publish_article(article.article_id)
                count += 1
            except Exception:
                with self._lock:
                    self._total_errors += 1
        return count

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            statuses: Dict[str, int] = {}
            for article in self._articles.values():
                status = article.status.value
                statuses[status] = statuses.get(status, 0) + 1
            return {"total_articles": len(self._articles), "by_status": statuses,
                    "total_published": self._total_published, "total_errors": self._total_errors,
                    "scheduled_due": len(self.get_due_articles())}

    @staticmethod
    def _generate_slug(title: str) -> str:
        import re
        slug = re.sub(r"[^a-z0-9\s-]", "", title.lower().strip())
        slug = re.sub(r"[\s]+", "-", slug)
        slug = re.sub(r"-+", "-", slug)
        return slug.strip("-")[:80] or "untitled"

    def _load_from_disk(self) -> None:
        path = os.path.join(self._storage_dir, "articles.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, list):
                raise ValueError("articles.json must contain a list")
            loaded: Dict[str, Article] = {}
            for item in data:
                if not isinstance(item, dict):
                    raise ValueError("article record must be an object")
                record = dict(item)
                record.pop("content_preview", None)
                record.pop("related_articles", None)
                record.setdefault("content", "")
                record.setdefault("excerpt", "")
                record.setdefault("og_title", "")
                record.setdefault("og_description", "")
                record.setdefault("og_image", "")
                record.setdefault("canonical_url", "")
                record.setdefault("related_article_ids", [])
                record.setdefault("internal_links", [])
                record["status"] = ArticleStatus(record.get("status", ArticleStatus.DRAFT))
                loaded[record["article_id"]] = Article(**record)
            with self._lock:
                self._articles = loaded
        except (OSError, ValueError, TypeError, KeyError) as exc:
            raise PublishError(f"failed to load article store: {exc}") from exc

    def _persist_locked(self) -> None:
        if not self._storage_dir:
            return
        os.makedirs(self._storage_dir, exist_ok=True)
        path = os.path.join(self._storage_dir, "articles.json")
        temp_path = f"{path}.tmp"
        payload = []
        for article in self._articles.values():
            item = asdict(article)
            item["status"] = item["status"].value
            payload.append(item)
        try:
            with open(temp_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, path)
        except OSError as exc:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
            except OSError:
                pass
            raise PublishError(f"failed to persist article store: {exc}") from exc

    def save_to_disk(self) -> None:
        with self._lock:
            self._persist_locked()
