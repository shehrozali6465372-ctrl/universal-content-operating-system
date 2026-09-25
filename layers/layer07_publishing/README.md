# Layer 07 — Publishing

**Layer:** 07 — Publishing  
**Status:** Production-hardening in progress  
**Scope:** account-aware publishing, platform adapters, media handling, scheduling, failure recovery, analytics hooks, memory, policies, and orchestration.

## Production invariants

- No silent platform-adapter import failures.
- Publish transactions execute their registered callables and compensate only completed steps.
- Circuit breakers are thread-safe and allow only one half-open probe at a time.
- Pipeline stages require explicit handlers and reset stale execution state.
- Retry backoff uses the configured production delay rather than a shortened test delay.
- Synthetic publisher results are not evidence of real provider success; live-provider evidence is required for certification.

## Verification

Run the Layer 7 test suite:

```bash
pytest tests/layer07_publishing/ -v
```

Layer 7 is not considered production-certified solely because a historical report says `certified: true`. Certification must be based on the current commit, current tests, current integration evidence, and production-gate checks.


<!-- Layer 7 certification candidate: CI rerun after repository-wide compile gate remediation. -->
