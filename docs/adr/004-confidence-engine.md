# ADR-004: Confidence Engine

**Status:** Accepted
**Date:** 2026-07-13

## Context

Every research module produces decisions, but confidence scoring was inconsistent.

## Decision

Shared ConfidenceEngine with:
- Standardized ConfidenceResult
- Evidence-based scoring
- Risk level assessment (VERY_LOW → CRITICAL)
- Trust threshold (≥0.7 and LOW/MEDIUM risk)

## Consequences

- Consistent confidence scoring across all modules
- Layer 9 (Self-Learning) can analyze decision quality
- Trust threshold prevents premature publishing
