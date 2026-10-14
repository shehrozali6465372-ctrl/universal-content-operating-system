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
- With `TAVILY_API_KEY` configured, AG01 uses the documented Tavily `POST /search` API. Otherwise it selects the public, keyless GDELT Context API via a bounded standard-library adapter. GDELT is rate-limited to one request per five seconds and capped at three candidate topics; it only accepts article records that contain a real source URL, title, and returned sentence/snippet. A provider/network/quota failure remains blocked; no synthetic evidence is substituted.
- Missing history, missing persistence, weak evidence, missing source URLs, or unknown duplicate status must hold/block the candidate. Factual verification belongs to AG06, scoring belongs to AG08, planning belongs to AG09. No publisher is called by AG01.
- `READY_FOR_VERIFICATION` is a hand-off to AG06 only; it does not mean factual claims are verified and is **not** publish authorization.
- Before production handoff, the account's UCOS history baseline must be verified. A present legacy SQLite store is imported into Neon without overwriting newer Neon rows; if the legacy store is missing or unreadable, AG01 holds. History coverage includes records synced to UCOS. Posts made outside UCOS need a verified import before they can be included in duplicate decisions. Live source providers must also be configured; an empty source registry returns `blocked_research_sources_unconfigured` rather than fake recommendations.

## Live source setup

Optional: set `TAVILY_API_KEY` in the deployed service environment for Tavily. Without it, AG01 attempts real live research through the public [GDELT Context API](https://blog.gdeltproject.org/announcing-the-gdelt-context-2-0-api/), which requires no key and is throttled to one request every five seconds. GDELT coverage is news-centric and may return no suitable sources for some niches; if so, the agent holds the candidate rather than inventing evidence. `UCOS_TAVILY_TIMEOUT_SECONDS` applies to Tavily only. No key is stored in source control.

## Real Pinterest history import

Before the first production recommendation on a Pinterest account, run `APP_ENV=production python -m scripts.agent01_import_pinterest_history --account-id <registered-account-id> --confirm-live-import` from an environment configured with the real Neon connection, `UCOS_CREDENTIAL_ENCRYPTION_KEY`, and that account's registered encrypted credential. The importer verifies the token's Pinterest identity against the configured external account ID, fetches every `GET /v5/pins` page (up to the explicit page cap), merges unseen Pin IDs into the account's execution history, reads the records back, and only then marks the history baseline complete. A pagination/API/identity/readback failure leaves the baseline uncertified. This imports only pins returned by that authorized Pinterest account; other platforms or posts omitted by the API require a separate verified import/review. See the official [Pinterest List Pins](https://developers.pinterest.com/docs/api/v5/pins-list/) and [API pagination](https://developers.pinterest.com/docs/reference/pagination/) docs.

## Real production smoke

Run `APP_ENV=production python -m scripts.agent01_live_smoke --account-id <registered-account-id>` only from the deployed service environment or an equivalent production-configured runner. This command uses the real selected research API and Neon/PostgreSQL account store; it does not inject fake dependencies. It blocks before outbound search unless preflight verifies the registered account, PostgreSQL pool, a configured real provider, a completed history baseline, and a readable account history. A successful smoke writes one bounded research run and confirms that candidate/evidence/run records can be read back from the durable store. It never publishes. A passed smoke is evidence for review, **not** automatic production certification.

## Automated real production validation

The `.github/workflows/agent01-live-certification.yml` workflow uses repository secrets `NEON_DATABASE_URL`, `UCOS_CREDENTIAL_ENCRYPTION_KEY`, and `TAVILY_API_KEY`. It connects to the actual Neon account registry, imports Pins from each enabled Pinterest account with that account's encrypted credentials, reads imported history back, then performs one bounded real research-provider smoke per account. It never publishes. If Tavily is absent, the workflow attempts the public GDELT fallback; live research still fails closed if that API is unavailable or cannot provide two independent source hosts. The workflow is evidence only; it must not mark AG01 `production_ready` unless the production orchestrator is wired and the deployed request-to-Neon path has also been verified.

## Completion evidence

Do not mark an agent production-ready from imports or unit tests alone. Its gate needs unit/contract tests, cross-account isolation tests, the relevant CI run, real durable-store verification, and a live smoke test against configured dependencies. If production credentials/database access are unavailable, record that as an unresolved gate rather than claiming success.

### Authenticated AG01 API dispatch

The API gateway exposes `POST /agents/AG01/research` behind UCOS authentication. The production certification workflow uses a route-scoped HMAC derived from the existing credential-encryption root key, so no additional API-token secret is required for the smoke. The request accepts only a registered `account_id` and a `mode` of `certification` or `production`; candidate lists and provider/evidence overrides are never accepted from callers.

- `certification` is restricted to `APP_ENV=production` and dispatches the real AG01 implementation through `AgentDispatcher`. It performs research and Neon read-back only; it never publishes. The HMAC signature covers method, exact route, timestamp, one-time nonce, and body digest; replayed or stale requests are rejected.
- `production` dispatch remains blocked until AG01's manifest status is explicitly `production_ready`.
- The live certification workflow calls the deployed endpoint for every enabled Pinterest account, verifies the provider request and Neon read-back, and does not treat a CI-only direct function call as deployed-path proof.
