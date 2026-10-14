# UCOS 28-Worker Agent Architecture

## Operating rule

UCOS has **28 named worker agents**. A deterministic orchestrator dispatches typed jobs to the right worker; agents do not free-chat with each other. Each worker owns one responsibility and exposes a versioned, JSON-serializable input/output contract.

**Only AG01 is being implemented in this change.** AG02–AG28 are architecture assignments, not claims that their code already exists. Current implementation status is tracked in `manifest.json`.

## One end-to-end path

`Account + request → AG01 research → AG02–AG08 topic strategy → AG09 plan → AG10–AG14 content/media/quality → AG15 account choice → AG16 product evidence (when requested) → AG17 duplicate guard → AG18 schedule → AG19 publish → AG20 verify → AG21–AG23 learn → AG24–AG28 cross-cutting controls`.

The deterministic entry point is `agents.dispatcher.AgentDispatcher`. It dispatches only implemented workers, rejects planned workers, and refuses production dispatch until a worker is explicitly marked `production_ready` in `manifest.json`. The orchestrator may skip an agent when its responsibility is irrelevant, but it may not skip a required safety, account-isolation, publication, or verification gate.

## Layer retirement rule

Existing `layers/` code is the source material for the migration; it is **not safe to delete by directory name**. Several modules are cross-layer dependencies. For each agent, move only the code it owns, update callers, retain thin compatibility adapters while needed, run contract/regression tests, and record production evidence. Remove legacy layer code only after no production path imports it. This prevents a cosmetic folder rename from silently breaking the working system.

## Agent 01 contract

- Entry point: `agents.agent_01_research_discovery.ResearchDiscoveryAgent`.
- Requires a registered, enabled `account_id`; resolves platform and niche from that account.
- Checks known account-local UCOS execution history, de-duplicates candidates in a batch, collects attributable evidence, scores topics, verifies supplied claims, stores a plan and emits one JSON report.
- Writes production account state through the existing account-store facade, which uses L13 PostgreSQL/Neon in production; local JSON/SQLite is development/test only.
- Missing history, missing persistence, weak evidence, failed verification, or unknown status must hold/block the candidate. No publisher is called by AG01.
- `READY_FOR_WRITING_REVIEW` is a hand-off only; it is **not** publish authorization.
- Before production handoff, the account's UCOS history baseline must be verified. A present legacy SQLite store is imported into Neon without overwriting newer Neon rows; if the legacy store is missing or unreadable, AG01 holds. History coverage includes records synced to UCOS. Posts made outside UCOS need a verified import before they can be included in duplicate decisions. Live source providers must also be configured; an empty source registry returns `blocked_research_sources_unconfigured` rather than fake recommendations.

## Completion evidence

Do not mark an agent production-ready from imports or unit tests alone. Its gate needs unit/contract tests, cross-account isolation tests, the relevant CI run, real durable-store verification, and a live smoke test against configured dependencies. If production credentials/database access are unavailable, record that as an unresolved gate rather than claiming success.
