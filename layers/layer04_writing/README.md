# Layer 4 — Writing Engine

**Status:** Production-ready after CI certification on the certified commit.  
**Role:** Convert Layer 2/3 research and intelligence context into validated, platform-aware writing plans, drafts, variants, and final platform outputs.

## Architecture

`Request/Topic → Content Planner → WritingPlan → Draft Generator → Draft Validation/Memory → Platform Adaptation → Caption/Hook/CTA/Hashtags → Content Optimization → Writing Memory → Orchestrator Result`

### 1. Content Planner
- Goal analysis
- Audience analysis
- Platform constraints
- Tone selection
- Content structure
- Constraint management
- Plan validation
- Versioned `WritingPlan`

### 2. Draft Generator
- Prompt construction
- LLM provider abstraction
- Production provider gate
- Draft validation
- Variant/A-B generation
- Bounded draft memory
- Token/latency accounting

### 3–10. Output Intelligence
- Caption Engine
- Hashtag Engine
- Tone Adapter
- Hook Engine
- CTA Generator
- Content Optimizer
- Writing Memory / brand voice
- Writing Orchestrator

## Production invariants

- Production environments cannot silently fall back to a mock LLM provider.
- Untrusted topic/research context is explicitly delimited in prompts and is treated as data, not instructions.
- Memory stores are bounded and use defensive reads where mutable state could leak.
- Invalid platform/plan inputs fail validation rather than silently producing an unsafe plan.
- Duplicate platform requests are rejected by the orchestrator.
- TikTok platform planning is represented consistently with the layer's supported platform contracts.
- Generated drafts are validated before downstream use.
- Orchestrator state is serialized with an explicit lock.

## Cross-layer contract

- **Layer 3 → Layer 4:** intelligence/research context is accepted as structured dictionaries and passed into planning/prompt construction without granting that context instruction authority.
- **Layer 4 → downstream:** the layer emits a validated `WritingPlan`, generated draft metadata, and platform-specific output data suitable for later quality/media/publishing stages.
- Canonical production execution is wired through the Layer 14 pipeline, which independently enforces real-provider, quality, policy, account, idempotency, and publishing gates.

## Tests

Primary Layer 4 tests:
- `tests/layer04_writing/test_content_planner.py`
- `tests/layer04_writing/test_draft_generator.py`
- `tests/layer04_writing/test_modules_3_10.py`

Run:

```bash
python -m pytest tests/layer04_writing/ -q
```
