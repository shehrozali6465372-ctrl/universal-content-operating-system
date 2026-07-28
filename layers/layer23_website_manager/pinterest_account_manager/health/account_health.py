"""AccountHealthChecker — Monitor Pinterest account health, suspension, restrictions."""
from __future__ import annotations
import time
from typing import Any, Dict, List, Optional, Tuple

from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus, AuthStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    AccountSuspendedError,
)


class AccountHealthChecker:
    """Check account health — token, suspension, restrictions, profile completeness."""

    def __init__(self) -> None:
        self._check_log: List[dict] = []

    def check_account(self, account: PinterestAccount,
                       has_valid_token: bool = True) -> Dict[str, Any]:
        """Run complete health check on a single account."""
        issues: List[str] = []

        # Token check
        if not has_valid_token:
            issues.append("Token is invalid or expired")
        if account.auth_status == AuthStatus.EXPIRED:
            issues.append("Authentication expired")
        elif account.auth_status == AuthStatus.FAILED:
            issues.append("Authentication failed")

        # Suspension check
        if account.is_suspended:
            issues.append("Account is suspended by Pinterest")
        if account.is_restricted:
            issues.append("Account is restricted")

        # Status check
        if account.status == AccountStatus.ERROR:
            issues.append("Account in error state")
        elif account.status == AccountStatus.EXPIRED:
            issues.append("Account expired")

        # Profile completeness
        if not account.username:
            issues.append("Username not set")
        if not account.business_name:
            issues.append("Business name not set")
        if not account.website:
            issues.append("Website not connected")
        if not account.website_claimed:
            issues.append("Website not claimed")

        # Error rate
        if account.error_rate > 20:
            issues.append(f"High error rate: {account.error_rate}%")

        # Calculate health score
        score = 100.0
        penalty_map = {
            "Token is invalid or expired": 30,
            "Account is suspended by Pinterest": 40,
            "Account is restricted": 25,
            "Account in error state": 30,
            "Authentication expired": 20,
            "Authentication failed": 25,
            "Username not set": 10,
            "Business name not set": 10,
            "Website not connected": 15,
            "Website not claimed": 10,
            "High error rate": 15,
        }

        # Deduct based on issues
        for issue in issues:
            penalty = penalty_map.get(issue, 10)
            # Only highest severity penalty for each category
            if "suspended" in issue:
                penalty = max(penalty, 40)
            if "expired" in issue.lower():
                penalty = max(penalty, 20)
            score -= penalty

        # Consecutive errors penalty
        score -= min(account.consecutive_errors * 2, 20)

        # Bonus for completed profile
        if account.website_claimed:
            score += 5
        if account.description:
            score += 5

        score = max(0, min(100, score))

        result = {
            "account_id": account.account_id,
            "health_score": round(score, 1),
            "status": "healthy" if score >= 70 else "degraded" if score >= 40 else "critical",
            "issues": issues,
            "issue_count": len(issues),
            "checked_at": time.time(),
        }

        self._check_log.append(result)
        return result

    def check_all(self, accounts: List[PinterestAccount],
                   token_status: Optional[Dict[str, bool]] = None) -> Dict[str, Any]:
        """Run health checks on all accounts."""
        token_status = token_status or {}
        results = []

        for acc in accounts:
            has_token = token_status.get(acc.account_id, True)
            result = self.check_account(acc, has_token)
            results.append(result)

        healthy = sum(1 for r in results if r["health_score"] >= 70)
        degraded = sum(1 for r in results if 40 <= r["health_score"] < 70)
        critical = sum(1 for r in results if r["health_score"] < 40)
        all_issues = [r["issues"] for r in results]

        return {
            "total_checked": len(results),
            "healthy": healthy,
            "degraded": degraded,
            "critical": critical,
            "overall_score": round(sum(r["health_score"] for r in results) / max(len(results), 1), 1),
            "checks": results,
            "checked_at": time.time(),
        }

    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_checks": len(self._check_log),
            "last_check": self._check_log[-1]["checked_at"] if self._check_log else 0,
        }
