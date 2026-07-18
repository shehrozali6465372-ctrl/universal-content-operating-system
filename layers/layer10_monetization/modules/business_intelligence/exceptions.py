"""Custom exceptions for Business Intelligence & Revenue Engine."""
from __future__ import annotations


class BusinessError(Exception):
    """Base exception for business errors."""


class RevenueError(BusinessError):
    """Raised when revenue tracking fails."""


class ROIError(BusinessError):
    """Raised when ROI calculation fails."""


class CampaignError(BusinessError):
    """Raised when campaign operations fail."""


class BudgetError(BusinessError):
    """Raised when budget operations fail."""


class ForecastError(BusinessError):
    """Raised when forecasting fails."""


class OpportunityError(BusinessError):
    """Raised when opportunity detection fails."""


class FinancialMemoryError(BusinessError):
    """Raised when financial memory operations fail."""
