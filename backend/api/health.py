"""
backend/api/health.py — Health check and dev utility endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.graph.builder import workflow_graph
from backend.store import pending_inputs, pending_resumes

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/api/threads")
async def list_threads():
    """Dev utility — list active thread IDs in pending stores."""
    return {
        "pending_inputs": list(pending_inputs.keys()),
        "pending_resumes": list(pending_resumes.keys()),
    }
