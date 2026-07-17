"""SEOOptimizer — Optimize content for search engines."""
from __future__ import annotations
from typing import Any, Dict, List, Optional


class SEOOptimizer:
    """Optimize content with SEO best practices."""

    def __init__(self) -> None:
        self._optimizations: List[Dict[str, Any]] = []

    def optimize_title(self, title: str, keyword: str = "") -> Dict[str, Any]:
        optimized = title
        if keyword and keyword.lower() not in title.lower():
            optimized = f"{keyword}: {title}"
        if len(optimized) > 60:
            optimized = optimized[:57] + "..."
        result = {"original": title, "optimized": optimized, "keyword_added": keyword.lower() not in title.lower()}
        self._optimizations.append(result)
        return result

    def optimize_description(self, description: str, keyword: str = "",
                              max_length: int = 160) -> Dict[str, Any]:
        optimized = description
        if keyword and keyword.lower() not in description.lower():
            optimized = f"{description} | {keyword}"
        if len(optimized) > max_length:
            optimized = optimized[:max_length-3] + "..."
        return {"original": description, "optimized": optimized}

    def generate_meta(self, title: str, description: str,
                       keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        return {
            "title": title[:60], "description": description[:160],
            "keywords": keywords or [], "og_title": title[:70],
            "og_description": description[:200],
        }

    def check_keyword_density(self, text: str, keyword: str) -> Dict[str, Any]:
        words = text.lower().split()
        if not words:
            return {"keyword": keyword, "count": 0, "density": 0.0}
        count = sum(1 for w in words if keyword.lower() in w)
        density = round(count / len(words) * 100, 2)
        return {"keyword": keyword, "count": count, "density": density}

    def get_stats(self) -> Dict[str, Any]:
        return {"total_optimizations": len(self._optimizations)}
