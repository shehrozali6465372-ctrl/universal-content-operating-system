"""Tests for the safe Facebook Page connection boundary."""
from unittest import TestCase
from unittest.mock import Mock

from layers.layer07_publishing.modules.platform_plugin_manager.facebook.facebook_page_connection import (
    FacebookPagePublisher,
    FacebookPageConnection,
)


class TestFacebookPagePublisher(TestCase):
    def test_authentication_is_read_only(self):
        publisher = FacebookPagePublisher()
        publisher._api_get = Mock(side_effect=[
            {"id": "123"},
            {"id": "123", "name": "Test Page", "category": "Education"},
        ])
        publisher._resolve_page_token_safe = Mock(return_value="page-token")

        self.assertTrue(publisher.authenticate({
            "page_id": "123",
            "access_token": "page-token",
        }))
        publisher._api_get.assert_called()

    def test_missing_credentials_do_not_authenticate(self):
        publisher = FacebookPagePublisher()
        self.assertFalse(publisher.authenticate({}))


class TestFacebookPageConnection(TestCase):
    def test_connect_returns_non_secret_page_status(self):
        publisher = FacebookPagePublisher()
        publisher.authenticate = Mock(return_value=True)
        publisher.get_page_info = Mock(return_value={
            "id": "123",
            "name": "Test Page",
            "category": "Education",
        })
        service = FacebookPageConnection(publisher)

        status = service.connect({"page_id": "123", "access_token": "secret"})

        self.assertEqual(status["page_id"], "123")
        self.assertEqual(status["page_name"], "Test Page")
        self.assertNotIn("access_token", status)


if __name__ == "__main__":
    import unittest
    unittest.main()
