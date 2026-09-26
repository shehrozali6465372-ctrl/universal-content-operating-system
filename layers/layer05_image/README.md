# Image & Visual

**Layer:** layer 05 image
**Status:** 🟡 Hardened — Not Production Certified
**Version:** See [VERSION](../../VERSION)

## Description

Image & Visual module for AI Self-Improving Facebook Agent.

## Modules

| Module | Description | Status |
|--------|-------------|--------|
| Planning, prompt, layout, provider orchestration, optimization, memory | Hardened | 🟡 |

## Usage

```python
from layers.layer05_image import *
```

## Real Providers

- **Gemini:** `GeminiImageProvider` using `GEMINI_API_KEY_1` / `GEMINI_API_KEY`.
- **OpenRouter:** `OpenRouterImageProvider` using `OPENROUTER_API_KEY`; temporary real-image smoke provider for certification.
- OpenRouter default model: `bytedance-seed/seedream-4.5`.
- Production boundary rejects mock providers and requires nonempty image bytes plus SHA-256 provenance.

## Certification Gates

The layer remains **Not Production Certified** until the CI gate verifies targeted tests, a real provider smoke test, persisted nonempty image bytes, SHA-256 provenance, and the remaining Layer 5 cross-layer/failure/concurrency gates.

**Current external gate blocker:** the latest real OpenRouter smoke reached the configured API but returned HTTP 402 (`insufficient credits`). The gate therefore remains blocking rather than treating a skipped/failed real generation as certification evidence.

## Tests

```bash
pytest tests/unit/layer05_image -q
```



<!-- Certification gate trigger: real OpenRouter smoke remains mandatory when configured. -->
<!-- Certification gate trigger: rerun after external provider readiness is verified. -->
