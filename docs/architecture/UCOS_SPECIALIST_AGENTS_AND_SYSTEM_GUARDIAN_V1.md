# UCOS Specialist Agents and System Guardian - UAOM v1.0

Freeze ID: UAOM-Workers-Guardian-v1.0  
Status: Design-frozen target architecture; not a production certificate.  
Companion: UCOS CEO Agent Architecture - UAOM v1.0  
Revision: 14 October 2026

## 1. One workforce under one CEO

The Super Intelligence Agent is the single goal owner, plan coordinator and central learning decision-maker. Specialists return bounded results with provenance, confidence, limitations and cost. The registry selects capabilities; the policy/tool gateway enforces permissions; PostgreSQL records durable truth; System Guardian independently observes runtime. Both files define one model, not parallel agent systems.

Agents are logical capabilities, not one microservice per role. Preserve 23 UCOS layers and seven service domains. Platform publishing agents serve multiple saved connections, but every run names the exact authorized connection/account/board/channel/page.

## 2. Frozen roster - 29 logical agents

| # | Role | Responsibility | Required output/evidence |
|---:|---|---|---|
| 1 | Goal & Planning | Draft task graph, dependencies, constraints and acceptance criteria | Versioned plan, assumptions |
| 2 | Research | Niche, market, source and competitor research | URLs, retrieval times, claims mapped to sources |
| 3 | Product Research | Discover/compare products for audience and use case | Product references, comparison, review evidence and confidence |
| 4 | Affiliate Marketing | Validate eligibility and destination/tracking link | Real destination, validation evidence and limitations |
| 5 | Browsing | Use authorized browser gateway for search/navigation/session-bound tasks | Page-ready evidence, URLs, sanitized screenshot/error refs |
| 6 | Writing | Long-form article/review/guide/outline | Content version and claim/source mapping |
| 7 | Text & Copywriting | Hooks, captions, headlines, short-form variants | Platform-specific copy and format checks |
| 8 | Image Intelligence | Analyze visual brief/assets/brand fit | Asset analysis, specs, licensing flags |
| 9 | Image Generation | Generate original visuals through authorized real provider | Provider job, prompt version, asset hash/URI, safety result |
| 10 | SEO | Search intent, keywords, metadata, internal links | Metadata and validation; no ranking guarantee |
| 11 | Security | Task authorization, prompt injection, tool access and data scope | Allow/deny/review, rule IDs and findings |
| 12 | Quality & Fact-Check | Claims, contradictions, originality and acceptance criteria | Claim matrix, issue list, pass/block evidence |
| 13 | Brand Voice | Apply versioned brand guidance | Guideline version, edits and deviations |
| 14 | Duplicate Detection | Detect repeated topics/text/assets/published content in permitted scope | Method/version, references, threshold |
| 15 | Content Strategy | Editorial priorities, niche coverage, calendar | Recommendation, rationale and KPI hypotheses |
| 16 | Pinterest Publishing | Publish to selected authorized Pinterest connection/board | Connection/board, idempotency key, receipt, public check |
| 17 | TikTok Publishing | Supported publish flow to selected authorized connection | Receipt, visibility and public URL when available |
| 18 | Instagram Publishing | Publish to selected authorized connection | Media status, receipt and verification |
| 19 | Facebook Publishing | Publish to selected authorized Page/account | Page ID, receipt and public check |
| 20 | YouTube Publishing | Upload/publish to selected authorized channel | Channel ID, privacy state, receipt, URL and visibility |
| 21 | Website & WordPress | Manage authorized website articles/pages/media | Site scope, content revision, receipt and external check |
| 22 | Scheduler | Trigger scheduled goals and reconciliations idempotently | Schedule version, due time, trigger key |
| 23 | Analytics | Normalize reach/click/engagement/conversion/revenue | Values, source, time window and completeness |
| 24 | Learning & Memory | Prepare scoped/provenanced lesson candidates for CEO | Lesson, traces, confidence, privacy status, rollback |
| 25 | Cost & Budget | Meter model/provider/tool spend and enforce ceilings | Actual/estimated spend, source, remaining budget |
| 26 | Workflow Monitoring & Recovery | Task failure classification, checkpointing and safe retry/resume | Error class, checkpoint, attempts and verification |
| 27 | Compliance | Platform rules, disclosure, consent, licensing and policy checks | Rule version, pass/block, evidence |
| 28 | Ad Intelligence | Research ad creatives/offers/trends and authorized campaign metrics | Source-backed angles, CTR/CPC/CPA/ROAS with source/time window |
| 29 | System Guardian / Live Observability | Correlate runtime telemetry, detect incidents, preserve evidence, alert, use approved containment | Incident severity/ID, trace links, timeline, redacted evidence, action and recovery proof |

Role boundaries: Agent 26 focuses on individual task execution/retry. Agent 29 focuses on cross-service health, trace correlation and incident evidence. Agent 11 evaluates action authorization/safety. CEO chooses the next business step and central learning policy. Guardian does not get unrestricted shell, SQL, credential or deployment permission.

## 3. Manifest and routing contract

Every production agent manifest declares stable ID/version, capabilities, input/output schema versions, required identity scope, allowed tools, egress allowlist, risk class, runtime/attempt/budget limits, side-effect class, required evidence, health probe, owner and rollback/version. Missing adapter, unhealthy provider, unknown schema, wrong scope, or ambiguous duplicate capability must fail closed; no mock adapter may be marked production-ready.

Each task result carries goal/task/agent/version/scope identity, status, typed output reference, evidence links, confidence/limitations, timestamps, cost, error class, attempt and trace IDs. The registry rejects missing/unhealthy capabilities, wrong platform, scope mismatch and ambiguous duplicate registration. Use the smallest sufficient agent set; only independent tasks run in parallel. Publisher tasks require exact selected connection and supported permissions, never a fallback to another account.

## 4. Example workflow: product research to public content

1. CEO validates goal, workspace/brand, region, target connections, budgets and approval policy, then persists plan.
2. Research/Product Research gather candidates and source-backed review evidence with URLs and retrieval timestamps.
3. Affiliate agent validates real program/link evidence; unavailable proof becomes unknown/blocked, never an invented link.
4. Writing/Text create content variants; Image Intelligence defines visual needs; Image Generation records real provider job/result IDs.
5. Fact-Check, Brand Voice, Duplicate Detection, Security, Compliance and SEO apply independent evidence-backed gates.
6. CEO requests approval for exact content/media versions and target connection when required. Material payload change invalidates prior approval.
7. Publisher reserves an idempotent operation and calls the real provider through the scoped credential gateway.
8. Reconcile receipt against public state. Ambiguous outcomes are not blindly republished.
9. Analytics reports source-backed metrics for a named time window. CEO reports real URLs, receipts, limits, spend and metrics only where available.
10. Learning agent proposes scoped candidates; CEO applies evidence/privacy gate.

## 5. Always-on System Guardian

Guardian is a continuously scheduled observability/security agent, independently supervised. “Always-on” is a target operating model, not a claim of literal 100% uptime. Host/provider/network failure and sleeping tiers can interrupt a process; external probes detect Guardian/collector silence. Deterministic health rules must continue when model inference is unavailable.

Service/agent/database/queue/provider signals feed OpenTelemetry traces, metrics, structured logs, audit events and heartbeats. Collector redacts data before export. Deterministic rules check freshness, liveness, API errors/latency, queue age, retries, database/outbox/scheduler health and provider state. Guardian correlates traces/logs/metrics/deploy/policy versions, ranks cause hypotheses with confidence and contrary evidence, opens incident, preserves a sanitized evidence bundle, alerts owner and selects only a pre-approved runbook or approval request. Then it independently verifies recovery.

Signals include service and worker heartbeats/restarts; API latency/errors; queue age/expired leases/retries/DLQ; PostgreSQL connections/errors/schema/migration drift; outbox and scheduler lag; browser navigation/blank render/screenshot freshness; model/tool schema failures and budgets; provider throttles/OAuth revocation; provider receipts vs public visibility; unauthorized tool calls, unexpected egress, secret-scan hits, backup freshness and available capacity.

## 6. Trace chain and incident bundle

Each goal run carries trace/span/parent IDs, goal/task/agent-run IDs, attempts, service/deploy version, agent/capability version, opaque scope identifiers, platform connection ID only where necessary, policy version, tool/provider version, operation reference, queue wait, duration, cost and error class.

Never log API keys, OAuth tokens, cookies, session state, passwords, private messages or full private page contents. OpenTelemetry baggage may be propagated downstream and must contain only low-sensitivity allowlisted fields [2]. Follow semantic conventions and avoid unbounded high-cardinality metric labels [3].

Incident record includes ID/time/severity/detector version; affected services/goals; ordered timeline; trace and failing spans; related logs/metric window; sanitized error/deploy/policy/provider context; task attempt and state; evidence-backed cause hypotheses plus confidence/disconfirming evidence; remediation identity/action/approval/verification; closure proof and retention. Access is role-scoped, audited and secret-scrubbed before export.

## 7. Example: browser URL changes but viewport is blank

This is a diagnostic scenario, not a claim of a live incident. Record requested URL, navigation response, page-ready markers, screenshot timestamp, visible-content check, process status and sanitized errors. If URL changes but content acceptance fails, emit a navigation-unverified event. Guardian correlates browser process status, screenshot freshness, timing, redirects, errors and related worker spans. It labels hypotheses with confidence rather than guessing a root cause from a blank image.

Only a reviewed safe runbook may wait/refresh once or restart an isolated disposable worker if no side effect is in flight. Never bypass CAPTCHA/2FA, submit forms, purchase or publish during diagnosis. Verify page content and acceptance criteria; otherwise block/escalate with trace evidence instead of looping forever.

## 8. Incident severity and remediation

| Level | Example | Safe automation | Escalation |
|---|---|---|---|
| SEV-0 Critical | Secret leak, cross-tenant access, destructive action underway | Configured kill switch/session revocation through authorized control; preserve audit | Immediate high-priority human incident commander |
| SEV-1 High | Duplicate publish, widespread outage, DB divergence | Pause affected side-effect workers, circuit-break connector, quarantine queue | Page operator; no destructive DB change without approval |
| SEV-2 Medium | Error/latency burst, retry storm, stale analytics | Drain unhealthy worker, bounded retry, open incident | Notify owner; escalate on timeout/threshold |
| SEV-3 Low | Isolated non-critical task failure | Capture trace, mark blocked/failed, create work item | Dashboard queue |

Runbooks are versioned with preconditions, permissions, blast radius, timeout, idempotency key, max attempts, rollback and recovery proof. Guardian cannot run arbitrary shell/SQL, expand its own permissions, change IAM or deploy code on a model hypothesis. High-impact remediation needs approval unless an explicit audited policy authorizes a narrow safe action.

## 9. UI target: actual data only

These are UI specifications, not fabricated screenshots/live metrics. Every live panel displays source and freshness with LIVE, STALE, DEGRADED or NO DATA based on actual observation time.

- System Command Center: environment/version, telemetry freshness, active goals, queue age, incidents, service/agent topology and trace-linked trends.
- Incident Workbench: timeline, trace waterfall, logs, metric window, deploy/policy diff, dependencies, evidence-backed hypotheses, sanitized evidence, action/approval history and verified closure.
- Agent Registry: role/capabilities, manifest/version, schemas, owner, health, outcomes, p50/p95 duration, spend and allowed tools.
- Trace Explorer: search by goal/task/agent/connection/incident/time and follow goal -> agent -> tool -> provider -> verification with sanitized evidence and costs.
- Alerts Console: threshold/rule version, source signal, owner, runbook, retention/redaction and approval. Test alerts are explicitly labelled synthetic and never reported as real incidents.

## 10. Durable records, alerts and tests

Persist manifest/version, capability, agent run/attempt, heartbeat, trace link, signal snapshot, alert rule/event, incident/event, evidence bundle, runbook, remediation action/verification, notification and audit event. PostgreSQL owns transaction-critical records, transactional outbox owns durable dispatch, telemetry backend handles high-volume signals and object storage holds large sanitized evidence. A consumer checkpoint advances only after durable processing.

Minimum alerts: Guardian/collector silence; API SLO breach; stale workers/queue; DB errors/schema drift; outbox/reconciliation lag; duplicate publish; auth/scope failures; unauthorized tool/egress/secret finding; retry or budget exhaustion; telemetry freshness loss.

Fault tests: kill worker after provider accepts publish; stop collector/Guardian and verify external alert; expire OAuth; inject hostile web content; fail PostgreSQL mid-transition; duplicate/delay outbox; leave browser page blank after URL change; create provider receipt without public visibility; trigger error burst and confirm secret redaction; exercise rate limits, malformed schemas, provider outage and budget ceilings.

Production evidence includes workflow URLs, report hashes, applied migration, deployed commit/service version, live probes, sanitized real trace, authorized test workspace, provider receipt/public URL where applicable, recovery drill and operator sign-off. No local mock or conceptual UI may substitute.

## Research references
1. OWASP Agentic Applications 2026: https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/
2. OpenTelemetry Baggage and security: https://opentelemetry.io/docs/concepts/signals/baggage/
3. OpenTelemetry Signals and semantic conventions: https://opentelemetry.io/docs/concepts/signals/ and https://opentelemetry.io/docs/concepts/semantic-conventions/
4. OWASP ASVS V16 Security Logging: https://github.com/OWASP/ASVS/blob/master/5.0/en/0x25-V16-Security-Logging-and-Error-Handling.md
5. NIST AI RMF Core: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
6. OpenTelemetry Collector: https://opentelemetry.io/docs/collector/
7. PostgreSQL Write-Ahead Log: https://www.postgresql.org/docs/current/runtime-config-wal.html
8. OpenAI Agents SDK Tracing: https://openai.github.io/openai-agents-python/tracing/

Freeze label: UAOM-Workers-Guardian-v1.0
