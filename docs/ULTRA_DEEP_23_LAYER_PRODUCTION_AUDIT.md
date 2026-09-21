# UCOS Ultra-Deep 23-Layer Production Audit

Audit target: `main` at commit `3f9411a5a0ccda9a06bfa3990f8c87d8db10bf4d`.

## Certification rule

UCOS is **not** production-certified merely because 10,132 tests pass. Production certification requires the real mutation path, fail-closed gates, account isolation, idempotency, reconciliation, dependency health, security tests, and exact-commit CI evidence.

## Critical verified defects

### L01 Core
- DatabaseManager still has a SQL identifier interpolation boundary. Values must be parameterized; identifiers must be allowlisted.
- BackupManager persists registry state separately from copied data; crash consistency/atomic commit is not demonstrated.
- Persistent memory/state must be account scoped.

### L02 Research
- `AudienceIntelManager.find_similar()` calls nonexistent `get_audiences()`; current API is `get_audience()`. This is a real runtime AttributeError.
- Audience persistence is optional/in-memory; restart can lose intelligence.
- Research claims need source/provenance IDs and retrieval timestamps.

### L03 Intelligence
- L3 must emit a typed intelligence bundle: keywords, entities, intent, audience fit, novelty, hook candidates, emotional angle, claims, evidence and confidence.
- Intelligence must be consumed by writing/quality/publishing, not stored as decorative metadata.
- Novelty must be account+niche+platform scoped.

### L04 Writing
- CTA lists are static and generic; they are not learned from account/platform performance.
- Writing-plan history currently returns an empty list.
- Production writing needs hypothesis → draft variants → evidence/quality → winner learning.

### L05 Image
- `ImageOrchestrator` defaults to `MockImageProvider`. A production path must never silently reach a mock provider.
- Generated assets need provider/job IDs, hashes, provenance and actual URLs.
- Accessibility/alt text should be grounded in the actual generated asset, not only the topic.

### L06 Quality
- Previous heuristic scoring accepted empty, short, refusal, placeholder and scam-like content.
- Hard gates have been added, but CI must prove them.
- Final publishing must be an AND gate: quality + safety + compliance + factuality + originality + platform policy + repetition + account identity.
- No weighted score may override a hard failure.
- Score scale must remain explicitly 0–1 at the analyzer boundary.

### L07 Publishing
- Double repetition reservation was fixed.
- Facebook attached-media JSON serialization and image `published=false` were hardened.
- Instagram containers now wait for `FINISHED`.
- Every external mutation still needs persistent idempotency + uncertain-result reconciliation.

### L08 Analytics
- Raw platform metrics cannot be blindly compared.
- Preserve raw payloads and normalized metrics.
- The system needs an attribution chain: impression → view/dwell → engagement → click → conversion → revenue.

### L09 Learning
- `SelfImprovementManager` only detects metric mistakes when `_thresholds` exists, but the attribute is never initialized. This silently disables one learning path.
- Learning must be account/platform/niche scoped.
- Automatic experiments require checkpoints, confidence thresholds and rollback.

### L10 Affiliate
Affiliate is a commerce decision engine, not merely URL insertion.

Required chain:
`intent → real catalog → eligibility → relevance → trust → commercial value → historical CTR/CVR → real affiliate URL → disclosure → click → conversion → revenue feedback`.

No catalog must mean no product; never manufacture a product or affiliate URL.

### L11 Integrations
Every provider needs real credential lifecycle, timeout, retry classification, idempotency, rate limits, response-schema validation and version pinning.

### L12 AI
Key selection/cooldown/rotation fixes are present. Production responses must carry model/provider/version, latency, usage and failure reason. Offline fallback must never be publishable.

### L13 Persistence
Production source of truth must be PostgreSQL. SQLite is development-only. Content, account, publication, analytics and learning rows need ownership and foreign keys.

### L14 Enterprise
HMAC replay/JSON fail-open issues were hardened. Remaining requirement: durable idempotency, inbox/outbox, correlation IDs and non-blocking request handling.

### L15 Async Runtime
Every task needs bounded retry, timeout, cancellation and dead-letter handling. Safety/validation failures must never be retried as transient failures.

### L16 Database
Require prepared values, allowlisted identifiers, explicit transactions, pool health, migration locks, indexes, query timeouts and recovery drills.

### L17 Security
Threat model must cover prompt injection, credential exfiltration, SSRF, path traversal, malicious media, webhook replay and unsafe tool calls. AI output is untrusted input.

### L18 Monitoring
Monitoring must identify account, platform, content, layer, error, external-mutation certainty and recovery action. Health must check dependencies, not only process liveness.

### L19 Analytics Engine
Forecasts require data windows/confidence. Recommendations must cite the underlying observations. Observed and projected revenue must be separate.

### L20 Image Pipeline
Real providers only; capability negotiation; provenance; deterministic validation; brand/style memory; content/image consistency gate.

### L21 Deployment
Docker API startup and HTTP healthcheck were hardened. Remaining requirements: immutable builds, SBOM, vulnerability scanning, secret injection, readiness/liveness separation, migration gate and rollback.

### L22 Documentation
Docs must describe actual supported interfaces and include incident, rollback and disaster-recovery runbooks.

### L23 Website Manager
Verified:
- AtoZ `request_id` is UUID-validated but is not an idempotency key.
- `context.publish=true` directly creates a published article.
- Pinterest accepts caller-supplied `image_path`; it must be confined to an approved asset root and validated as a regular image file.
- ProductMatcher uses simplistic hard-coded scoring.

## AtoZ required fix

Implement a durable inbox:
- key: request_id
- payload_hash
- account/site identity
- state
- result_ref
- created_at/updated_at

Same request ID + same hash → return original result.
Same request ID + different hash → reject replay/conflict.
Publishing requires an explicit policy authorization, not merely a caller boolean.

## Creative Mind architecture

The system should implement a **Creative Hypothesis Engine**, not random text generation:

Observe → diagnose → hypothesize → create variants → verify → publish → measure → learn.

Example diagnostic:
`views high + clicks low`
→ inspect hook/promise/CTA/product relevance/landing alignment
→ form competing hypotheses
→ controlled variant
→ measure CTR/CVR
→ record causal evidence
→ update account/platform memory.

Every hypothesis needs evidence and an exit reason.

## Human-feeling content

Model:
specific human situation + tension + credible observation + useful resolution + appropriate emotion + proof + natural voice + non-generic detail.

Never fabricate personal experience, customer testimony, statistics or product experience.

## Anti-repetition system

Three independent gates:
1. exact content hash
2. template/fingerprint similarity
3. semantic novelty

Plus account fatigue memory for recent:
topics, hooks, opening structures, CTAs, visual concepts, product angles, claims and reusable phrases.

The goal is genuine originality and audience value, not evasion of platform AI labeling.

## Affiliate intelligence

For every product record:
identity, merchant, current availability, price timestamp, commission, geography, affiliate URL, disclosure requirement, problem-fit, user intent, CTR/CVR and revenue.

The decision must answer: **why this exact product for this exact audience at this exact moment?**

If evidence is weak, do not insert the link.

## Multimodal studio

Creative brief → script → image/video plan → real provider → editing → music intelligence → voice → captions → quality → platform adapter.

Every asset requires provenance, rights status, provider/job ID, hash, dimensions and transcript/audio metadata.

Blender, image generation, editing, music and voice must be real providers/executors; capability flags alone are not acceptable.

## Voice agent

STT → intent/state → tool policy → retrieval → reasoning → response planning → TTS → interruption handling → audit.

Measure WER, latency, interruption recovery, pronunciation, naturalness, hallucination rate and task completion.

## Account isolation

Every persistent business record must carry:
`account_id + platform + external_account_id + niche`.

No global mutable publishing history, analytics cache, learning profile or credentials.

## Crash-resilience target

“Never crash” means no unhandled failure may corrupt state, duplicate an external mutation, leak another account's data or silently publish unsafe content.

Required: circuit breakers, bounded retries, durable queues, dead letters, idempotency, reconciliation workers, transactional outbox and readiness checks.

## Final production checklist

- [ ] all 23 layers have executable integration coverage
- [ ] no production mock provider is reachable
- [ ] all external mutations are idempotent
- [ ] all account data is isolated
- [ ] all hard safety/quality/compliance/fact/originality gates fail closed
- [ ] Meta/platform versions are consistent
- [ ] uncertain external mutations reconcile
- [ ] affiliate catalog is real
- [ ] analytics actually feeds learning
- [ ] learning is evidence-driven and reversible
- [ ] Docker readiness/dependencies verified
- [ ] security tests cover injection/SSRF/path traversal/replay
- [ ] disaster recovery exercised
- [ ] exact production commit has green CI
- [ ] actual UCOS orchestration path has a verified real Meta E2E

**Status:** architecture is substantially hardened, but this checklist is intentionally not marked complete until runtime evidence exists.
