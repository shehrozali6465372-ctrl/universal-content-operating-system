"""ConfigLoader — load config from environment, files, or defaults."""
from __future__ import annotations
import os
import json
from typing import Any, Dict

class ConfigLoader:
    def __init__(self, env_prefix: str = 'AIOS_') -> None:
        self.env_prefix = env_prefix

    def from_env(self) -> Dict[str, Any]:
        config: Dict[str, Any] = {}
        for key, value in os.environ.items():
            if key.startswith(self.env_prefix):
                config_key = key[len(self.env_prefix):].lower()
                # Try to parse as number
                try: config[config_key] = int(value)
                except ValueError:
                    try: config[config_key] = float(value)
                    except ValueError:
                        if value.lower() in ('true', 'false'):
                            config[config_key] = value.lower() == 'true'
                        else:
                            config[config_key] = value
        return config

    def from_file(self, path: str) -> Dict[str, Any]:
        try:
            with open(path) as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def merge(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        merged: Dict[str, Any] = {}
        for cfg in configs:
            merged.update(cfg)
        return merged
