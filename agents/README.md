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

Set `TAVILY_API_KEY` in the deployed service environment for Tavily. An optional `UCOS_TAVILY_TIMEOUT_SECONDS` may be set from 3 to 30 (default 12). If Tavily is not configured in production, AG01 uses the public Google News RSS endpoint and resolves each item to its publisher's HTTPS article URL; if fewer than two independent publisher hosts are available, the topic is held. This is a real public source fallback, not canned data. See the [official Tavily Search endpoint documentation](https://docs.tavily.com/documentation/api-reference/endpoint/search) and [Google News RSS search](https://news.google.com/rss/search?q=home%20organization&hl=en-US&gl=US&ceid=US:en). CI unit tests verify parsing/redirect safety separately from the real live production gate.

## Real Pinterest history import

Before the first production recommendation on a Pinterest account, run `APP_ENV=production python -m scripts.agent01_import_pinterest_history --account-id <registered-account-id> --confirm-live-import` from an environment configured with the real Neon connection, `UCOS_CREDENTIAL_ENCRYPTION_KEY`, and that account's registered encrypted credential. The importer verifies the token's Pinterest identity against the configured external account ID, fetches every `GET /v5/pins` page (up to the explicit page cap), merges unseen Pin IDs into the account's execution history, reads the records back, and only then marks the history baseline complete. A pagination/API/identity/readback failure leaves the baseline uncertified. This imports only pins returned by that authorized Pinterest account; other platforms or posts omitted by the API require a separate verified import/review. See the official [Pinterest List Pins](https://developers.pinterest.com/docs/api/v5/pins-list/) and [API pagination](https://developers.pinterest.com/docs/reference/pagination/) docs.

## Real production smoke

Run `APP_ENV=production python -m scripts.agent01_live_smoke --account-id <registered-account-id>` only from the deployed service environment or an equivalent production-configured runner. This command uses the real Tavily API and Neon/PostgreSQL account store; it does not inject fake dependencies. It blocks before outbound search unless preflight verifies the registered account, PostgreSQL pool, Tavily key presence, a completed history baseline, and a readable account history. A successful smoke writes one bounded research run and confirms that candidate/evidence/run records can be read back from the durable store. It never publishes. A passed smoke is evidence for review, **not** automatic production certification.

## Automated real production validation

The `.github/workflows/agent01-live-certification.yml` workflow requires repository secrets `NEON_DATABASE_URL` and `UCOS_CREDENTIAL_ENCRYPTION_KEY`. It connects to the real Neon account registry, imports Pins for each enabled Pinterest account using that account's encrypted credential, reads imported history back, then attempts a bounded real Tavily search if configured or the real Google News RSS publisher fallback. It never publishes. The workflow is evidence only; it must not mark AG01 `production_ready` unless the production orchestrator is wired and the deployed request-to-Neon path has also been verified.

## Completion evidence

Do not mark an agent production-ready from imports or unit tests alone. Its gate needs unit/contract tests, cross-account isolation tests, the relevant CI run, real durable-store verification, and a live smoke test against configured dependencies. If production credentials/database access are unavailable, record that as an unresolved gate rather than claiming success.
