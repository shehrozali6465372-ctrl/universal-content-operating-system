# ADR-003: Global Event Bus

**Status:** Accepted
**Date:** 2026-07-14

## Context

Layers need to communicate without direct coupling. Settings changes, research completion, and publishing events must propagate across the system.

## Decision

Implement a global EventBus with:
- Subscribe/unsubscribe by EventType
- Priority-based handler ordering
- Wildcard subscriptions
- Error isolation
- Event history and replay

## Consequences

- Loose coupling between layers
- Event-driven architecture enables async communication
- Error in one handler doesn't break others
- Event history enables debugging and replay
