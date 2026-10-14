# UCOS Specialist Agents + System Guardian — UAOM v1.0

**Status:** FROZEN CANONICAL ARCHITECTURE  
**Revision:** 14 October 2026  
**Freeze ID:** `UAOM-Workers-Guardian-v1.0`  
**Production status:** NOT CERTIFIED BY THIS SPECIFICATION

This is the workforce, security and live-operations view of [UCOS CEO Agent Architecture](UCOS_CEO_AGENT_ARCHITECTURE_V1.md). The two files define one model, not competing architectures. The Super Intelligence Agent (SIA) owns the goal and learning decisions; specialists perform bounded tasks; deterministic gateways enforce permissions; PostgreSQL records durable truth; the independent System Guardian observes operations and builds incident evidence.

## 1. Workforce rules

- One CEO, one canonical plan and memory policy. Specialists return evidence, results, confidence, limitations and cost; they do not independently rewrite organization-wide strategy.
- Route by declared capability, schema, health, scope, risk, budget and provider readiness, not by display name.
- Agents are logical workers; reuse the existing 23 UCOS layers as implementation capabilities within the seven approved service domains. Never deploy one service per agent.
- A platform agent may serve many authorized connections, but every run is pinned to an explicitly selected connection/account.
- Web pages, reviews, PDFs, emails, browser contents and other agent outputs are untrusted evidence, not system commands.
- Evidence beats assertion. A model saying “done” is not completion proof.
- Deterministic code enforces tool permissions, spend, retries, deadlines, approvals, egress and stop rules.
- Missing provider, credentials, scopes or evidence produces BLOCKED/UNKNOWN, never a fabricated success. No mock adapter may be production-ready.

## 2. Canonical roster — 29 logical roles

| # | Agent role | Primary responsibility | Required output/evidence |
|---:|---|---|---|
| 1 | Goal & Planning Agent | Convert user intent into dependencies, constraints, acceptance criteria and bounded plan proposal | Versioned plan DAG, assumptions, risk/dependency list |
| 2 | Research Agent | Market/niche/topic research, facts, sources and competitor landscape | Source-backed findings, canonical URLs, timestamps, claim-to-source map |
| 3 | Product Research Agent | Discover/compare products for an audience/use case | Candidates, attributes, comparison matrix, review evidence and confidence |
| 4 | Affiliate Marketing Agent | Validate program eligibility, actual affiliate link and tracking | Verified destination, program evidence, link test/time and limitations; never fabricate links |
| 5 | Browsing Agent | Operate approved browser gateway for scoped browsing/session workflows | Navigation/page-ready evidence, source URLs, sanitized screenshots/errors |
| 6 | Writing Agent | Long-form articles, reviews, guides and outlines from evidence | Content version, claim/source links, brief compliance and quality status |
| 7 | Text & Copywriting Agent | Short-form hooks, captions, titles, descriptions and variants | Platform-specific copy, character/format checks and provenance |
| 8 | Image Intelligence Agent | Analyze visual brief, assets, layout, brand fit and image requirements | Asset analysis/specs, alt text, rights/provenance flags |
| 9 | Image Generation Agent | Create original assets through authorized provider | Provider job/result IDs, prompt version, asset URI/hash and safety result |
| 10 | SEO Agent | Search intent, headings, metadata, schema candidates and internal linking | Keyword/intent rationale, metadata and validation; no ranking guarantee |
| 11 | Security Agent | Authorization, data scope, prompt injection, tool access and secret exposure | Allow/deny/review decision, policy IDs, risk findings and evidence |
| 12 | Quality & Fact-Check Agent | Claims, product details, originality, consistency and acceptance criteria | Claim matrix, duplicate/similarity results, issues and pass/block rationale |
| 13 | Brand Voice Agent | Apply workspace/brand guidelines | Guideline version, adherence checks, edits and deviations |
| 14 | Duplicate Detection Agent | Detect repeated topics/text/assets and prior publication within permitted scope | Method/version, candidate references, threshold and disposition |
| 15 | Content Strategy Agent | Niche coverage, editorial priorities and calendar | Recommendation, rationale, schedule candidates and KPI hypotheses |
| 16 | Pinterest Publishing Agent | Publish to selected authorized Pinterest connection/board | Exact connection/board, idempotency key, provider receipt, canonical URL and public check |
| 17 | TikTok Publishing Agent | Publish via supported API/account flow | Exact connection, receipt, visibility status and verified URL when available |
| 18 | Instagram Publishing Agent | Publish to selected authorized Instagram connection under API/account rules | Request/receipt, media state, exact connection and public verification |
| 19 | Facebook Publishing Agent | Publish to authorized Page/account with supported permissions | Target Page ID, receipt, status and public verification |
| 20 | YouTube Publishing Agent | Upload/publish to authorized channel using available API permissions | Channel ID, upload receipt, privacy state, URL and visibility verification |
| 21 | Website & WordPress Agent | Manage authorized site content, media and publication | Tenant/site scope, content revision, response receipt and external verification |
| 22 | Scheduler Agent | Trigger due jobs/reconciliation and prevent overlapping schedules | Schedule version, due time, trigger event and idempotent job key |
| 23 | Analytics Agent | Normalize reach, clicks, engagement, conversions and revenue | Metrics with source/time window/attribution definition and completeness flags |
| 24 | Learning & Memory Agent | Prepare scoped, provenance-backed lessons and assess historical evidence | Lesson candidate, source traces, scope, confidence, privacy status and rollback reference |
| 25 | Cost & Budget Agent | Meter provider/model/tool costs and enforce ceilings | Estimated/actual cost, remaining budget, source and threshold alerts |
| 26 | Workflow Monitoring & Recovery Agent | Classify task failures, retry eligibility, checkpoints and resumptions | Failure class, retry decision, checkpoint, attempt count and final verification |
| 27 | Compliance Agent | Platform rules, disclosure, consent, licensing and policy requirements | Checklist version, pass/block, affected claims/assets and evidence |
| 28 | Ad Intelligence Agent | Research ad creatives/offers, audience signals, competitor patterns and authorized metrics | Source-backed angles/test proposal and CTR/CPC/CPA/ROAS with source/time window; no invented metrics |
| 29 | System Guardian / Live Observability Agent | Correlate telemetry, detect anomalies, preserve evidence, notify owners and contain safely | Incident/severity, trace/log/metric links, timeline, redacted diagnostics, actions and recovery proof |

### Responsibility boundaries

- **CEO/SIA:** business decision, plan, approvals, result integration and learning acceptance.
- **Security Agent #11:** whether an action is authorized and safe.
- **Workflow Monitoring & Recovery #26:** task-level execution, checkpoints, retries and resume.
- **System Guardian #29:** cross-service health, suspicious patterns, correlated incident evidence and bounded containment.
- **Tool/provider gateway:** actual authorization and execution enforcement.

These responsibilities cooperate; none substitutes for another.

## 3. Standard agent manifest

Every production-capable registry entry must declare a versioned contract before receiving production tasks:

```yaml
agent_id: research.product
agent_version: 1.0.0
role: product_research
capabilities:
  - product.discover
  - product.compare
input_schema: product-research-input.v1
output_schema: product-research-result.v1
required_scope: [tenant_id, workspace_id, brand_id]
allowed_tools: [approved_search, product_catalog_read, review_evidence_read]
network_egress: [declared domains only]
risk_class: medium
max_runtime_seconds: 300
max_attempts: 3
budget_class: standard
required_evidence: [source_reference, retrieved_at, claim_source_mapping]
side_effects: none
healthcheck: agent.health.v1
```

This is a contract example, not a claim those particular adapters are installed. Production entries must resolve to real implementations; missing required providers/adapters fail health checks. Unknown schema versions are rejected, never guessed. Every result includes task/scope identity, agent/version, status, typed output reference, evidence references, confidence/limitations, timestamps, attempt, cost/resources, error code, trace/span IDs and output schema version.

## 4. Capability routing and handoffs

The CEO/registry checks schema compatibility, risk, connection support, health, scope, budget, allowed operations, provider readiness and evidence quality. If multiple candidates are equally valid, require an explicit policy/ranking decision; never choose by nondeterministic list order.

1. Select the smallest sufficient agent set.
2. Parallelize only independent work; serialize side effects per connection/content key.
3. Gather evidence before claim-dependent writing or publishing.
4. Place security, quality, brand and compliance gates at the required joins.
5. A publisher must receive an exact authorized platform connection/account/board/channel/page.
6. Missing connection/scope returns BLOCKED with reauthorization action; never fall back to another person's account or an unapproved browser session.
7. Missing official metrics remain UNKNOWN/unavailable.
8. Persist originating goal/task, parent run, capability, input/output contract and policy decision for each handoff.

## 5. Canonical end-to-end publishing flow

1. User supplies outcome, niche, audience, region and explicit authorized publishing target(s).
2. CEO validates scope, deadline/spend budget, connection and approval class; persists a versioned plan.
3. Research/Product Research produce source-backed candidates and comparison evidence.
4. Affiliate Marketing verifies eligibility and the actual destination/link, or reports the missing proof.
5. Writing and Copywriting draft content; Image Intelligence specifies assets; Image Generation creates assets only through real authorized providers.
6. Quality/Fact-Check, Brand Voice, Duplicate Detection, Security, Compliance and SEO run their defined gates.
7. CEO aggregates evidence. Approval is tied to exact content/media version, target connection and payload hash; a changed payload invalidates the old approval.
8. Publisher reserves idempotent operation and calls the scoped provider gateway.
9. Verify external state/public URL. Ambiguous timeout requires reconciliation first; `PUBLISHED_NOT_PUBLIC` is held, never blindly republished.
10. Analytics reports only source-backed metrics over a declared window.
11. Learning proposes scoped lessons; CEO accepts/rejects/limits them through an evidence/privacy gate.

## 6. System Guardian — continuous operational design

The Guardian is a continuously scheduled and independently supervised observability/security agent. “Always-on” describes the target operating design; external infrastructure and provider availability prevent any honest promise of literal 100% uptime. An external monitor detects a stale/missing Guardian heartbeat.

### Telemetry path

```text
Services / workers / adapters
  -> OpenTelemetry SDKs: traces, metrics, structured logs, audit events, heartbeats
  -> collector: redaction, sampling, health checks
  -> telemetry backend + durable security-audit sink
  -> Guardian analysis loop
       1. freshness/heartbeat checks
       2. SLO/error-budget evaluation
       3. anomaly/correlation rules
       4. trace + log + metric pivots
       5. confidence-labeled cause hypotheses
       6. severity/blast-radius evaluation
       7. sanitized evidence bundle
       8. approved runbook or human approval
  -> safe containment OR incident page/human handoff
  -> verify recovery and close
```

Telemetry and deterministic health alerts must continue if Guardian model calls fail. Process heartbeat, queue age, HTTP availability, database reachability, error ratio, outbox lag, memory/disk and stale heartbeat rules are deterministic and independent of the model.

### Required signal families

- Service readiness/liveness, deploy/version ID, process/worker heartbeat and restart count.
- API latency/error rate, queue depth/oldest age, leases and retry rate.
- PostgreSQL connection/query latency/errors, migration/schema version, transaction failure and pool saturation.
- Outbox lag, dead-letter depth, scheduler drift, duplicate/idempotency conflicts and task-state inconsistencies.
- Browser navigation/page-ready timeouts, blank/stale render indicators, session health and provider rate limits.
- Agent handoff/model timeout, schema failures, tool denials and token/cost ceilings.
- Publishing receipt vs public visibility, verification lag, duplicate attempts and connection authorization failures.
- Secret/egress alerts, unexpected tool calls, scope mismatch, permission-denial patterns and prompt-injection indicators.
- Backup age/restore drills, capacity headroom and certificate expiry where exposed.

## 7. Live trace and root-cause evidence

Every goal execution has one end-to-end trace or linked trace group. Required correlation fields include `trace_id`, `span_id`, `parent_span_id`, `goal_id`, `task_id`, `agent_run_id`, `attempt`, service/deployment/environment/version, worker pool and capability/agent version. Scope IDs are access-controlled and must not leak secrets.

Every incident records first-detected time, severity, detector/rule version, affected services/goals, linked traces/logs/metrics, sanitized timeline, task attempts, safe input/output references, deployment/config changes, cause hypotheses with confidence, action approvals, recovery verification and closure. Preserve enough evidence to reproduce diagnosis without persisting credentials or unnecessary private content.

### Browser blank-viewport example

If URL changes but visible content is blank/stale: record navigation timing, response/timeout class, safe DOM/network-ready markers and screenshot timestamp; emit a navigation-unverified event when acceptance deadline expires; correlate browser process, page errors, worker latency and screenshot freshness; open an incident with confidence-ranked hypotheses rather than asserting an unsupported cause. A pre-approved runbook may perform one bounded refresh/wait or restart an isolated disposable worker if no external side effect is in flight. Re-check the actual page-ready criterion. If still unresolved, pause/escalate; never loop forever.

## 8. Severity and remediation boundaries

- **SEV-1:** active credential/data exposure, cross-tenant access, unauthorized irreversible side effect or critical production outage. Contain through pre-approved bounded action, page owner immediately and preserve evidence.
- **SEV-2:** major capability/service degraded, sustained errors/queue backlog or publishing verification failures. Notify owner, apply bounded safe runbook when pre-authorized, verify recovery.
- **SEV-3:** localized non-critical task/provider failure with workaround. Record and route to task recovery or service owner.
- **SEV-4:** informational drift, warning or low-impact anomaly. Aggregate and track.

Severity thresholds and paging targets are configuration-backed operational values; they must not be fabricated as measured SLAs. The Guardian is read-only by default except for dedicated incident/evidence APIs. A separate remediation gateway exposes reviewed runbooks only—no unrestricted shell, SQL or browser access. Every automatic action has preconditions, idempotency key, execution cap, audit link and post-action verification. If telemetry is unavailable, alert on its absence.

## 9. Dashboard and alerting

The Guardian/operator dashboard reads real telemetry and persisted incidents; it is not a source of synthetic live metrics. Each visualization supports time range, workspace filter, severity, source drill-down and trace-to-log pivot. Incident detail includes severity/blast radius, ordered timeline, trace waterfall, correlated redacted logs, deploy/config diff, dependency graph, cause hypotheses and approved actions.

Alert families include stale service/Guardian heartbeat; API error/latency budget; oldest queue task/lease expiry; DB reachability/pool/migration drift; outbox/DLQ lag; scheduler drift; provider authentication/rate limit; repeated schema/policy failures; publish receipt/public-state mismatch; credential/egress/prompt-injection events; backup/restore and capacity risk. Alert evaluation must remain operational when the LLM is unavailable.

## 10. Persistence and security safeguards

Persist incident and telemetry references with tenant/workspace/brand scope, retention class, integrity metadata and access audit. Large screenshots/documents live in controlled object storage and are referenced by opaque IDs with short-lived authorized access. Redact tokens, cookies, authorization headers, private messages and sensitive payloads before telemetry leaves a service. Separate security audit logs from debug logs and protect their integrity.

Retrieved content and Guardian-generated cause hypotheses are untrusted. Deterministic signals trigger known-safe actions; model correlation can enrich triage but cannot override authorization or hard safety rules. Guardian access is least-privilege and user-visible evidence remains scope-checked. Model failure, rate limits, prompt injection or telemetry loss degrade to deterministic alerts, not silence.

## 11. Test and certification contract

Required checks:
- Agent manifest/schema compatibility, capability routing, scope isolation and authorization denials.
- Bounded runtime/retry/budget, cancellation, lease expiry and idempotency under duplicate delivery.
- Prompt-injection/untrusted-data and secret-redaction tests.
- Real provider readiness and real non-publishing smoke tests before enabling any publish flow.
- Guardian signal correlation, missing-heartbeat alerts, incident evidence integrity and safe-runbook preconditions/caps.
- Fault injection for DB/queue/provider/model/collector failure, restart/recovery and late results.
- End-to-end flow on a real authorized test connection, with provider receipt and external-state verification.
- CI and live evidence tied to the exact deployed commit.

A unit test or architecture diagram alone does not certify a production agent. Mock providers may be used only in isolated unit tests and must never be presented as live certification evidence.

## 12. Freeze contract

The 29-role roster, responsibility boundaries, standard agent manifest, seven-service deployment boundary, routing/authorization rules, evidence contract, Guardian telemetry/incident model, safe-remediation limits and certification gates are frozen for UAOM v1.0.

Any change requires an ADR containing rationale, security/operational impact, migration and compatibility plan, tests, rollback and explicit version decision. Do not introduce a competing architecture, a second roster or a new per-agent service topology. Implementation may evolve only within the frozen contracts.

**Freeze statement:** This file and the companion CEO architecture are the only canonical architecture specifications for UCOS UAOM v1.0. This is a design freeze, not a claim that all 29 roles are implemented or production-certified.
