"""SiteStructure — Website navigation and structure model."""
from __future__ import annotations
import time
import uuid
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class NavigationItem:
    """Single navigation menu item."""
    item_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str = ""
    url: str = ""
    parent_id: Optional[str] = None
    order: int = 0
    is_external: bool = False
    is_active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "label": self.label,
            "url": self.url,
            "parent_id": self.parent_id,
            "order": self.order,
            "is_external": self.is_external,
            "is_active": self.is_active,
        }


@dataclass
class Category:
    """Content category."""
    category_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    slug: str = ""
    description: str = ""
    parent_id: Optional[str] = None
    order: int = 0
    article_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "parent_id": self.parent_id,
            "order": self.order,
            "article_count": self.article_count,
        }


class SiteStructure:
    """Complete website structure — navigation, categories, pages."""

    def __init__(self) -> None:
        self._navigation: List[NavigationItem] = []
        self._categories: Dict[str, Category] = {}
        self._pages: Dict[str, dict] = {}

        # Default pages
        self._pages["home"] = {"title": "Home", "slug": "/", "active": True}
        self._pages["about"] = {"title": "About", "slug": "/about", "active": True}
        self._pages["contact"] = {"title": "Contact", "slug": "/contact", "active": True}
        self._pages["privacy"] = {"title": "Privacy Policy", "slug": "/privacy-policy", "active": True}
        self._pages["affiliate"] = {"title": "Affiliate Disclosure", "slug": "/affiliate-disclosure", "active": True}

    # ─── Navigation ────────────────────────────────────────

    def add_nav_item(self, label: str, url: str, parent_id: Optional[str] = None,
                     order: int = 0, is_external: bool = False) -> NavigationItem:
        item = NavigationItem(
            label=label, url=url, parent_id=parent_id,
            order=order, is_external=is_external,
        )
        self._navigation.append(item)
        return item

    def remove_nav_item(self, item_id: str) -> bool:
        for i, item in enumerate(self._navigation):
            if item.item_id == item_id:
                del self._navigation[i]
                return True
        return False

    def get_navigation(self) -> List[NavigationItem]:
        return sorted(self._navigation, key=lambda x: (x.order, x.label))

    # ─── Categories ─────────────────────────────────────────

    def add_category(self, name: str, slug: str = "", description: str = "",
                     parent_id: Optional[str] = None, order: int = 0) -> Category:
        slug = slug or name.lower().replace(" ", "-")
        cat = Category(name=name, slug=slug, description=description,
                       parent_id=parent_id, order=order)
        self._categories[cat.category_id] = cat
        return cat

    def get_category(self, category_id: str) -> Optional[Category]:
        return self._categories.get(category_id)

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        for cat in self._categories.values():
            if cat.slug == slug:
                return cat
        return None

    def get_all_categories(self) -> List[Category]:
        return sorted(self._categories.values(), key=lambda x: (x.order, x.name))

    def remove_category(self, category_id: str) -> bool:
        if category_id in self._categories:
            del self._categories[category_id]
            return True
        return False

    # ─── Pages ──────────────────────────────────────────────

    def get_page(self, page_key: str) -> Optional[dict]:
        return self._pages.get(page_key)

    def get_all_pages(self) -> Dict[str, dict]:
        return dict(self._pages)

    def update_page(self, page_key: str, data: dict) -> bool:
        if page_key in self._pages:
            self._pages[page_key].update(data)
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "navigation": [item.to_dict() for item in self._navigation],
            "categories": [cat.to_dict() for cat in self._categories.values()],
            "pages": self._pages,
        }
