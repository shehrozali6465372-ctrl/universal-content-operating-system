# UAOM v1.0 - Frozen Architecture Index

**Model:** UCOS Agentic Operating Model (UAOM) v1.0  
**Freeze date:** 14 October 2026  
**Status:** Design-frozen target architecture; implementation remains subject to CI and production certification gates.

## The single model

UAOM has one CEO/control plane and one workforce/operations plane. These are the two canonical views of the same architecture. They do not form separate products or competing orchestration brains.

1. [CEO Agent Architecture](UCOS_CEO_AGENT_ARCHITECTURE_V1.md) - Super Intelligence as the accountable goal owner, planner, router, evidence judge, learning decision-maker and operator console control plane.
2. [Specialist Agents and System Guardian](UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md) - frozen 29-role workforce, standard contracts, platform publishers, System Guardian, telemetry/incident lifecycle, UI design and security/testing requirements.

The PDFs delivered with this release are expanded visual reading editions of these two specifications. The Markdown files in this directory define the versioned source specification; a generated PDF alone does not certify code or services as deployed.

## Architectural constants

- Preserve the 23 UCOS layers as logical capabilities during staged migration.
- Preserve the seven-service deployment boundary. Logical agents are not one-microservice-per-agent.
- One CEO (Super Intelligence Agent); specialists return bounded results and evidence.
- Platform publishing agents are platform-based, while each run selects an exact authorized platform connection/account.
- PostgreSQL is the canonical durable workflow ledger; Redis is never the only task/incident source of truth.
- Every task has explicit identity scope, tools, acceptance criteria, cost/deadline limits and idempotency semantics.
- External publication requires reconciliation and public-state verification; provider receipt alone is not proof of success.
- System Guardian continuously correlates telemetry and preserves incidents, while an independent probe monitors Guardian/collector silence.
- Live UI must show source and freshness, with LIVE / STALE / DEGRADED / NO DATA state. No mock values can be presented as production telemetry.

## Freeze and change control

The two specifications jointly define freeze ID UAOM-v1.0. A change to service boundaries, identity scope, task/result schemas, state transitions, publishing idempotency, telemetry correlation or Guardian remediation authority requires an Architecture Decision Record (ADR), compatibility and migration notes, threat review, tests, observability and rollback plan.

## Production certification is separate

Design freeze is not production readiness. A production claim requires current CI evidence, the deployed commit/service version, applied database migrations, real provider authorization, live probes, a real end-to-end authorized run, external publication verification where relevant, incident/recovery drill and operator sign-off. The specs intentionally do not claim that every role or integration is already live.
