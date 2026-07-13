"""
Custom Exceptions for Config Manager Module
Layer 1: Core System
"""


class ConfigError(Exception):
    """Base exception for all config errors."""
    pass


class ConfigNotFound(ConfigError):
    """Config file (.env or .yaml) not found."""
    def __init__(self, filepath: str):
        self.filepath = filepath
        super().__init__(f"Config file not found: {filepath}")


class InvalidConfig(ConfigError):
    """Config value is invalid."""
    def __init__(self, key: str, reason: str):
        self.key = key
        self.reason = reason
        super().__init__(f"Invalid config '{key}': {reason}")


class MissingAPIKey(ConfigError):
    """Required API key is missing."""
    def __init__(self, key_name: str):
        self.key_name = key_name
        super().__init__(f"Missing required API key: {key_name}")


class InvalidPath(ConfigError):
    """File or directory path is invalid."""
    def __init__(self, path: str, reason: str = "Path does not exist"):
        self.path = path
        self.reason = reason
        super().__init__(f"Invalid path '{path}': {reason}")


class SchemaError(ConfigError):
    """Schema validation failed."""
    def __init__(self, errors: list):
        self.errors = errors
        msg = f"Schema validation failed with {len(errors)} error(s):\n"
        msg += "\n".join(f"  - {e}" for e in errors)
        super().__init__(msg)
