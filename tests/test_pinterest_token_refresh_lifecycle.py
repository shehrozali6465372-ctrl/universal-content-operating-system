"""Regression tests for UCOS Pinterest credential refresh lifecycle."""
from __future__ import annotations

import json
import os
import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from layers.layer14_enterprise_integration.modules.api_gateway.api_gateway import (
    APIGateway,
    PinterestCredentialRefreshError,
)


class PinterestTokenRefreshTests(unittest.TestCase):
    def setUp(self):
        self.gateway = APIGateway()
        self.account = SimpleNamespace(
            account_id="pinterest:test-account",
            credentials_ref="pinterest:test-account",
            platform_account_id="test-pinterest-user",
        )

    def test_valid_token_is_not_refreshed(self):
        expiry = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        credentials = {"access_token": "safe-test-token", "expires_at": expiry}
        with patch("layers.layer14_enterprise_integration.modules.api_gateway.api_gateway.urlopen") as urlopen:
            result = self.gateway._refresh_pinterest_token_if_needed(
                self.account, credentials, "test-client", "test-secret"
            )
        self.assertEqual(result, credentials)
        urlopen.assert_not_called()

    def test_expiring_token_is_refreshed_and_rotated_into_vault(self):
        os.environ["UCOS_CREDENTIAL_ENCRYPTION_KEY"] = "test-key-material-long-enough"
        expiry = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        credentials = {
            "access_token": "old-test-token",
            "refresh_token": "old-refresh-token",
            "expires_at": expiry,
            "scope": "boards:read pins:write",
            "pinterest_user_id": "test-pinterest-user",
        }
        response = MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps({
            "access_token": "new-test-token",
            "refresh_token": "rotated-refresh-token",
            "expires_in": 2592000,
            "token_type": "bearer",
            "scope": "boards:read pins:write",
            "refresh_token_expires_in": 5184000,
        }).encode()
        with patch(
            "layers.layer14_enterprise_integration.modules.api_gateway.api_gateway.urlopen",
            return_value=response,
        ), patch(
            "layers.layer13_persistence.modules.postgresql.repositories.credential_repository.CredentialRepository"
        ) as repository:
            result = self.gateway._refresh_pinterest_token_if_needed(
                self.account, credentials, "test-client", "test-secret"
            )
        self.assertEqual(result["access_token"], "new-test-token")
        self.assertEqual(result["refresh_token"], "rotated-refresh-token")
        repository.return_value.upsert.assert_called_once()
        saved = repository.return_value.upsert.call_args.kwargs
        self.assertEqual(saved["account_id"], self.account.account_id)
        self.assertEqual(saved["credential_ref"], self.account.credentials_ref)
        self.assertEqual(saved["payload"]["access_token"], "new-test-token")
        self.assertEqual(saved["payload"]["refresh_token"], "rotated-refresh-token")
        self.assertNotIn("test-secret", json.dumps(result))
        os.environ.pop("UCOS_CREDENTIAL_ENCRYPTION_KEY", None)

    def test_expiring_token_without_refresh_token_fails_closed(self):
        expiry = (datetime.now(timezone.utc) + timedelta(seconds=60)).isoformat()
        with self.assertRaises(PinterestCredentialRefreshError):
            self.gateway._refresh_pinterest_token_if_needed(
                self.account,
                {"access_token": "old-test-token", "expires_at": expiry},
                "test-client",
                "test-secret",
            )


if __name__ == "__main__":
    unittest.main()
