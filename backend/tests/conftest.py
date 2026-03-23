"""
backend/tests/conftest.py — Shared pytest fixtures.

Patches API clients to None so tests run without real API keys.
AsyncSqliteSaver uses an in-memory DB to avoid leaving test artefacts on disk.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def patch_clients():
    """
    Ensure gemini_client and anthropic_client are None in all tests.
    Tools that use these clients must be mocked in their own tests.
    """
    with (
        patch("backend.clients.gemini_client", None),
        patch("backend.clients.anthropic_client", None),
    ):
        yield


@pytest.fixture(autouse=True)
def patch_memory_checkpointer():
    """
    Replace the checkpointer with a fresh InMemorySaver so tests
    are isolated from each other.
    """
    from langgraph.checkpoint.memory import InMemorySaver

    with patch("backend.graph.builder.InMemorySaver", return_value=InMemorySaver()):
        yield


def make_mock_gemini_response(text: str) -> MagicMock:
    """Return a minimal mock of a Gemini GenerateContentResponse with .text."""
    resp = MagicMock()
    resp.text = text
    return resp
