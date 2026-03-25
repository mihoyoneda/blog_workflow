"""
backend/tests/test_image_proxy.py — Tests for the hero image proxy endpoint.

GET /api/image/hero/{thread_id}
All external calls (aget_state, httpx) are mocked.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def _make_state(hero_image_url: str = "") -> MagicMock:
    """Return a mock LangGraph StateSnapshot."""
    state = MagicMock()
    state.metadata = {"thread_id": "test-thread"}  # non-None = thread exists
    state.values = {"hero_image_url": hero_image_url} if hero_image_url else {}
    return state


# ── GET /api/image/hero/{thread_id} ──────────────────────────────

class TestGetHeroImage:
    def test_unknown_thread_returns_404(self):
        """Non-existent thread (metadata=None) returns 404."""
        state = MagicMock()
        state.metadata = None
        with patch(
            "backend.api.image_proxy.workflow_graph.aget_state",
            new_callable=AsyncMock,
            return_value=state,
        ):
            resp = client.get("/api/image/hero/nonexistent-thread")
        assert resp.status_code == 404

    def test_no_hero_url_returns_404(self):
        """Thread exists but hero_image_url not set yet."""
        with patch(
            "backend.api.image_proxy.workflow_graph.aget_state",
            new_callable=AsyncMock,
            return_value=_make_state(""),
        ):
            resp = client.get("/api/image/hero/test-thread")
        assert resp.status_code == 404
        assert "Hero image" in resp.json()["detail"]

    def test_successful_image_fetch(self):
        """Happy path: state has image URL and upstream returns image bytes."""
        fake_image = b"\x89PNG\r\n\x1a\n"
        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 200
        mock_http_resp.content = fake_image
        mock_http_resp.headers = {"content-type": "image/png"}

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.get = AsyncMock(return_value=mock_http_resp)

        with (
            patch(
                "backend.api.image_proxy.workflow_graph.aget_state",
                new_callable=AsyncMock,
                return_value=_make_state("https://example.com/image.png"),
            ),
            patch("backend.api.image_proxy.httpx.AsyncClient", return_value=mock_http_client),
        ):
            resp = client.get("/api/image/hero/test-thread")

        assert resp.status_code == 200
        assert resp.content == fake_image

    def test_upstream_non_200_returns_502(self):
        """Upstream image server returns non-200 → 502."""
        mock_http_resp = MagicMock()
        mock_http_resp.status_code = 503
        mock_http_resp.content = b""
        mock_http_resp.headers = {}

        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.get = AsyncMock(return_value=mock_http_resp)

        with (
            patch(
                "backend.api.image_proxy.workflow_graph.aget_state",
                new_callable=AsyncMock,
                return_value=_make_state("https://example.com/image.png"),
            ),
            patch("backend.api.image_proxy.httpx.AsyncClient", return_value=mock_http_client),
        ):
            resp = client.get("/api/image/hero/test-thread")

        assert resp.status_code == 502

    def test_timeout_returns_504(self):
        """httpx.TimeoutException → 504."""
        mock_http_client = AsyncMock()
        mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
        mock_http_client.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.get = AsyncMock(
            side_effect=httpx.TimeoutException("timed out")
        )

        with (
            patch(
                "backend.api.image_proxy.workflow_graph.aget_state",
                new_callable=AsyncMock,
                return_value=_make_state("https://example.com/image.png"),
            ),
            patch("backend.api.image_proxy.httpx.AsyncClient", return_value=mock_http_client),
        ):
            resp = client.get("/api/image/hero/test-thread")

        assert resp.status_code == 504

    def test_aget_state_exception_returns_500(self):
        """aget_state raises an unexpected error → 500."""
        with patch(
            "backend.api.image_proxy.workflow_graph.aget_state",
            new_callable=AsyncMock,
            side_effect=RuntimeError("DB connection failed"),
        ):
            resp = client.get("/api/image/hero/test-thread")
        assert resp.status_code == 500
