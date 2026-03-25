"""
backend/tests/test_workflow_api.py — Integration tests for workflow API endpoints.

Uses FastAPI's synchronous TestClient (built on httpx + anyio) so no
async test infrastructure is required here.

Graph execution does NOT happen during /start or /resume — they only
read/write to in-memory dicts — so these tests are fast and reliable.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.store import pending_inputs, pending_resumes

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_stores():
    """Isolate each test by emptying shared stores before and after."""
    pending_inputs.clear()
    pending_resumes.clear()
    yield
    pending_inputs.clear()
    pending_resumes.clear()


# ── POST /api/workflow/start ──────────────────────────────────────

class TestStartWorkflow:
    def test_returns_thread_id(self):
        resp = client.post("/api/workflow/start", json={"category": "AI Infrastructure"})
        assert resp.status_code == 200
        data = resp.json()
        assert "thread_id" in data
        assert isinstance(data["thread_id"], str)
        assert len(data["thread_id"]) > 0

    def test_stores_category_in_pending_inputs(self):
        resp = client.post("/api/workflow/start", json={"category": "Kubernetes"})
        thread_id = resp.json()["thread_id"]
        assert thread_id in pending_inputs
        assert pending_inputs[thread_id]["category"] == "Kubernetes"

    def test_missing_category_returns_422(self):
        resp = client.post("/api/workflow/start", json={})
        assert resp.status_code == 422

    def test_each_call_generates_unique_thread_id(self):
        id1 = client.post("/api/workflow/start", json={"category": "A"}).json()["thread_id"]
        id2 = client.post("/api/workflow/start", json={"category": "A"}).json()["thread_id"]
        assert id1 != id2


# ── POST /api/workflow/resume ─────────────────────────────────────

class TestResumeWorkflow:
    def test_stores_approve_action(self):
        thread_id = "test-thread-approve"
        resp = client.post("/api/workflow/resume", json={
            "thread_id": thread_id,
            "human_action": "approve",
            "topic": {"title": "T", "description": "D", "trend_signal": "S"},
        })
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}
        assert pending_resumes[thread_id]["human_action"] == "approve"

    def test_stores_regenerate_with_feedback(self):
        thread_id = "test-thread-regen"
        resp = client.post("/api/workflow/resume", json={
            "thread_id": thread_id,
            "human_action": "regenerate",
            "human_feedback": "More enterprise focus",
        })
        assert resp.status_code == 200
        assert pending_resumes[thread_id]["human_feedback"] == "More enterprise focus"

    def test_missing_human_action_returns_422(self):
        resp = client.post("/api/workflow/resume", json={"thread_id": "x"})
        assert resp.status_code == 422

    def test_overwrites_previous_resume_for_same_thread(self):
        thread_id = "test-thread-overwrite"
        client.post("/api/workflow/resume", json={
            "thread_id": thread_id, "human_action": "approve"
        })
        client.post("/api/workflow/resume", json={
            "thread_id": thread_id, "human_action": "regenerate"
        })
        assert pending_resumes[thread_id]["human_action"] == "regenerate"


# ── GET /api/workflow/state/{thread_id} ───────────────────────────

class TestGetWorkflowState:
    def test_unknown_thread_returns_404(self):
        # InMemorySaver returns StateSnapshot with metadata=None for unknown threads.
        # The API checks state.metadata is None and raises HTTPException(404).
        resp = client.get("/api/workflow/state/nonexistent-thread-id-12345")
        assert resp.status_code == 404
