"""
backend/config.py — Constants extracted from techaudit_agent.py (v1).
CATEGORIES is intentionally omitted: handled as frontend-only UI in v2.
"""

from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys ─────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")

# ── Model constants (extracted from techaudit_agent.py L242-247) ─
MODEL_REASONING: str = "gemini-2.5-pro"
MODEL_FALLBACK: str = "gemini-2.5-flash"
CLAUDE_MODEL: str = "claude-opus-4-6"
CLAUDE_FALLBACK: str = "claude-sonnet-4-6"

# ── Rubric criteria (extracted from techaudit_agent.py L258-265) ─
RUBRIC_CRITERIA: list[tuple[str, float]] = [
    ("Technical depth",      8.5),
    ("Clarity & structure",  8.0),
    ("Original insight",     7.0),
    ("Evidence & rigor",     6.5),
    ("Practical usefulness", 8.0),
    ("Writing quality",      8.5),
]
