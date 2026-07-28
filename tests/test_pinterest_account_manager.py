"""Comprehensive tests for Layer 23 — Module 2: Pinterest Account Manager."""
from __future__ import annotations
import pytest
import time

from layers.layer23_website_manager.pinterest_account_manager.pinterest_account_manager import (
    PinterestAccountManager, get_pinterest_manager,
)
from layers.layer23_website_manager.pinterest_account_manager.models.pinterest_account import (
    PinterestAccount, AccountStatus, AuthStatus,
)
from layers.layer23_website_manager.pinterest_account_manager.models.account_token import AccountToken
from layers.layer23_website_manager.pinterest_account_manager.models.brand_profile import BrandProfile
from layers.layer23_website_manager.pinterest_account_manager.exceptions import (
    AccountNotFoundError, InvalidTokenError, DuplicateAccountError,
    AccountLimitError, PermissionDeniedError, AccountSuspendedError,
    SelectionError, WebsiteNotClaimedError,
)


# ═══════════════════════════════════════════════════════════════════
# PinterestAccount Model
# ═══════════════════════════════════════════════════════════════════

class TestPinterestAccount:
    def test_default_account(self):
        acc = PinterestAccount()
        assert acc.status == AccountStatus.ACTIVE
        assert acc.auth_status == AuthStatus.PENDING
        assert acc.health_score == 100.0
        assert acc.account_id is not None

    def test_account_with_values(self):
        acc = PinterestAccount(
            account_name="Home Decor Pro",
            username="homedecorpro",
            niche="home_decor",
            business_name="Home Decor Studio",
        )
        assert acc.account_name == "Home Decor Pro"
        assert acc.niche == "home_decor"

    def test_is_healthy(self):
        acc = PinterestAccount(
            health_score=85, status=AccountStatus.ACTIVE,
            auth_status=AuthStatus.AUTHENTICATED,
        )
        assert acc.is_healthy is True

    def test_is_not_healthy_suspended(self):
        acc = PinterestAccount(
            health_score=85, status=AccountStatus.ACTIVE,
            is_suspended=True, auth_status=AuthStatus.AUTHENTICATED,
        )
        assert acc.is_healthy is False

    def test_is_not_healthy_low_score(self):
        acc = PinterestAccount(
            health_score=30, status=AccountStatus.ACTIVE,
            auth_status=AuthStatus.AUTHENTICATED,
        )
        assert acc.is_healthy is False

    def test_to_dict(self):
        acc = PinterestAccount(account_name="Test", username="test")
        d = acc.to_dict()
        assert d["account_name"] == "Test"
        assert d["status"] == "active"
        assert "health_score" in d

    def test_error_rate(self):
        acc = PinterestAccount(total_posts=80, total_errors=20)
        assert acc.error_rate == 20.0

    def test_display_name(self):
        acc = PinterestAccount(business_name="Biz Name")
        assert acc.display_name == "Biz Name"


# ═══════════════════════════════════════════════════════════════════
# AccountToken Model
# ═══════════════════════════════════════════════════════════════════

class TestAccountToken:
    def test_default_token(self):
        token = AccountToken()
        assert token.is_valid is True
        assert not token.is_expired

    def test_should_refresh_true(self):
        token = AccountToken(expires_in=3600)  # 1 hour
        token.issued_at = time.time() - 3600 * 25  # 25 days ago
        assert token.should_refresh is True

    def test_should_refresh_false(self):
        token = AccountToken(expires_in=3600 * 24 * 30)
        token.issued_at = time.time()
        assert token.should_refresh is False

    def test_to_dict_masks_token(self):
        token = AccountToken(access_token="abcdefghijklmnopqrstuvwxyz123456")
        d = token.to_dict()
        assert "sk_live" not in d["access_token"]
        assert "..." in d["access_token"]


# ═══════════════════════════════════════════════════════════════════
# BrandProfile Model
# ═══════════════════════════════════════════════════════════════════

class TestBrandProfile:
    def test_default_profile(self):
        bp = BrandProfile()
        assert bp.brand_voice == "professional"
        assert bp.consistency_score == 0.0

    def test_from_niche_home_decor(self):
        bp = BrandProfile.from_niche("home decor")
        assert bp.brand_voice == "inspirational"
        assert bp.brand_name == "Home Decor Studio"

    def test_from_niche_unknown(self):
        bp = BrandProfile.from_niche("gaming")
        assert bp.brand_voice == "professional"


# ═══════════════════════════════════════════════════════════════════
# PinterestAccountManager Integration
# ═══════════════════════════════════════════════════════════════════

class TestAccountRegistry:
    def setup_method(self):
        self.pm = PinterestAccountManager(max_accounts=61)

    def test_register_account(self):
        acc = self.pm.register_account("Test Account", niche="tech")
        assert acc.account_name == "Test Account"
        assert acc.niche == "tech"
        assert acc.status == AccountStatus.ACTIVE

    def test_register_with_full_details(self):
        acc = self.pm.register_account(
            account_name="Full Account",
            username="fullaccount",
            niche="fashion",
            business_name="Fashion Studio",
            website="https://fashionstudio.com",
            access_token="pina_test_token",
        )
        assert acc.username == "fullaccount"
        assert acc.business_name == "Fashion Studio"
        assert acc.auth_status == AuthStatus.AUTHENTICATED

    def test_register_duplicate(self):
        self.pm.register_account("Unique Name")
        with pytest.raises(DuplicateAccountError):
            self.pm.register_account("Unique Name")

    def test_get_account(self):
        created = self.pm.register_account("Get This")
        fetched = self.pm.get_account(created.account_id)
        assert fetched is not None
        assert fetched.account_name == "Get This"

    def test_get_nonexistent(self):
        assert self.pm.get_account("nonexistent") is None

    def test_update_account(self):
        acc = self.pm.register_account("Update Me")
        updated = self.pm.update_account(acc.account_id, account_name="Updated Name")
        assert updated is not None
        assert updated.account_name == "Updated Name"

    def test_remove_account(self):
        acc = self.pm.register_account("Remove Me")
        assert self.pm.remove_account(acc.account_id) is True
        assert self.pm.get_account(acc.account_id) is None

    def test_enable_disable_account(self):
        acc = self.pm.register_account("Toggle")
        assert self.pm.disable_account(acc.account_id) is True
        assert self.pm.get_account(acc.account_id).status == AccountStatus.DISABLED
        assert self.pm.enable_account(acc.account_id) is True
        assert self.pm.get_account(acc.account_id).status == AccountStatus.ACTIVE

    def test_account_limit(self):
        pm = PinterestAccountManager(max_accounts=2)
        pm.register_account("Account 1")
        pm.register_account("Account 2")
        with pytest.raises(AccountLimitError):
            pm.register_account("Account 3")


class TestAuthentication:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_set_token(self):
        acc = self.pm.register_account("Auth Test")
        token = self.pm.set_token(acc.account_id, "pina_valid_token", "pina_refresh_token")
        assert token.is_valid is True
        assert token.access_token.startswith("pina_")

    def test_validate_authenticated(self):
        acc = self.pm.register_account("Validate Test", access_token="pina_valid")
        is_valid, msg = self.pm.validate_auth(acc.account_id)
        assert is_valid is True

    def test_refresh_token(self):
        acc = self.pm.register_account("Refresh Test")
        self.pm.set_token(acc.account_id, "old_token", "refresh_token", expires_in=3600)
        # Make token look expired
        token = self.pm.auth.get_token(acc.account_id)
        token.issued_at = time.time() - 3600 * 31 * 24  # 31 days ago
        assert token.is_expired is True
        # Refresh
        refreshed = self.pm.refresh_token(acc.account_id)
        assert refreshed is not None
        assert refreshed.refresh_count >= 1


class TestPermissions:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_check_permission_post(self):
        acc = self.pm.register_account("Perm Test")
        assert self.pm.check_permission(acc.account_id, "post") is True

    def test_check_permission_denied(self):
        acc = self.pm.register_account("No Post")
        self.pm.set_permission(acc.account_id, "post", False)
        assert self.pm.check_permission(acc.account_id, "post") is False

    def test_set_permission(self):
        acc = self.pm.register_account("Set Perm")
        assert self.pm.set_permission(acc.account_id, "analytics", False) is True
        assert self.pm.check_permission(acc.account_id, "analytics") is False


class TestBranding:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_create_brand_profile(self):
        acc = self.pm.register_account("Brand Test", niche="beauty")
        profile = self.pm.create_brand_profile(
            acc.account_id, "Beauty Studio", brand_voice="inspirational"
        )
        assert profile.brand_name == "Beauty Studio"
        assert profile.brand_voice == "inspirational"

    def test_auto_brand_from_niche(self):
        acc = self.pm.register_account("Niche Brand", niche="home_decor")
        profile = self.pm.get_brand_profile(acc.account_id)
        assert profile is not None
        assert "Home" in profile.brand_name and "Decor" in profile.brand_name

    def test_sync_branding(self):
        acc = self.pm.register_account("Sync Test", niche="tech")
        result = self.pm.sync_branding(acc.account_id)
        assert result["status"] == "synced"


class TestWebsiteClaim:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_claim_website(self):
        acc = self.pm.register_account("Web Claim")
        result = self.pm.claim_website(acc.account_id, "https://mywebsite.com")
        assert result["claim_status"] == "pending"
        assert acc.website == "https://mywebsite.com"

    def test_verify_claim(self):
        acc = self.pm.register_account("Verify Claim")
        self.pm.claim_website(acc.account_id, "https://example.com")
        result = self.pm.verify_website_claim(acc.account_id)
        assert result["claim_status"] == "verified"
        assert acc.website_claimed is True


class TestHealth:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_check_single_health(self):
        acc = self.pm.register_account("Health Check", access_token="pina_token")
        result = self.pm.check_health(acc.account_id)
        assert "health_score" in result
        assert result["health_score"] >= 0

    def test_check_all_health(self):
        self.pm.register_account("Healthy 1", access_token="tok1")
        self.pm.register_account("Healthy 2", access_token="tok2")
        report = self.pm.check_all_health()
        assert report["total_checked"] == 2
        assert report["overall_score"] >= 0


class TestAccountSelector:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_select_home_decor_account(self):
        acc1 = self.pm.register_account("Home Decor Pro", niche="home_decor",
                                          access_token="tok1")
        acc2 = self.pm.register_account("Tech Trends", niche="tech",
                                          access_token="tok2")
        selected = self.pm.select_account("Modern Living Room Design", niche="home_decor")
        assert selected.niche == "home_decor"

    def test_select_tech_account(self):
        self.pm.register_account("Home Decor Pro", niche="home_decor", access_token="tok1")
        self.pm.register_account("Tech Trends", niche="tech", access_token="tok2")
        selected = self.pm.select_account("Latest AI Technology News")
        assert selected.niche == "tech"

    def test_select_multi_topics(self):
        for i, niche in enumerate(["fashion", "food", "travel"]):
            self.pm.register_account(f"Account {i}", niche=niche, access_token=f"tok{i}")
        topics = ["Summer outfit ideas", "Easy pasta recipe", "Best travel destinations"]
        results = self.pm.select_accounts_for_topics(topics)
        assert len(results) == 3

    def test_select_no_accounts(self):
        with pytest.raises(SelectionError):
            self.pm.select_account("Any topic")


class TestMultiAccount:
    def setup_method(self):
        self.pm = PinterestAccountManager(max_accounts=10)

    def test_register_10_accounts(self):
        for i in range(10):
            self.pm.register_account(f"Account_{i}", niche="tech", access_token=f"tok{i}")
        assert len(self.pm.registry.get_all()) == 10

    def test_get_all_by_niche(self):
        self.pm.register_account("Foodie1", niche="food")
        self.pm.register_account("Foodie2", niche="food")
        self.pm.register_account("Tech1", niche="tech")
        food_accounts = self.pm.registry.get_by_niche("food")
        assert len(food_accounts) == 2

    def test_get_all_healthy(self):
        self.pm.register_account("Healthy Acc", access_token="tok1")
        acc2 = self.pm.register_account("Unhealthy", access_token="tok2")
        acc2.health_score = 30
        healthy = self.pm.registry.get_all(healthy_only=True)
        assert len(healthy) == 1


class TestStatusAndCLI:
    def setup_method(self):
        self.pm = PinterestAccountManager(max_accounts=61)
        self.pm.register_account("Status Test", niche="fashion", access_token="tok1")

    def test_get_status(self):
        status = self.pm.get_status()
        assert status["module"] == "Pinterest Account Manager (Layer 23 / Module 2)"
        assert status["version"] == "1.0.0"
        assert status["overall"] in ("Healthy", "Degraded")
        assert "accounts" in status
        assert "health" in status
        assert "authentication" in status

    def test_account_stats(self):
        status = self.pm.get_status()
        assert status["accounts"]["total"] >= 1
        assert status["accounts"]["max"] == 61


class TestErrorHandling:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_remove_nonexistent(self):
        assert self.pm.remove_account("nonexistent") is False

    def test_update_nonexistent(self):
        assert self.pm.update_account("nonexistent", account_name="X") is None

    def test_check_health_nonexistent(self):
        result = self.pm.check_health("nonexistent")
        assert "error" in result


class TestSingleton:
    def test_get_pinterest_manager(self):
        pm1 = get_pinterest_manager()
        pm2 = get_pinterest_manager()
        assert pm1 is pm2

    def test_singleton_max_accounts(self):
        pm = get_pinterest_manager(61)
        assert pm.registry._max_accounts == 61


class TestNicheBranding:
    def test_all_niches(self):
        niches = ["home decor", "beauty", "fashion", "food", "tech",
                   "fitness", "travel", "finance", "education", "health"]
        for niche in niches:
            bp = BrandProfile.from_niche(niche)
            assert bp.brand_name is not None
            assert bp.brand_voice is not None
            assert bp.brand_colors is not None
            assert len(bp.brand_colors) == 3

    def test_niche_colors_different(self):
        colors_set = set()
        niches = ["home decor", "tech", "beauty", "food"]
        for niche in niches:
            bp = BrandProfile.from_niche(niche)
            colors_set.add(str(bp.brand_colors))
        assert len(colors_set) == 4  # All different


class TestAccountSelectorHistory:
    def setup_method(self):
        self.pm = PinterestAccountManager()

    def test_selection_logged(self):
        self.pm.register_account("Selector Test Acc", niche="tech", access_token="tok1")
        self.pm.select_account("Artificial Intelligence")
        history = self.pm.selector.get_selection_history()
        assert len(history) >= 1
        assert history[0]["topic"] == "Artificial Intelligence"

    def test_selector_stats(self):
        self.pm.register_account("Stats Acc", niche="tech", access_token="tok1")
        self.pm.register_account("Stats Acc 2", niche="food", access_token="tok2")
        self.pm.select_account("Python Programming")
        self.pm.select_account("Healthy Recipes")
        stats = self.pm.selector.get_stats()
        assert stats["total_selections"] >= 2
