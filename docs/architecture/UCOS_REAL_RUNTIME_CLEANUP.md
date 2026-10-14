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
2. `AIPipeline.execute()` no longer creates `executed_<task>` output when no executor is supplied. A populated pipeline fails closed without an executor.
3. `PipelineWiring._run_step()` requires a dictionary result; `None` cannot silently become a successful step. Skips must be explicit.
4. `LLMManager` treats either `APP_ENV=production|prod` or `UCOS_ENV=production|prod` as production. It checks the absence of a real generator before consulting cache, so cached development placeholder output cannot bypass the production check. Production pricing validation uses the same environment check.

## CI acceptance gates

The CI audit reports layer count, production import edges, test-only references, agent ownership, duplicate candidates, provider/model paths, and scaffold-success patterns. The workflow fails on Python syntax errors or remaining high-signal scaffold-success patterns. Unit tests cover the audit, missing real providers, executor-less pipelines, pipeline step result types, production environment detection, cache bypass, and production pricing.

Static import analysis cannot prove the absence of dynamic imports or external third-party imports. All removals are therefore confined to exact placeholder files with no package exports and no in-repository callers. Merge remains blocked until the latest full CI run and required checks pass.

## Scope

This is a source cleanup and test-gating change on a pull-request branch. It does not deploy services, change database schemas, or certify the 28 agents. Production certification still requires real provider, database, account-history, publishing, and deployed-path evidence for each agent.
