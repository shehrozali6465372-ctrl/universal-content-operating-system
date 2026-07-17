"""Brand Safety — Brand-specific content policies."""
from __future__ import annotations
from typing import Any, Dict, List


class BrandPolicy:
    """Brand-specific content safety policy."""

    __slots__ = ("brand_id", "blocked_topics", "blocked_competitors",
                 "required_disclaimers", "tone_requirements",
                 "content_guidelines")

    def __init__(self, brand_id: str = "") -> None:
        self.brand_id = brand_id
        self.blocked_topics: List[str] = []
        self.blocked_competitors: List[str] = []
        self.required_disclaimers: List[str] = []
        self.tone_requirements: List[str] = []
        self.content_guidelines: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "brand_id": self.brand_id,
            "blocked_topics": self.blocked_topics,
            "blocked_competitors": self.blocked_competitors,
            "required_disclaimers": self.required_disclaimers,
        }


class BrandSafety:
    """Brand safety policies for content."""

    def __init__(self) -> None:
        self._policies: Dict[str, BrandPolicy] = {}

    def add_policy(self, policy: BrandPolicy) -> None:
        self._policies[policy.brand_id] = policy

    def get_policy(self, brand_id: str) -> BrandPolicy:
        return self._policies.get(brand_id, BrandPolicy(brand_id))

    def check_content(self, brand_id: str, content: str) -> List[str]:
        policy = self.get_policy(brand_id)
        violations: List[str] = []
        content_lower = content.lower()
        for topic in policy.blocked_topics:
            if topic.lower() in content_lower:
                violations.append(f"Blocked topic: {topic}")
        for competitor in policy.blocked_competitors:
            if competitor.lower() in content_lower:
                violations.append(f"Competitor mention: {competitor}")
        return violations

    def is_safe(self, brand_id: str, content: str) -> bool:
        return len(self.check_content(brand_id, content)) == 0

    def get_all_policies(self) -> Dict[str, BrandPolicy]:
        return dict(self._policies)
