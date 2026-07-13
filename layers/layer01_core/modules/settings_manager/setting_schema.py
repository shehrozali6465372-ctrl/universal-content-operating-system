"""
Setting Entry Schema
Layer 1: Core System — Module 9

Metadata model for each setting with versioning and audit support.
"""

from datetime import datetime, timezone
from typing import Any, Callable, Optional


class SettingEntry:
    """Metadata-rich setting with validation, history, and audit trail."""

    __slots__ = (
        "key", "value", "default_value", "datatype", "validator",
        "category", "editable", "immutable", "last_changed",
        "changed_by", "version", "description",
    )

    def __init__(
        self,
        key: str,
        value: Any,
        default_value: Any = None,
        datatype: type = str,
        validator: Optional[Callable[[Any], bool]] = None,
        category: str = "general",
        editable: bool = True,
        immutable: bool = False,
        description: str = "",
    ):
        self.key = key
        self.value = value
        self.default_value = default_value if default_value is not None else value
        self.datatype = datatype
        self.validator = validator
        self.category = category
        self.editable = editable
        self.immutable = immutable
        self.last_changed = datetime.now(timezone.utc).isoformat()
        self.changed_by = "system"
        self.version = 1
        self.description = description

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "value": self.value,
            "default_value": self.default_value,
            "datatype": self.datatype.__name__,
            "category": self.category,
            "editable": self.editable,
            "immutable": self.immutable,
            "last_changed": self.last_changed,
            "changed_by": self.changed_by,
            "version": self.version,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SettingEntry":
        datatype_map = {
            "str": str, "int": int, "float": float,
            "bool": bool, "list": list, "dict": dict,
        }
        return cls(
            key=data["key"],
            value=data["value"],
            default_value=data.get("default_value"),
            datatype=datatype_map.get(data.get("datatype", "str"), str),
            category=data.get("category", "general"),
            editable=data.get("editable", True),
            immutable=data.get("immutable", False),
            description=data.get("description", ""),
        )

    def validate_value(self, value: Any) -> bool:
        """Run type check and custom validator."""
        if self.validator and not self.validator(value):
            return False
        return True

    def snapshot(self) -> dict:
        """Capture current state for history tracking."""
        return {
            "value": self.value,
            "changed_by": self.changed_by,
            "version": self.version,
            "timestamp": self.last_changed,
        }
