# UCOS Research Agent — implementation and operational contract v1.0

**Owner:** CEO / Super Intelligence Agent  
**Specialist:** Research Agent (AgentRole.RESEARCH)  
**Capability owner:** Layer 02 — Research Engine  
**External search owner:** Layer 11 — IntegrationGateway  
**Status:** Code and CI gate; production certification still requires live deployment/E2E evidence.

## Single-agent topology

~~~~mermaid
flowchart TD
    CEO["CEO / Super Intelligence"] --> TASK["Scoped research task"]
    TASK --> AGENT["One Research Agent"]
    AGENT --> PLAN["Layer 02 Research Planner"]
    PLAN --> ORCH["Layer 02 Research Orchestrator"]
    ORCH --> L11["Layer 11 IntegrationGateway"]
    L11 --> SEARCH["Google News RSS or configured SerpAPI"]
    SEARCH --> SOURCES["Actual source links, titles and snippets"]
    SOURCES --> MODS["Existing Layer 02 research modules"]
    MODS --> VERIFY["Source provenance + limitations"]
    VERIFY --> LEDGER["CEO durable goal/task/evidence ledger (PostgreSQL)"]
~~~~

This is one specialist that uses the existing Layer 02 pipeline; it does not create a second research engine or eight new agents. The Research Agent's module bindings and in-memory manager instances are created per task. Durable task results belong to the CEO's injected PostgreSQL-backed goal/task store, not to cross-tenant process globals.

## Real source execution

- With no search API key, the Layer 11 gateway makes real HTTPS requests to Google News RSS. With `UCOS_SERPAPI_API_KEY` or `SERPAPI_API_KEY` configured, Layer 11 uses SerpAPI.
- Missing network access, invalid provider responses, or an empty source list do not trigger generated/mock evidence. The workflow fails or reports partial status.
- Source records include the provider, query, observed timestamp, title, snippet and returned URL.
- URL format is validated; this is not an assertion that each article URL is reachable, accurate, or independently verified.
- The existing Layer 02 fact checker uses lexical evidence matching and contradiction heuristics. Its output is marked preliminary and still requires editorial review.
- Competitor search snippets are article/publisher samples only. Follower counts, engagement, demographics, revenue and conversions are not inferred or fabricated.
- Since Layer 11 search returns sources rather than verified market-performance metrics, topic scoring reports `market_score_unavailable` and explains why instead of inventing a numeric score or publish recommendation.
- Layer 02 manager indexes are task-local working state. Cross-run durability comes from the CEO's durable task/evidence persistence adapter.

## Security and isolation

- Tenant/workspace/brand scope is derived from the CEO-issued `AgentTask`; user input cannot override it.
- Each task receives fresh Layer 02 managers. The pipeline executor resets results before each run and only passes successful prior-wave outputs to dependent modules.
- A failed dependency blocks downstream modules. Sibling modules in a parallel wave cannot read each other's partial results.
- External retrieval is delegated to Layer 11; this agent does not implement a duplicate HTTP client.

## Production acceptance gate

1. Focused Research Agent/runtime and Layer 02 regression tests pass on the exact commit.
2. Real search provider smoke test produces live query/timestamp/source receipts.
3. The CEO production goal/task/evidence store persists the full result to canonical PostgreSQL.
4. Live task execution demonstrates scope isolation, dependency failure propagation, explicit provider outage behavior and no source/metric fabrication.
5. Deployed service health and end-to-end evidence are attached to the exact production commit.

Green CI alone does not satisfy live production acceptance.
