"""
backend/api/image_proxy.py — Hero image proxy endpoint.
GET /api/image/hero/{thread_id}

Fetches the Pollinations.ai image server-side to avoid browser CSP blocks
(same reason v1 used requests.get() in _do_generate()).
Uses the hero_image_url stored in the workflow checkpoint.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from backend.graph.builder import workflow_graph

router = APIRouter(prefix="/api/image", tags=["image"])


@router.get("/hero/{thread_id}")
async def get_hero_image(thread_id: str):
    """
    Download the hero image for the given workflow thread and stream it to the client.
    Falls back to 404 if the thread has no hero_image_url yet.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await workflow_graph.aget_state(config)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to retrieve workflow state.") from exc

    if state is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    image_url: str = state.values.get("hero_image_url", "")
    if not image_url:
        raise HTTPException(status_code=404, detail="Hero image not yet generated")

    try:
        async with httpx.AsyncClient(timeout=35.0) as client:
            r = await client.get(image_url)
        if r.status_code != 200:
            raise HTTPException(status_code=502, detail=f"Upstream image fetch failed: {r.status_code}")
        content_type = r.headers.get("content-type", "image/jpeg")
        return Response(content=r.content, media_type=content_type)
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Image fetch timed out") from exc
