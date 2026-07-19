"""ConfigValidator — validate all layer configurations."""
from __future__ import annotations
from typing import Any, Dict, List

class ConfigValidator:
    SCHEMAS: Dict[str, Dict[str, tuple]] = {
        'layer12': {
            'daily_budget': (float, int), 'enable_retry': (bool,),
            'max_concurrent': (int,), 'timeout_seconds': (float, int),
            'min_quality_score': (float, int), 'min_accuracy': (float, int),
        },
        'layer13': {
            'max_pool_size': (int,), 'vector_dimensions': (int,),
            'cache_ttl': (int,), 'backup_retention_days': (int,),
        }
    }

    def __init__(self) -> None:
        self._errors: List[str] = []

    def validate(self, layer: str, config: Dict[str, Any]) -> Dict[str, Any]:
        schema = self.SCHEMAS.get(layer, {})
        errors: List[str] = []
        for key, expected_types in schema.items():
            if key in config:
                if not isinstance(config[key], expected_types):
                    errors.append(f'{key}: expected {expected_types}, got {type(config[key]).__name__}')
        self._errors.extend(errors)
        return {'valid': len(errors) == 0, 'errors': errors, 'layer': layer}

    def validate_all(self, configs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        all_errors: Dict[str, List[str]] = {}
        for layer, config in configs.items():
            result = self.validate(layer, config)
            if not result['valid']:
                all_errors[layer] = result['errors']
        return {'valid': len(all_errors) == 0, 'layer_errors': all_errors}

    def get_errors(self) -> List[str]:
        return list(self._errors)

    def clear(self) -> None:
        self._errors.clear()
