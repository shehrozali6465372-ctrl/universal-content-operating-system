"""OutputSanitizer — sanitize outputs before returning to users."""
from __future__ import annotations
import re
from typing import Any, Dict, List, Optional


class OutputSanitizer:
    def __init__(self) -> None:
        self._patterns: Dict[str, str] = {
            "html_tags": r'<[^>]+>',
            "script_tags": r'<script[^>]*>.*?</script>',
            "sql_injection": r"(--|;|'|\"|\\|\/\*|\*/|UNION|SELECT|INSERT|UPDATE|DELETE|DROP)",
            "xss_events": r'on\w+\s*=',
        }

    def sanitize_html(self, text: str) -> str:
        text = re.sub(self._patterns["html_tags"], '', text)
        text = re.sub(self._patterns["script_tags"], '', text, flags=re.IGNORECASE)
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return text

    def sanitize_sql(self, text: str) -> str:
        for char in ["'", '"', ";", "--"]:
            text = text.replace(char, "")
        return text

    def sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.sanitize_html(value)
            elif isinstance(value, dict):
                result[key] = self.sanitize_dict(value)
            elif isinstance(value, list):
                result[key] = [self.sanitize_html(v) if isinstance(v, str) else v for v in value]
            else:
                result[key] = value
        return result

    def strip_null_bytes(self, text: str) -> str:
        return text.replace("\x00", "")

    def limit_length(self, text: str, max_length: int = 10000) -> str:
        return text[:max_length]
