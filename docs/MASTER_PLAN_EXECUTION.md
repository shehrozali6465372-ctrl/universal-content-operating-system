# UCOS Master Plan — Execution Control

This document is an execution checkpoint for the Master Plan. It records what is verified in the repository and what is still gated by real external evidence.

## Verified baseline
- 23 architectural layers are present in the control-plane architecture.
- Production behavior is fail-closed when required external evidence or credentials are unavailable.
- Production intelligence must not use fabricated clicks, conversions, revenue, post IDs, prices, commissions, or synthetic provider results.
- PostgreSQL is the production persistence direction; SQLite test fixtures are not production evidence.
- Real integration boundaries exist for Search/SEO, affiliate data, GA4 analytics, and WordPress publishing.
- Hostinger referral data is represented as an integration-ready real-link boundary. Performance metrics remain unknown until observed from the authoritative Hostinger dashboard.
- CI certification is tied to an exact commit. A green historical run must not be represented as proof for a newer commit without matching evidence.

## Master Plan execution order

### Phase 0 — Architecture and contract baseline
Status: VERIFIED BASELINE

The architecture/control-plane hardening and 23-layer contract gates are already merged on main.

### Phase 1 — Build vs Integrate
Status: IN PROGRESS

For each capability, UCOS should prefer a mature provider/OSS boundary over a duplicate in-house implementation. Every production adapter must expose explicit configuration, health/error state, provenance, and fail-closed behavior.

### Phase 2 — Data Foundation
Status: IN PROGRESS

Required lineage:
source -> niche -> keyword -> content -> asset -> platform -> account -> publish -> click -> conversion -> revenue

Rules:
- Every observed external value must retain its source/provenance.
- Unknown values remain unknown.
- Test fixtures are never promoted to production intelligence.
- Account/platform/niche learning state must remain isolated.

### Phase 3 — Real Data Connectors
Status: READY FOR LIVE VERIFICATION

Connector families currently represented by production boundaries:
- Search/SEO
- Affiliate
- GA4
- WordPress
- platform publishing adapters already present in the control plane

Live activation requires real credentials/configuration plus provider-health and end-to-end evidence. Credential presence alone is not provider-health proof.

### Phase 4 — Intelligence
Status: NEXT ENGINEERING TARGET

The next implementation work should consume observed Phase 2/3 data rather than create parallel synthetic datasets. Opportunity, keyword, content, product, platform, and refresh decisions must preserve source and account scope.

### Phase 5 — Content Factory
Status: FOLLOWING PHASE

Content generation remains downstream of research/intelligence and upstream of quality/publishing gates.

### Phase 6–10
Status: SEQUENCED

Execution remains:
OSS execution -> publishing -> analytics/attribution -> learning -> permissioned autonomous agents.

## Production evidence states

A capability may only advance through these evidence states:
1. CI_VERIFIED
2. ARCHITECTURE_VERIFIED
3. INTEGRATION_READY
4. LIVE_PROVIDER_VERIFIED
5. LIVE_E2E_VERIFIED
6. PRODUCTION_DEPLOYMENT_VERIFIED

A source-code change is not automatically live-provider evidence.

## Immediate execution gates
1. Keep repository-to-architecture-registry synchronization deterministic.
2. Verify PostgreSQL/Redis/runtime deployment configuration on the target environment.
3. Activate real Search/SEO credentials and verify one observed response.
4. Activate one real affiliate source and verify one observed program/product record.
5. Activate GA4 and verify one observed analytics response.
6. Activate WordPress only after a real publish target and credentials are configured.
7. Verify one complete observed lineage without inventing missing metrics.
8. Feed only observed outcomes into learning.
9. Run exact-commit CI after each production-boundary change.

## Current repository truth

The latest main change is the Hostinger referral data-path correction. This branch starts from that main state and does not claim a new CI result until GitHub Actions provides evidence for the resulting commit.
