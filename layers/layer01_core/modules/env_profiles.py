"""
Environment Profiles
Layer 1: Core System — Module 3 Support

Defines profiles for dev, test, and production environments.
Each profile sets defaults for its environment.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class EnvProfile:
    """Single environment profile definition."""
    name: str
    description: str
    defaults: Dict[str, str] = field(default_factory=dict)
    required_vars: list = field(default_factory=list)


# ──────────────────────────────────────────────
# ENVIRONMENT PROFILES
# ──────────────────────────────────────────────

DEV_PROFILE = EnvProfile(
    name="development",
    description="Local development environment",
    defaults={
        "LOG_LEVEL": "DEBUG",
        "DEBUG": "true",
        "DATABASE_PATH": "data/dev.db",
        "AI_MODEL": "gpt-3.5-turbo",
        "AI_TEMPERATURE": "0.9",
        "MAX_POSTS_PER_DAY": "2",
        "BACKUP_ENABLED": "false",
    },
    required_vars=[
        "OPENAI_API_KEY",
    ],
)

TEST_PROFILE = EnvProfile(
    name="testing",
    description="Automated testing environment",
    defaults={
        "LOG_LEVEL": "WARNING",
        "DEBUG": "false",
        "DATABASE_PATH": "data/test.db",
        "AI_MODEL": "gpt-3.5-turbo",
        "AI_TEMPERATURE": "0.0",
        "MAX_POSTS_PER_DAY": "0",
        "BACKUP_ENABLED": "false",
    },
    required_vars=[
        "OPENAI_API_KEY",
    ],
)

PROD_PROFILE = EnvProfile(
    name="production",
    description="Live production environment",
    defaults={
        "LOG_LEVEL": "INFO",
        "DEBUG": "false",
        "DATABASE_PATH": "data/prod.db",
        "AI_MODEL": "gpt-4",
        "AI_TEMPERATURE": "0.7",
        "MAX_POSTS_PER_DAY": "5",
        "BACKUP_ENABLED": "true",
    },
    required_vars=[
        "OPENAI_API_KEY",
        "FACEBOOK_PAGE_ID",
        "FACEBOOK_ACCESS_TOKEN",
    ],
)


# ──────────────────────────────────────────────
# PROFILE REGISTRY
# ──────────────────────────────────────────────

PROFILES: Dict[str, EnvProfile] = {
    "dev": DEV_PROFILE,
    "development": DEV_PROFILE,
    "test": TEST_PROFILE,
    "testing": TEST_PROFILE,
    "prod": PROD_PROFILE,
    "production": PROD_PROFILE,
}


def get_profile(name: str) -> Optional[EnvProfile]:
    """Get environment profile by name."""
    return PROFILES.get(name.lower().strip())


def get_available_profiles() -> list:
    """Return list of unique profile names."""
    seen = set()
    result = []
    for key, profile in PROFILES.items():
        if profile.name not in seen:
            seen.add(profile.name)
            result.append(profile.name)
    return result
