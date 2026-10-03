# UCOS v1.2 Production Architecture Cross-Check

## Purpose

This document is the release-gate architecture contract for UCOS v1.2. It does not replace the 23-layer architecture; it verifies that implementation, CI, providers, persistence, security, publishing, analytics, and deployment remain aligned with it.

## Canonical architecture

1. Core System
2. Research & Scraping
3. AI Intelligence
4. Content Writing
5. Image Intelligence
6. Quality & Safety
7. Publishing
8. Analytics
9. Self-Learning
10. Monetization
11. Async Runtime
12. AI Foundation / Model Router
13. Persistence
14. Enterprise Integration / Control Plane
15. Async Runtime
16. Database Engineering
17. Security
18. Monitoring
19. Analytics Engine
20. Image Pipeline
21. Deployment
22. Documentation
23. Website Manager

## Canonical dependency direction

request → research/intelligence → account/platform/niche decision → strategy → verified evidence → content → media → quality/policy → repetition → real platform adapter → publication result → analytics → account-local learning.

Cross-layer access must use the owning layer's public contract. No layer may bypass persistence, security, publishing policy, provider abstraction, or account isolation.

## Production invariants

- Layer 13 PostgreSQL is the production source of truth.
- Legacy SQLite repetition/persistence paths remain fail-closed in production.
- Layer 14 is server-authoritative for publish mode, account selection, platform policy, and execution gates.
- Layer 17 owns credential resolution/security boundaries; credentials are never hard-coded into business-layer code.
- Layer 5 image generation uses the provider abstraction and must persist real image bytes before downstream quality/publishing use.
- Layer 6 quality/policy gates precede publication.
- Layer 7 records only real adapter publication results; no fabricated IDs or success.
- Analytics and learning remain account-local and must not leak state across accounts.
- External providers may report UNKNOWN/PENDING/UNCONFIGURED when evidence is unavailable; readiness must not be simulated.
- CI certification is commit-specific evidence, not a source-code claim.

## v1.2 certification gate

A v1.2 production certificate is valid only when all required architecture gates are green on the same release commit:

1. Python compilation/import integrity.
2. Layer 1 security/static audit.
3. Layer 5 provider abstraction + real image smoke.
4. Layer 10 monetization production tests and lint.
5. Layer 13 real PostgreSQL production gate.
6. Layer 14 control-plane production and security regression.
7. Layer 15 async-runtime production tests and lint.
8. Layer 17 credential/security boundary verification.
9. Layer 7 real publishing evidence where configured.
10. Real Meta/System User integration evidence where configured.
11. Real DeepSeek provider smoke where configured.
12. Production provider readiness for every provider marked required by the release configuration.
13. Full integration/test suite.
14. Deployment/health/security evidence.
15. Release evidence tied to the exact commit.

## Certification state

**CERTIFIED — v1.2 production certification gate passed on exact release commit `11280d0a13bda55043c563323ab66c4609cd226d`.**

Evidence on that exact commit:
- CI: run `37088842822` — success.
- Cross-layer architecture conformance: run `37088842932` — success.
- Layer 10: run `37088842852` — success.
- Layer 14: run `37088842898` — success.
- Layer 15: run `37088842837` — success.
- DeepSeek smoke: run `37088842909` — success.
- Meta/System User: run `37088842851` — success.
- Provider readiness: run `37088842881` — success.
- Real autonomous E2E: run `37088842827` — success.
- Canonical production certificate gate: run `37088842896` — success, including live health/authentication fail-closed checks.

This certificate is evidence-bound to the exact commit above. A subsequent architecture/runtime change invalidates this exact-commit certificate until the certification gate passes again. Missing optional providers remain explicitly classified as optional; no external availability is fabricated.
