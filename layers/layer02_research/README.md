# Research & Scraping

**Layer:** Layer 02 — Research Engine
**Status:** 🔄 In Progress (2/10 modules)
**Version:** v0.2.1

## Description

Facebook topic research, trend discovery, competitor analysis, audience intelligence, and content planning engine.

## Modules

| # | Module | Description | Status |
|---|--------|-------------|--------|
| 1 | Trend Discovery | Multi-source trend aggregation, scoring, filtering | ✅ Complete (43 tests) |
| 2 | Topic Intelligence | Topic scoring, categorization, clustering, opportunities | ✅ Complete (92 tests) |
| 3 | Competitor Analysis | Competitor tracking, content gap analysis | 🔜 Pending |
| 4 | Audience Research | Audience profiling, interest mapping | 🔜 Pending |
| 5 | Knowledge Collector | Knowledge base building from research | 🔜 Pending |
| 6 | Research Memory | Research history and pattern recall | 🔜 Pending |
| 7 | Fact Verification | Claim validation, source credibility | 🔜 Pending |
| 8 | Topic Scoring | Advanced multi-factor topic ranking | 🔜 Pending |
| 9 | Research Planner | Automated research scheduling | 🔜 Pending |
| 10 | Research Orchestrator | End-to-end research pipeline | 🔜 Pending |

## Usage

```python
from layers.layer02_research.modules.trend_discovery.trend_manager import TrendManager
from layers.layer02_research.modules.topic_intelligence.topic_intel_manager import TopicIntelManager

# Trend Discovery
tm = TrendManager()
tm.register_source("my_source", fetch_fn=my_fetch)
tm.discover()

# Topic Intelligence
tim = TopicIntelManager()
topic = tim.add_topic("AI in Finance", niche="ai", engagement_score=8.0)
top = tim.get_top_topics(count=5)
```

## Tests

```bash
pytest layers/layer02_research/tests/ -v
```
