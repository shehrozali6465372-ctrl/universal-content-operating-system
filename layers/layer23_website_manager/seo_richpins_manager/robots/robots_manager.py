"""RobotsManager — Generate robots.txt with crawl rules, AI bot rules, sitemap reference."""
from __future__ import annotations
from typing import Any, Dict, List, Optional

from layers.layer23_website_manager.seo_richpins_manager.exceptions import RobotsError


class RobotsManager:
    """Generate and manage robots.txt — crawl rules, AI bot rules, sitemap reference."""

    AI_BOTS = ["GPTBot", "CCBot", "Claude-Web", "OAI-SearchBot", "PerplexityBot",
               "anthropic-ai", "Google-Extended", "cohere-ai"]

    def __init__(self) -> None:
        self._robots_log: List[dict] = []

    def generate_robots_txt(self, sitemap_url: str = "",
                              allow_all: bool = True,
                              restricted_paths: Optional[List[str]] = None,
                              restrict_ai_bots: bool = False) -> str:
        """Generate robots.txt content."""
        lines = ["User-agent: *"]

        if allow_all:
            lines.append("Disallow:")
        else:
            lines.append("Disallow: /")

        if restricted_paths:
            for path in restricted_paths:
                lines.append(f"Disallow: {path}")

        if restrict_ai_bots:
            for bot in self.AI_BOTS:
                lines.append(f"\nUser-agent: {bot}")
                lines.append("Disallow: /")

        lines.append(f"\nSitemap: {sitemap_url}")

        result = "\n".join(lines)

        self._robots_log.append({"allow_all": allow_all, "restrict_ai": restrict_ai_bots})
        return result

    def generate_ai_bot_rules(self) -> str:
        """Generate specific rules for AI crawler bots."""
        rules = []
        for bot in self.AI_BOTS:
            rules.append(f"User-agent: {bot}\nDisallow: /\n")
        return "\n".join(rules)

    def get_stats(self) -> Dict[str, Any]:
        return {"total_robots": len(self._robots_log)}
