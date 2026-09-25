# Layer 7 Production Certification

**Layer:** 07 — Publishing  
**Certification class:** Production code-gate certification  
**Branch:** `hardening/layer7-production`  
**Certified commit:** `917707d70bf52d29ceb848dcb0a346f94cd6bee7`  
**GitHub Actions gate:** Layer 7 Production Gate  
**Gate run:** `36154771980`  
**Evidence:** 762 Layer 7 tests passed; critical static checks passed; Python compilation passed.

## Certified controls

- Real publishing entry point routes through `PublisherManager`; no synthetic provider success is accepted.
- Publish transactions execute registered callables and compensate only completed steps.
- Transaction instances are single-use.
- Circuit breakers are concurrency-safe and permit only one half-open probe.
- Retry backoff uses configured production delays.
- Scheduler queue operations are lock-protected and duplicate job IDs are rejected.
- Worker reservation/completion is concurrency-safe.
- Retryable queue failures are requeued; exhausted jobs enter the dead-letter queue.
- URL-only platforms reject local media unless a configured public media URL can be resolved.
- Runtime media paths are account-scoped and path-traversal constrained.
- Publishing policy validation is enforced on the canonical publish path.
- Production orchestrator results originate from the real publisher manager.

## Certification boundary

This certificate covers the Layer 7 **code and automated production gate** at the certified commit.

It does **not** claim that a live social-platform account was mutated during CI, and it does not replace deployment-specific provider authorization, platform approval, or a live-provider smoke test. Those are environment-specific release gates and must be evidenced separately before enabling real-world publishing.

## Re-certification rule

Any source or test change to Layer 7 invalidates this certificate until the Layer 7 Production Gate passes again on the new commit.
