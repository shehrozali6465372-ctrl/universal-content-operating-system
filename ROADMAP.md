# UCOS Roadmap

UCOS is now organized as a 23-layer production architecture. The roadmap tracks integration and hardening work rather than treating the original ten-layer prototype plan as the current system state.

## Current architecture

| Area | Layers | State |
|---|---|---|
| Core, configuration, security | L1, L17 | Implemented |
| Research and intelligence | L2-L4 | Implemented; external research sources remain configuration-dependent |
| Image and quality | L5-L6, L20 | Implemented; external generation/provider access remains configuration-dependent |
| Publishing | L7 | Five target platform adapters integrated: Facebook, Instagram, Pinterest, YouTube, TikTok |
| Analytics and forecasting | L8, L19 | Implemented; real platform metrics only when the platform exposes/configures them |
| Self-learning | L9 | Implemented; account-local performance feedback is isolated |
| Monetization | L10 | Implemented; affiliate selection requires verified external evidence |
| Async/runtime | L11, L15 | Existing runtime components retained; integration/hardening is ongoing |
| AI foundation | L12 | ModelRouter + KeyManager + provider architecture implemented |
| Persistence/database | L13, L16 | Implemented; account-local stores and transactional protections are enforced |
| Enterprise/control plane | L14 | Canonical account-aware orchestration and production pipeline |
| Monitoring | L18 | Implemented |
| Deployment | L21 | Implemented |
| Documentation | L22 | In progress as implementation evolves |
| Website manager | L23 | Implemented; integration/hardening continues |

## Integration priorities

1. Keep the canonical request path account-aware from decision through publishing, analytics, and learning.
2. Keep account-local memory, history, analytics, learning, templates, media, and publishing state physically isolated.
3. Keep credentials account-specific; never fall back to another account's credentials.
4. Keep publishing honest: a platform API response is the source of truth, and no post ID or success is fabricated.
5. Keep TikTok publication asynchronous: `publish_id` is a tracking identifier until status reconciliation yields a real publicly available post ID.
6. Keep content repetition protection transactional and account-scoped, including safe legacy migrations.
7. Route canonical text generation through L12 ModelRouter; provider failures remain explicit.
8. Feed only real observations into account-local learning and decision optimization.
9. Keep affiliate/product data evidence-based; unavailable external evidence remains unavailable/UNKNOWN.
10. Keep documentation synchronized with the actual 23-layer runtime and verified CI results.

## External production prerequisites

Code completeness does not create external authorization. Production publishing may still require platform OAuth/access tokens, API approvals/audits, quotas, public media hosting, and provider credentials. When those prerequisites are missing, UCOS must report the integration as unavailable/unconfigured rather than claiming production success.
