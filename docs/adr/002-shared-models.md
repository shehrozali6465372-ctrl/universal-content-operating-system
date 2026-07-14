# ADR-002: Shared Models

**Status:** Accepted
**Date:** 2026-07-14

## Context

Each layer was creating its own data models, leading to duplication and inconsistency.

## Decision

Create `layers/shared/models/` with frozen, versioned interfaces:
- Topic, TopicScore
- ConfidenceResult
- Evidence, EvidenceBundle
- DecisionRecord, DecisionTrace
- ContentPost, ContentVariant
- EngagementMetrics, AnalyticsSnapshot
- Event, EventType

## Consequences

- Single source of truth for cross-layer data
- Backward compatibility via versioning
- All layers use the same models
- Changes require explicit version bumps
