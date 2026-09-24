# Layer 1 Static Audit Reconciliation

This record reconciles the static AST audit on the Layer 1 production-hardening branch. Static call-name analysis intentionally produces false positives for public APIs, properties, enums/exceptions, and externally invoked lifecycle entry points.

## Current inventory evidence

The CI static audit at run #635 reported:

- Python modules: 51
- Classes: 167
- Functions/methods: 795
- Syntax errors: 0
- Duplicate body groups: 3
- Orphan candidates: 51

The registry baseline of 51/165/743 predates the current hardening branch. The implementation tree is authoritative; registry counts must be refreshed after the production branch is accepted.

## Duplicate-body reconciliation

All three duplicate groups are intentional, responsibility-distinct implementations:

1. `ConfigManager.is_loaded` and `EnvironmentLoader.is_loaded`
   - Both expose lifecycle state for different configuration domains.
   - Shared implementation shape is expected and does not represent competing ownership.

2. `DatabaseManager.is_initialized` and `MemoryManager.is_initialized`
   - Both expose component lifecycle state.
   - Database and memory remain separate resources and ownership boundaries.

3. `DatabaseManager.close` and `MemoryManager.close`
   - Both release their own database resources.
   - The identical small lifecycle pattern is not a duplicate persistence implementation.

No duplicate group represents two competing Layer 1 sources of truth.

## Orphan-candidate reconciliation

The 51 candidates below are retained because static AST call-name analysis cannot see all valid external/public callers. They are classified as public API, lifecycle entry point, exported type/exception, property, introspection helper, or externally callable scheduler/settings operation. They are not deletion candidates without runtime/coverage evidence.

### Runtime/public lifecycle

- `Layer1Runtime`
- `Layer1Runtime.start`
- `Layer1Runtime.is_ready`
- `SchedulerManager.process_cron_jobs`
- `SettingsManager.events`

These are external lifecycle/control-plane surfaces.

### Exported audit, backup, configuration and environment API

- `AuditAction`
- `AuditStatus`
- `AuditLogger.count_actions`
- `BackupError`
- `BackupEncryptionError`
- `RestoreError`
- `DisasterRecoveryError`
- `ConfigManager.project_root`
- `ConfigManager.is_loaded`
- `ConfigManager.config_version`
- `get_required_keys`
- `get_optional_keys`
- `get_field`
- `ConfigError`
- `ConfigNotFound`
- `MissingAPIKey`
- `InvalidPath`
- `EnvironmentLoader.current_profile`
- `EnvironmentLoader.is_loaded`
- `EnvironmentLoader.get_profile_info`

These are public schema/state/error surfaces and may be consumed outside the local AST graph.

### Public file, key-store and logging API

- `FileCache.size`
- `FileCache.hit_rate`
- `FileManager.release_lock`
- `FileManager.cache_stats`
- `KeyStore.path`
- `LogRotation.log_dir`

These expose state, lifecycle or operational controls to callers outside the static call graph.

### Database, memory and model API

- `DatabaseManager.db_path`
- `DatabaseManager.is_initialized`
- `MemoryManager.is_initialized`
- `MemorySearchEngine.find_by_category`
- `MemorySearchEngine.find_by_tags`
- `get_all_levels`
- `MigrationRegistry.get_all`
- `get_table`

These are public query/schema/lifecycle APIs.

### Scheduler queue API

- `CronParser.get_next_runs`
- `TaskQueue.get_by_name`
- `TaskQueue.clear_completed`
- `TaskQueue.pending_count`
- `TaskQueue.total_count`

These are externally useful queue/cron inspection and maintenance surfaces.

### Settings and validation API

- `SettingsError`
- `validate_not_empty`
- `validate_api_key`
- `validate_path`
- `validate_log_level`
- `validate_bool`
- `validate_number`

These are exported errors and validation primitives, not dead production flows.

## Gate interpretation

The static audit is evidence for inventory and candidate discovery, not a deletion oracle. A candidate is only actionable when a runtime/coverage trace proves there is no supported external caller. No critical Layer 1 responsibility is being removed based solely on this AST heuristic.

The remaining production gates are therefore runtime/recovery/security evidence, real Layer 13 contract evidence, and registry synchronization after the implementation baseline is accepted.
