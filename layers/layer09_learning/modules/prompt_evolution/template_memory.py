"""TemplateMemory — Persistent storage for prompt templates.

Stores templates organized by platform, topic, and performance tier.
Supports search, filtering, and retrieval of best-performing templates.
"""
from __future__ import annotations
import json
import os
import time
from typing import Any, Dict, List, Optional

from layers.layer09_learning.modules.prompt_evolution.prompt_template import PromptTemplate


class TemplateMemory:
    """Stores and retrieves prompt templates with performance tracking."""

    def __init__(self, storage_path: Optional[str] = None, max_entries: int = 5000) -> None:
        self._templates: Dict[str, PromptTemplate] = {}
        self._by_platform: Dict[str, List[str]] = {}
        self._by_topic: Dict[str, List[str]] = {}
        self._by_hook_type: Dict[str, List[str]] = {}
        self._storage_path = storage_path
        self._max_entries = max_entries
        self._load()

    def store(self, template: PromptTemplate) -> str:
        """Store a template. Returns template_id."""
        self._templates[template.template_id] = template

        # Index by platform
        plat = template.platform
        self._by_platform.setdefault(plat, []).append(template.template_id)

        # Index by topic
        topic_key = template.topic.lower().strip() if template.topic else "__general__"
        self._by_topic.setdefault(topic_key, []).append(template.template_id)

        # Index by hook type
        self._by_hook_type.setdefault(template.hook_type, []).append(template.template_id)

        self._enforce_limit()
        self._save()
        return template.template_id

    def get(self, template_id: str) -> Optional[PromptTemplate]:
        """Get template by ID."""
        return self._templates.get(template_id)

    def search(
        self,
        platform: Optional[str] = None,
        topic: Optional[str] = None,
        hook_type: Optional[str] = None,
        min_score: float = 0.0,
        max_score: float = 10.0,
        tags: Optional[List[str]] = None,
        limit: int = 50,
    ) -> List[PromptTemplate]:
        """Search templates with filters."""
        candidates = list(self._templates.values())

        if platform:
            ids = set(self._by_platform.get(platform, []))
            candidates = [t for t in candidates if t.template_id in ids]

        if topic:
            topic_key = topic.lower().strip()
            ids = set(self._by_topic.get(topic_key, []))
            candidates = [t for t in candidates if t.template_id in ids]

        if hook_type:
            ids = set(self._by_hook_type.get(hook_type, []))
            candidates = [t for t in candidates if t.template_id in ids]

        candidates = [t for t in candidates if min_score <= t.score <= max_score]

        if tags:
            tag_set = set(tags)
            candidates = [t for t in candidates if tag_set.intersection(t.tags)]

        # Sort by score descending
        candidates.sort(key=lambda t: t.score, reverse=True)
        return candidates[:limit]

    def get_champions(self, platform: Optional[str] = None,
                      limit: int = 10) -> List[PromptTemplate]:
        """Get best-performing templates (score >= 8.0)."""
        return self.search(platform=platform, min_score=8.0, limit=limit)

    def get_challengers(self, platform: Optional[str] = None,
                        limit: int = 10) -> List[PromptTemplate]:
        """Get templates being A/B tested (score 5.0-8.0)."""
        return self.search(platform=platform, min_score=5.0, max_score=7.99, limit=limit)

    def get_retired(self, limit: int = 50) -> List[PromptTemplate]:
        """Get templates that should be retired."""
        return [t for t in self._templates.values() if t.is_retired][:limit]

    def get_best_for_topic(self, topic: str, platform: str = "facebook",
                           limit: int = 5) -> List[PromptTemplate]:
        """Get best templates for a specific topic + platform."""
        return self.search(platform=platform, topic=topic, min_score=0.0, limit=limit)

    def remove(self, template_id: str) -> bool:
        """Remove a template."""
        if template_id not in self._templates:
            return False
        tpl = self._templates.pop(template_id)
        # Clean up indices
        for idx in (self._by_platform, self._by_topic, self._by_hook_type):
            for key, ids in idx.items():
                if template_id in ids:
                    ids.remove(template_id)
        self._save()
        return True

    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        templates = list(self._templates.values())
        return {
            "total_templates": len(templates),
            "champions": len([t for t in templates if t.is_champion]),
            "challengers": len([t for t in templates if t.is_challenger]),
            "retired": len([t for t in templates if t.is_retired]),
            "platforms": {p: len(ids) for p, ids in self._by_platform.items()},
            "avg_score": round(sum(t.score for t in templates) / max(len(templates), 1), 2),
            "total_uses": sum(t.total_uses for t in templates),
        }

    def _enforce_limit(self) -> None:
        """Remove oldest low-score templates if over limit."""
        if len(self._templates) <= self._max_entries:
            return
        sorted_tpls = sorted(self._templates.values(), key=lambda t: (t.score, -t.created_at))
        to_remove = len(self._templates) - self._max_entries
        for tpl in sorted_tpls[:to_remove]:
            self.remove(tpl.template_id)

    def _save(self) -> None:
        """Persist to disk if storage path set."""
        if not self._storage_path:
            return
        try:
            os.makedirs(os.path.dirname(self._storage_path), exist_ok=True)
            data = {tid: t.to_dict() for tid, t in self._templates.items()}
            with open(self._storage_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception:
            pass

    def _load(self) -> None:
        """Load from disk if storage path set."""
        if not self._storage_path or not os.path.exists(self._storage_path):
            return
        try:
            with open(self._storage_path) as f:
                data = json.load(f)
            for tid, d in data.items():
                t = PromptTemplate(
                    topic=d.get("topic", ""), platform=d.get("platform", "facebook"),
                    tone=d.get("tone", ""), style=d.get("style", ""),
                    hook_type=d.get("hook_type", "question"),
                    cta_type=d.get("cta_type", "ask_question"),
                )
                t.template_id = d.get("template_id", tid)
                t.body_template = d.get("body_template", "")
                t.hook_template = d.get("hook_template", "")
                t.cta_template = d.get("cta_template", "")
                t.hashtags_template = d.get("hashtags_template", "")
                t.tags = d.get("tags", [])
                t.generation = d.get("generation", 1)
                t.total_uses = d.get("total_uses", 0)
                t.total_impressions = d.get("total_impressions", 0)
                t.total_engagements = d.get("total_engagements", 0)
                t.total_clicks = d.get("total_clicks", 0)
                t.score = d.get("score", 0.0)
                self._templates[t.template_id] = t
        except Exception:
            pass
