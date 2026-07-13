"""
Config Schema Definition
Layer 1: Core System

Defines required and optional configuration keys
with their types, defaults, and validation rules.
"""

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConfigField:
    """Single configuration field definition."""
    key: str
    required: bool = False
    default: Any = None
    field_type: str = "str"
    description: str = ""
    validator: Optional[str] = None


# ──────────────────────────────────────────────
# REQUIRED SETTINGS (must be provided)
# ──────────────────────────────────────────────
REQUIRED_FIELDS = [
    ConfigField(
        key="OPENAI_API_KEY",
        required=True,
        field_type="str",
        description="OpenAI API key (starts with sk-)",
        validator="api_key",
    ),
    ConfigField(
        key="FACEBOOK_PAGE_ID",
        required=True,
        field_type="str",
        description="Facebook Page ID for publishing",
        validator="not_empty",
    ),
    ConfigField(
        key="FACEBOOK_ACCESS_TOKEN",
        required=True,
        field_type="str",
        description="Facebook Graph API access token",
        validator="not_empty",
    ),
]

# ──────────────────────────────────────────────
# OPTIONAL SETTINGS (defaults provided)
# ──────────────────────────────────────────────
OPTIONAL_FIELDS = [
    ConfigField(
        key="LOG_LEVEL",
        required=False,
        default="INFO",
        field_type="str",
        description="Logging level: DEBUG, INFO, WARNING, ERROR",
        validator="log_level",
    ),
    ConfigField(
        key="DATABASE_PATH",
        required=False,
        default="data/agent.db",
        field_type="str",
        description="SQLite database file path",
        validator="path",
    ),
    ConfigField(
        key="DEBUG",
        required=False,
        default=False,
        field_type="bool",
        description="Enable debug mode",
        validator="bool",
    ),
    ConfigField(
        key="MAX_POSTS_PER_DAY",
        required=False,
        default=5,
        field_type="int",
        description="Maximum Facebook posts per day",
        validator="number",
    ),
    ConfigField(
        key="AI_MODEL",
        required=False,
        default="gpt-4",
        field_type="str",
        description="AI model to use for content generation",
        validator="not_empty",
    ),
    ConfigField(
        key="AI_TEMPERATURE",
        required=False,
        default=0.7,
        field_type="float",
        description="AI temperature (0.0 - 1.0)",
        validator="number",
    ),
    ConfigField(
        key="MEMORY_MAX_SIZE",
        required=False,
        default=1000,
        field_type="int",
        description="Maximum memory entries to keep",
        validator="number",
    ),
    ConfigField(
        key="CONTENT_LANGUAGES",
        required=False,
        default="en,ur",
        field_type="str",
        description="Comma-separated content languages",
        validator="not_empty",
    ),
    ConfigField(
        key="BACKUP_ENABLED",
        required=False,
        default=True,
        field_type="bool",
        description="Enable automatic data backups",
        validator="bool",
    ),
    ConfigField(
        key="SCHEDULER_INTERVAL_MINUTES",
        required=False,
        default=60,
        field_type="int",
        description="Minutes between scheduled tasks",
        validator="number",
    ),
]


def get_all_fields() -> list:
    """Return all config fields combined."""
    return REQUIRED_FIELDS + OPTIONAL_FIELDS


def get_required_keys() -> list:
    """Return list of required config key names."""
    return [f.key for f in REQUIRED_FIELDS]


def get_optional_keys() -> list:
    """Return list of optional config key names."""
    return [f.key for f in OPTIONAL_FIELDS]


def get_defaults() -> dict:
    """Return dict of optional keys to their default values."""
    return {f.key: f.default for f in OPTIONAL_FIELDS}


def get_field(key: str) -> Optional[ConfigField]:
    """Get field definition by key name."""
    for field_def in get_all_fields():
        if field_def.key == key:
            return field_def
    return None
