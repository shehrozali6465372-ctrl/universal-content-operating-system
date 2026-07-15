"""Content Structure — Define content structure templates."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


STRUCTURE_TEMPLATES = {
    "educational_post": {
        "sections": ["hook", "context", "main_points", "summary", "cta"],
        "estimated_words": {"hook": 20, "context": 50, "main_points": 200, "summary": 30, "cta": 20},
    },
    "entertaining_post": {
        "sections": ["hook", "story", "punchline", "engagement_ask"],
        "estimated_words": {"hook": 15, "story": 150, "punchline": 20, "engagement_ask": 15},
    },
    "promotional_post": {
        "sections": ["hook", "problem", "solution", "benefits", "cta"],
        "estimated_words": {"hook": 15, "problem": 40, "solution": 60, "benefits": 80, "cta": 25},
    },
    "inspiring_post": {
        "sections": ["hook", "story", "lesson", "call_to_action"],
        "estimated_words": {"hook": 15, "story": 120, "lesson": 40, "call_to_action": 20},
    },
    "engaging_post": {
        "sections": ["hook", "question", "options", "cta"],
        "estimated_words": {"hook": 15, "question": 30, "options": 50, "cta": 15},
    },
    "carousel": {
        "sections": ["title_slide", "content_slides", "summary_slide", "cta_slide"],
        "estimated_words": {"title_slide": 10, "content_slides": 50, "summary_slide": 30, "cta_slide": 15},
    },
    "story": {
        "sections": ["attention_grab", "content", "swipe_prompt"],
        "estimated_words": {"attention_grab": 10, "content": 30, "swipe_prompt": 5},
    },
}


class ContentStructure:
    """Defines the structure for a piece of content."""
    __slots__ = ("template_name", "sections", "estimated_words",
                 "total_estimated_words", "custom_sections")

    def __init__(self, template_name: str = "educational_post") -> None:
        self.template_name = template_name
        template = STRUCTURE_TEMPLATES.get(template_name, STRUCTURE_TEMPLATES["educational_post"])
        self.sections = list(template["sections"])
        self.estimated_words = dict(template["estimated_words"])
        self.total_estimated_words = sum(self.estimated_words.values())
        self.custom_sections: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "template": self.template_name,
            "sections": self.sections,
            "estimated_words": self.estimated_words,
            "total_estimated_words": self.total_estimated_words,
            "custom_sections": self.custom_sections,
        }


class ContentStructureBuilder:
    """Builds content structures based on goal and platform."""

    GOAL_TEMPLATE_MAP = {
        "educate": "educational_post",
        "entertain": "entertaining_post",
        "inspire": "inspiring_post",
        "promote": "promotional_post",
        "engage": "engaging_post",
    }

    def __init__(self) -> None:
        pass

    def build(self, goal: str = "educate", content_type: str = "post",
              custom_sections: Optional[List[str]] = None) -> ContentStructure:
        """Build a content structure."""
        if content_type == "carousel":
            template = "carousel"
        elif content_type == "story":
            template = "story"
        else:
            template = self.GOAL_TEMPLATE_MAP.get(goal, "educational_post")

        structure = ContentStructure(template)
        if custom_sections:
            structure.custom_sections = [{"name": s, "words": 50} for s in custom_sections]
        return structure

    def get_available_templates(self) -> List[str]:
        return list(STRUCTURE_TEMPLATES.keys())

    def add_custom_template(self, name: str, sections: List[str],
                            words: Optional[Dict[str, int]] = None) -> None:
        """Register a custom template."""
        words = words or {s: 50 for s in sections}
        STRUCTURE_TEMPLATES[name] = {
            "sections": sections,
            "estimated_words": words,
        }
