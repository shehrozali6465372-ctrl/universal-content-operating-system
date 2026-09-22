# Production Activation Gate

This document is the operational gate between repository certification and live external-provider certification.

## Evidence states

- **CI_VERIFIED** — automated repository tests pass on a specific commit.
- **ARCHITECTURE_VERIFIED** — the 23-layer architecture contracts and registry inventories are synchronized.
- **INTEGRATION_READY** — real provider adapters exist and fail closed when credentials are absent.
- **LIVE_PROVIDER_VERIFIED** — a real provider was contacted successfully with production credentials.
- **LIVE_E2E_VERIFIED** — the requested production flow completed against real external systems and produced independently verifiable IDs/metrics.
- **PRODUCTION_DEPLOYMENT_VERIFIED** — the deployed runtime, secrets, persistence, monitoring, recovery and HTTPS boundaries were verified.

No state may be promoted to a stronger state without evidence from that state.

## Current baseline

Implementation source of truth: `production/master-plan-hardening`.

Latest repository certification baseline recorded for this activation cycle:
- Commit: `0f0c92bdf2bc815df3ec1f9bdf033d0613e44a20`
- CI: 10,162 passed, 87 warnings, 0 failures, 0 errors
- Architecture: 23/23 layers boot
- Real external credentials: not embedded in source and not claimed here.

## Live activation sequence

1. Configure production secrets outside source control.
2. Run the **Production Integration Activation Gate** workflow manually.
3. Confirm provider-by-provider live health:
   - Search/SEO
   - Affiliate
   - GA4
   - WordPress
   - Social/publishing accounts
4. Run one controlled real end-to-end post through the canonical UCOS pipeline.
5. Verify the external publication ID independently.
6. Verify analytics ingestion for the same account/content identity.
7. Verify observed click/conversion/revenue events when they actually occur.
8. Confirm learning consumes observed outcomes only.
9. Record evidence in the architecture registry.
10. Only then mark the corresponding provider or end-to-end path as LIVE.

## Failure isolation rule

A failed provider must stop its own activation gate and must not cause unrelated providers to be marked failed. Repairs are made at the affected integration boundary and followed by targeted regression plus the full certification suite.

## No-fake rule

Missing credentials, unavailable providers, absent analytics observations, or unverified revenue must remain explicit unavailable/unknown states. Tests must never manufacture production evidence to make a gate green.
