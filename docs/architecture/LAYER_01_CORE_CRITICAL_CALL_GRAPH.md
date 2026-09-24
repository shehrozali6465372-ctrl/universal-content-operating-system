# Layer 1 — Critical Caller/Callee Graph

**Scope:** Layer 1 production-hardening branch  
**Evidence source:** current implementation tree, Layer1Runtime, Layer 1 regression/integration tests.

This is a static contract graph. It does not claim that dynamic reflection, callbacks, or external callers are exhaustively resolved.

## 1. Startup / readiness

```
Layer1Runtime.start
  -> EnvironmentLoader.load
  -> EnvironmentLoader.validate_strict
  -> ConfigManager.load
  -> ConfigManager.validate_strict (strict mode)
  -> SecretsManager.setup
  -> [production] explicit Layer 13 database_backend + memory_backend
  -> [development/test] DatabaseManager.initialize
       -> MigrationManager.migrate
  -> [development/test] MemoryManager.initialize
  -> FileManager
  -> LoggerManager
  -> SchedulerManager
       -> TaskQueue
       -> RetryManager
  -> SettingsManager
  -> BackupManager
  -> Layer1Runtime.health_check
       -> component.health_check()
  -> READY
```

Startup is fail-closed: an initialization exception triggers shutdown; after initialization, the aggregate health check must not report a failed dependency.

## 2. Secrets

```
SecretsManager.store
  -> encrypt
  -> KeyStore.add
       -> KeyStore.load
       -> KeyStore.save (atomic + fsync + restrictive permissions)
  -> AuditLogger.log (metadata only)

SecretsManager.retrieve
  -> KeyStore.get
  -> decrypt
  -> AuditLogger.log (metadata only)
  -> SecretAccessError on existing-but-undecryptable value
```

## 3. Persistence

```
DatabaseManager.initialize
  -> MigrationManager._ensure_version_table
  -> MigrationManager._register_migrations
  -> MigrationManager.migrate
       -> BEGIN IMMEDIATE
       -> execute migration statements
       -> record schema version
       -> COMMIT / ROLLBACK

DatabaseManager.insert/update/delete
  -> identifier validation
  -> parameterized values
  -> _run
  -> transaction
```

Production runtime does not initialize Layer 1 SQLite persistence. Production persistence is supplied explicitly by Layer 13 PostgreSQL.

## 4. File / artifact integrity

```
FileManager.write
  -> _resolve (base containment)
  -> optional backup
  -> temporary file + fsync
  -> atomic replace
  -> invalidate stale hash metadata / optionally save new hash
  -> cache invalidation

FileManager.restore
  -> _resolve
  -> verify_hash
  -> stage copy
  -> verify staged hash
  -> displace existing target
  -> atomic replace
  -> rollback displaced target on failure
```

Resolved symlink targets outside the base directory are rejected by the same containment check.

## 5. Memory

```
MemoryManager.save/save_batch
  -> lock
  -> STM buffer OR SQLite transaction
  -> bounded STM policy

MemoryManager.snapshot
  -> lock
  -> consistent persistent-level read
  -> atomic snapshot replacement

MemoryManager.restore
  -> validate snapshot structure
  -> validate level/count consistency
  -> transactional replacement
```

## 6. Scheduler / retry

```
SchedulerManager.add_task
  -> TaskQueue.add (active-task idempotency)

SchedulerManager.run_next
  -> TaskQueue.next_task
       -> dependency check
       -> not_before check
       -> atomic PENDING -> RUNNING claim
  -> SchedulerManager.run_task
       -> handler
       -> SUCCESS OR retry/failure
       -> RetryManager
       -> durable not_before for retry
```

A timed-out handler that cannot be cancelled is not blindly retried because a second execution could duplicate side effects.

## 7. Backup / restore

```
BackupManager.backup
  -> source copy
  -> deterministic payload hash
  -> optional staged gzip
  -> registry atomic persistence

BackupManager.restore
  -> registry/path validation
  -> integrity verification
  -> staged restore
  -> staged payload hash verification
  -> atomic replacement with rollback
  -> restore audit
```

Registry paths are required to remain inside the backup directory.

## 8. Layer 1 ↔ Layer 13 boundary

```
Layer1Runtime.start(profile=production)
  -> explicit database_backend
  -> explicit memory_backend
  -> health_check + close lifecycle contract
  -> Layer 13 PostgreSQL-owned implementation in production
```

The Layer 1 runtime does not silently instantiate competing production SQLite state.

## Verification references

- Static inventory: `tools/layer1_code_audit.py`
- Layer 1 production regression gates: `tests/test_layer1_production_gate.py`
- Runtime lifecycle: `tests/test_layer1_runtime.py`
- Scheduler regression suite: `layers/layer01_core/tests/test_scheduler.py`
- File manager regression suite: `layers/layer01_core/tests/test_file_manager.py`
- Database regression suite: `layers/layer01_core/tests/test_database_manager.py`
- Backup regression suite: `layers/layer01_core/tests/test_backup_manager.py`
- Layer 13 PostgreSQL manager: `layers/layer13_persistence/modules/postgresql/manager.py`

## Limitation

This graph is evidence of the critical static/runtime paths above; it is not a claim that every dynamic callback, reflection path, framework hook, or external caller is statically enumerable.
