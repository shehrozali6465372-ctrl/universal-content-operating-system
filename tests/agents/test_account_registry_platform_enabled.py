"""Production identity mapper regression tests for account-level enablement."""
from __future__ import annotations

from layers.layer07_publishing.modules.account_control.account_registry import AccountRegistry


def row(**overrides):
    value = {
        "account_id": "account-a",
        "platform": "pinterest",
        "niche": "home decor",
        "display_name": "Account A",
        "audience": "",
        "credentials_ref": "pinterest-account-a",
        "affiliate_rules": {},
        "capabilities": [],
        "constraints": {},
        "enabled": True,
        "tenant_id": "tenant-a",
        "workspace_id": "workspace-a",
        "brand_id": "brand-a",
        "platform_account_id": "pa-a",
        "external_account_id": "external-a",
        "platform_account_name": "Account A",
        "platform_account_enabled": True,
    }
    value.update(overrides)
    return value


def test_disabled_platform_account_is_not_dispatchable_even_when_parent_is_enabled():
    account = AccountRegistry._from_row(row(enabled=True, platform_account_enabled=False))
    assert account.enabled is False


def test_enabled_platform_account_remains_enabled_when_parent_is_enabled():
    account = AccountRegistry._from_row(row(enabled=True, platform_account_enabled=True))
    assert account.enabled is True


def test_legacy_registry_row_without_platform_flag_preserves_parent_state():
    legacy = row()
    legacy.pop("platform_account_enabled")
    assert AccountRegistry._from_row(legacy).enabled is True
