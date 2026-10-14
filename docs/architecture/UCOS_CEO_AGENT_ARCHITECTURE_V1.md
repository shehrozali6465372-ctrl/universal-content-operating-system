# UCOS CEO Agent Architecture — UAOM v1.0

**Status:** FROZEN CANONICAL ARCHITECTURE  
**Revision:** 14 October 2026  
**Owner:** UCOS  
**Repository:** `shehrozali6465372-ctrl/universal-content-operating-system`  
**Production status:** NOT CERTIFIED BY THIS SPECIFICATION

This is the single normative control-plane architecture for UCOS. The companion canonical document is [UCOS Specialist Agents + System Guardian](UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md). They are two views of one architecture, not competing designs. No alternative top-level architecture is approved by UAOM v1.0.

## 1. Executive decision

The **Super Intelligence Agent (SIA)** is UCOS's CEO: one accountable goal owner, planner, delegator, evidence reviewer, policy-aware decision-maker and central learning coordinator. The user requests an outcome; SIA turns it into a bounded plan, dispatches the smallest sufficient set of logical specialist agents, persists state transitions, verifies acceptance criteria and reports only outcomes supported by evidence.

The LLM proposes plans and explanations. Deterministic code enforces identity, permissions, schemas, budgets, state transitions, idempotency, approval and authorization. PostgreSQL owns durable workflow truth. All real tool access passes through a scoped tool/provider gateway. The independently supervised System Guardian observes operations and preserves incident evidence.

### Design invariants

1. Goal-first: the user requests an outcome, not a click sequence.
2. Evidence-first: model assertions are not proof; material completion claims map to evidence and acceptance criteria.
3. Durable-by-default: goals, plans, tasks, runs, approvals, side-effect intents, receipts, incidents and final results survive process restarts.
4. Least privilege: every task has explicit tenant/workspace/brand/connection scope, tools, limits and expiry.
5. Human authority remains for configured high-impact or irreversible actions.
6. Bounded execution: deadlines, cost/token budgets, tool timeouts, attempts, handoffs and stop conditions are enforced in code.
7. No duplicate side effects: idempotency keys and reconciliation protect publishing, purchases and account changes.
8. Learning is evidence-gated, scoped and reversible; untrusted web content never becomes policy.
9. Agents cannot grant themselves permissions. Only deterministic policy/gateway code authorizes tools.
10. One architecture: 23 existing UCOS layers remain logical capability boundaries, while deployments stay inside the seven service domains below. Never create one deployed service per agent.

## 2. Canonical topology

```text
User / Scheduler / approved event
             |
             v
API Gateway + Identity / Scope / Policy
             |
             v
SUPER INTELLIGENCE AGENT (CEO)
  normalize goal -> plan -> delegate -> judge -> learn
             |
             v
Goal contract + versioned Task DAG + acceptance criteria
             |
             v
Capability registry + agent manifests + health/scope checks
             |
             v
Deterministic policy / approval / budget gates
             |
             v
Persist before dispatch: PostgreSQL ledger + transactional outbox
             |
             v
Logical specialist agents -> scoped tool/provider gateway
             |                       |
             v                       v
Evidence/schema validation     Real browser/platform/site/model APIs
             |                       |
             +---- receipt + external-state verification
                                  |
                                  v
                     Verified / partial / blocked result
                                  |
                                  v
                   CEO report + gated scoped learning

All services -> OpenTelemetry traces/metrics/logs + security audit sink
             -> independent heartbeat monitor -> System Guardian
             -> incident evidence / approved safe runbook / human handoff
```

A provider receipt does not prove public success. External state must be verified where the requested outcome requires it.

## 3. Frozen service boundary

Keep exactly these seven UCOS service domains. Provider and hosting mappings are environment configuration, not permission to create additional agent microservices.

| # | Service domain | Ownership |
|---|---|---|
| 1 | API Gateway / Control Plane | Authentication, tenant/workspace/brand scope, authorization, goal intake, service APIs, capability registry and policy decision point |
| 2 | Content Service | Content records/versions, briefs, approvals, metadata and public content APIs |
| 3 | User / Identity Service | Users, memberships, roles, platform connections and account ownership |
| 4 | Analytics Service | Outcomes, funnels, attribution, reporting and metric normalization |
| 5 | Monetization Service | Product records, affiliate programs/links, campaign metadata and revenue attribution |
| 6 | AI Worker Service (Celery or equivalent) | Bounded asynchronous logical-agent jobs, worker pools, timeouts, retries and checkpoints |
| 7 | Scheduler Service | Scheduled goals, event triggers, periodic reconciliation and outbox relay; supervised Guardian control loop |

Shared platform services: PostgreSQL is the canonical transactional workflow ledger; Redis may support ephemeral coordination/cache/rate limits but is never the only task-truth store; object storage holds generated assets and large evidence blobs; vector search, if enabled, is a retrieval index, not policy or transaction truth. Secrets remain in a secret store or restricted encrypted credential boundary.

## 4. CEO ownership and limits

**SIA owns:** goal interpretation and clarification; the outcome contract; plan and dependency graph; capability selection; conflict/evidence evaluation; approval requests and pause/resume/abort decisions; final verification/reporting; and decisions to propose scoped lessons.

**SIA does not own:** raw OAuth tokens or secret retrieval; unrestricted network/browser/SQL execution; granting itself permission or changing security policy; undocumented publication side effects; silent budget increases; infinite retries; arbitrary code execution; or sole monitoring of its own health. Those boundaries are enforced outside the model.

## 5. Goal and task contracts

Every accepted goal persists at minimum:

- `goal_id`, tenant/workspace/brand IDs, requester and request timestamp.
- User intent, structured objective, inputs and approved source scope.
- Allowed platforms and selected `platform_connection_id` values (never raw tokens).
- Success conditions and machine-verifiable acceptance criteria.
- Risk tier, approval policy, deadline, attempt and spend/token/API budgets.
- Retention/privacy constraints, state, plan version, parent/child relationships and concurrency version.

Each task additionally declares `task_id`, goal and dependency IDs, required capability, assigned agent/version, instruction, schema-versioned input/output, accepted evidence types, timeout, idempotency key, scoped principal, permitted tools and stop conditions. A plan without measurable acceptance criteria cannot enter production execution.

### Planning rules

1. Decompose by outcomes and dependencies, not arbitrary layer numbers.
2. Parallelize only independent tasks; define explicit aggregation criteria at joins.
3. Select agents from declared capabilities and policy, never a free-form model-supplied agent name as authorization.
4. Pass references to large evidence payloads; do not copy secrets or unbounded histories into prompts.
5. Preserve provenance/confidence and distinguish facts, inference and unknowns.
6. Stop on missing permission/evidence, ambiguous irreversible side effects, budget breach or safety-gate failure.
7. Re-plan only with a persisted reason and a bounded plan-revision count.

## 6. Execution and learning

### Bounded execution loop

1. Accept goal; validate identity, scope, schema, budgets and objective.
2. Persist a versioned plan DAG and acceptance criteria.
3. Dispatch only authorized, dependency-ready work using a lease and idempotency key.
4. Execute a bounded specialist task and collect evidence, trace and cost.
5. Validate output schema and evidence against acceptance criteria.
6. Verify external state; reconcile uncertain side effects before any retry.
7. Persist truthful terminal state and report evidence, limitations and safe next action.
8. Submit candidate learning separately through a scope/privacy/evidence gate.

Each transition is durable before or transactionally coupled to dispatch using an outbox pattern or equivalent. Delivery is at-least-once; handlers must be idempotent. A queue does not guarantee exactly-once execution.

### Failure recovery

Classify failures as transient, rate-limited, auth-expired, invalid input, permission denial, safety blocker, permanent provider error, ambiguous side-effect outcome or internal defect. Retry only permitted classes with exponential backoff/jitter, provider Retry-After compliance, maximum attempts, overall deadline and total budget. Auth failures normally pause for reauthorization. Never retry a publish/payment/account change after an ambiguous timeout until external state is reconciled by stable operation key.

### Learning loop

A lesson candidate records source trace IDs, scope, observation window, confidence, privacy class, review state and rollback/version. It may affect future ranking only after validation against known outcomes or explicit owner approval. Per-brand/workspace/global knowledge is isolated; cross-scope aggregation is opt-in, privacy-reviewed and de-identified.

## 7. Goal/task state machine

Allowed lifecycle states include:

`ACCEPTED -> VALIDATING -> PLANNED -> READY -> RUNNING -> VERIFYING`

Additional explicit states: `NEEDS_CLARIFICATION`, `WAITING_APPROVAL`, `RETRY_WAIT`, `BLOCKED`, `LEARNING_PENDING`, `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED`, `CANCELLED`.

Terminal states are immutable except through audited correction/superseding events. Late results cannot overwrite a newer terminal state; they become auditable late-result events. Use compare-and-swap/version checks for concurrency.

## 8. Evidence and external verification

Each agent result carries goal/task/agent identity and version, scope, status, start/finish time, output schema version, typed output reference, evidence references, confidence/limitations, error code, trace/span IDs and cost/resource use. Evidence records source type, canonical URL/provider reference, retrieval timestamp, observed status, relevant content hash, verification procedure/version, scope and retention class.

Publishing invariants:
- Reserve a unique operation and idempotency key before the provider call.
- Record exact platform connection ID and content version.
- A provider receipt is reconciliation evidence, not proof of public visibility.
- If receipt exists but public state is not verified, use `PUBLISHED_NOT_PUBLIC` and reconcile; do not blindly republish.
- Terminal outcomes distinguish `VERIFIED_PUBLIC`, `PUBLISHED_NOT_PUBLIC`, `FAILED_VERIFICATION`, blocked and unknown.
- Retry ambiguous provider timeouts only after checking provider state or a supported idempotent endpoint.

## 9. Identity, permission and tool gateway

Identity hierarchy: `tenant -> workspace -> brand -> platform connection/account`. The connection ID identifies the target; it does not itself grant permission. On every call the gateway checks current membership, consent, OAuth scopes, connection status, allowed operations, risk, budget and task expiry.

Each tool manifest declares name/version, input/output JSON schema, capability, permission class, network egress allowlist, timeout, rate limit, idempotency behavior, sensitivity and safe failure behavior. High-risk tools require a separate policy decision or human approval. Browser execution uses isolated, account-bound sessions; cookies and session storage are never returned to the model. CAPTCHA/2FA/consent challenges require the authorized human where applicable; bypass is prohibited.

Retrieved web pages, reviews, emails, PDFs, browser contents and agent output are untrusted data, never system instructions. Validate URLs/redirects/egress, content types, size, MIME signatures and output schema. Retrieved content cannot choose credentials, expand scope, change policy or issue privileged calls.

## 10. Minimum durable data model

`goal`, `goal_plan`, `agent_task`, `agent_run`, `agent_result`, `evidence`, `approval_request`, `tool_invocation`, `publish_operation`, `outbox_event`, `learning_candidate`, `incident`, `incident_event`, `audit_event`.

PostgreSQL owns transactional state. Enforce foreign keys, unique idempotency keys, optimistic version columns, tenant-aware access, migrations, backup and restore tests. Use a non-owner runtime DB role where row-level security is enabled; RLS complements but does not replace application authorization. Redis is not authoritative for terminal task state. Credential ciphertext belongs only in a restricted credential boundary with key rotation and audited decryption.

## 11. CEO/operator experience

The designed target UI (not a claim of a deployed console) contains:
- **Goal Workbench:** workspace/brand, goal history, outcome composer, scope, targets, deadline, budget, acceptance criteria and approval policy; a CEO plan DAG with capabilities, risks and missing prerequisites.
- **Live Run Explorer:** goal -> task -> agent run -> tool call -> evidence -> verification, with state, duration, retries, ownership, source links and correlated traces.
- **Approval Inbox:** exact action/payload hash/version, target connection, risk, evidence, approver and expiry.
- **Incident/Guardian view:** severity, blast radius, timeline, trace waterfall, redacted logs, hypotheses, approved actions and recovery verification.
- Every live display uses actual API/database data, a visible freshness timestamp and source. Synthetic sample metrics must never appear as production data.

## 12. Monitoring, security and reliability

Collect correlated traces, metrics, structured logs, audit events and heartbeats. Monitor API latency/errors, queue age/leases/retries, DB connectivity/query latency/pool saturation, outbox/DLQ lag, scheduler drift, browser readiness, provider rate limits, agent handoffs/model errors/cost, publish receipts vs public visibility, credential/scope/prompt-injection alerts, backup/restore and capacity. An independent monitor detects missing Guardian/collector heartbeat.

Secrets, authorization headers, cookies, private messages and sensitive payloads are redacted before telemetry/persistence. Audit events are separated from debug logs and protected against casual modification. Guardian/model failure degrades to deterministic alerts, not silence. No architecture promises literal 100% uptime; service-level values are targets until measured from live evidence.

## 13. Freeze contract and change control

Frozen interfaces: seven service domains; tenant/workspace/brand/connection identity hierarchy; agent/task/result/evidence schemas; goal/task states; PostgreSQL/outbox durability; scoped gateway and approval policy; idempotent side-effect reconciliation; Guardian telemetry/incident contracts; and production evidence rules.

A change requires an Architecture Decision Record (ADR) with rationale, threat/operational impact, migration/backward-compatibility plan, tests, rollback and explicit version decision. No parallel architecture or silent interface drift. Implementation details may evolve only inside these contracts.

## 14. Implementation and production gates

- **A — Spec:** both canonical UAOM v1.0 documents are merged; schemas and ownership reviewed.
- **B — Persistence:** real PostgreSQL migrations and durable goal/task/result/outbox/incident records; no in-memory substitute on the production path.
- **C — Contracts:** schema validation, registry, scope checks, idempotency and tests.
- **D — Integrations:** real planner/model/provider gateway, browser, data/review APIs, platform connectors and credential broker; capability health reflects real readiness.
- **E — Observability/security:** trace/metric/log correlation, secret redaction, independent Guardian heartbeat, alerts/runbooks, authorization and threat tests.
- **F — End-to-end:** real test workspace/account; goal -> research -> content/media -> gates -> approved publishing -> public verification -> analytics, plus failure injection and restart recovery.
- **G — Production certificate:** green CI on the exact commit, identified deployment, live endpoint checks, DB/migration evidence, account authorization, external public-result verification where applicable, security/observability evidence and rollback proof.

### Acceptance checklist

- [ ] Only this UAOM v1.0 is the canonical top-level architecture.
- [ ] Exactly seven service domains; no per-agent service proliferation.
- [ ] All 29 logical agent roles and the CEO have explicit contracts.
- [ ] All production tasks are scoped, bounded, persisted and idempotent.
- [ ] Real integrations are distinguished from configured-but-unverified adapters.
- [ ] Provider receipts are reconciled against external state.
- [ ] No mocks, fabricated metrics or false success in production paths.
- [ ] Security, observability, recovery and independent Guardian checks pass.
- [ ] Certification evidence is tied to the exact deployed commit.

**Freeze statement:** UAOM v1.0 is the sole approved target architecture. This document is a specification, not a production certificate.
