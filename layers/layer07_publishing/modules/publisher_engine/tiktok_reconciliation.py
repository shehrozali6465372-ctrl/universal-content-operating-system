"""Reconcile asynchronous TikTok Direct Post submissions without false success."""
from __future__ import annotations
from typing import Any, Dict, Optional

from .content_repetition_guard import ContentRepetitionGuard


class TikTokReconciliation:
    """Poll TikTok status and finalize/release account-local reservations."""

    FINAL_SUCCESS = "PUBLISH_COMPLETE"
    FINAL_FAILURE = "FAILED"

    def __init__(self, guard: ContentRepetitionGuard) -> None:
        self.guard = guard

    @staticmethod
    def _post_id(status_payload: Dict[str, Any]) -> Optional[str]:
        data = status_payload.get("data") or {}
        ids = data.get("publicaly_available_post_id") or []
        if not isinstance(ids, list):
            ids = [ids]
        for value in ids:
            if value is not None and str(value).strip():
                return str(value)
        return None

    def reconcile(self, publisher: Any, *, account_id: Optional[str] = None) -> list[Dict[str, Any]]:
        outcomes: list[Dict[str, Any]] = []
        for item in self.guard.pending(account_id):
            reservation_id = int(item["reservation_id"])
            tracking_id = str(item["tracking_id"] or "")
            if not tracking_id:
                continue
            try:
                payload = publisher.get_post(tracking_id) or {}
                data = payload.get("data") or {}
                status = str(data.get("status") or "unknown").upper()
                if status == self.FINAL_FAILURE:
                    self.guard.release(reservation_id)
                    outcomes.append({"reservation_id": reservation_id, "account_id": item["account_id"], "tracking_id": tracking_id, "status": status, "released": True, "post_id": None, "reason": data.get("fail_reason") or "platform_failed"})
                    continue
                post_id = self._post_id(payload)
                if status == self.FINAL_SUCCESS and post_id:
                    self.guard.finalize(reservation_id, post_id)
                    outcomes.append({"reservation_id": reservation_id, "account_id": item["account_id"], "tracking_id": tracking_id, "status": status, "released": False, "published": True, "post_id": post_id})
                else:
                    outcomes.append({"reservation_id": reservation_id, "account_id": item["account_id"], "tracking_id": tracking_id, "status": status, "released": False, "published": False, "post_id": None, "reason": "awaiting_final_public_post_id"})
            except Exception as exc:
                # Network/API errors are not proof of failure. Keep the pending
                # reservation so retry cannot create a duplicate.
                outcomes.append({"reservation_id": reservation_id, "account_id": item["account_id"], "tracking_id": tracking_id, "status": "UNKNOWN", "released": False, "published": False, "post_id": None, "error": str(exc)})
        return outcomes
