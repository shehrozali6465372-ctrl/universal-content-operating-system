# ADR-007: State Machine for Orchestrator

**Status:** Accepted
**Date:** 2026-07-14

## Context

Research orchestration requires managing complex state transitions.

## Decision

Formal state machine with:
- Defined valid transitions
- Transition history
- Terminal state detection
- Active state queries

States: created → planned → running → paused/resuming/completed/failed/cancelled/retrying

## Consequences

- Prevents invalid state transitions
- Full audit trail
- Easy to query current state
- Supports pause/resume workflow
