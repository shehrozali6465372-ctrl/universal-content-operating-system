"""SiteStructureManager — Manage website structure, navigation, categories, and pages."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.models.site_structure import (
    SiteStructure, NavigationItem, Category,
)


class SiteStructureManager:
    """Manage website structure — navigation menus, categories, static pages."""

    def __init__(self) -> None:
        self._structure = SiteStructure()

    # ─── Navigation ────────────────────────────────────────

    def add_nav_item(self, label: str, url: str, parent_id: Optional[str] = None,
                     order: int = 0, is_external: bool = False) -> NavigationItem:
        return self._structure.add_nav_item(label, url, parent_id, order, is_external)

    def remove_nav_item(self, item_id: str) -> bool:
        return self._structure.remove_nav_item(item_id)

    def get_navigation(self) -> List[NavigationItem]:
        return self._structure.get_navigation()

    def rebuild_navigation(self, items: List[Dict[str, Any]]) -> None:
        """Replace all navigation items with a new list."""
        self._structure._navigation.clear()
        for item in items:
            self._structure.add_nav_item(
                label=item.get("label", ""),
                url=item.get("url", ""),
                parent_id=item.get("parent_id"),
                order=item.get("order", 0),
                is_external=item.get("is_external", False),
            )

    # ─── Categories ────────────────────────────────────────

    def add_category(self, name: str, slug: str = "", description: str = "",
                     parent_id: Optional[str] = None, order: int = 0) -> Category:
        return self._structure.add_category(name, slug, description, parent_id, order)

    def get_category(self, category_id: str) -> Optional[Category]:
        return self._structure.get_category(category_id)

    def get_category_by_slug(self, slug: str) -> Optional[Category]:
        return self._structure.get_category_by_slug(slug)

    def get_all_categories(self) -> List[Category]:
        return self._structure.get_all_categories()

    def remove_category(self, category_id: str) -> bool:
        return self._structure.remove_category(category_id)

    # ─── Static Pages ──────────────────────────────────────

    def get_page(self, page_key: str) -> Optional[dict]:
        return self._structure.get_page(page_key)

    def get_all_pages(self) -> Dict[str, dict]:
        return self._structure.get_all_pages()

    def update_page(self, page_key: str, data: dict) -> bool:
        return self._structure.update_page(page_key, data)

    # ─── Serialization ─────────────────────────────────────

    def to_dict(self) -> Dict[str, Any]:
        return self._structure.to_dict()
