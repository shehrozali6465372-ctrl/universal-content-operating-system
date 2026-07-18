"""backup_validator.py — Backup validation."""
from __future__ import annotations
from typing import Any, Dict, List


class BackupValidator:
    """Validates backup integrity."""

    def __init__(self) -> None:
        self._validations: List[Dict[str, Any]] = []

    def validate(self, backup_id: int, expected_size: int,
                 actual_size: int, checksum_match: bool = True) -> Dict[str, Any]:
        result = {"backup_id": backup_id, "size_match": expected_size == actual_size,
                  "checksum_match": checksum_match,
                  "valid": expected_size == actual_size and checksum_match}
        self._validations.append(result)
        return result

    def get_validations(self) -> List[Dict[str, Any]]:
        return list(self._validations)

    def stats(self) -> Dict[str, Any]:
        valid = sum(1 for v in self._validations if v["valid"])
        return {"total": len(self._validations), "valid": valid}
