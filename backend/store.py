"""
backend/store.py — Shared in-memory stores for pending workflow inputs and HITL resumes.

Both workflow.py and stream.py import from here to avoid circular imports.

WARNING: Single-process only (uvicorn --workers 1).
         For multi-worker production, replace with Redis or similar.
"""

# thread_id → initial input dict {"category": "..."}
pending_inputs: dict[str, dict] = {}

# thread_id → HITL response dict (HITLResponse structure from frontend)
pending_resumes: dict[str, dict] = {}
