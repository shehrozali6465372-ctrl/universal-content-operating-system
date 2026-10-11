# UCOS Agent-Callable API Contract (Implementation Baseline)

Status: code-derived contract; live runtime/E2E remains unverified.
Source of truth: API Gateway handlers, Layer 10 affiliate contract, Layer 14 browser adapter, Layer 23 job bridge.

## Transport and authentication

All routes below are registered by Layer 14 `APIGateway`.

- Remote API requests require `Authorization: Bearer <UCOS_API_TOKEN>` or the configured `UCOS_MLH_SERVICE_TOKEN`.
- `POST /v1/jobs` uses a distinct HMAC contract with `AIOS_API_KEY`: headers `X-AIOS-Timestamp`, `X-AIOS-Nonce`, and `X-AIOS-Signature`. The signature is HMAC-SHA256 over UTF-8 bytes of `METHOD\nPATH\nTIMESTAMP\nNONCE\nRAW_BODY`; timestamps must be within 300 seconds and nonces are rejected on replay.
- Browser Gateway → Browser Worker uses `UCOS_BROWSER_WORKER_URL` and `Authorization: Bearer <UCOS_BROWSER_TOKEN>`. The worker rejects calls without the token.
- Do not send affiliate credentials, passwords, cookies, or provider access tokens in browser task JSON.

## 1. Generate content through the Control Plane

`POST /generate`

Required:
- `topic`: non-empty topic string in intended use (handler currently supplies a default if omitted).

Optional:
- `platform`, `account_id`, `tone` (default `professional`), `style` (default `educational`), `include_image` (default true), `publish_mode` (`staging` or `production`).

The response envelope is `{success, status, data?, error?, timestamp}`. The `data` value is the ControlPlane pipeline result. An explicit `account_id` must resolve to an enabled registered account and must match `platform` if provided.

Configured browser affiliate account settings are read from that account's `affiliate_rules`:
- `browser_provider: "amazon"`
- `browser_account_ref: "<named persistent browser profile>"`
- optional `marketplace: "www.amazon.com"`
- `browser_required: true|false` (defaults to true when a configured browser flow fails).

A configured browser flow must return a tagged HTTPS affiliate URL with authenticated-browser provenance and product evidence. Failure is fail-closed by default; never fabricate a link.

## 2. Direct Amazon product/link discovery

`POST /affiliate/amazon/search`

Request JSON:
```json
{
  "account_ref": "amazon-primary",
  "query": "facial mist for sensitive skin",
  "marketplace": "www.amazon.com"
}
```

Required: `account_ref`, `query`. `marketplace` defaults to `www.amazon.com` and is restricted by the Layer 14 adapter to Amazon marketplace hosts.

Verified success data shape:
```json
{
  "state": "verified",
  "provider": "amazon",
  "account_ref": "amazon-primary",
  "affiliate_url": "https://www.amazon.com/...",
  "product_ref": "B000000001",
  "source": "authenticated_browser",
  "evidence": {
    "method": "amazon_sitestripe",
    "product_title": "...",
    "product_url": "https://www.amazon.com/dp/...",
    "profile_ref": "amazon-primary",
    "final_url": "https://www.amazon.com/dp/..."
  }
}
```

The sample identifiers/URL above illustrate the schema only; they are not a live product result. The browser adapter searches product pages, then attempts SiteStripe link creation, and accepts only an HTTPS Amazon URL containing a tracking tag. Runtime success still depends on a logged-in Associates profile and current SiteStripe UI selectors.

## 3. Generic bounded browser task

`POST /browser/tasks`

Request JSON is passed through to the browser worker. At minimum:
```json
{
  "url": "https://www.amazon.com/",
  "profile_ref": "amazon-primary",
  "actions": [{"type": "extract"}],
  "timeout_ms": 30000
}
```

Worker contract:
- `url`: absolute HTTP(S); private/local network targets are blocked.
- `profile_ref`: named profile, sanitized to safe characters; persistent storage must be configured and writable to survive restarts.
- `actions`: at most 20 bounded actions. Supported actions include `navigate`, `back`, `forward`, `reload`, `new_tab`, `switch_tab`, `close_tab`, `list_tabs`, `click`, `wait`, `press`, `fill`, `inspect`, `extract`, `extract_selector`, `screenshot`.
- It does not accept credentials, arbitrary JavaScript, file uploads, or CAPTCHA/anti-bot bypass instructions.

Gateway success data shape:
`{state: "completed", source: "ucos_personal_browser", result: <worker result>}`.
Although the handler responds with HTTP 202, the current implementation runs the worker call synchronously and returns a completed result; it is not yet a durable asynchronous task-queue contract.

## 4. AIOS / Layer 23 jobs

`POST /v1/jobs` uses the HMAC authentication above.

Common required JSON fields:
- `request_id`: UUID; acts as an idempotency key.
- `niche_id`: UUID.
- `job_type`: one of `content`, `seo_metadata`, `pinterest_assets`, `analytics_insights`.
- `context`: object with required `domain` and `site_name`, plus job-specific fields.

For `job_type: "content"`, require `context.title` and `context.content`. Draft mode creates a local Layer 23 draft. Publishing additionally requires `context.publish: true`, `context.account_id`, and `context.publish_authorized: true`; publishing is not implied by merely submitting a job. Duplicate `request_id` + same payload returns its cached response; same ID with a different payload is rejected.

The bridge uses a local SQLite inbox at `UCOS_JOB_INBOX_DB` (default `data/job_inbox.sqlite3`), not the browser audit table. Do not assume that it is a Postgres/Neon queue.

## Known limits and next verification gates

1. Contract/schema is now documented from source; it is not an OpenAPI-validated public schema yet.
2. `/browser/tasks` is a generic execution endpoint, not a semantic "find me a product" task. Use `/affiliate/amazon/search` for that specific intent.
3. Verify live browser worker health, persistent profile storage, Amazon Associates login, SiteStripe selector compatibility, and a real tagged-link result before claiming E2E success.
4. Verify the content pipeline consumes `affiliate_url` in the final draft and enforces duplicate checks, account/platform disclosure policy, and publication gates.
5. No live account credentials or secrets belong in this document.
