# Layer 8 — Analytics & Tracking

**Layer:** 08  
**Scope:** analytics ingestion, metrics, trends/anomalies, A/B experiments, funnels, attribution, reporting, dashboard state, and the Layer 13 persistence boundary.

## Production boundary

Layer 8 never creates or closes a Layer 13 database pool. Production callers must inject a durable `AnalyticsPersistence` implementation. The supplied `PostgreSQLAnalyticsPersistence` adapter delegates to the Layer 13 `AnalyticsRepository`.

`AnalyticsOrchestrator(production=True)` fails closed when durable persistence is absent.

## Data integrity rules

- Every observation has source, metric name, timestamp, dimensions, and finite numeric value.
- Source failures are raised instead of silently becoming false success.
- Metric formulas are validated and aggregation honors the requested formula.
- Trend detection is deterministic and does not double-run a metric.
- A/B conversions cannot exceed recorded impressions and significance is calculated from observed proportions.
- Attribution models conserve observed revenue.
- Funnel counts reject impossible negative/exceeding values.
- IDs use UUIDs rather than time modulo counters.

## Verification

Run the dedicated Layer 8 gate and the full suite.

The layer is **not production-certified until the current commit passes the dedicated Layer 8 gate, the complete CI suite, and post-merge main-branch verification with the real Layer 13 PostgreSQL path.**
