"""Custom exceptions for Traffic Manager."""
from __future__ import annotations
class TrafficTrackingError(Exception): pass
class SourceNotFoundError(Exception): pass
class AttributionError(Exception): pass
class ForecastError(Exception): pass
class CampaignError(Exception): pass
class AlertError(Exception): pass
class TrafficHealthError(Exception): pass
class VisitorTrackingError(Exception): pass
class DashboardError(Exception): pass
