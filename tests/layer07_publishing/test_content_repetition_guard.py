"""Tests for the real no-template-repeat publishing gate."""
from __future__ import annotations

import tempfile
import unittest

from layers.layer07_publishing.modules.publisher_engine.content_repetition_guard import (
    ContentRepetitionGuard,
)


class TestContentRepetitionGuard(unittest.TestCase):
    def test_same_template_is_rejected_with_different_words(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            guard = ContentRepetitionGuard(handle.name)
            first = guard.reserve(
                account_id="instagram:niche-01",
                platform="instagram",
                content="Start here. Learn three useful facts today. Save this post for later.",
            )
            self.assertTrue(first.allowed)
            guard.finalize(first.reservation_id, "post-1")

            second = guard.reserve(
                account_id="instagram:niche-01",
                platform="instagram",
                content="Begin now. Discover three practical ideas today. Save this post for later.",
            )
            self.assertFalse(second.allowed)
            self.assertEqual(second.reason, "template_repeat")

    def test_same_template_is_allowed_on_a_different_account(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            guard = ContentRepetitionGuard(handle.name)
            first = guard.reserve(
                account_id="instagram:niche-01",
                platform="instagram",
                content="Start here. Learn three useful facts today. Save this post for later.",
            )
            guard.finalize(first.reservation_id, "post-1")
            second = guard.reserve(
                account_id="instagram:niche-02",
                platform="instagram",
                content="Begin now. Discover three practical ideas today. Save this post for later.",
            )
            self.assertTrue(second.allowed)

    def test_failed_publish_reservation_can_be_released(self):
        with tempfile.NamedTemporaryFile(suffix=".sqlite3") as handle:
            guard = ContentRepetitionGuard(handle.name)
            first = guard.reserve(
                account_id="youtube:niche-01",
                platform="youtube",
                content="One idea. Two examples. Three practical steps.",
            )
            self.assertTrue(first.allowed)
            guard.release(first.reservation_id)
            second = guard.reserve(
                account_id="youtube:niche-01",
                platform="youtube",
                content="One idea. Two examples. Three practical steps.",
            )
            self.assertTrue(second.allowed)


if __name__ == "__main__":
    unittest.main()
