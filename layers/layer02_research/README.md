# 🔍 Research Engine

**Layer:** Layer 02 — Research Engine
**Status:** ✅ Complete (10/10 modules)
**Version:** v0.2.9
**Tests:** 299/299 passing

## Description

End-to-end research pipeline that discovers trends, analyzes competitors, profiles audiences, collects knowledge, verifies facts, and produces scored, evidence-backed topic recommendations for the Writing Layer.

## Architecture

```
Trend Discovery
       ↓
Topic Intelligence
       ↓
Competitor Analysis ─┐
                     │
Audience Research ───┤
                     │
Knowledge Collector ─┤
                     ├→ Topic Scoring → Research Planner → Research Orchestrator
Fact Verification ───┤
                     │
Research Memory ─────┘
```

## Modules

| # | Module | Description | Status | Tests |
|---|--------|-------------|--------|-------|
| 1 | Trend Discovery | Multi-source trend aggregation, scoring, filtering | ✅ | 43 |
| 2 | Topic Intelligence | Topic scoring, categorization, clustering, opportunities | ✅ | 92 |
| 3 | Competitor Analysis | Competitor profiling, engagement analysis, gap detection | ✅ | 109 |
| 4 | Audience Research | Audience profiling, interest mapping, behavior analysis | ✅ | 94 |
| 5 | Knowledge Collector | Multi-source collection, cleaning, dedup, caching | ✅ | 108 |
| 6 | Fact Verification | Claim extraction, evidence matching, contradiction detection | ✅ | 64 |
| 7 | Research Memory | Research indexing, semantic search, knowledge graph, decision traces | ✅ | 89 |
| 8 | Topic Scoring Engine | Multi-factor scoring with niche weights, risk/opportunity/confidence | ✅ | 62 |
| 9 | Research Planner | Goal decomposition, dependency graphs, priority engine, resource estimation | ✅ | 146 |
| 10 | Research Orchestrator | State machine, checkpoint/resume, parallel execution, retry, metrics | ✅ | 153 |

## Shared Components

| Component | Description | Location |
|-----------|-------------|----------|
| Confidence Engine | Global confidence scoring with evidence + risk levels | `shared/confidence_engine.py` |

## Key Patterns

- **Evidence-based decisions**: Every conclusion carries evidence, confidence, and citations
- **Decision Trace Engine**: Full reasoning chain stored for Layer 9 self-learning
- **Niche-aware scoring**: 14+ weight profiles for different content domains
- **Checkpoint/resume**: Crash recovery via SHA-256 integrity-verified checkpoints
- **Parallel execution**: Dependency-aware wave-based module execution

## Tests

```bash
pytest tests/layer02_research/ -v
```
