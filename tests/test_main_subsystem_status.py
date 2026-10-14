"""CLI status output must not claim health without a live probe."""
import pytest

from main import subsystem_status


def test_subsystem_status_does_not_claim_unverified_service_is_available():
    result = subsystem_status("Database")
    assert result["subsystem"] == "database"
    assert result["status"] == "unverified"
    assert result["verified"] is False
    assert "not been verified" in result["note"]


def test_subsystem_status_rejects_empty_name():
    with pytest.raises(ValueError, match="subsystem name"):
        subsystem_status("   ")
