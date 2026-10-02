"""PostgreSQL identity hierarchy repository for L13 Persistence."""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional


class IdentityRepository:
    """Own tenant/workspace/brand/account/platform-account persistence."""

    def __init__(self, database: Any = None) -> None:
        if database is None:
            from layers.layer13_persistence.modules.postgresql.manager import get_database
            database = get_database()
        self._database = database
        self._pool = getattr(database, "_pool", None)
        if self._pool is None or not getattr(database, "_postgresql_available", False):
            raise RuntimeError("IdentityRepository requires canonical PostgreSQL")

    @staticmethod
    def _json(value: Any, default: Any) -> str:
        return json.dumps(value if value is not None else default, sort_keys=True, separators=(",", ":"), default=str)

    def upsert(self, spec: Dict[str, Any]) -> None:
        tenant_id = str(spec["tenant_id"]).strip()
        workspace_id = str(spec["workspace_id"]).strip()
        brand_id = str(spec["brand_id"]).strip()
        account_id = str(spec["account_id"]).strip()
        platform = str(spec["platform"]).strip().lower()
        platform_account_id = str(spec["platform_account_id"]).strip()
        if not all((tenant_id, workspace_id, brand_id, account_id, platform, platform_account_id)):
            raise ValueError("tenant_id, workspace_id, brand_id, account_id, platform and platform_account_id are required")
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO tenants(tenant_id,name) VALUES (%s,%s)
                ON CONFLICT (tenant_id) DO UPDATE SET name=EXCLUDED.name,updated_at=CURRENT_TIMESTAMP
                """,
                (tenant_id, str(spec.get("tenant_name") or tenant_id)),
            )
            cur.execute(
                """
                INSERT INTO workspaces(workspace_id,tenant_id,name) VALUES (%s,%s,%s)
                ON CONFLICT (workspace_id) DO UPDATE SET
                  tenant_id=EXCLUDED.tenant_id,name=EXCLUDED.name,updated_at=CURRENT_TIMESTAMP
                """,
                (workspace_id, tenant_id, str(spec.get("workspace_name") or workspace_id)),
            )
            cur.execute(
                """
                INSERT INTO brands(brand_id,workspace_id,name) VALUES (%s,%s,%s)
                ON CONFLICT (brand_id) DO UPDATE SET
                  workspace_id=EXCLUDED.workspace_id,name=EXCLUDED.name,updated_at=CURRENT_TIMESTAMP
                """,
                (brand_id, workspace_id, str(spec.get("brand_name") or brand_id)),
            )
            cur.execute(
                """
                INSERT INTO accounts(
                  account_id,brand_id,platform,niche,display_name,audience,credentials_ref,
                  affiliate_rules,capabilities,constraints,enabled
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb,%s::jsonb,%s)
                ON CONFLICT (account_id) DO UPDATE SET
                  brand_id=EXCLUDED.brand_id,platform=EXCLUDED.platform,niche=EXCLUDED.niche,
                  display_name=EXCLUDED.display_name,audience=EXCLUDED.audience,
                  credentials_ref=EXCLUDED.credentials_ref,affiliate_rules=EXCLUDED.affiliate_rules,
                  capabilities=EXCLUDED.capabilities,constraints=EXCLUDED.constraints,
                  enabled=EXCLUDED.enabled,updated_at=CURRENT_TIMESTAMP
                """,
                (
                    account_id, brand_id, platform, str(spec["niche"]).strip(),
                    str(spec.get("display_name") or ""),
                    str(spec.get("audience") or ""),
                    str(spec.get("credentials_ref") or ""),
                    self._json(spec.get("affiliate_rules"), {}),
                    self._json(spec.get("capabilities"), []),
                    self._json(spec.get("constraints"), {}),
                    bool(spec.get("enabled", True)),
                ),
            )
            cur.execute(
                """
                INSERT INTO platform_accounts(
                  platform_account_id,account_id,platform,external_account_id,display_name,enabled
                ) VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (platform_account_id) DO UPDATE SET
                  account_id=EXCLUDED.account_id,platform=EXCLUDED.platform,
                  external_account_id=EXCLUDED.external_account_id,
                  display_name=EXCLUDED.display_name,enabled=EXCLUDED.enabled,
                  updated_at=CURRENT_TIMESTAMP
                """,
                (
                    platform_account_id,
                    account_id,
                    platform,
                    str(spec.get("external_account_id") or platform_account_id),
                    str(spec.get("platform_account_name") or spec.get("display_name") or ""),
                    bool(spec.get("enabled", True)),
                ),
            )

    def get(self, account_id: str) -> Optional[Dict[str, Any]]:
        return self._pool.query_one(
            """
            SELECT a.account_id,a.platform,a.niche,a.display_name,a.audience,a.credentials_ref,
                   a.affiliate_rules,a.capabilities,a.constraints,a.enabled,
                   b.brand_id,w.workspace_id,t.tenant_id,
                   pa.platform_account_id,pa.external_account_id,pa.display_name AS platform_account_name,
                   pa.enabled AS platform_account_enabled
            FROM accounts a
            JOIN brands b ON b.brand_id=a.brand_id
            JOIN workspaces w ON w.workspace_id=b.workspace_id
            JOIN tenants t ON t.tenant_id=w.tenant_id
            JOIN platform_accounts pa ON pa.account_id=a.account_id AND pa.platform=a.platform
            WHERE a.account_id=%s
            LIMIT 1
            """,
            (account_id,),
        )

    def list(self, platform: Optional[str] = None, enabled_only: bool = True) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if platform:
            clauses.append("a.platform=%s")
            params.append(str(platform).strip().lower())
        if enabled_only:
            clauses.extend(["a.enabled=TRUE", "pa.enabled=TRUE"])
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return self._pool.query(
            f"""
            SELECT a.account_id,a.platform,a.niche,a.display_name,a.audience,a.credentials_ref,
                   a.affiliate_rules,a.capabilities,a.constraints,a.enabled,
                   b.brand_id,w.workspace_id,t.tenant_id,
                   pa.platform_account_id,pa.external_account_id,pa.display_name AS platform_account_name,
                   pa.enabled AS platform_account_enabled
            FROM accounts a
            JOIN brands b ON b.brand_id=a.brand_id
            JOIN workspaces w ON w.workspace_id=b.workspace_id
            JOIN tenants t ON t.tenant_id=w.tenant_id
            JOIN platform_accounts pa ON pa.account_id=a.account_id AND pa.platform=a.platform
            {where}
            ORDER BY a.account_id
            """,
            tuple(params),
        )

    def disable(self, account_id: str) -> bool:
        with self._pool.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE accounts SET enabled=FALSE,updated_at=CURRENT_TIMESTAMP WHERE account_id=%s",
                (account_id,),
            )
            changed = cur.rowcount == 1
            cur.execute(
                "UPDATE platform_accounts SET enabled=FALSE,updated_at=CURRENT_TIMESTAMP WHERE account_id=%s",
                (account_id,),
            )
            return changed
