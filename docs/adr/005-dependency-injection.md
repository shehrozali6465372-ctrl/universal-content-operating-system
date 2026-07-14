# ADR-005: Dependency Injection

**Status:** Accepted
**Date:** 2026-07-14

## Context

Managers were instantiating their dependencies directly, creating tight coupling.

## Decision

Lightweight DI Container with:
- Factory-based registration
- Singleton and transient lifetimes
- Circular dependency detection
- Child containers for scoped resolution
- Tag-based service discovery

## Consequences

- Loose coupling between components
- Easy to mock for testing
- Clear dependency graph
- Minimal overhead (no reflection)
