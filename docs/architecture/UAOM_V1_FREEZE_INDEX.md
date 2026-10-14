# UCOS 1 — Frozen Architecture Index

**Canonical architecture:** UCOS 1 (the frozen CEO + specialist workforce model)  
**Freeze date:** 14 October 2026  
**Status:** Design-frozen. Runtime implementation and production certification remain separate gates.

## Authority rule

**This document and the two linked specifications are the sole authoritative architecture for UCOS 1.** Superseded architecture drafts and competing architecture proposals have been removed from this branch. Do not introduce another architecture in parallel. If a change is genuinely required, submit an Architecture Decision Record (ADR), compatibility/migration notes, threat review, tests, observability and rollback plan before changing the frozen design.

## The one architecture, in two views

1. [CEO / Super Intelligence Agent](UCOS_CEO_AGENT_ARCHITECTURE_V1.md) — accountable goal owner, planner, router, evidence judge, learning decision-maker and control-plane operator console.
2. [Specialist Agents and System Guardian](UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md) — the 29-role workforce, shared contracts, platform publishers, live observability, incident/debugging lifecycle, UI design and security/testing requirements.

These are two views of the same UCOS 1 system, not separate products or competing brains. PDFs are reading editions; these Markdown specifications are the source of truth.

## Frozen architectural constants

- Preserve the existing 23 logical layers as capabilities; do not equate layers or agents with separate deployed microservices.
- Preserve the seven-service deployment boundary.
- One CEO agent coordinates specialist agents; specialists return bounded results and evidence.
- Publisher agents are platform-based, with each run selecting an explicitly authorized account/connection.
- PostgreSQL is the canonical durable workflow ledger; Redis must not be the sole source of durable task or incident state.
- Each task has explicit identity scope, allowed tools, acceptance criteria, cost/deadline limits and idempotency semantics.
- External publishing requires reconciliation and public-state verification; a provider receipt alone is not proof of public success.
- System Guardian correlates telemetry and preserves incidents; an independent probe must detect Guardian/collector silence.
- Live UI must display source and freshness with LIVE / STALE / DEGRADED / NO DATA states. Mock values must never be presented as production telemetry.

## Production status is not implied by architecture freeze

Architecture freeze does not certify the runtime as production-ready. Certification requires current CI evidence, deployed commit/service version, applied database migrations, real provider authorization, live probes, a real authorized end-to-end run, public verification where relevant, recovery drills and operator sign-off. Do not claim integrations, monitoring, agents or UI are live without current evidence.
