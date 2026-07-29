"""CommissionTracker — Track earned, pending, approved, rejected, paid commissions."""
from __future__ import annotations
import time, threading
from typing import Any, Dict, List, Optional
from layers.layer23_website_manager.revenue_manager.models.revenue_models import CommissionRecord, TransactionStatus


class CommissionTracker:
    def __init__(self):
        self._commissions: Dict[str, CommissionRecord] = {}
        self._lock = threading.Lock()

    def record_commission(self, source_id: str, amount: float, sale_amount: float, rate: float,
                           product_id: str = "", article_id: str = "") -> CommissionRecord:
        c = CommissionRecord(source_id=source_id, amount=amount, sale_amount=sale_amount, rate=rate,
                              product_id=product_id, article_id=article_id, status=TransactionStatus.PENDING)
        with self._lock: self._commissions[c.commission_id] = c
        return c

    def approve(self, commission_id: str) -> bool:
        c = self._commissions.get(commission_id)
        if not c: return False
        with self._lock: c.status = TransactionStatus.APPROVED; return True

    def mark_paid(self, commission_id: str) -> bool:
        c = self._commissions.get(commission_id)
        if not c: return False
        with self._lock: c.status = TransactionStatus.PAID; c.paid_date = time.time(); return True

    def reject(self, commission_id: str) -> bool:
        c = self._commissions.get(commission_id)
        if not c: return False
        with self._lock: c.status = TransactionStatus.REJECTED; return True

    def get_summary(self) -> Dict[str, Any]:
        all_c = list(self._commissions.values())
        return {"total": len(all_c), "pending": sum(1 for c in all_c if c.status == TransactionStatus.PENDING),
                "approved": sum(1 for c in all_c if c.status == TransactionStatus.APPROVED),
                "paid": sum(1 for c in all_c if c.status == TransactionStatus.PAID),
                "rejected": sum(1 for c in all_c if c.status == TransactionStatus.REJECTED),
                "total_amount": round(sum(c.amount for c in all_c), 2)}

    def get_stats(self) -> Dict: return self.get_summary()
