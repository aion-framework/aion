"""
Pytest configuration and shared fixtures.

Provides a mock Hatchet client so unit tests do not require a running engine.
"""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_hatchet_client() -> Generator[MagicMock, None, None]:
    """Provide a mock Hatchet client that captures event pushes."""
    with patch("aion.core.engine.get_hatchet") as get_hatchet:
        mock_client = MagicMock()
        mock_client.client.event.push.return_value = "mock-event-id"
        get_hatchet.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_event_push() -> Generator[MagicMock, None, None]:
    """Patch run_aion_workflow / event push so start() does not hit the network."""
    with patch("aion.agent.run_aion_workflow") as run_wf:
        run_wf.return_value = "test-event-123"
        yield run_wf
