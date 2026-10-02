"""PostgreSQL Schema — All table definitions for the Universal AI Content OS."""
from __future__ import annotations


SCHEMA_VERSION = "1.2.1"

TABLES = [
    {
        "name": "agent_config",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "key VARCHAR(255) UNIQUE NOT NULL",
            "value TEXT NOT NULL",
            "category VARCHAR(100) DEFAULT 'general'",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_config_category ON agent_config(category)",
        ],
    },
    {
        "name": "agent_memory",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "level VARCHAR(50) NOT NULL",
            "category VARCHAR(100) NOT NULL",
            "key VARCHAR(255) NOT NULL",
            "value TEXT NOT NULL",
            "tags TEXT DEFAULT ''",
            "importance REAL DEFAULT 0.5",
            "access_count INTEGER DEFAULT 0",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            "UNIQUE(level, category, key)",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_memory_level ON agent_memory(level)",
            "CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_memory(category)",
            "CREATE INDEX IF NOT EXISTS idx_memory_importance ON agent_memory(importance DESC)",
        ],
    },
    {
        "name": "agent_logs",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "level VARCHAR(20) NOT NULL",
            "module VARCHAR(100) NOT NULL",
            "message TEXT NOT NULL",
            "details JSONB",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_logs_level ON agent_logs(level)",
            "CREATE INDEX IF NOT EXISTS idx_logs_module ON agent_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_logs_created ON agent_logs(created_at DESC)",
        ],
    },
    {
        "name": "agent_versions",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "version VARCHAR(50) NOT NULL",
            "component VARCHAR(100) NOT NULL",
            "change_description TEXT NOT NULL",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_versions_component ON agent_versions(component)",
        ],
    },
    {
        "name": "scheduled_jobs",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "name VARCHAR(255) UNIQUE NOT NULL",
            "job_type VARCHAR(100) NOT NULL",
            "schedule_cron VARCHAR(100)",
            "config_json JSONB",
            "enabled BOOLEAN DEFAULT TRUE",
            "last_run TIMESTAMP",
            "next_run TIMESTAMP",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_jobs_type ON scheduled_jobs(job_type)",
            "CREATE INDEX IF NOT EXISTS idx_jobs_enabled ON scheduled_jobs(enabled)",
        ],
    },
    {
        "name": "published_posts",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "platform VARCHAR(50) NOT NULL",
            "post_id VARCHAR(255)",
            "content TEXT NOT NULL",
            "image_path TEXT",
            "status VARCHAR(50) DEFAULT 'draft'",
            "engagement_score REAL DEFAULT 0.0",
            "scheduled_at TIMESTAMP",
            "published_at TIMESTAMP",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_posts_platform ON published_posts(platform)",
            "CREATE INDEX IF NOT EXISTS idx_posts_status ON published_posts(status)",
            "CREATE INDEX IF NOT EXISTS idx_posts_published ON published_posts(published_at DESC)",
        ],
    },
    {
        "name": "analytics_cache",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "metric_name VARCHAR(255) NOT NULL",
            "metric_value REAL NOT NULL",
            "dimensions JSONB DEFAULT '{}'",
            "recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_analytics_metric ON analytics_cache(metric_name)",
            "CREATE INDEX IF NOT EXISTS idx_analytics_recorded ON analytics_cache(recorded_at DESC)",
        ],
    },
    {
        "name": "learning_history",
        "columns": [
            "id SERIAL PRIMARY KEY",
            "lesson_type VARCHAR(100) NOT NULL",
            "content TEXT NOT NULL",
            "source VARCHAR(100)",
            "confidence REAL DEFAULT 0.5",
            "applied BOOLEAN DEFAULT FALSE",
            "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
        ],
        "indexes": [
            "CREATE INDEX IF NOT EXISTS idx_learning_type ON learning_history(lesson_type)",
            "CREATE INDEX IF NOT EXISTS idx_learning_confidence ON learning_history(confidence DESC)",
        ],
    },
]



# v1.2 canonical workflow/publication records. Legacy tables remain during
# migration, but production business state must use these canonical records.
TABLES.extend([
    {"name": "tenants", "columns": [
        "tenant_id VARCHAR(255) PRIMARY KEY",
        "name VARCHAR(255) NOT NULL",
        "enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": []},
    {"name": "workspaces", "columns": [
        "workspace_id VARCHAR(255) PRIMARY KEY",
        "tenant_id VARCHAR(255) NOT NULL REFERENCES tenants(tenant_id)",
        "name VARCHAR(255) NOT NULL",
        "enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON workspaces(tenant_id)",
    ]},
    {"name": "brands", "columns": [
        "brand_id VARCHAR(255) PRIMARY KEY",
        "workspace_id VARCHAR(255) NOT NULL REFERENCES workspaces(workspace_id)",
        "name VARCHAR(255) NOT NULL",
        "enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_brands_workspace ON brands(workspace_id)",
    ]},
    {"name": "accounts", "columns": [
        "account_id VARCHAR(255) PRIMARY KEY",
        "brand_id VARCHAR(255) NOT NULL REFERENCES brands(brand_id)",
        "platform VARCHAR(100) NOT NULL",
        "niche VARCHAR(255) NOT NULL",
        "display_name VARCHAR(255) NOT NULL DEFAULT ''",
        "audience TEXT NOT NULL DEFAULT ''",
        "credentials_ref VARCHAR(512) NOT NULL DEFAULT ''",
        "affiliate_rules JSONB NOT NULL DEFAULT '{}'::jsonb",
        "capabilities JSONB NOT NULL DEFAULT '[]'::jsonb",
        "constraints JSONB NOT NULL DEFAULT '{}'::jsonb",
        "enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_accounts_brand ON accounts(brand_id)",
        "CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)",
        "CREATE INDEX IF NOT EXISTS idx_accounts_niche ON accounts(niche)",
    ]},
    {"name": "platform_accounts", "columns": [
        "platform_account_id VARCHAR(255) PRIMARY KEY",
        "account_id VARCHAR(255) NOT NULL REFERENCES accounts(account_id)",
        "platform VARCHAR(100) NOT NULL",
        "external_account_id VARCHAR(512) NOT NULL",
        "display_name VARCHAR(255) NOT NULL DEFAULT ''",
        "enabled BOOLEAN NOT NULL DEFAULT TRUE",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE(account_id, platform, external_account_id)",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_platform_accounts_account ON platform_accounts(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_platform_accounts_external ON platform_accounts(platform, external_account_id)",
    ]},
])

TABLES.extend([
    {"name": "credentials", "columns": [
        "credential_id UUID PRIMARY KEY",
        "credential_ref VARCHAR(512) NOT NULL UNIQUE",
        "account_id VARCHAR(255) NOT NULL REFERENCES accounts(account_id)",
        "platform_account_id VARCHAR(255) REFERENCES platform_accounts(platform_account_id)",
        "encrypted_payload TEXT NOT NULL",
        "key_version VARCHAR(100) NOT NULL",
        "active BOOLEAN NOT NULL DEFAULT TRUE",
        "revoked_at TIMESTAMPTZ",
        "expires_at TIMESTAMPTZ",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_credentials_account ON credentials(account_id, active)",
        "CREATE INDEX IF NOT EXISTS idx_credentials_platform_account ON credentials(platform_account_id, active)",
    ]},
])

TABLES.extend([
    {"name": "workflow_runs", "columns": [
        "workflow_id UUID PRIMARY KEY", "tenant_id VARCHAR(255) NOT NULL",
        "workspace_id VARCHAR(255)", "brand_id VARCHAR(255)", "account_id VARCHAR(255)",
        "platform VARCHAR(100)", "status VARCHAR(50) NOT NULL",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_workflow_runs_account ON workflow_runs(account_id, created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status, updated_at DESC)",
    ]},
    {"name": "publish_intents", "columns": [
        "intent_id UUID PRIMARY KEY", "workflow_id UUID REFERENCES workflow_runs(workflow_id)",
        "publish_operation_id UUID NOT NULL UNIQUE", "tenant_id VARCHAR(255) NOT NULL",
        "workspace_id VARCHAR(255)", "brand_id VARCHAR(255)", "account_id VARCHAR(255) NOT NULL",
        "platform VARCHAR(100) NOT NULL", "platform_account_id VARCHAR(255) NOT NULL",
        "publish_mode VARCHAR(20) NOT NULL", "state VARCHAR(50) NOT NULL",
        "idempotency_key VARCHAR(512) NOT NULL", "content_hash VARCHAR(128)",
        "reserved_at TIMESTAMPTZ", "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE(account_id, platform, platform_account_id, idempotency_key)",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_publish_intents_state ON publish_intents(state, updated_at)",
        "CREATE INDEX IF NOT EXISTS idx_publish_intents_account ON publish_intents(account_id, platform, platform_account_id)",
    ]},
    {"name": "publish_attempts", "columns": [
        "attempt_id UUID PRIMARY KEY", "intent_id UUID NOT NULL REFERENCES publish_intents(intent_id)",
        "attempt_number INTEGER NOT NULL", "started_at TIMESTAMPTZ NOT NULL",
        "call_deadline_at TIMESTAMPTZ NOT NULL", "attempt_lease_expires_at TIMESTAMPTZ NOT NULL",
        "provider VARCHAR(100) NOT NULL", "provider_idempotency_key VARCHAR(512) NOT NULL",
        "status VARCHAR(50) NOT NULL", "outcome VARCHAR(50)", "error_class VARCHAR(100)",
        "error_message TEXT", "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE(intent_id, attempt_number)",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_publish_attempts_reconcile ON publish_attempts(status, attempt_lease_expires_at)",
    ]},
    {"name": "provider_effects", "columns": [
        "effect_id UUID PRIMARY KEY", "attempt_id UUID NOT NULL REFERENCES publish_attempts(attempt_id)",
        "provider_tracking_id VARCHAR(512)", "external_post_id VARCHAR(512)", "external_url TEXT",
        "provider_status VARCHAR(100)", "evidence JSONB NOT NULL DEFAULT '{}'::jsonb",
        "observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_provider_effects_attempt ON provider_effects(attempt_id)",
        "CREATE INDEX IF NOT EXISTS idx_provider_effects_external ON provider_effects(external_post_id)",
    ]},
    {"name": "publication_verifications", "columns": [
        "verification_id UUID PRIMARY KEY", "intent_id UUID NOT NULL REFERENCES publish_intents(intent_id)",
        "state VARCHAR(50) NOT NULL", "evidence JSONB NOT NULL DEFAULT '{}'::jsonb",
        "verified_at TIMESTAMPTZ", "next_reconcile_at TIMESTAMPTZ", "expires_at TIMESTAMPTZ",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_publication_verifications_reconcile ON publication_verifications(next_reconcile_at, state)",
    ]},
    {"name": "inbox_events", "columns": [
        "inbox_id UUID PRIMARY KEY", "provider VARCHAR(100) NOT NULL",
        "platform VARCHAR(100) NOT NULL", "platform_account_id VARCHAR(255) NOT NULL",
        "external_event_id VARCHAR(512) NOT NULL", "payload_hash VARCHAR(128) NOT NULL",
        "payload JSONB NOT NULL", "status VARCHAR(50) NOT NULL DEFAULT 'RECEIVED'",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE(provider, platform, platform_account_id, external_event_id)",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_inbox_events_status ON inbox_events(status, created_at)",
    ]},
    {"name": "outbox_events", "columns": [
        "outbox_id UUID PRIMARY KEY", "event_type VARCHAR(255) NOT NULL",
        "aggregate_type VARCHAR(100) NOT NULL", "aggregate_id UUID NOT NULL",
        "idempotency_key VARCHAR(512) NOT NULL UNIQUE", "payload_hash VARCHAR(128) NOT NULL",
        "payload JSONB NOT NULL", "available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "attempt_count INTEGER NOT NULL DEFAULT 0", "lease_owner VARCHAR(255)",
        "lease_expires_at TIMESTAMPTZ", "status VARCHAR(50) NOT NULL DEFAULT 'PENDING'",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_outbox_events_dispatch ON outbox_events(status, available_at)",
    ]},
    {"name": "durable_tasks", "columns": [
        "task_id UUID PRIMARY KEY", "workflow_id UUID REFERENCES workflow_runs(workflow_id)",
        "dedupe_key VARCHAR(512) UNIQUE", "task_type VARCHAR(255) NOT NULL", "state VARCHAR(50) NOT NULL",
        "available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP", "lease_owner VARCHAR(255)",
        "lease_expires_at TIMESTAMPTZ", "attempt_count INTEGER NOT NULL DEFAULT 0",
        "max_attempts INTEGER NOT NULL DEFAULT 3", "backoff_seconds INTEGER NOT NULL DEFAULT 5",
        "retry_at TIMESTAMPTZ", "cancel_requested BOOLEAN NOT NULL DEFAULT FALSE",
        "last_error TEXT", "error_class VARCHAR(100)", "dlq_reason TEXT",
        "payload JSONB NOT NULL DEFAULT '{}'::jsonb",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
        "updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_durable_tasks_dispatch ON durable_tasks(state, available_at)",
        "CREATE INDEX IF NOT EXISTS idx_durable_tasks_lease ON durable_tasks(lease_expires_at)",
    ]},
    {"name": "operator_resolutions", "columns": [
        "resolution_id UUID PRIMARY KEY", "intent_id UUID NOT NULL REFERENCES publish_intents(intent_id)",
        "actor_id VARCHAR(255) NOT NULL", "reason TEXT NOT NULL", "evidence JSONB NOT NULL",
        "prior_state VARCHAR(50) NOT NULL", "resulting_state VARCHAR(50) NOT NULL",
        "created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ], "indexes": [
        "CREATE INDEX IF NOT EXISTS idx_operator_resolutions_intent ON operator_resolutions(intent_id, created_at DESC)",
    ]},
])


def get_create_table_sql(table):
    cols = ",\n            ".join(table["columns"])
    return f"CREATE TABLE IF NOT EXISTS {table['name']} (\n            {cols}\n        )"


def get_all_create_sql():
    return [get_create_table_sql(t) for t in TABLES]


def get_all_indexes_sql():
    indexes = []
    for t in TABLES:
        indexes.extend(t.get("indexes", []))
    indexes.extend([
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_publish_intents_active_content "
        "ON publish_intents(account_id, platform, content_hash) "
        "WHERE content_hash IS NOT NULL AND state <> 'FAILED_CONFIRMED'",
        "CREATE INDEX IF NOT EXISTS idx_publish_intents_unresolved "
        "ON publish_intents(account_id, platform, platform_account_id, state, updated_at)",
    ])
    return indexes


def get_all_migration_sql():
    """Return idempotent PostgreSQL migrations for databases created pre-v1.2.1."""
    return [
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS template_hash VARCHAR(128)",
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS publish_marker VARCHAR(512)",
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS requested_visibility VARCHAR(100)",
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS policy_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb",
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS content_asset_refs JSONB NOT NULL DEFAULT '[]'::jsonb",
        "ALTER TABLE publish_intents ADD COLUMN IF NOT EXISTS tracked_link_ref VARCHAR(512)",
        "ALTER TABLE durable_tasks ADD COLUMN IF NOT EXISTS dedupe_key VARCHAR(512)",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_durable_tasks_dedupe ON durable_tasks(dedupe_key) WHERE dedupe_key IS NOT NULL",
        "ALTER TABLE durable_tasks ADD COLUMN IF NOT EXISTS max_attempts INTEGER NOT NULL DEFAULT 3",
        "ALTER TABLE durable_tasks ADD COLUMN IF NOT EXISTS backoff_seconds INTEGER NOT NULL DEFAULT 5",
        "ALTER TABLE durable_tasks ADD COLUMN IF NOT EXISTS error_class VARCHAR(100)",
        "ALTER TABLE durable_tasks ADD COLUMN IF NOT EXISTS dlq_reason TEXT",
    ]
