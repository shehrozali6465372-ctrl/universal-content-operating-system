"""Shared pytest fixtures for cross-layer tests."""

import pytest

from layers.shared.event_bus import EventBus


@pytest.fixture
def event_bus():
    """Provide an isolated event bus for each test."""
    return EventBus()
