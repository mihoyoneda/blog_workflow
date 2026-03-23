"""
backend/clients.py — Gemini and Claude client singletons.
Extracted from techaudit_agent.py (L306-314), @st.cache_resource replaced with
module-level singletons. Initialization failures are logged but do NOT crash the
process at import time — errors surface at first API call instead.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from google import genai
from backend.config import GEMINI_API_KEY, ANTHROPIC_API_KEY

logger = logging.getLogger(__name__)

try:
    import anthropic as _anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


@lru_cache(maxsize=1)
def get_gemini_client() -> genai.Client:
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set. Add it to blog_workflow/.env and restart."
        )
    return genai.Client(api_key=GEMINI_API_KEY)


@lru_cache(maxsize=1)
def get_anthropic_client():
    if not ANTHROPIC_AVAILABLE:
        return None
    if not ANTHROPIC_API_KEY:
        return None
    return _anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# Module-level singletons — initialized eagerly so import errors are visible at startup,
# but wrapped in try/except so a missing key logs a warning instead of crashing uvicorn.
try:
    gemini_client: genai.Client = get_gemini_client()
except RuntimeError as _e:
    logger.warning("Gemini client not initialized: %s", _e)
    gemini_client = None  # type: ignore[assignment]

try:
    anthropic_client = get_anthropic_client()
except Exception as _e:
    logger.warning("Anthropic client not initialized: %s", _e)
    anthropic_client = None
