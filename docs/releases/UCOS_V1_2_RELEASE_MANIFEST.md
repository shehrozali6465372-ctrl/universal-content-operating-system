# UCOS v1.2 Release Manifest

## Release target

**UCOS v1.2 — production certification release train**

The repository's historical application version remains authoritative unless changed by an explicit release decision. This manifest identifies the v1.2 production-certification target without creating a second runtime architecture.

## Architecture authority

- Canonical architecture: 23 layers.
- Cross-layer dependency direction is enforced by the architecture-conformance workflow.
- Layer ownership and production boundaries are not replaced by this manifest.

## Production-critical path

L01 Core → L02 Research → L03 Intelligence → L04 Writing → L05 Image → L06 Quality → L07 Publishing → L08 Analytics → L09 Learning, coordinated by L14, persisted by L13, secured by L17, with runtime support from L11/L15 and model/provider routing through L12.

## Production certification evidence

- CI green on the exact release commit.
- Cross-layer architecture conformance green on the exact release commit.
- Real PostgreSQL persistence gate green.
- L10 monetization tests green.
- L14 control-plane and security tests green.
- L15 async-runtime tests green.
- Real DeepSeek provider smoke green.
- Real Meta/System User integration green where publishing is enabled.
- Real autonomous E2E green for the configured production account.
- Live production health and authentication fail-closed checks green.
- Provider readiness records optional providers as CONFIGURED or explicit UNCONFIGURED_OPTIONAL; it must never fabricate availability.
- Certification gate records the exact commit.

## Optional provider policy

SerpAPI, affiliate-search, and GA4 credentials are optional integrations unless a release configuration explicitly promotes them to required status. Missing optional credentials are represented as UNCONFIGURED_OPTIONAL; they are not silently replaced by fake success.

## Certification rule

No PRODUCTION_CERTIFICATE=PASS marker is valid until the canonical production activation gate observes the required evidence for the same commit.

## Current release state

**CERTIFIED — v1.2 production certification gate passed on the exact release commit.**


## Certification evidence binding

The canonical `UCOS Production Certificate Gate` is the authoritative final certificate. Its successful run requires the exact same commit to pass CI, architecture conformance, live production health/authentication checks, real-provider autonomous E2E, and provider readiness. The certified commit is the repository revision containing this manifest state.
