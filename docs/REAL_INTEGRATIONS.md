# UCOS real integration boundary

UCOS uses real-provider adapters and fails closed when credentials are missing.

Providers:
SERP API: UCOS_SERPAPI_API_KEY
Affiliate REST: UCOS_AFFILIATE_BASE_URL, UCOS_AFFILIATE_API_KEY, optional UCOS_AFFILIATE_SEARCH_PATH
Google Analytics 4 Data API: UCOS_GA4_PROPERTY_ID and UCOS_GA4_ACCESS_TOKEN, optional UCOS_GA4_PROJECT_ID
WordPress REST: UCOS_WORDPRESS_URL, UCOS_WORDPRESS_USERNAME, UCOS_WORDPRESS_APPLICATION_PASSWORD

Transport:
HTTP requests have explicit timeout and bounded retry handling for 429, 5xx, and transient transport failures.
Production provider URLs must use HTTPS. Credentials may not be embedded in URLs.

Lineage:
SOURCE -> NICHE -> KEYWORD -> CONTENT -> ASSET -> PLATFORM -> ACCOUNT -> PUBLISH -> CLICK -> CONVERSION -> REVENUE

Each lineage event stores a deterministic event ID, parent event ID, source/source ID, provider, status, confidence, payload hash, error code, and observation timestamp.
Duplicate events are idempotent. Invalid parent-stage transitions are rejected.
Production persistence uses the existing PostgreSQL ConnectionPool. SQLite is only injectable for tests/development.

Verification:
python main.py --integration-status reports credential/configuration presence only.
Actual provider reachability is claimed only after a real provider call succeeds with valid credentials.