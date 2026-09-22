"""Hostinger Referral Program integration boundary.

The referral URL is a real user-supplied asset. Hostinger referral performance
is authoritative only when observed from the Hostinger dashboard; this module
never invents clicks, referrals, commission, or payout values.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional
from urllib.parse import parse_qs, urlsplit


@dataclass(frozen=True)
class HostingerReferral:
    program_id: str
    referral_url: str
    referral_code: str
    status: str
    metrics: Mapping[str, Any]

    @property
    def has_live_metrics(self) -> bool:
        return any(value is not None for value in self.metrics.values())


def load_hostinger_referral(path: Optional[str] = None) -> HostingerReferral:
    """Load the committed real-link record without fabricating performance data."""
    record_path = Path(path) if path else (
        Path(__file__).resolve().parents[4] / "data" / "affiliate" / "hostinger_referral.json"
    )
    data = json.loads(record_path.read_text(encoding="utf-8"))
    return normalize_hostinger_referral(data)


def normalize_hostinger_referral(data: Mapping[str, Any]) -> HostingerReferral:
    url = str(data.get("referral_url") or "").strip()
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname != "www.hostinger.com":
        raise ValueError("Hostinger referral URL must be an HTTPS www.hostinger.com URL")

    query = parse_qs(parts.query)
    code = str(data.get("referral_code") or "").strip()
    url_code = (query.get("REFERRALCODE") or [""])[0]
    if not code or code != url_code:
        raise ValueError("referral_code must match the REFERRALCODE URL parameter")

    metrics = dict(data.get("metrics") or {})
    return HostingerReferral(
        program_id=str(data.get("program_id") or "hostinger_referral"),
        referral_url=url,
        referral_code=code,
        status=str(data.get("status") or "integration_ready"),
        metrics=metrics,
    )


def ingest_dashboard_rows(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Normalize observed Hostinger dashboard rows.

    Expected fields are intentionally generic because Hostinger dashboard
    exports/interfaces can change. Missing values remain unknown.
    """
    normalized = []
    for row in rows:
        normalized.append({
            "status": row.get("status"),
            "purchase_date": row.get("purchase_date"),
            "commission": row.get("commission"),
            "currency": row.get("currency"),
            "source": "hostinger_dashboard",
        })

    counts = {"pending": 0, "qualified": 0, "approved": 0, "declined": 0}
    commission_total: Optional[float] = 0.0
    saw_commission = False

    for row in normalized:
        status = str(row.get("status") or "").lower()
        if status in counts:
            counts[status] += 1
        value = row.get("commission")
        if value is not None:
            saw_commission = True
            try:
                commission_total += float(value)
            except (TypeError, ValueError):
                commission_total = None

    return {
        "source": "hostinger_dashboard",
        "referrals": len(normalized),
        "status_counts": counts,
        "commission_total": commission_total if saw_commission else None,
        "rows": normalized,
    }
