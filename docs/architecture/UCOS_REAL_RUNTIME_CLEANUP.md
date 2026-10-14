# UCOS Real-Runtime Cleanup — First Pass

## Decision boundary

UCOS retains the legacy layer code needed to build the 28-worker system. This cleanup removes only confirmed placeholder handlers and fixes code paths that could report completion without real work. It does not claim the 28 workers are implemented or production-certified.

## Verified Layer 11 cleanup

The audit found 81 Python modules across these six generated subpackages:

- `async_ai_engine`
- `async_http_engine`
- `async_plugin_framework`
- `background_workers`
- `distributed_cluster`
- `performance_optimization`

Each removed module appended the incoming payload to an in-memory `self._data` list and returned a literal `{"status": "ok", "processed": true}`. It did not run a queue, scheduler, balancer, dispatcher, distributed task, or plugin. Static AST analysis found no production import edges and no test-only imports for these 81 files. Their package `__init__.py` files were empty markers and did not export the classes.

The files were removed from the cleanup branch after narrowing agent ownership. The corresponding directories now retain only modules that have real, separately implemented behavior.

A second pass removed another **73 dead Layer 11 scaffold files** across the same generated engine families plus `concurrent_execution`. These consisted of instance-local event/health/metric/report lists, “parallel queue/worker/scheduler” classes that only recorded payloads, duplicate generic exceptions, empty package markers, and model classes whose `to_dict()` used a malformed double-brace dictionary expression. The audit found no production imports or test-only importers for these paths; they were also absent from the narrowed agent ownership manifest and had no package re-exports or other in-repository path references.

Across both passes, **154 Layer 11 scaffold files** were removed. The substantive execution implementation remains in the separate runtime/task-manager/provider-integration modules.

### Second-pass event-loop cleanup

A repository-wide import/ownership scan identified 17 additional files under `layer11_async_runtime/modules/event_loop_management` with no production imports, test importers, or manifest owners. Manual source inspection confirmed that the dispatch/recovery/restart helpers only recorded requests and could report `success: true` without dispatching or restarting a real loop; the remaining unreferenced helpers were isolated in-memory registries, metrics, context, event, policy, and report utilities that were not connected to the retained runtime. These 17 unowned utility modules were removed. The actual `event_loop.py` and `loop_manager.py` entry points and package marker remain.

### Test doubles isolated from production packages

The platform plugin manager's `MockPublisher` was referenced only by two test files and returned fabricated publication IDs, success states, and analytics. It was moved to `tests_helpers/mock_publisher.py`, both test imports were updated, and the production-package copy was removed. The real platform adapters and publishing gateway were not changed.

### Monitoring package consolidation

- Removed seven monitoring modules that had no production imports or Guardian-agent ownership: the in-memory dashboard duplicate, duplicate error tracker, unnormalized performance scorer, unconnected profiler/tracer, incomplete resource probe, and in-memory usage analytics.
- Kept the canonical monitoring engine, system monitor, metrics engine, health monitor, alert manager, and their focused tests. This avoids treating isolated in-memory utilities as live system monitoring.

### Provider and multi-model execution hardening

- Removed 22 unconnected provider helper modules that were only tested in isolation and not used by the real provider factory/adapters. The provider base, factory/registry, and real HTTP-backed OpenAI, Claude, Gemini, DeepSeek, Grok, Mistral, Cohere, Ollama, and OpenRouter adapters remain.
- Removed the Llama and Qwen classes that returned fabricated prompt-derived text while claiming initialization success; they had no production callers. Real adapters must perform a provider call or return/raise an explicit failure.
- Removed the unused embedding helper that derived synthetic vectors from a text hash.
- `ParallelGeneration`, `ParallelReasoning`, and `ParallelReview` now run real callbacks concurrently with bounded workers and preserve result order. They reject a missing callback instead of simulating output; review no longer fabricates positive feedback.
- `MultiModelFallback` now requires a real provider callback when a fallback is available. The callback's failures are recorded and never replaced by synthetic success.
- Removed unconnected multi-model context/metrics/monitor/cache/registry/scheduler/request/response helper modules; retained the actual model response type, provider-backed executor, parallel execution, routing/strategy, consensus/voting/ranking, ensemble, response selection, reasoning merge, and callback-based fallback.

### Disconnected Layer 12 duplicate subsystems removed

The repository import graph showed no production callers or agent-manifest ownership for the following Layer 12 subpackages; their only external callers were the monolithic unit-test file. Their responsibilities already have canonical implementation boundaries elsewhere in UCOS, so retaining them created parallel, unconnected implementations:

- `ai_orchestrator` — duplicate task orchestration removed; the canonical account-aware control plane remains in Layer 14.
- `ai_governance` — duplicate governance helpers removed; authorization/security remains owned by Layer 17.
- `ai_evaluation_engine` — duplicate evaluation helpers removed; content quality/safety remains owned by Layer 6.
- `ai_memory_layer` — duplicate in-memory helpers removed; durable/account-scoped state remains owned by the persistence and memory paths.
- `ai_reasoning_engine` — duplicate reasoning helpers removed; the existing Layer 3 reasoning/intelligence path remains.
- `prompt_intelligence` — duplicate prompt utilities removed; writing and the canonical model-router prompt builder remain.
- The standalone `ai_cost_optimizer` family was pruned to the `price_calculator.py` module that the retained `LLMManager` actually imports. Its other unreferenced, in-memory trackers, schedulers, registries, and hard-coded model-switch helpers were removed with their disconnected unit-test section.

The large `tests/test_layer12_ai_foundation.py` suite now retains tests for the actual LLM manager, provider adapters, multi-model execution, and the wired price calculator rather than treating disconnected helper classes as production capabilities.

### Additional LLM and image-provider cleanup

- Removed unreferenced LLM utility modules whose implementations only recorded in-memory lists, pretended a model was loaded, or duplicated the canonical model-router/response-selector behavior. Provider adapters, the canonical model router/key manager, LLM manager, and multi-model execution components remain.
- Removed unreferenced Layer 12 exception-only files and a stale supported-model constants file after the dependency audit found no production callers, tests, or manifest ownership.
- Removed the development-only synthetic response path from `LLMManager.generate()`. Every environment now requires an injected generator backed by a real provider; the guard runs before cache lookup. A regression test covers the development case.
- Moved `MockImageProvider` to `tests_helpers/mock_image_provider.py`; production image-provider interfaces and real OpenRouter/Puter/Gemini adapters remain. Tests now import the mock from the test-only package.
- Changed CLI subsystem status reporting so an unprobed subsystem is reported as `unverified`, not `available`. Added tests for the truthful status and empty-name validation.

## Runtime code intentionally retained

The following execution paths remain in the repository:

- Layer 11 `async_runtime_engine` and `async_task_manager`
- Layer 11 `provider_integration`
- Layer 15 `async_scheduler` and PostgreSQL-backed `durable_execution`
- Layer 15 `task_queue` and `worker_pool`
- Layer 18 `monitoring_engine`
- Layer 7 publication scheduler and `scheduler_queue`
- Layer 12 model provider adapters, model router, key management, LLM manager, and multi-model components

Agent source ownership for AG18 (Publishing Planner and Scheduler) and AG27 (Runtime, Queue and Recovery) is restricted to these substantive modules instead of the entire Layer 11 directory.

## Confirmed false-success fixes

1. `MultiModelExecutor.execute()` no longer fabricates `Response from {model}` as model output. A real provider callback is required, and late responses are not marked successful after the overall deadline.
2. The duplicate Layer 12 `ai_orchestrator` package was removed after dependency analysis found no production callers; canonical orchestration remains in Layer 14.
3. `PipelineWiring._run_step()` requires a dictionary result; `None` cannot silently become a successful step. Skips must be explicit.
4. `LLMManager` refuses to generate without an injected real provider-backed generator in every environment. The guard runs before cache lookup, so a cached development placeholder cannot masquerade as execution. Production pricing validation treats either `APP_ENV=production|prod` or `UCOS_ENV=production|prod` as production.

### Unowned monitoring modules removed

The new ownership gate identified seven Layer 18 modules with no production importers, test importers, or manifest owners: a dashboard backend, a second error tracker, a standalone performance analyzer, a profiler, a resource monitor, a tracer, and in-memory usage analytics. They were removed after checking their contents and the retained monitoring path. System and error monitoring remain in `monitoring_engine`; runtime profiling remains in Layer 11; business/content analytics remain in their owning layers. The removed modules had no route, registration, durable storage, or caller connecting them to those canonical paths.

### Shared implementation consolidation

The cleanup also consolidated repeated cross-layer primitives without deleting provider capability:
- `ConfidenceResult` now has one canonical implementation under `layers/shared/models/confidence.py`; the research layer imports it instead of maintaining a duplicate model.
- SQL identifier validation is shared by the core database manager and PostgreSQL pool code.
- Image-size parsing is shared by the OpenRouter and Puter image adapters.
- Atomic JSON writes and tolerant JSON-object loading are shared by the fact-verification and topic-scoring managers.
- Layer 12 provider adapters, the real multi-model executor, the active model-router path, and the LLM factory remain in place.

These changes reduce duplicated behavior while preserving domain-specific scoring, verification, provider routing, and account policy.

## CI acceptance gates

The CI audit reports layer count, production import edges, test-only references, agent ownership, duplicate candidates, provider/model paths, and scaffold-success patterns. The workflow fails on Python syntax errors, unresolved internal imports, remaining high-signal scaffold-success patterns, or layer modules that have no static production importer, no test importer, and no manifest owner. Unit tests cover the audit, missing real providers, executor-less pipelines, pipeline step result types, production environment detection, cache bypass, and production pricing.

Static import analysis cannot prove the absence of dynamic imports or external third-party imports. All removals are therefore confined to exact placeholder files with no package exports and no in-repository callers. Merge remains blocked until the latest full CI run and required checks pass.

## Scope

This is a source cleanup and test-gating change on a pull-request branch. It does not deploy services, change database schemas, or certify the 28 agents. Production certification still requires real provider, database, account-history, publishing, and deployed-path evidence for each agent.
