"""Shared SQL identifier validation contract for persistence adapters."""
import pytest

from layers.layer01_core.modules.database_manager import DatabaseManager
from layers.layer13_persistence.modules.postgresql.connection.pool import ConnectionPool as PostgresConnectionPool


@pytest.mark.parametrize("adapter", [DatabaseManager, PostgresConnectionPool])
def test_identifier_mixin_accepts_safe_identifiers(adapter):
    assert adapter._identifier("tenant_id") == "tenant_id"
    assert adapter._identifier("_internal_7") == "_internal_7"


@pytest.mark.parametrize("adapter", [DatabaseManager, PostgresConnectionPool])
@pytest.mark.parametrize("value", ["tenant-id", "tenant id", "tenant;DROP TABLE users", "1tenant", ""])
def test_identifier_mixin_rejects_unsafe_identifiers(adapter, value):
    with pytest.raises(ValueError, match="unsafe SQL identifier"):
        adapter._identifier(value)
