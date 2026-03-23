"""
backend/main.py — FastAPI application entry point.

Run with:
  uvicorn backend.main:app --reload --port 3001

Both this server AND the Vite dev server (npm run dev, :5173) must run simultaneously.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import health, image_proxy, workflow
from backend.api.stream import stream_workflow

app = FastAPI(title="TechBlog v2 API", version="2.0.0")

# ── CORS — allow Vite dev server ──────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(workflow.router)
app.include_router(image_proxy.router)

# SSE endpoint registered separately to preserve EventSourceResponse type
app.add_api_route(
    "/api/workflow/stream/{thread_id}",
    stream_workflow,
    methods=["GET"],
    tags=["stream"],
)
