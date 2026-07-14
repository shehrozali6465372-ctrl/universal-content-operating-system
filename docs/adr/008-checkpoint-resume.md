# ADR-008: Checkpoint/Resume Pattern

**Status:** Accepted
**Date:** 2026-07-14

## Context

Long-running research pipelines may fail mid-execution.

## Decision

Checkpoint system with:
- Save at each module completion
- SHA-256 integrity verification
- Restore from last valid checkpoint
- Skip already-completed modules

## Consequences

- No re-execution of completed work
- Crash recovery without data loss
- Integrity verification prevents corruption
- Supports long-running workflows
