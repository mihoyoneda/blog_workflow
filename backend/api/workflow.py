"""
backend/api/workflow.py — Workflow control endpoints.
POST /api/workflow/start   — create thread, store initial input (no graph execution)
POST /api/workflow/resume  — store HITL response in pending_resumes (no graph execution)
GET  /api/workflow/state/{thread_id} — checkpoint state query (SSE fallback)
"""

from __future__ import annotations

import uuid

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.graph.builder import workflow_graph
from backend.store import pending_inputs, pending_resumes

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/workflow", tags=["workflow"])


# ── Request models ────────────────────────────────────────────────

class StartRequest(BaseModel):
    category: str


class ResumeRequest(BaseModel):
    thread_id: str
    human_action: str                     # "approve" | "edit" | "regenerate"
    human_feedback: str | None = None
    selected_strategy: dict | None = None
    topic: dict | None = None
    title: dict | None = None
    accepted_sources: list | None = None
    edited_outline: dict | None = None
    edited_draft: str | None = None


# ── Endpoints ────────────────────────────────────────────────────

@router.post("/start")
async def start_workflow(body: StartRequest):
    """
    Create a new workflow thread. Stores the initial category in pending_inputs.
    Graph execution begins when the client connects to the SSE stream.
    """
    thread_id = str(uuid.uuid4())
    pending_inputs[thread_id] = {"category": body.category}
    return {"thread_id": thread_id}


@router.post("/resume")
async def resume_workflow(body: ResumeRequest):
    """
    Store a HITL response in pending_resumes. Graph execution resumes when
    the client reconnects to the SSE stream (GET /api/workflow/stream/{thread_id}).
    NOTE: LangGraph Command objects cannot be stored in the checkpointer directly —
    we store the raw payload here and construct Command(resume=...) in stream.py.
    """
    pending_resumes[body.thread_id] = body.model_dump(exclude={"thread_id"}, exclude_none=False)
    return {"ok": True}


@router.get("/state/{thread_id}")
async def get_workflow_state(thread_id: str):
    """
    Return the current checkpoint state for a thread (SSE fallback for polling clients).
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await workflow_graph.aget_state(config)
        if state is None or state.metadata is None:
            raise HTTPException(status_code=404, detail="Thread not found")
        return {
            "thread_id": thread_id,
            "values": state.values,
            "next": list(state.next) if state.next else [],
            "tasks": [t.name for t in state.tasks] if state.tasks else [],
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("aget_state error for thread %s", thread_id)
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow state.") from exc
