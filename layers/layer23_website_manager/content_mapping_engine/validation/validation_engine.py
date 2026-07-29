"""ValidationEngine — AI validation of complete mapping before publishing."""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.content_mapping_engine.exceptions import ValidationError


# Required fields for a valid mapping
REQUIRED_FIELDS = [
    "website_id", "website_url",
    "account_id", "board_id",
    "pin_strategy",
    "seo_keywords",
    "featured_image",
]

# Validation rules per field
VALIDATION_RULES: Dict[str, Dict[str, Any]] = {
    "website_id": {"required": True, "min_length": 3, "score_weight": 15},
    "website_url": {"required": True, "pattern": "http", "score_weight": 10},
    "account_id": {"required": True, "min_length": 3, "score_weight": 15},
    "board_id": {"required": True, "min_length": 3, "score_weight": 15},
    "pin_strategy": {"required": True, "score_weight": 10},
    "seo_keywords": {"required": True, "min_items": 3, "score_weight": 10},
    "featured_image": {"required": False, "score_weight": 5},
    "affiliate_url": {"required": False, "pattern": "http", "score_weight": 5},
    "validation_score": {"required": False, "min_value": 50, "score_weight": 5},
}


class ValidationEngine:
    """Validate entire content mapping for completeness and correctness."""

    def __init__(self) -> None:
        self._validation_log: List[dict] = []
        self._total_validated = 0

    def validate_mapping(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """Run all validations on a content mapping."""
        issues: List[str] = []
        warnings: List[str] = []
        score = 100.0

        # Check required fields
        for field, rules in VALIDATION_RULES.items():
            value = mapping.get(field)
            if rules["required"] and (value is None or value == ""):
                issues.append(f"Missing required field: {field}")
                score -= rules["score_weight"]
            elif value:
                # Length check
                min_len = rules.get("min_length")
                if min_len and isinstance(value, str) and len(value) < min_len:
                    issues.append(f"{field} too short ({len(value)} < {min_len})")
                    score -= rules["score_weight"] * 0.5

                # Pattern check
                pattern = rules.get("pattern")
                if pattern and isinstance(value, str) and pattern not in value:
                    issues.append(f"{field} missing required pattern: {pattern}")
                    score -= rules["score_weight"] * 0.5

                # Items check for lists
                min_items = rules.get("min_items")
                if min_items and isinstance(value, list) and len(value) < min_items:
                    issues.append(f"{field} has fewer than {min_items} items ({len(value)})")
                    score -= rules["score_weight"] * 0.5

        # Check that account and board match
        self._validate_relationships(mapping, issues, warnings)

        # Validation score consistency
        mapping_score = mapping.get("validation_score", 0)
        if mapping_score < 30:
            warnings.append(f"Low AI validation score: {mapping_score}")

        score = max(0, score)

        result = {
            "is_valid": len(issues) == 0,
            "validation_score": round(score, 1),
            "status": "passed" if score >= 70 else "failed" if score < 40 else "review",
            "issues": issues,
            "warnings": warnings,
            "issue_count": len(issues),
        }

        self._validation_log.append(result)
        self._total_validated += 1
        return result

    def _validate_relationships(self, mapping: Dict[str, Any],
                                 issues: List[str], warnings: List[str]) -> None:
        """Validate that related fields are consistent."""
        # Account and board consistency
        if mapping.get("account_id") and mapping.get("board_id"):
            acc = str(mapping["account_id"])
            board = str(mapping["board_id"])
            if not board.startswith(acc.replace("pinterest_", "board_")):
                warnings.append(f"Board {board} may not belong to account {acc}")

    def get_stats(self) -> Dict[str, Any]:
        return {"total_validated": self._total_validated}
