# Layer 01 — Core: End-to-End Production Architecture

**Status:** Architecture target for Layer 1 completion  
**Implementation boundary:** `layers/layer01_core`  
**Baseline:** `39b6fd682f18589fd8d104a5766bef50a10c0e75`  
**Current source inventory:** 51 Python modules, 165 classes, 743 functions/methods  
**Rule:** This document defines the Layer 1 production completion target. It does not claim that every target is already implemented or runtime-verified.

---

## 1. Mission

Layer 1 is the UCOS foundational runtime. It owns the cross-cutting primitives required by higher layers without owning their business/domain logic.

Layer 1 must provide:

- configuration and environment resolution
- secure credential/secret lifecycle
- foundational persistence and database access
- file and artifact storage primitives
- memory/state primitives
- structured logging and audit
- settings and event propagation
- scheduling, queueing, retries and bounded execution
- migrations
- backup/restore and disaster recovery primitives
- validation and failure taxonomy
- health/readiness signals
- deterministic startup/shutdown
- operational safety, recovery and observability

Layer 1 must not become a dumping ground for higher-layer business logic.

---

## 2. Production principles

1. **Fail closed:** missing, corrupt or invalid security/configuration state must fail explicitly.
2. **No fabricated success:** integration-ready is not live; unknown is not success.
3. **Single source of truth:** no duplicate credential/config/state stores without an explicit contract.
4. **Least privilege:** callers receive only the secret/data/capability they require.
5. **Atomicity:** state-changing critical writes are atomic or transactional.
6. **Idempotency:** retries must not duplicate durable side effects.
7. **Bounded execution:** timeouts, retry limits and cancellation must be explicit.
8. **Recoverability:** backup/restore and failure recovery must be testable, not theoretical.
9. **Auditability:** security-sensitive and operationally significant mutations must be attributable.
10. **Determinism:** startup, migration and configuration precedence must be predictable.
11. **Isolation:** tenant/account/platform/niche state must not cross boundaries.
12. **Explicit contracts:** higher layers consume stable interfaces, not internal implementation details.
13. **No secrets in source/registry/logs/tests:** credentials remain runtime secrets.
14. **Evidence-gated completion:** Layer 1 is complete only when implementation + tests + CI + runtime evidence satisfy the gate.

---

## 3. End-to-end lifecycle

### Startup

```
Process start
  -> environment discovery
  -> configuration source discovery
  -> configuration precedence resolution
  -> schema validation
  -> immutable settings validation
  -> secret-store availability
  -> database connectivity
  -> migration check/apply
  -> file/storage initialization
  -> memory/state initialization
  -> logger/audit initialization
  -> event system initialization
  -> queue/scheduler initialization
  -> backup/recovery capability check
  -> dependency health evaluation
  -> readiness = READY
```

Any mandatory prerequisite failure must produce a deterministic failure state; the system must not report readiness while a required dependency is unusable.

### Runtime request

```
Higher-layer caller
  -> Layer 1 contract
  -> identity/scope validation
  -> input validation
  -> authorization/capability check where applicable
  -> state/config/secret lookup
  -> operation
  -> transaction/atomic persistence
  -> audit/structured logging
  -> event emission where required
  -> result
```

### Failure

```
Operation
  -> typed failure
  -> rollback/atomic recovery
  -> bounded retry if retryable
  -> dead-letter/permanent failure if exhausted
  -> audit
  -> health impact evaluation
  -> caller receives explicit failure
```

### Shutdown

```
shutdown signal
  -> stop accepting new work
  -> cancel/finish bounded in-flight work
  -> flush audit/log buffers
  -> persist required state
  -> release locks/connections
  -> stop scheduler/workers
  -> final health/state record
  -> process exit
```

---

## 4. Layer 1 component topology

```
                         LAYER 1 CORE
                              |
        +---------------------+----------------------+
        |                     |                      |
 Configuration            Security               Persistence
        |                     |                      |
 ConfigManager          SecretsManager          DatabaseManager
 ConfigSchema            KeyStore               Models/Migrations
 EnvironmentLoader       Secret policy           FileManager
 EnvProfiles
 ImmutableSettings
 Validators
        |                     |                      |
        +---------------------+----------------------+
                              |
                    State / Memory Services
                              |
             MemoryManager / MemoryStore / Search
                              |
        +---------------------+----------------------+
        |                     |                      |
 Observability           Execution Runtime       Recovery
        |                     |                      |
 LoggerManager           SchedulerManager        BackupManager
 DecisionLogger          TaskQueue               Restore
 LogRotation             RetryManager            Integrity
 AuditLogger             CronParser              Disaster Recovery
        |                     |
        +----------+----------+
                   |
             Settings / Events
                   |
          SettingsManager
          SettingSchema
          EventSystem
```

---

## 5. Configuration plane

### Components

- `ConfigManager`
- `config_schema.py`
- `EnvironmentLoader`
- `EnvProfile`
- `ImmutableSettings`
- `Validators`

### Required flow

```
Defaults
  -> profile configuration
  -> environment variables
  -> deployment/runtime overrides
  -> explicit application configuration
  -> precedence resolution
  -> schema validation
  -> immutable-field enforcement
  -> normalized configuration snapshot
```

### Production requirements

- deterministic precedence
- type validation
- required/optional distinction
- safe defaults only where explicitly approved
- no secret values in ordinary config snapshots
- immutable setting protection
- configuration versioning
- atomic persistence where configuration is persisted
- reload semantics defined
- snapshot/reset semantics defined
- startup validation before readiness

---

## 6. Secret and credential plane

### Components

- `SecretsManager`
- `KeyStore`
- secret-related exceptions

### Responsibilities

Layer 1 is the central credential lifecycle boundary. Higher layers should request credentials through a stable interface rather than owning independent secret stores.

### Secret lifecycle

```
Provision
  -> validate metadata
  -> encrypt/protect
  -> atomic persist
  -> access-control
  -> retrieve on demand
  -> use by authorized caller
  -> audit metadata only
  -> rotate
  -> revoke/delete
```

### Required controls

- encryption at rest
- secure key source
- strict file/storage permissions
- explicit missing vs corrupt vs undecryptable distinction
- no secret values in logs
- no secret values in exceptions
- caller authorization/scope
- rotation without delete/create gap
- atomic writes
- corruption detection
- key rotation strategy
- revocation semantics
- audit of access/mutation without recording secret material
- test fixtures must use synthetic credentials only

### Credential namespace

The secret store may contain credentials for external providers such as AI, GitHub, publishing or storage integrations, but Layer 1 does not own those providers' business logic. It owns the secure lifecycle and exposes credentials through contracts.

---

## 7. Persistence plane

### DatabaseManager

Responsibilities:

- connection lifecycle
- initialization
- transaction boundaries
- query execution
- health checks
- statistics/diagnostics
- controlled backup/restore integration
- migration integration

### Architecture rule

The registry identifies L13 as the production PostgreSQL persistence source of truth. Layer 1 must therefore have an explicit, tested contract with the production persistence architecture rather than silently creating a competing source of truth.

Before certification, trace:

```
Layer 1 DatabaseManager
  -> all callers
  -> database abstraction boundary
  -> L13 persistence boundary
  -> production PostgreSQL path
  -> migrations
  -> transactions
  -> backup/restore
```

Any intentional local SQLite/core-state role must be explicitly documented and isolated from business persistence.

### Transaction requirements

- begin/commit/rollback
- no partial durable state
- retry only when safe
- connection cleanup
- timeout policy
- concurrency behavior
- health/readiness semantics
- migration locking
- corruption/error behavior

---

## 8. File and artifact plane

### Components

- `FileManager`
- `FileCache`
- `hash_utils`

### Required flow

```
Caller
 -> logical path
 -> normalize
 -> resolve
 -> base-boundary validation
 -> authorization
 -> lock/concurrency control
 -> atomic read/write
 -> hash/integrity check
 -> cache policy
 -> result
```

### Production controls

- path traversal prevention
- symlink/reparse-point policy
- base-directory containment
- atomic writes
- file locks
- checksum/hash verification
- corruption detection
- import/export validation
- compression/decompression safety
- cache invalidation
- size limits
- safe temporary files
- permission policy
- cleanup/recovery after interrupted writes

---

## 9. Memory and state plane

### Components

- `MemoryManager`
- `MemoryStore`
- `MemorySearchEngine`
- memory models/configuration

### Required lifecycle

```
Create/update memory
  -> validate scope + level
  -> normalize
  -> persist
  -> index/search representation
  -> retrieve
  -> update/delete
  -> consistency maintenance
```

### Production requirements

- explicit memory levels
- account/tenant isolation
- deterministic serialization
- durable vs ephemeral distinction
- search consistency
- update/delete consistency
- stale index handling
- corruption recovery
- size/retention policy
- concurrency safety
- no secret leakage into memory
- provenance/metadata where required
- backup/restore compatibility

---

## 10. Logging and audit plane

### Components

- `LoggerManager`
- `DecisionLogger`
- `LogRotation`
- `AuditLogger`

### Logging must answer

- what happened?
- when?
- which component?
- which operation?
- which request/correlation context?
- which scoped account/platform where applicable?
- outcome?
- error class?
- duration where relevant?

### Audit must answer

- who/what initiated the mutation?
- what resource was affected?
- what action occurred?
- success/failure?
- timestamp/correlation ID?
- security-relevant metadata?

Never record:

- API keys
- passwords
- decrypted secrets
- raw authorization tokens
- sensitive exception payloads

---

## 11. Settings and event plane

### Components

- `SettingsManager`
- `SettingSchema`
- `SettingsEventBus`
- settings exceptions

### Flow

```
Setting request
 -> schema validation
 -> permission/immutability check
 -> atomic state update
 -> version/event creation
 -> event dispatch
 -> subscribers react
 -> audit
```

### Required semantics

- typed settings
- defaults
- feature flags
- immutable settings
- rollback
- validation failure
- event ordering
- subscriber failure isolation
- duplicate event handling
- event correlation
- no event emitted for failed transaction
- deterministic restart behavior

---

## 12. Scheduler / queue / retry plane

### Components

- `SchedulerManager`
- `TaskQueue`
- `RetryManager`
- `CronParser`

### Task lifecycle

```
Create
 -> validate
 -> enqueue
 -> scheduled/ready
 -> claim
 -> running
 -> success
      OR
 -> retryable failure
 -> bounded retry
      OR
 -> permanent failure
 -> dead-letter/failure state
```

### Production controls

- unique task identity
- idempotency key
- priority
- scheduling time
- timeout
- cancellation
- retry classification
- exponential/backoff policy where appropriate
- maximum attempts
- worker ownership/lease
- stuck-task recovery
- dead-letter state
- duplicate execution protection
- graceful shutdown
- persistence across restart
- observability

### Critical rule

A retry must never blindly repeat a non-idempotent external mutation.

---

## 13. Migration plane

### Components

- `MigrationRegistry`
- `MigrationManager`

### Required lifecycle

```
Current schema version
 -> discover pending migrations
 -> acquire migration lock
 -> validate ordering
 -> execute transactionally where supported
 -> record applied version
 -> verify schema
 -> release lock
```

Required:

- ordered migrations
- duplicate detection
- checksum/version integrity
- locking
- partial-failure behavior
- restart safety
- compatibility window
- rollback strategy where feasible
- backup before destructive migration
- production verification

---

## 14. Backup / restore / disaster recovery plane

### Components

- `BackupManager`
- `BackupEntry`
- backup exceptions

### Backup lifecycle

```
Select state
 -> quiesce/consistent snapshot
 -> create backup
 -> encrypt/protect
 -> hash/integrity metadata
 -> durable storage
 -> verify
 -> retention
```

### Restore lifecycle

```
Backup selection
 -> verify identity/integrity
 -> validate compatibility
 -> isolate target
 -> restore
 -> schema/data verification
 -> application health check
 -> recovery audit
```

### Certification requirements

A backup is not considered production-ready until a restore has been executed successfully in a controlled environment.

---

## 15. Validation and failure architecture

Layer 1 must distinguish at least:

- missing configuration
- invalid configuration
- missing credential
- corrupt credential store
- undecryptable credential
- invalid path
- invalid schema
- database unavailable
- migration failure
- file integrity failure
- queue failure
- retry exhaustion
- backup integrity failure
- restore failure
- settings validation failure
- immutable setting mutation
- unexpected internal failure

### Failure contract

Every failure must define:

```
type
 -> retryable?
 -> safe to retry?
 -> rollback required?
 -> health impact?
 -> audit required?
 -> caller-visible?
 -> recovery path?
```

No broad catch-and-ignore behavior on critical paths.

---

## 16. Security boundary

Layer 1 is a security-sensitive boundary.

### Threats to cover

- secret disclosure
- path traversal
- symlink/reparse escape
- configuration injection
- malicious serialized state
- SQL injection
- race conditions
- concurrent writes
- replay/duplicate tasks
- log injection
- credential misuse
- unauthorized cross-account access
- corrupted persistence
- malicious backup/restore input
- denial through unbounded queue/retry/storage growth

### Security verification

- static analysis
- dependency scanning
- secret scanning
- negative tests
- permission tests
- malformed-input tests
- concurrency tests
- recovery tests

---

## 17. Identity and isolation

Every persistent record that represents business or user-scoped state must have an explicit ownership/isolation model where applicable:

```
Account
  -> external platform/account
  -> niche/project scope
  -> resource
```

Credentials are not business data and must never be copied into architecture registries.

Cross-scope access must be denied by contract, not merely by convention.

---

## 18. Health / readiness model

Layer 1 should expose deterministic states:

- STARTING
- READY
- DEGRADED
- NOT_READY
- FAILED
- STOPPING

Health checks must distinguish:

- process alive
- configuration valid
- secret store available
- database available
- storage available
- scheduler available
- required migrations complete
- backup capability available where required

A process being alive is not equivalent to being production-ready.

---

## 19. Dependency direction

Target dependency direction:

```
Environment / OS
       ↓
Configuration
       ↓
Security + Persistence primitives
       ↓
State / Memory
       ↓
Logging / Audit
       ↓
Settings / Events
       ↓
Scheduler / Queue / Retry
       ↓
Recovery / Operational services
       ↓
Higher UCOS layers
```

Avoid:

- higher-layer business logic inside Layer 1
- circular imports
- Layer 1 importing application-specific domain behavior
- duplicate persistence implementations
- direct provider-specific business logic in the secret store

---

## 20. Module ownership map

| Area | Current modules |
|---|---|
| Configuration | config_manager, config_schema, environment_loader, env_profiles, immutable_settings |
| Secrets | key_store, secrets_manager |
| Database | database_manager, models, migrations |
| Files | file_manager package, file_cache, hash_utils |
| Memory | memory_manager, memory_store, memory_search |
| Logging/Audit | audit_logger, logger package |
| Scheduler | scheduler package |
| Settings/Events | settings_manager package |
| Backup | backup_manager package |
| Validation/Errors | validators, exceptions packages |
| Tests | Layer 1 unit/integration/regression test modules |

Every module must have one declared owner/responsibility. Duplicate or orphan implementations must be removed, merged, or explicitly classified as compatibility boundaries.

---

## 21. Cross-layer contract

Higher layers must consume Layer 1 through explicit contracts for:

- configuration access
- secret retrieval
- persistent state
- file/artifact operations
- memory operations
- logging/audit
- scheduling
- events/settings
- health/readiness
- recovery

Higher layers must not:

- access Layer 1 private internals
- read secret-store files directly
- bypass path validation
- bypass persistence transactions
- write audit files directly
- implement competing global schedulers
- create hidden credential stores

---

## 22. API-key / credential architecture

The principle is:

**Layer 1 manages credentials; the consuming integration layer performs the external API call.**

Example:

```
L07 Publishing
  -> request credential
  -> Layer 1 SecretsManager
  -> scoped credential
  -> L07 adapter
  -> external platform
```

Similarly:

```
L12 AI Foundation
  -> request provider credential
  -> Layer 1
  -> provider adapter
  -> model API
```

Therefore external provider keys are Layer 1's **managed secrets**, not Layer 1's business integrations.

---

## 23. Testing pyramid

### Unit

Every critical component:

- normal path
- invalid input
- missing dependency
- corruption
- timeout
- concurrency
- recovery
- boundary conditions

### Integration

At minimum:

- configuration + environment
- configuration + secrets
- database + migrations
- memory + persistence
- file manager + cache
- scheduler + queue + retry
- settings + event bus
- backup + restore
- logging + audit
- full Layer 1 workflow

### System/runtime

- clean startup
- readiness
- real persistence path
- migration startup
- secret retrieval
- scheduled task execution
- graceful shutdown
- restart recovery
- backup/restore
- failure injection

### Regression

Every discovered production defect receives a regression test at the appropriate layer.

---

## 24. Production certification gate

Layer 1 is **NOT COMPLETE** until all applicable gates below are evidenced:

- [ ] 51/51 source modules reviewed
- [ ] 165/165 classes reviewed
- [ ] 743/743 functions/methods classified by responsibility/call path
- [ ] caller/callee graph established for critical paths
- [ ] configuration lifecycle verified
- [ ] environment precedence verified
- [ ] secret lifecycle verified
- [ ] credential access controls verified
- [ ] database boundary verified against production persistence architecture
- [ ] migration lifecycle verified
- [ ] file/path security verified
- [ ] memory lifecycle verified
- [ ] logging/audit verified
- [ ] settings/event semantics verified
- [ ] scheduler/queue/retry verified
- [ ] idempotency verified
- [ ] cancellation/timeouts verified
- [ ] backup integrity verified
- [ ] restore executed successfully
- [ ] disaster recovery path verified
- [ ] health/readiness verified
- [ ] startup/shutdown verified
- [ ] concurrency/race-sensitive paths tested
- [ ] security/negative tests pass
- [ ] no critical duplicate/orphan implementation remains unexplained
- [ ] no secrets in source/tests/logs
- [ ] integration boundaries fail closed
- [ ] CI green on the final Layer 1 commit
- [ ] production runtime evidence recorded
- [ ] architecture registry synchronized from implementation evidence

Only after every applicable gate has evidence may work move to Layer 2.

---

## 25. Definition of Done

The final Layer 1 result must be:

**Implemented → Tested → Integrated → Failure-tested → Security-tested → Recovery-tested → CI-certified → Runtime-verified → Documented → Registry-synchronized.**

A green unit-test suite alone is not sufficient.

A module existing is not sufficient.

An API key being configured is not sufficient.

A mocked provider is not live evidence.

A successful startup is not sufficient.

The final certification must demonstrate that Layer 1 can reliably provide its foundational contracts to the rest of UCOS under normal operation, failure, restart, recovery and security-boundary conditions.

---

## 26. Work sequence

Work remains locked to Layer 1:

1. Inventory and architecture reconciliation
2. Full module/class/function classification
3. Dependency and caller/callee tracing
4. Configuration/environment completion
5. Secret/credential lifecycle completion
6. Persistence/database boundary completion
7. File/storage completion
8. Memory/state completion
9. Logging/audit completion
10. Settings/events completion
11. Scheduler/queue/retry completion
12. Migration completion
13. Backup/restore/DR completion
14. Security and isolation hardening
15. Cross-layer contract verification
16. Full test/regression expansion
17. CI verification
18. Runtime/recovery verification
19. Registry synchronization
20. Layer 1 production certification

**Layer 2 remains blocked until this definition of done is satisfied.**
