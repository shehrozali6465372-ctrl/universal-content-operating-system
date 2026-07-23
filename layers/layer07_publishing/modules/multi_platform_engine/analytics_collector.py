"""AnalyticsCollector — Collect and analyze publishing metrics.

Features:
- Track views, clicks, engagement, CTR
- Per-platform analytics
- Per-account analytics
- Per-post analytics
- Time-series data
- Aggregate reporting
- Affiliate click tracking
"""
from __future__ import annotations
import time
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class PostAnalytics:
    post_id: str
    platform: str
    account_id: str
    views: int = 0
    clicks: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    impressions: int = 0
    reach: int = 0
    engagement_rate: float = 0.0
    ctr: float = 0.0
    affiliate_clicks: int = 0
    affiliate_revenue: float = 0.0
    published_at: float = 0.0
    updated_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "platform": self.platform,
            "views": self.views,
            "clicks": self.clicks,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "saves": self.saves,
            "impressions": self.impressions,
            "reach": self.reach,
            "engagement_rate": round(self.engagement_rate, 4),
            "ctr": round(self.ctr, 4),
            "affiliate_clicks": self.affiliate_clicks,
            "affiliate_revenue": round(self.affiliate_revenue, 2),
        }


class AnalyticsCollector:
    """Collect and analyze publishing analytics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._analytics: Dict[str, PostAnalytics] = {}
        self._time_series: List[Dict[str, Any]] = []

        # Aggregate cache
        self._platform_totals: Dict[str, Dict[str, int]] = {}
        self._account_totals: Dict[str, Dict[str, int]] = {}

    def record_post(self, post_id: str, platform: str, account_id: str,
                    published_at: float = 0.0) -> None:
        """Record a new published post."""
        with self._lock:
            self._analytics[post_id] = PostAnalytics(
                post_id=post_id,
                platform=platform,
                account_id=account_id,
                published_at=published_at or time.time(),
            )

    def update_metrics(self, post_id: str, **metrics) -> bool:
        """Update metrics for a post."""
        analytics = self._analytics.get(post_id)
        if not analytics:
            return False

        with self._lock:
            for key, value in metrics.items():
                if hasattr(analytics, key):
                    setattr(analytics, key, value)

            # Recalculate derived metrics
            analytics.updated_at = time.time()
            total_engagement = (
                analytics.likes + analytics.comments +
                analytics.shares + analytics.saves
            )
            if analytics.views > 0:
                analytics.engagement_rate = total_engagement / analytics.views
            if analytics.impressions > 0:
                analytics.ctr = analytics.clicks / analytics.impressions

            # Update aggregates
            self._update_aggregates(analytics)

            # Record time series point
            self._time_series.append({
                "post_id": post_id,
                "platform": analytics.platform,
                "timestamp": time.time(),
                "metrics": metrics,
            })

        return True

    def _update_aggregates(self, analytics: PostAnalytics) -> None:
        """Update aggregate totals."""
        platform = analytics.platform
        account = analytics.account_id

        if platform not in self._platform_totals:
            self._platform_totals[platform] = {
                "views": 0, "clicks": 0, "likes": 0, "comments": 0,
                "shares": 0, "affiliate_clicks": 0, "posts": 0,
            }
        pt = self._platform_totals[platform]
        pt["views"] += analytics.views
        pt["clicks"] += analytics.clicks
        pt["likes"] += analytics.likes
        pt["comments"] += analytics.comments
        pt["shares"] += analytics.shares
        pt["affiliate_clicks"] += analytics.affiliate_clicks
        pt["posts"] = len([a for a in self._analytics.values() if a.platform == platform])

        if account not in self._account_totals:
            self._account_totals[account] = {
                "views": 0, "clicks": 0, "likes": 0, "posts": 0,
            }
        at = self._account_totals[account]
        at["views"] += analytics.views
        at["clicks"] += analytics.clicks
        at["likes"] += analytics.likes
        at["posts"] = len([a for a in self._analytics.values() if a.account_id == account])

    def get_post_analytics(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get analytics for a specific post."""
        analytics = self._analytics.get(post_id)
        return analytics.to_dict() if analytics else None

    def get_platform_analytics(self, platform: str) -> Dict[str, Any]:
        """Get aggregated analytics for a platform."""
        posts = [a for a in self._analytics.values() if a.platform == platform]
        if not posts:
            return {"platform": platform, "posts": 0}

        total_views = sum(p.views for p in posts)
        total_clicks = sum(p.clicks for p in posts)
        total_likes = sum(p.likes for p in posts)
        total_comments = sum(p.comments for p in posts)
        total_shares = sum(p.shares for p in posts)
        total_affiliate = sum(p.affiliate_clicks for p in posts)
        total_revenue = sum(p.affiliate_revenue for p in posts)

        return {
            "platform": platform,
            "posts": len(posts),
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_likes": total_likes,
            "total_comments": total_comments,
            "total_shares": total_shares,
            "total_affiliate_clicks": total_affiliate,
            "total_affiliate_revenue": round(total_revenue, 2),
            "avg_engagement_rate": round(
                sum(p.engagement_rate for p in posts) / len(posts), 4
            ),
            "avg_ctr": round(
                sum(p.ctr for p in posts) / len(posts), 4
            ),
        }

    def get_account_analytics(self, account_id: str) -> Dict[str, Any]:
        """Get aggregated analytics for an account."""
        posts = [a for a in self._analytics.values() if a.account_id == account_id]
        if not posts:
            return {"account_id": account_id, "posts": 0}

        return {
            "account_id": account_id,
            "posts": len(posts),
            "total_views": sum(p.views for p in posts),
            "total_clicks": sum(p.clicks for p in posts),
            "total_engagement": sum(p.likes + p.comments + p.shares for p in posts),
            "total_affiliate_clicks": sum(p.affiliate_clicks for p in posts),
        }

    def get_dashboard(self) -> Dict[str, Any]:
        """Get full analytics dashboard."""
        all_posts = list(self._analytics.values())
        total_views = sum(p.views for p in all_posts)
        total_clicks = sum(p.clicks for p in all_posts)
        total_engagement = sum(p.likes + p.comments + p.shares for p in all_posts)
        total_affiliate = sum(p.affiliate_clicks for p in all_posts)
        total_revenue = sum(p.affiliate_revenue for p in all_posts)

        # Top posts
        top_by_views = sorted(all_posts, key=lambda p: p.views, reverse=True)[:5]
        top_by_engagement = sorted(
            all_posts,
            key=lambda p: p.likes + p.comments + p.shares,
            reverse=True,
        )[:5]

        return {
            "total_posts": len(all_posts),
            "total_views": total_views,
            "total_clicks": total_clicks,
            "total_engagement": total_engagement,
            "total_affiliate_clicks": total_affiliate,
            "total_affiliate_revenue": round(total_revenue, 2),
            "avg_engagement_rate": round(
                total_engagement / total_views, 4
            ) if total_views > 0 else 0,
            "avg_ctr": round(total_clicks / total_views, 4) if total_views > 0 else 0,
            "platform_breakdown": dict(self._platform_totals),
            "top_by_views": [p.to_dict() for p in top_by_views],
            "top_by_engagement": [p.to_dict() for p in top_by_engagement],
        }

    def get_time_series(self, post_id: str = None, platform: str = None,
                        hours: int = 24) -> List[Dict[str, Any]]:
        """Get time-series data."""
        cutoff = time.time() - (hours * 3600)
        series = self._time_series

        if post_id:
            series = [s for s in series if s["post_id"] == post_id]
        if platform:
            series = [s for s in series if s["platform"] == platform]

        return [s for s in series if s["timestamp"] >= cutoff]

    def stats(self) -> Dict[str, Any]:
        """Get collector statistics."""
        return {
            "total_posts_tracked": len(self._analytics),
            "platforms_tracked": list(self._platform_totals.keys()),
            "accounts_tracked": list(self._account_totals.keys()),
            "time_series_points": len(self._time_series),
        }
