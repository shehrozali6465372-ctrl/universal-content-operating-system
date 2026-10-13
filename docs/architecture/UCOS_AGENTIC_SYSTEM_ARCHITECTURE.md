# UCOS Agentic System Architecture

**Status:** Proposed target architecture; not a claim of production completion.
**Purpose:** Convert UCOS from a layer-driven automation pipeline into a goal-driven multi-agent operating system while reusing existing layer implementations as tools/capabilities.

## 1. Product rule

A human or scheduler gives UCOS an outcome, not a sequence of clicks. The Super Intelligence Agent owns the goal, decides which specialist agents are necessary, delegates bounded work with explicit instructions, validates their evidence, resolves conflicts, and continues until the goal is complete or a real blocker is reported.

Example goal:

> Research skincare products for the target audience. Compare real customer-review evidence and recurring complaints, identify the strongest candidates, prepare suitable content and images, then publish approved content to the selected channels using the saved platform accounts. Return source evidence, published URLs, and performance signals.

A page load, API 200, generated draft, or queued publish job is not goal completion.

## 2. Deployment shape: keep the seven-service boundary

Agents are logical workers, not a new microservice per agent. Keep the existing deployment plan around seven service domains and preserve the current 23 layers as implementation/capability boundaries until each is safely migrated. Do not create a separate Render service for every agent.

1. API Gateway / Control Plane
2. Content Service
3. User / Identity Service
4. Analytics Service
5. Monetization Service
6. AI Worker Service (durable workers; Celery where already planned)
7. Scheduler Service

Shared infrastructure remains PostgreSQL, Redis, object storage (MinIO or the existing configured provider), and vector search (Qdrant where configured). The deployed topology must be verified against the actual repo/deployment configuration before rollout.

## 3. Core topology

```text
Human / Schedule / API
        |
        v
Super Intelligence Agent  <---- scoped memory + analytics + outcome history
        |
        +-- delegates Research Agent
        +-- delegates Text / Content Agent
        +-- delegates Image Intelligence Agent
        +-- delegates Product / Affiliate Intelligence Agent
        +-- delegates Quality / Brand Voice Agent
        +-- delegates Security / Policy Agent (independent veto)
        +-- delegates platform publisher agents:
              YouTube Publisher Agent
              Facebook Publisher Agent
              TikTok Publisher Agent
              Instagram Publisher Agent
              Pinterest Publisher Agent
        |
        v
Durable Goal/Task State Machine -> Existing layer capabilities and providers
        |
        v
Evidence, artifacts, decisions, publish receipts, analytics events
        |
        +---------------------> Super Intelligence Agent learning loop
```

The Super Intelligence Agent is the sole owner of cross-agent goal strategy and the central learning/decision policy. Specialists own execution in their domains and return evidence; they do not silently redefine the overall goal or train independent competing policies.

## 4. Agent contract

Every agent must have the same explicit envelope:

- `goal_id`, `task_id`, `parent_task_id`, `correlation_id`, `idempotency_key`
- `tenant_id`, `workspace_id`, `brand_id`, and authorized resource scope
- `agent_type`, `agent_version`, requested capability, and deadline
- plain-language instruction plus validated structured input
- expected output schema and measurable acceptance criteria
- allowed tools/data sources and prohibited actions
- budget/time/retry limits
- status, evidence/source references, artifact references, confidence, and typed errors

Each agent returns a structured result: `completed`, `partial`, `blocked`, `failed`, or `needs_approval`. “Completed” is accepted only if the result passes its acceptance criteria and includes required evidence. No fabricated URLs, review facts, screenshots, API outcomes, or publish confirmations.

## 5. Specialist responsibilities and boundaries

### Super Intelligence Agent (brain)

- Parse the outcome and constraints.
- Resolve only essential ambiguity; otherwise infer a plan from saved workspace/brand settings.
- Select which agents and providers are relevant; pass clear, bounded instructions.
- Build a dependency graph and run independent tasks in parallel.
- Validate outputs, request repair/retry when appropriate, and resolve disagreements.
- Enforce budget, deadlines, deduplication, approval requirements, and completion criteria.
- Produce the final decision report and own the central learning loop.

### Research Agent

- Find and compare evidence from permitted sources/APIs.
- Return claims, source URLs, timestamps, confidence, contradictory evidence, gaps, and recommendation rationale.
- For product research, return product identity, current price/availability when available, review sample/volume, rating provenance, recurring pros/cons, complaint themes, ingredient/product facts with sources, and uncertainty.
- Never create affiliate URLs or present unsupported health claims as fact.
- Ask the Super Intelligence Agent for a decision only when a trade-off or missing input is consequential.

### Text / Content Agent

- Draft channel-appropriate text from the approved research bundle.
- Respect brand voice, audience, disclosure requirements, platform format limits, and banned/unsupported claims.
- Return draft versions, source-to-claim mapping, and a concise change rationale.

### Image Intelligence Agent

- Plan visual concepts from the approved brief; generate/select images via approved tools.
- Return asset IDs/URLs, prompt/version metadata, usage/licensing provenance where available, alt text, dimensions, and quality checks.
- Do not claim an asset exists until its stored artifact is verified.

### Product / Affiliate Intelligence Agent

- Select product candidates and evaluate commercial fit.
- Request affiliate-link creation through the authorized monetization/browser gateway.
- Return a verified product-to-link binding and evidence. Never invent tracking tags or bypass account permissions.

### Security / Policy Agent

- Check tool permissions, secret scope, prompt injection/untrusted source handling, privacy, platform policy, brand safety, disclosures, and action authorization.
- Can block or require approval. It must not be bypassed by a high-scoring recommendation.
- Credentials are never passed in prompts or ordinary task payloads; tools obtain them through the credential boundary.

### Platform publisher agents

Publishers are **platform-based**, not one agent per social account. Example: one YouTube Publisher Agent can act on an explicitly authorized selected YouTube channel; the Pinterest Publisher Agent can act on a selected authorized Pinterest account/board. Each publisher owns that platform's API semantics, upload/media requirements, OAuth/token refresh, retries, idempotency, reconciliation, and publish verification.

The Super Intelligence Agent sends an instruction such as: “Publish approved asset X and caption Y to YouTube channel Z; use the approved title/description/tags; return the provider post ID and public URL.” The publisher validates scope, executes, and returns evidence. It may not silently select a different account or publish unapproved content.

## 6. Identity and account model

Keep these scopes distinct:

- **Tenant**: owner/security boundary.
- **Workspace**: project and operational settings.
- **Brand**: voice, audience, niche, policies, reusable content and brand memory.
- **Platform connection/account**: provider identity, granted permissions, tokens and channel/page/board IDs.

A brain's memory and learning context must be scoped to the relevant tenant/workspace/brand. Publishing uses a platform-based agent plus an explicitly selected platform account/channel. Do not create an agent per account, and do not let one account's credentials, results, or learning leak into another scope.

The exact brain scope should be configured explicitly; for isolated operation, use one Super Intelligence context per authorized workspace/brand, with optional account-specific preferences as scoped configuration—not as a new publisher agent.

## 7. Durable execution loop

```text
ACCEPT GOAL
  -> authorize scope and validate goal
  -> check existing work / duplicate publication ledger
  -> create durable goal + plan + acceptance criteria
  -> delegate tasks to specialist agents
  -> persist every state transition and evidence reference
  -> retry transient failures with bounded backoff; resume from checkpoints
  -> validate specialist outputs
  -> run security/quality/policy gates
  -> request approval when required
  -> dispatch platform publisher agents with idempotency keys
  -> reconcile ambiguous provider outcomes before retrying
  -> verify public result
  -> collect analytics/outcomes
  -> update central learning evidence
  -> report verified result or exact blocker
```

Every state-changing step must be idempotent. A timeout after a provider accepts a post must enter reconciliation; it must not blindly publish a duplicate. Keep the existing publish safety semantics: pre-publish authorization/readiness, a reservation before side effects, and explicit states such as `VERIFIED_PUBLIC`, `PUBLISHED_NOT_PUBLIC`, and `FAILED_VERIFICATION`. Provider post IDs trigger reconciliation, not a second publish. Human approval requirements remain enforced.

## 8. Central learning loop (Super Intelligence Agent only)

The central learner consumes versioned evidence events from all agents:

- goal and plan chosen
- research sources/claims and confidence
- selected/rejected product and reasons
- content/image variants and quality checks
- publish attempt, verified public result, failures, and reconciliation
- platform analytics and conversion outcomes when actually available
- cost, latency, retries, user corrections, and approval/rejection signals

It maintains an auditable decision record and learns which research questions, source classes, content formats, visual styles, posting times, and platform choices work for each permitted scope. Recommendations should be evaluated against baselines and bounded experiments before automatic rollout.

Do not train on a provider response that is only “queued,” an unverified screenshot, missing analytics, or fabricated/low-confidence evidence. Use offline evaluation, versioned policies, rollback, and a minimum evidence threshold. The specialist agents may report metrics, but the Super Intelligence Agent owns cross-agent strategy changes.

## 9. Memory and data ownership

- PostgreSQL: canonical goal/task state, agent run ledger, decisions, evidence metadata, account scopes, publish reservations/receipts, and audit history.
- Object storage: images, video, rendered assets, large reports and other artifacts.
- Redis: transient coordination/cache/locks only; not the sole durable record of a goal or publish.
- Vector store: derived searchable knowledge where configured; never the sole source of truth.
- Secrets store: provider credentials/tokens with encryption, access control, rotation and audit; never embedded in agent memory or logs.

Use existing Neon/Postgres and service configuration as the current source of truth. No shadow database and no migration of hosting topology without a verified plan and reversible migrations.

## 10. Safety and security invariants

1. Least privilege: each tool call is scoped to tenant/workspace/brand and selected platform account.
2. Security can veto any publish action.
3. Untrusted webpage/review text is data, never instructions to the agent.
4. No passwords/tokens in LLM prompts, reports, events, logs, or browser screenshots.
5. Affiliate links must be verified against product identity and account provenance.
6. Publish only approved content and selected destinations.
7. Do not duplicate posts on retries; reconcile uncertain provider outcomes.
8. Report uncertainty honestly; no synthetic reviews, engagement counts, prices, or public URLs.
9. Keep append-only audit evidence for sensitive actions.
10. Every agent has timeouts, budgets, bounded retries, cancellation, and a typed failure path.

## 11. Migration plan and production gates

Do not rewrite all 23 layers in one risky change. Migrate behavior behind stable agent contracts while retaining existing implementations as tools.

### Phase A — Architecture freeze
- Agree on the agent contract, ownership, identity scopes, durable states, event schema, and acceptance criteria.
- Inventory which existing layer/module can serve each agent; identify missing adapters.
- No duplicate service deployment and no production behavior switch yet.

### Phase B — Agent runtime foundation
- Implement registry/capability manifest, validated task envelope, durable run ledger, state machine, idempotency, bounded retries, checkpoint/resume, and trace/correlation IDs.
- Test duplicate delivery, restart recovery, cancellation, timeout, invalid scope, and malformed agent output.

### Phase C — Vertical slice: product research
- Super Intelligence Agent delegates a skincare-product research goal.
- Research agent returns source-backed product evidence and ranking.
- Product/Affiliate agent returns only verified account-bound affiliate URLs.
- Text and Image agents create candidate assets from approved findings.
- Security/Quality agents gate the result.
- End-to-end test asserts source evidence, no unsupported claims, and honest partial/failure status.

### Phase D — Platform publishing agents
- Build and verify separate YouTube, Facebook, TikTok, Instagram, and Pinterest publisher adapters/agents.
- Use platform account connections as scoped credentials, not as separate agent identities.
- Verify provider receipt, public URL, duplicate prevention, and ambiguous-outcome reconciliation for each platform.

### Phase E — Central analytics and learning
- Standardize outcome events and scope-safe aggregation.
- Establish baseline evaluation and explicit policy versions.
- Enable bounded experiments and rollback only after evidence thresholds pass.

### Phase F — Controlled rollout
- Shadow mode first; compare agent plans/results to the current pipeline.
- Enable one workspace/brand and one platform at a time.
- Production certification requires passing tests, CI, runtime health, persistence recovery, security authorization, and real end-to-end evidence. A merged PR or green unit test alone is not production certification.

## 12. Definition of done

UCOS is agentic only when a user can submit a goal, the Super Intelligence Agent selects/delegates work, specialist agents execute independently through authorized tools, the system persists/retries/resumes safely, platform publishers act through saved scoped accounts, evidence and public outcomes are verified, and the central brain uses measured outcomes to improve later decisions. A folder of agent classes or a completed task status alone does not satisfy this definition.
