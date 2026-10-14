# UCOS 28-Worker Agent Architecture

## Operating rule

UCOS has **28 named worker agents**. A deterministic orchestrator dispatches typed jobs to the right worker; agents do not free-chat with each other. Each worker owns one responsibility and exposes a versioned, JSON-serializable input/output contract.

**Only AG01 is being implemented in this change.** AG02–AG28 are architecture assignments, not claims that their code already exists. Current implementation status is tracked in `manifest.json`.

## One end-to-end path

`Request → AG25 tenant/account checks + AG26 database readiness → AG01 discovery/history gate → AG02–AG05 research enrichment + AG06 fact verification + AG07 memory/dedup → AG08 scoring → AG09 plan → AG10–AG14 content/media/quality → AG15 account choice → AG16 product evidence (when requested) → AG17 publication repeat guard → AG18 schedule → AG19 publish → AG20 verify → AG21–AG23 learn → AG24–AG28 cross-cutting controls`.

The deterministic entry point is `agents.dispatcher.AgentDispatcher`. It dispatches only implemented workers, rejects planned workers, and refuses production dispatch until a worker is explicitly marked `production_ready` in `manifest.json`. The orchestrator may skip an agent when its responsibility is irrelevant, but it may not skip a required safety, account-isolation, publication, or verification gate.

## Layer retirement rule

Existing `layers/` code is the source material for the migration; it is **not safe to delete by directory name**. Several modules are cross-layer dependencies. For each agent, move only the code it owns, update callers, retain thin compatibility adapters while needed, run contract/regression tests, and record production evidence. Remove legacy layer code only after no production path imports it. This prevents a cosmetic folder rename from silently breaking the working system.

## Agent 01 contract

- Entry point: `agents.agent_01_research_discovery.ResearchDiscoveryAgent`.
- Requires a registered, enabled `account_id`; resolves platform and niche from that account.
- Checks known account-local UCOS execution history, removes duplicate candidates within a batch, gathers at least two independent source hosts for a candidate, persists the evidence pack, and emits a JSON handoff report.
- Writes production account state through the existing account-store facade, which uses L13 PostgreSQL/Neon in production; local JSON/SQLite is development/test only.
- With `TAVILY_API_KEY` configured, AG01 uses the documented Tavily `POST /search` API via a bounded, timeout-limited standard-library adapter; each evidence item must carry an HTTP(S) source URL and source hostname. If the key or provider is missing/failing, discovery is explicitly blocked. The default Tavily run is capped at five topics to bound API use.
- Missing history, missing persistence, weak evidence, missing source URLs, or unknown duplicate status must hold/block the candidate. Factual verification belongs to AG06, scoring belongs to AG08, planning belongs to AG09. No publisher is called by AG01.
- `READY_FOR_VERIFICATION` is a hand-off to AG06 only; it does not mean factual claims are verified and is **not** publish authorization.
- Before production handoff, the account's UCOS history baseline must be verified. A present legacy SQLite store is imported into Neon without overwriting newer Neon rows; if the legacy store is missing or unreadable, AG01 holds. History coverage includes records synced to UCOS. Posts made outside UCOS need a verified import before they can be included in duplicate decisions. Live source providers must also be configured; an empty source registry returns `blocked_research_sources_unconfigured` rather than fake recommendations.

## Live source setup

Set `TAVILY_API_KEY` in the deployed service environment. An optional `UCOS_TAVILY_TIMEOUT_SECONDS` may be set from 3 to 30 (default 12). No key is stored in source control. See the [official Tavily Search endpoint documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search). Provider availability and quota are environment-dependent; CI tests use a mock API, not a real Tavily account.

## Real production smoke

Run `APP_ENV=production python -m scripts.agent01_live_smoke --account-id <registered-account-id>` only from the deployed service environment or an equivalent production-configured runner. This command uses the real Tavily API and Neon/PostgreSQL account store; it does not inject fake dependencies. It blocks before outbound search unless preflight verifies the registered account, PostgreSQL pool, Tavily key presence, a completed history baseline, and a readable account history. A successful smoke writes one bounded research run and confirms that candidate/evidence/run records can be read back from the durable store. It never publishes. A passed smoke is evidence for review, **not** automatic production certification.

## Completion evidence

Do not mark an agent production-ready from imports or unit tests alone. Its gate needs unit/contract tests, cross-account isolation tests, the relevant CI run, real durable-store verification, and a live smoke test against configured dependencies. If production credentials/database access are unavailable, record that as an unresolved gate rather than claiming success.
