"""
backend/tools/image.py — Pollinations.ai hero image URL generation.
Extracted from techaudit_agent.py (L492-502).
"""

from __future__ import annotations

import hashlib
from urllib.parse import quote


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16) % 100_000


def pollinations_url(
    prompt: str,
    w: int = 1200,
    h: int = 630,
    seed: int = 42,
) -> str:
    """Return a Pollinations.ai Flux image URL (no API key needed)."""
    enc = quote(prompt[:400])
    return (
        f"https://image.pollinations.ai/prompt/{enc}"
        f"?width={w}&height={h}&model=flux&nologo=true&enhance=true&seed={seed}"
    )


def hero_image_url(title: str) -> str:
    """Generate the standard hero image URL for a given article title."""
    prompt = (
        f"cinematic wide-angle technical illustration for: {title}, "
        "dark background, indigo and cyan glow, professional tech photography style, "
        "high detail, 8k, no text"
    )
    return pollinations_url(prompt, w=1400, h=500, seed=_seed(title))
