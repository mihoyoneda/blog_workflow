"""
backend/tools/utils.py — Low-level Gemini API helpers.
Extracted from techaudit_agent.py (L317-487), all st.session_state references removed.

Key change vs v1:
  _call() now returns tuple[GenerateContentResponse, str] — (response, actual_model_used).
  All callers MUST unpack: response, actual_model = _call(...)
  Use response, _ = _call(...) only when model tracking is irrelevant.
"""

from __future__ import annotations

import json
import re

from google.genai import types
from google.genai.types import GenerateContentResponse

from backend.config import MODEL_REASONING, MODEL_FALLBACK


# ── Config builders ──────────────────────────────────────────────

def _search_cfg() -> types.GenerateContentConfig:
    """GenerateContentConfig with Google Search grounding."""
    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.4,
    )


def _json_cfg(schema: dict | None = None) -> types.GenerateContentConfig:
    """GenerateContentConfig for structured JSON output (no search)."""
    cfg: dict = dict(
        response_mime_type="application/json",
        temperature=0.5,
    )
    if schema:
        cfg["response_schema"] = schema
    return types.GenerateContentConfig(**cfg)


def _plain_cfg() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(temperature=0.6)


# ── Text extraction ──────────────────────────────────────────────

def _extract_text(resp) -> str:
    """
    Safely pull text from a Gemini response.
    Tries resp.text first, then walks all parts skipping 'thought' parts
    (gemini-2.5 thinking tokens).
    Raises ValueError only if truly no text is found anywhere.
    """
    try:
        if resp.text:
            return resp.text
    except Exception:
        pass

    try:
        parts = resp.candidates[0].content.parts or []
        for part in parts:
            if getattr(part, "thought", False):
                continue
            t = getattr(part, "text", None)
            if t:
                return t
    except Exception:
        pass

    try:
        reason = str(resp.candidates[0].finish_reason)
    except Exception:
        reason = "unknown"

    raise ValueError(
        f"Model returned no usable text (finish_reason={reason}). "
        "This is a known intermittent behaviour of Google Search grounding — "
        "the request will be retried automatically."
    )


def _extract_text_safe(resp) -> str | None:
    """Like _extract_text but returns None instead of raising."""
    try:
        return _extract_text(resp)
    except ValueError:
        return None


# ── Core call ────────────────────────────────────────────────────

def _call(
    client,
    prompt: str,
    cfg,
    model: str = MODEL_REASONING,
) -> tuple[GenerateContentResponse, str]:
    """
    Call the Gemini API. Falls back to MODEL_FALLBACK on error (unless already using it).
    Returns (response, actual_model_used) — callers must unpack both values.
    """
    try:
        resp = client.models.generate_content(model=model, contents=prompt, config=cfg)
        return resp, model
    except Exception as e:
        if MODEL_FALLBACK not in str(model):
            resp = client.models.generate_content(
                model=MODEL_FALLBACK, contents=prompt, config=cfg
            )
            return resp, MODEL_FALLBACK
        raise e


# ── Search call with grounding fallback ─────────────────────────

def _call_search(client, prompt: str) -> tuple[GenerateContentResponse, str]:
    """
    Run a prompt with Google Search grounding.
    If the grounded response contains no text (known intermittent issue),
    silently retry with plain JSON mode.
    Returns (response, actual_model_used).
    """
    resp, actual_model = _call(client, prompt, _search_cfg())
    if _extract_text_safe(resp) is not None:
        return resp, actual_model
    # No text from grounded response — fall back to JSON mode (no search tool)
    resp2, actual_model2 = _call(client, prompt, _json_cfg())
    return resp2, actual_model2


# ── JSON parsing ─────────────────────────────────────────────────

def _parse_json(text: str | None) -> list | dict:
    """
    Robust JSON extraction from model output.
    Handles: markdown fences, mixed prose + JSON (grounding adds footnotes),
    trailing commas, and unescaped characters in string values.

    Strategy:
      1. Strip markdown fences and try direct parse.
      2. Walk the text to find the outermost balanced [ ] or { } block.
      3. Apply light repair (trailing commas, JS-style comments) and retry.
    """
    if not text:
        raise ValueError("Empty response — model returned no content.")

    # ── Step 1: fence strip + direct attempt ──────────────────────
    clean = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.M)
    clean = re.sub(r"\s*```\s*$", "", clean.strip(), flags=re.M)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # ── Step 2: extract outermost balanced bracket block ──────────
    def _extract_balanced(src: str, open_ch: str, close_ch: str) -> str | None:
        start = src.find(open_ch)
        if start == -1:
            return None
        depth, in_str, esc, i = 0, False, False, start
        while i < len(src):
            ch = src[i]
            if esc:
                esc = False
            elif ch == "\\" and in_str:
                esc = True
            elif ch == '"':
                in_str = not in_str
            elif not in_str:
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        return src[start : i + 1]
            i += 1
        return None

    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        block = _extract_balanced(clean, open_ch, close_ch)
        if block is None:
            continue
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            pass
        # ── Step 3: light repair ──────────────────────────────────
        repaired = block
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        repaired = re.sub(r"(?<!:)//[^\n\"]*", "", repaired)
        repaired = repaired.replace("\u2018", "'").replace("\u2019", "'")
        repaired = repaired.replace("\u201c", '"').replace("\u201d", '"')
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse JSON from model response.\n"
        f"First 300 chars of response:\n{text[:300]}"
    )
