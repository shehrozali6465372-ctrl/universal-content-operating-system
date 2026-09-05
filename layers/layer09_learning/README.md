# Autonomous Continuous Learning & Optimization

**Layer:** 09 — Learning
**Status:** Production implementation on `v7-real-self-learning`; external telemetry required for live learning

Layer 9 provides an evidence-gated learning lifecycle. It does not invent production observations, rewards, metrics, or successful experiments.

## Lifecycle

1. Real platform telemetry is normalized into an exact `LearningScope`.
2. Measured outcomes are persisted in SQLite with source and lineage.
3. Experiments assign control/treatment deterministically and require an outcome after assignment.
4. Statistical evaluation reports sample counts, uplift, p-value, and 95% confidence interval.
5. Supervised models train on chronological holdouts from one exact scope.
6. Model candidates are evaluated against the active model using measurable guardrails.
7. Policies are immutable versions with model/experiment/evidence lineage.
8. Deployment progresses through challenger → canary → active only with evidence.
9. Measured regression can trigger an exact-scope rollback to the last retired verified policy.
10. Missing evidence fails closed as `insufficient_evidence`; it is never converted into success.

## Context isolation

A scope contains:

- platform
- niche
- audience
- country
- language
- content type

No implicit cross-platform or cross-niche fallback is allowed. The implementation is designed to represent at least 1,000 distinct platform×niche contexts without mixing their state.

## Real-data requirement

Layer 9 intentionally does **not** generate synthetic production data. A live deployment must connect real platform outcome adapters and provide trustworthy event source IDs. Until those sources exist, training and deployment remain evidence-gated.

## Tests

```bash
pytest tests/layer09_learning/ -q
```
