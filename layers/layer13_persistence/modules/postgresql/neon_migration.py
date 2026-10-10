"""One-shot, transaction-safe copy of canonical L13 PostgreSQL data to Neon.

Enable explicitly with UCOS_NEON_MIGRATION_ON_BOOT=true and NEON_DATABASE_URL.
The source is the currently configured L13 PostgreSQL database. Only counts and
table names are reported; credential payloads, tokens, and connection strings
are never logged.
"""
from __future__ import annotations

import os
from typing import Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, execute_values, register_default_json, register_default_jsonb

from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionConfig
from layers.layer13_persistence.modules.postgresql.migrations.schema import (
    TABLES,
    get_all_create_sql,
    get_all_indexes_sql,
    get_all_migration_sql,
)

CONTROL_TABLE = "ucos_neon_migration_control"


def _source_dsn() -> str:
    """Resolve the same POSTGRES_*/PG_* settings used by the canonical L13 pool."""
    env = os.environ
    host = env.get("POSTGRES_HOST") or env.get("PG_HOST")
    database = env.get("POSTGRES_DB") or env.get("PG_DATABASE")
    user = env.get("POSTGRES_USER") or env.get("PG_USER")
    password = env.get("POSTGRES_PASSWORD") or env.get("PG_PASSWORD")
    if host and database and user and password:
        port = env.get("POSTGRES_PORT") or env.get("PG_PORT") or "5432"
        return psycopg2.extensions.make_dsn(
            host=host, port=port, dbname=database, user=user, password=password,
            connect_timeout=8, sslmode=env.get("POSTGRES_SSLMODE", "prefer"),
        )
    # Some deployments inject only a PostgreSQL URL. Do not guess localhost.
    fallback = (env.get("UCOS_SOURCE_DATABASE_URL") or env.get("DATABASE_URL") or "").strip()
    if fallback.startswith(("postgres://", "postgresql://")):
        return fallback
    raise RuntimeError("source PostgreSQL settings are not configured")


def _columns(conn, table: str) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema='public' AND table_name=%s ORDER BY ordinal_position",
            (table,),
        )
        return [row[0] for row in cur.fetchall()]


def _tables(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public' AND table_type='BASE TABLE'"
        )
        return {row[0] for row in cur.fetchall()}


def _count(conn, table: str) -> int:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier("public", table)))
        return int(cur.fetchone()[0])


def migrate_to_neon() -> dict[str, Any]:
    """Create the canonical schema, copy all rows, verify counts, then commit."""
    target_dsn = (os.getenv("NEON_DATABASE_URL") or "").strip()
    if not target_dsn.startswith(("postgres://", "postgresql://")):
        raise RuntimeError("NEON_DATABASE_URL must be a PostgreSQL URI")

    source_dsn = _source_dsn()
    source = psycopg2.connect(source_dsn)
    target = psycopg2.connect(target_dsn)
    try:
        # JSON/JSONB values are returned as JSON text, avoiding accidental
        # plaintext serialization or custom adapters for credential payloads.
        register_default_json(source, loads=lambda value: value)
        register_default_jsonb(source, loads=lambda value: value)

        target.autocommit = False
        with target.cursor() as cur:
            cur.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema='public' AND table_name=%s)",
                (CONTROL_TABLE,),
            )
            has_control = bool(cur.fetchone()[0])
            if has_control:
                cur.execute(
                    sql.SQL("SELECT completed_at FROM {} WHERE migration_key=%s").format(
                        sql.Identifier("public", CONTROL_TABLE)
                    ),
                    ("l13-to-neon-v1",),
                )
                if cur.fetchone():
                    target.rollback()
                    return {"status": "already_completed", "table_count": len(TABLES)}

        source_tables = _tables(source)
        expected_tables = {item["name"] for item in TABLES}
        unexpected = sorted(source_tables - expected_tables)
        if unexpected:
            raise RuntimeError("source contains tables outside the canonical schema: " + ",".join(unexpected))

        with target.cursor() as cur:
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS public.{CONTROL_TABLE} "
                "(migration_key TEXT PRIMARY KEY, completed_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                "row_counts JSONB NOT NULL DEFAULT '{}'::jsonb)"
            )
            for statement in get_all_create_sql():
                cur.execute(statement)
            for statement in get_all_migration_sql():
                cur.execute(statement)
            for statement in get_all_indexes_sql():
                cur.execute(statement)

            # Copy in canonical dependency order. The target remains in one
            # transaction; any schema, FK, or row-count mismatch rolls it back.
            row_counts: dict[str, int] = {}
            for table in TABLES:
                name = table["name"]
                if name not in source_tables:
                    row_counts[name] = 0
                    continue
                source_columns = _columns(source, name)
                target_columns = set(_columns(target, name))
                missing = sorted(set(source_columns) - target_columns)
                if missing:
                    raise RuntimeError(f"target schema is missing columns for {name}: {','.join(missing)}")
                col_sql = sql.SQL(",").join(sql.Identifier(column) for column in source_columns)
                select_sql = sql.SQL("SELECT {} FROM {}").format(
                    col_sql, sql.Identifier("public", name)
                )
                insert_sql = sql.SQL("INSERT INTO {} ({}) VALUES %s ON CONFLICT DO NOTHING").format(
                    sql.Identifier("public", name), col_sql
                ).as_string(target)
                copied_source = 0
                with source.cursor() as src_cur:
                    src_cur.execute(select_sql)
                    while True:
                        rows = src_cur.fetchmany(500)
                        if not rows:
                            break
                        # psycopg2 JSON decoders above yield text. Dict/list values
                        # from custom adapters are still safely adapted as JSON.
                        normalized = [
                            tuple(Json(value) if isinstance(value, (dict, list)) else value for value in row)
                            for row in rows
                        ]
                        execute_values(cur, insert_sql, normalized, page_size=500)
                        copied_source += len(rows)
                actual = _count(target, name)
                if actual != copied_source:
                    raise RuntimeError(
                        f"row-count verification failed for {name}: source={copied_source}, target={actual}"
                    )
                row_counts[name] = actual

            # Keep serial sequences aligned after copying explicit IDs.
            cur.execute(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND column_default LIKE 'nextval(%'"
            )
            serial_columns = cur.fetchall()
            for table_name, column_name in serial_columns:
                cur.execute(
                    sql.SQL(
                        "SELECT setval(pg_get_serial_sequence(%s,%s), "
                        "GREATEST(COALESCE(MAX({}),1),1), COUNT(*) > 0) FROM {}"
                    ).format(sql.Identifier(column_name), sql.Identifier("public", table_name)),
                    (f"public.{table_name}", column_name),
                )

            cur.execute(
                sql.SQL("INSERT INTO {} (migration_key, row_counts) VALUES (%s,%s) "
                        "ON CONFLICT (migration_key) DO UPDATE SET completed_at=now(), row_counts=EXCLUDED.row_counts").format(
                    sql.Identifier("public", CONTROL_TABLE)
                ),
                ("l13-to-neon-v1", Json(row_counts)),
            )
        target.commit()
        return {
            "status": "completed",
            "table_count": len(source_tables),
            "total_rows": sum(row_counts.values()),
            "row_counts": row_counts,
        }
    except Exception:
        target.rollback()
        raise
    finally:
        source.close()
        target.close()
