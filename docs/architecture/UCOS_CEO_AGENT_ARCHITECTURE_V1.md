# UCOS CEO Agent Architecture - UAOM v1.0

Freeze ID: UAOM-CEO-v1.0  
Status: Design-frozen target architecture; not a production certificate.  
Companion: UCOS Specialist Agents and System Guardian - UAOM v1.0  
Revision: 14 October 2026

## 1. One model, two views

UCOS Agentic Operating Model (UAOM) has one CEO/control plane and one specialist workforce/operations plane. These are complementary views, not competing architectures. The Super Intelligence Agent (SIA) is the single accountable goal owner, planner, delegate coordinator, evidence judge and central learning decision-maker. Specialists perform bounded work. Deterministic gateways enforce permissions and side-effect safety. PostgreSQL records durable workflow truth. System Guardian independently observes operations and assembles incident evidence.

Existing 23 UCOS layers remain logical capability boundaries. Keep the seven-service deployment boundary; a logical agent is not a dedicated microservice by default.

## 2. Normative invariants

1. Outcome-first goals: users describe success; CEO derives the task graph.
2. Evidence-first completion: model text, a draft, HTTP 200 or a queued job is not proof of goal completion.
3. Durable state: goals, tasks, attempts, approvals, external receipts, evidence, learning candidates and incidents survive worker restarts.
4. Least privilege: every task declares tenant/workspace/brand scope, selected platform connection IDs, allowed tools, limits and expiry.
5. Deterministic controls: authorization, budgets, schema validation, idempotency, deadlines, retry ceilings and terminal states are enforced outside the model.
6. Approval gates: high-impact or irreversible actions require approval tied to the exact payload hash and target scope when policy says so.
7. Reconciliation before retry: ambiguous provider outcomes are reconciled against external state before repeating side effects.
8. Evidence-gated learning: scoped, traceable observations may inform future plans after validation; untrusted web text never becomes system policy.
9. One CEO: specialists report findings and lesson candidates; they do not establish competing global strategies.
10. Honest reporting: unverified, blocked, stale and unknown outcomes stay explicit.

## 3. Seven-service deployment model

| Service boundary | UAOM responsibilities |
|---|---|
| API Gateway / Control Plane | Authentication, scope resolution, policy decisions, goal intake and routing |
| Content Service | Content objects, versions, briefs, approvals and public content APIs |
| User / Identity Service | Memberships, roles, tenant/workspace/brand structure and platform connections |
| Analytics Service | Source-backed outcomes, attribution windows and normalized metrics |
| Monetization Service | Product records, affiliate links/program metadata, campaigns and revenue attribution |
| AI Worker Service | Bounded CEO and specialist tasks, model/tool calls, retries and checkpoints |
| Scheduler Service | Scheduled goals, reconciliation jobs, periodic checks and durable event relay |

Shared infrastructure: PostgreSQL is the source of durable workflow truth; Redis may support ephemeral cache/coordination/rate limits but is never the only final task ledger; object storage holds approved assets/evidence; optional vector search is a retrieval index, not policy or transaction authority; credentials remain behind a restricted secret/credential broker.

## 4. CEO boundaries

CEO owns goal interpretation, outcome contract, plan versions/dependencies, capability routing, evidence/conflict resolution, approval requests, pause/resume/abort, final verification, scoped learning decisions and the final report.

CEO does not get unrestricted SQL/network/browser access, raw tokens/cookies, authority to grant itself access, permission to silently expand budgets, or the only monitoring channel watching its health. CEO may request an action; an external policy gateway authorizes it.

## 5. Goal and task contract

A durable goal declares goal ID, requester, tenant/workspace/brand IDs, objective, input references, exact platform connection IDs, acceptance criteria, risk/approval class, deadline, cost/token/API budget, privacy/retention class, current state, plan version and optimistic concurrency version.

Each task declares task/goal IDs, dependencies, required capability, assigned agent version, bounded instructions, schema-versioned inputs/outputs, accepted evidence types, timeout, maximum attempts, permitted tools, scoped principal, idempotency key and stop conditions. Tasks must be independently resumable. Plans without measurable acceptance criteria cannot enter production execution.

CEO plan rules:
- Parallelize only independent tasks; joins define aggregation criteria.
- Route by reviewed/versioned capability manifest and scope, never a free-form model-provided agent name.
- Separate retrieved content from trusted instructions/policy.
- Use evidence references instead of copying sensitive or very large payloads into prompts.
- Re-plan only with a persisted reason and bounded plan revisions.
- Stop on missing authorization, ambiguous side-effect state, evidence gaps, budget breach or security failure.

## 6. Execution loops and state

Plan loop: intake -> authenticate -> resolve scope -> classify risk -> plan and persist -> dispatch authorized tasks -> validate result schema/evidence -> verify external outcome -> persist terminal state -> learning gate -> report verified results only.

Recovery loop: classify transient, rate-limited, expired-auth, invalid-input, permission-denied, safety-blocked, permanent-provider, ambiguous-side-effect or internal-defect outcomes. Retry only allowed classes with bounded attempts, exponential backoff and jitter, provider Retry-After, deadlines, budgets and checkpoints. Expired authorization blocks for reauthorization. Permission denial never triggers privilege escalation.

Learning loop: compare expected and observed results. Candidate lessons store source traces, scope, time window, confidence, privacy classification, evaluation and rollback/version. Knowledge remains scoped by brand/workspace unless reviewed policy explicitly allows de-identified cross-scope aggregation.

Goal states: ACCEPTED, VALIDATING, NEEDS_CLARIFICATION, PLANNED, WAITING_APPROVAL, READY, RUNNING, RETRY_WAIT, BLOCKED, VERIFYING, LEARNING_PENDING, COMPLETED, COMPLETED_WITH_WARNINGS, FAILED and CANCELLED. Every transition is durable; terminal states change only through an audited correction event. A late worker result cannot overwrite a newer state. At-least-once delivery means handlers must be idempotent.

## 7. Evidence and publishing

Every result carries goal/task/agent/version/scope identity, typed output reference, status, evidence links, confidence/limitations, timestamps, cost, error class and trace IDs. Evidence stores provenance, canonical source/provider reference, retrieval time, verification procedure/version, integrity hash where useful, scope and retention class. Credentials/cookies must never appear in prompts, traces, logs or incident bundles.

Before publish, reserve a unique idempotent operation and record the exact platform connection and content version. Provider receipt alone does not prove public visibility. Publishing states include VERIFIED_PUBLIC, PUBLISHED_NOT_PUBLIC and FAILED_VERIFICATION. An ambiguous provider timeout requires reconciliation before retry.

## 8. Identity and tool gateway

Identity hierarchy is tenant -> workspace -> brand -> platform connection/account. Account IDs do not themselves grant permission. Gateway checks membership, consent, OAuth scopes, connection health, operation, risk, budget, expiry and idempotency on every call. Browser profiles remain isolated; raw cookies never enter model context. CAPTCHA/2FA and consent flows remain with an authorized human when required.

Each tool manifest declares version, input/output schema, capabilities, permission class, egress allowlist, timeout, rate limit, side-effect semantics, sensitivity and safe failure. Retrieved pages, reviews, documents and tool output are untrusted data and cannot amend system instructions, credentials or permissions.

## 9. Durable data entities

Goal, versioned goal plan, agent task, agent run/attempt, typed result, evidence, approval request, tool invocation, publish operation, transactional outbox event, learning candidate, incident/event and audit event. PostgreSQL owns transaction-critical truth with foreign keys, idempotency uniqueness, migrations, version checks, indexes, tenant-aware authorization and restore tests. Row-level security is defense in depth, not a replacement for application authorization. Use a runtime DB role that cannot bypass configured RLS. Redis is not authoritative state.

## 10. CEO UI target

This defines the target UI, not a deployed console or live screenshot.

- Goal Workbench: workspace/brand and connection selectors, outcome composer, deadlines, budget, acceptance criteria, plan graph, risks and missing prerequisites. Run is disabled if required identity/scope/connection/authorization/budget is invalid.
- Live Run Explorer: goal -> task -> agent -> tool -> evidence -> external verification graph; status, duration, retries, trace links and redacted errors. Distinguish planned/running/verified/blocked/failed/unknown/late-result.
- Approval Center: exact action and content/media version, target connection, payload hash, requested scope, risk, cost, expiry and approval evidence.
- Learning Review: candidate lesson, source traces, scope, validation/privacy status and rollback.
- Cost & Policy Console: spend by goal/agent/provider/workspace, quotas, connections, policy version and stop switches.
- Live panels show source and data freshness. No sample metrics may be presented as live production values.

## 11. Guardian, telemetry and security

CEO is not the only monitor of itself. The System Guardian and independent probes observe API, workers, queue, database, outbox, scheduler, browser gateway, connectors and publish reconciliation. An external host/uptime monitor detects Guardian/collector silence.

Propagate trace IDs, goal/task/run IDs, service/version, scoped opaque account identifiers where needed, policy version and operation reference. Do not put secrets or sensitive payloads in OpenTelemetry baggage; baggage may propagate downstream [3]. Use traces for causality, metrics for rates/latency/saturation and structured logs for discrete events/errors [2][3]. Trace model/tool/handoff/guardrail/approval/database/provider/verification spans [4].

Security baseline: OWASP Agentic Top 10 2026 [1], NIST AI RMF Govern/Map/Measure/Manage [5], protected audit logging [6], workload identity, scoped secret broker, default-deny egress, source redaction before export, reviewed manifests/dependencies, prompt-injection isolation, bounded loops/budgets, circuit breakers, tenant isolation, backups and incident response.

## 12. Proposed SLOs and certification gates

Proposed starting targets only, not achieved metrics:
- Control-plane availability 99.5% monthly, measured after deployment.
- Accepted goal transitions committed or explicitly failed.
- Critical event-to-alert within 60 seconds on a healthy telemetry path.
- Guardian silence detection within 2 minutes by an independent monitor.
- Zero duplicate publishing in defined fault-injection tests.
- At least 99% trace linkage among sampled goal runs.
- Approved RPO/RTO and a passed restore drill.

A sleeping hosting tier or lack of independent monitoring prevents a continuous-availability promise. SLOs are not achieved until measured over an explicit production window.

Production certification requires real PostgreSQL models/migrations and outbox; planner/worker and authorized provider adapters; schema/scope/fault/secret-redaction tests; independent Guardian heartbeat; end-to-end goal -> research -> gates -> approved publish -> public verification -> analytics; plus CI links, deployed commit/service version, live probes, migration evidence, incident drill and operator sign-off. CI green alone is insufficient.

## 13. Freeze and change control

This file and its companion workforce/Guardian spec together freeze UAOM v1.0. Frozen contracts: seven-service boundary, identity hierarchy, task/result/evidence contract, goal state machine, tool gateway, publish idempotency/reconciliation, trace context and Guardian incident contract. Any change requires an Architecture Decision Record covering compatibility/migration, data/permission impact, failure modes, observability, rollback and tests.

## Research references
1. OWASP Agentic Applications 2026: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
2. OpenTelemetry Signals: https://opentelemetry.io/docs/concepts/signals/
3. OpenTelemetry Baggage and security: https://opentelemetry.io/docs/concepts/signals/baggage/
4. OpenAI Agents SDK Tracing: https://openai.github.io/openai-agents-python/tracing/
5. NIST AI RMF Core: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
6. OWASP ASVS V16: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md
7. PostgreSQL Write-Ahead Log: https://www.postgresql.org/docs/current/runtime-config-wal.html

Freeze label: UAOM-CEO-v1.0
