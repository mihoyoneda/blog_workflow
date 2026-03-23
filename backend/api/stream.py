"""
backend/api/stream.py — SSE streaming endpoint.
GET /api/workflow/stream/{thread_id} is the single graph execution entry point.

Flow:
  1. Client connects → check pending_inputs (first run) or pending_resumes (resume)
  2. astream_events() drives graph execution; stream ends when graph pauses or completes
  3. Post-stream: inspect get_state().next — if non-empty, graph is at an interrupt
  4. Emit hitl_waiting or complete accordingly
  5. Client sends POST /resume → reconnects to SSE → repeat from step 1

NOTE: GraphInterrupt is NOT raised as a catchable exception from astream_events().
The graph simply stops yielding events when it hits an interrupt(). The correct way
to detect a pause is to call get_state() after the stream drains and check .next.
"""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter
from langgraph.types import Command
from sse_starlette.sse import EventSourceResponse

from backend.graph.builder import NODE_NAMES, workflow_graph
from backend.store import pending_inputs, pending_resumes

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/workflow", tags=["stream"])

PHASE_MAP: dict[str, int] = {
    "hitl_topics": 1,
    "hitl_titles": 1,
    "hitl_sources": 1,
    "hitl_outline": 2,
    "hitl_draft": 3,
    "hitl_final": 4,
}


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data)}


def _sanitize_error(exc: Exception) -> str:
    """Return a safe error message — omit API keys and internal stack details."""
    msg = str(exc)
    # Truncate at first newline to drop stack traces from SDK errors
    return msg.split("\n")[0][:200]


async def _event_generator(thread_id: str):
    config = {"configurable": {"thread_id": thread_id}}

    # ── Determine input: initial run vs. HITL resume ──────────────
    if thread_id in pending_inputs:
        input_or_command = pending_inputs.pop(thread_id)
    elif thread_id in pending_resumes:
        resume_value = pending_resumes.pop(thread_id)
        input_or_command = Command(resume=resume_value)
    else:
        yield _sse("error", {"message": "No pending input or resume for this thread."})
        return

    # ── Stream graph events ───────────────────────────────────────
    try:
        async for event in workflow_graph.astream_events(
            input_or_command,
            config=config,
            version="v2",
        ):
            kind = event["event"]
            name = event.get("name", "")

            if kind == "on_chain_start" and name in NODE_NAMES:
                yield _sse("phase_start", {"node": name})

            elif kind == "on_chain_end" and name in NODE_NAMES:
                output = event.get("data", {}).get("output", {})
                yield _sse("progress", {"node": name, "data": output})

    except Exception as exc:
        logger.exception("astream_events error for thread %s", thread_id)
        yield _sse("error", {"message": _sanitize_error(exc), "thread_id": thread_id})
        return

    # ── Post-stream: check if graph paused at an interrupt ────────
    # astream_events() ends normally whether the graph completed OR hit interrupt().
    # get_state().next is non-empty iff the graph is paused waiting for a resume.
    try:
        state = await workflow_graph.aget_state(config)
    except Exception as exc:
        logger.exception("aget_state error for thread %s", thread_id)
        yield _sse("error", {"message": _sanitize_error(exc), "thread_id": thread_id})
        return

    if state and state.next:
        # Graph is paused — extract interrupt payload from tasks
        interrupt_data: dict = {}
        node_name = "unknown"
        try:
            for task in state.tasks:
                if hasattr(task, "interrupts") and task.interrupts:
                    interrupt_data = task.interrupts[0].value or {}
                    node_name = interrupt_data.get("node", task.name or "unknown")
                    break
        except Exception:
            pass

        phase = PHASE_MAP.get(node_name, 0)
        yield _sse("hitl_waiting", {
            "phase": phase,
            "step": node_name,
            "data": interrupt_data,
            "thread_id": thread_id,
        })
    else:
        yield _sse("complete", {"thread_id": thread_id})


async def stream_workflow(thread_id: str):
    return EventSourceResponse(_event_generator(thread_id))


router_get_stream = stream_workflow
