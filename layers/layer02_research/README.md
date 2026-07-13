# Research & Scraping

**Layer:** Layer 02 — Research Engine
**Status:** 🔄 In Progress (8/10 modules)
**Version:** v0.2.7

## Description

Facebook topic research, trend discovery, competitor analysis, audience intelligence, knowledge collection, fact verification, research memory, and topic scoring engine.

## Modules

| # | Module | Description | Status |
|---|--------|-------------|--------|
| 1 | Trend Discovery | Multi-source trend aggregation, scoring, filtering | ✅ Complete (43 tests) |
| 2 | Topic Intelligence | Topic scoring, categorization, clustering, opportunities | ✅ Complete (92 tests) |
| 3 | Competitor Analysis | Competitor profiling, engagement analysis, gap detection | ✅ Complete (109 tests) |
| 4 | Audience Research | Audience profiling, interest mapping, behavior analysis | ✅ Complete (94 tests) |
| 5 | Knowledge Collector | Multi-source collection, cleaning, dedup, caching | ✅ Complete (108 tests) |
| 6 | Fact Verification | Claim extraction, evidence matching, contradiction detection | ✅ Complete (64 tests) |
| 7 | Research Memory | Research indexing, semantic search, knowledge graph, decision traces | ✅ Complete (89 tests) |
| 8 | Topic Scoring Engine | Multi-factor scoring with niche weights, risk/opportunity/confidence | ✅ Complete (62 tests) |
| 9 | Research Planner | Automated research scheduling | 🔜 Pending |
| 10 | Research Orchestrator | End-to-end research pipeline | 🔜 Pending |

## Shared Components

| Component | Description | Location |
|-----------|-------------|----------|
| Confidence Engine | Global confidence scoring with evidence + risk levels | `shared/confidence_engine.py` |

## Tests

```bash
pytest layers/layer02_research/tests/ -v
```
