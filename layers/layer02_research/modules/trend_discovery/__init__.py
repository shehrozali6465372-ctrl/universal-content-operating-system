"""
Trend Discovery Module
Layer 2: Research Engine — Module 1

Discovers trending topics, keywords, and content ideas:
- Multi-source trend aggregation
- Trend scoring (virality, relevance, freshness)
- Category/niche filtering
- Trend history and comparison
- Extensible source adapter pattern
"""

from layers.layer02_research.modules.trend_discovery.trend_manager import TrendManager
from layers.layer02_research.modules.trend_discovery.trend_entry import TrendEntry

__all__ = ["TrendManager", "TrendEntry"]
