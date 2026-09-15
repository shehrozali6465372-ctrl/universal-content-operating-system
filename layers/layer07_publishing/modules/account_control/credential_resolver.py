"""Account credential reference resolver; never falls back across accounts."""
from __future__ import annotations
import json, os, re
from pathlib import Path
from typing import Dict

class AccountCredentialResolver:
    @staticmethod
    def resolve(credentials_ref: str) -> Dict[str,str]:
        ref=(credentials_ref or "").strip()
        if not ref: return {}
        keys=[ref,f"UCOS_CREDENTIALS_{re.sub(r'[^A-Za-z0-9_]', '_', ref).upper()}"]
        for key in keys:
            raw=os.environ.get(key,"").strip()
            if raw:
                try:
                    value=json.loads(raw)
                    if isinstance(value,dict): return {str(k):str(v) for k,v in value.items()}
                except json.JSONDecodeError: pass
        path=Path(ref)
        if path.is_file():
            try:
                value=json.loads(path.read_text(encoding="utf-8")); return {str(k):str(v) for k,v in value.items()} if isinstance(value,dict) else {}
            except (OSError,json.JSONDecodeError): return {}
        return {}
