# ADR-006: Plugin Architecture

**Status:** Accepted
**Date:** 2026-07-14

## Context

Research sources (Facebook, RSS, News) and platforms (YouTube, X, LinkedIn) should be extensible without modifying core code.

## Decision

Plugin system with:
- Abstract Plugin base class
- PluginManager for lifecycle management
- Capability-based discovery
- Priority ordering
- Lifecycle hooks (init, activate, deactivate, destroy)

## Consequences

- New sources/platforms added without core changes
- Plugins can be independently developed and tested
- Dynamic activation/deactivation
- Clear interface contracts
