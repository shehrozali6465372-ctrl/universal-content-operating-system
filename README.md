# 🤖 Universal AI Content Operating System

**v6.0.0** — An account-isolated AI content creation, quality, monetization, publishing, analytics, and learning control plane.

## Frozen canonical architecture — UAOM v1.0

**Architecture freeze: 14 October 2026.** UCOS has one approved top-level architecture, defined by exactly these two canonical specifications:

1. [CEO Agent Architecture](docs/architecture/UCOS_CEO_AGENT_ARCHITECTURE_V1.md) — SIA/CEO control plane, goal/task contracts, seven service domains, persistence, security and production gates.
2. [Specialist Agents + System Guardian](docs/architecture/UCOS_SPECIALIST_AGENTS_AND_SYSTEM_GUARDIAN_V1.md) — the 29 logical roles, capability contracts, routing, continuous diagnostics and incident response.

These are two views of the **same** architecture, not alternatives. No other top-level architecture is approved. The existing 23 UCOS layers remain logical implementation/capability boundaries; they are not 23 deployed services. Deployments stay inside these seven service domains:

1. API Gateway / Control Plane
2. Content Service
3. User / Identity Service
4. Analytics Service
5. Monetization Service
6. AI Worker Service (Celery or equivalent)
7. Scheduler Service

PostgreSQL is the canonical durable workflow ledger. Redis is not authoritative task truth. All tool/provider calls are scoped and policy-gated. Every production completion claim requires real evidence; mocks and architecture documents cannot certify runtime readiness.

**Truth status:** this freeze defines the target and acceptance gates. It does not claim all components are deployed, connected or production-certified. Production status requires live evidence tied to the exact deployed commit.

## Account isolation

Accounts are dynamic; the system is not limited to a fixed number of accounts. Every registered account receives its own provisioned workspace and account-local stores for memory, content history, analytics, learning, and publishing/repetition state.

Account-local data is never used as another account's history or learning state. Unsafe account IDs are mapped to collision-resistant workspace names. Credentials are resolved only from the account's configured credential reference.

## Target platform families

The production control plane currently provides adapters and policy snapshots for:

- Facebook
- Instagram
- Pinterest
- YouTube
- TikTok

Other legacy/plugin adapters may exist in the repository, but production capability is reported only by the adapter and credentials actually configured.

## Autonomous execution flow

```text
request
  ↓
research / intelligence
  ↓
account + platform + niche decision
  ↓
topic / content-type strategy
  ↓
verified product / affiliate evidence (when configured)
  ↓
content generation
  ↓
media planning / runtime media
  ↓
quality + technical policy gates
  ↓
account-local repetition / template gate
  ↓
real platform adapter
  ↓
real publication result or explicit pending/unconfigured state
  ↓
real analytics when available
  ↓
account-local learning
  ↓
future account-specific decisions
```

The system does **not** fabricate post IDs, publishing success, analytics, conversions, sales, prices, commissions, or affiliate products. Unavailable external evidence is represented as `UNKNOWN` or an explicit unconfigured/pending state.

## Quick Start

```bash
# Boot the system
python main.py

# Check status
python main.py --status

# Generate content through the control plane
python main.py --generate "artificial intelligence trends"

# Generate for an explicit account
python main.py --generate "artificial intelligence trends" --account-id my-account
```

A production publish requires a registered account, an account-specific credential reference, a configured platform adapter, and any media/public-URL requirements imposed by that adapter.

## API keys and credentials

AI providers and platform credentials are configured through environment variables or account credential references. Never commit secrets to the repository.

Example AI configuration:

```bash
export GEMINI_API_KEY_1="..."
export GEMINI_API_KEY_2="..."
```

Account credentials can be supplied through the configured credential reference mechanism. Platform publishing is blocked when the account's required credentials are unavailable.

## API security

The API gateway defaults to loopback. When exposed on a non-loopback host, `UCOS_API_TOKEN` is required and requests must use a Bearer token.

## Testing

The repository contains **10,000+ tests** across the full test surface. Production certification is only claimed when the exact production commit has a recorded green CI run and the required integration/security evidence is present. A source-level test count is not certification evidence.

```bash
# Full CI test scope
python -m pytest tests/ layers/layer01_core/tests/ layers/layer02_research/tests/ -q --tb=short

# Lint
ruff check layers/ --select E,F,W --ignore E501,E402
```

## Runtime status

```bash
python main.py --status
```

The status command reports the current architectural layer count and Python-file inventory from the checked-out repository rather than relying on hard-coded historical counts.
