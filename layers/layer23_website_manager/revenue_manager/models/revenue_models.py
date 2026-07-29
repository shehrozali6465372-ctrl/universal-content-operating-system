from __future__ import annotations
import time, uuid
from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

class TransactionStatus(str, Enum):
    PENDING = "pending"; APPROVED = "approved"; PAID = "paid"; REJECTED = "rejected"
class RevenuePeriod(str, Enum):
    DAILY = "daily"; WEEKLY = "weekly"; MONTHLY = "monthly"; YEARLY = "yearly"
class AlertSeverity(str, Enum):
    INFO = "info"; WARNING = "warning"; CRITICAL = "critical"

@dataclass
class RevenueSource:
    source_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""; network: str = ""; commission_rate: float = 0.0
    total_revenue: float = 0.0; total_commission: float = 0.0; transaction_count: int = 0
    status: str = "active"; created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict: return {"source_id": self.source_id, "name": self.name, "total_revenue": round(self.total_revenue, 2), "total_commission": round(self.total_commission, 2), "transactions": self.transaction_count, "status": self.status}

@dataclass
class CommissionRecord:
    commission_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source_id: str = ""; product_id: str = ""; article_id: str = ""
    amount: float = 0.0; sale_amount: float = 0.0; rate: float = 0.0
    status: TransactionStatus = TransactionStatus.PENDING
    earned_date: float = field(default_factory=time.time)
    paid_date: float = 0.0
    def to_dict(self) -> Dict: return {"commission_id": self.commission_id, "amount": round(self.amount, 2), "sale_amount": round(self.sale_amount, 2), "status": self.status.value}

@dataclass
class RevenueTransaction:
    transaction_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    source_id: str = ""; merchant: str = ""; product_id: str = ""
    article_id: str = ""; pin_id: str = ""; visitor_id: str = ""
    sale_amount: float = 0.0; commission: float = 0.0; fee: float = 0.0
    status: TransactionStatus = TransactionStatus.PENDING
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict: return {"transaction_id": self.transaction_id, "sale_amount": round(self.sale_amount, 2), "commission": round(self.commission, 2), "status": self.status.value, "merchant": self.merchant}

@dataclass
class RevenueSummary:
    summary_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    period: RevenuePeriod = RevenuePeriod.DAILY
    date: float = field(default_factory=time.time)
    gross_revenue: float = 0.0; total_commission: float = 0.0
    expenses: float = 0.0; net_profit: float = 0.0; roi: float = 0.0
    growth_rate: float = 0.0; transaction_count: int = 0
    def to_dict(self) -> Dict: return {"period": self.period.value, "gross_revenue": round(self.gross_revenue, 2), "total_commission": round(self.total_commission, 2), "expenses": round(self.expenses, 2), "net_profit": round(self.net_profit, 2), "roi": round(self.roi, 1), "growth": round(self.growth_rate, 1)}

@dataclass
class Budget:
    budget_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    category: str = ""; name: str = ""; allocated: float = 0.0; spent: float = 0.0
    period: RevenuePeriod = RevenuePeriod.MONTHLY
    created_at: float = field(default_factory=time.time)
    @property
    def remaining(self) -> float: return max(self.allocated - self.spent, 0)
    @property
    def usage_pct(self) -> float: return round((self.spent / max(self.allocated, 1)) * 100, 1)
    def to_dict(self) -> Dict: return {"category": self.category, "name": self.name, "allocated": self.allocated, "spent": self.spent, "remaining": self.remaining, "usage": self.usage_pct}

@dataclass
class RevenueForecast:
    forecast_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    period: RevenuePeriod = RevenuePeriod.MONTHLY
    predicted_revenue: float = 0.0; predicted_commission: float = 0.0
    confidence: float = 0.0; low_estimate: float = 0.0; high_estimate: float = 0.0
    factors: List[str] = field(default_factory=list); generated_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict: return {"period": self.period.value, "predicted_revenue": round(self.predicted_revenue, 2), "confidence": round(self.confidence, 2), "low": round(self.low_estimate, 2), "high": round(self.high_estimate, 2)}

@dataclass
class RevenueAlert:
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    severity: AlertSeverity = AlertSeverity.INFO; title: str = ""; message: str = ""
    metric_value: float = 0.0; threshold: float = 0.0; is_read: bool = False
    created_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict: return {"alert_id": self.alert_id, "severity": self.severity.value, "title": self.title, "message": self.message[:80], "is_read": self.is_read}

@dataclass
class FinancialReport:
    report_id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    report_type: str = "daily"; period: str = ""; data: Dict[str, Any] = field(default_factory=dict)
    generated_at: float = field(default_factory=time.time)
    def to_dict(self) -> Dict: return {"report_type": self.report_type, "period": self.period}
