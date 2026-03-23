"""
backend/tools/outline.py — Article outline generation (new in v2).
Produces a structured JSON outline compatible with generate_article() schema.
"""

from __future__ import annotations

from backend.tools.utils import (
    _call,
    _extract_text,
    _json_cfg,
    _parse_json,
)

OUTLINE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading":         {"type": "string"},
                    "key_points":      {"type": "array", "items": {"type": "string"}},
                    "estimated_words": {"type": "integer"},
                },
            },
        },
        "comparison": {
            "type": "object",
            "properties": {
                "heading":      {"type": "string"},
                "alternatives": {"type": "array", "items": {"type": "string"}},
            },
        },
        "anti_recommendation": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "focus":   {"type": "string"},
            },
        },
        "tco_analysis": {
            "type": "object",
            "properties": {
                "heading":        {"type": "string"},
                "cost_categories": {"type": "array", "items": {"type": "string"}},
            },
        },
    },
}


def generate_outline(
    client,
    title: str,
    search_results: list[dict],
    notebooklm_context: str,
    user_direction: str = "",
) -> dict:
    """
    Generate a structured article outline using Gemini.
    The outline drives article generation and can be edited by the user (HITL 2).
    """
    sources_summary = "\n".join(
        f"[{s['id']}] ({s['tier']}) {s['title']} — {s['snippet']}"
        for s in search_results
    )

    prompt = f"""
You are a senior technical editor planning an article outline for a senior engineering audience.
Using the research sources below, produce a detailed JSON article outline.

━━━━━━━━━━━━ ARTICLE TITLE ━━━━━━━━━━━━
{title}

━━━━━━━━━━━━ NOTEBOOKLM SYNTHESIS ━━━━━━━━━━━━
{notebooklm_context[:2000]}

━━━━━━━━━━━━ RESEARCH SOURCES ━━━━━━━━━━━━
{sources_summary}

━━━━━━━━━━━━ OUTLINE REQUIREMENTS ━━━━━━━━━━━━
- 3–5 body sections, each 250–350 estimated words
- Each section: a clear H2 heading + 3–5 key points (specific claims, not vague topics)
- comparison: heading + 2–3 named alternatives to compare
- anti_recommendation: heading + specific failure scenario or scale limit to cover
- tco_analysis: heading + 4–5 cost categories (licensing, infra, training, maintenance, exit)

━━━━━━━━━━━━ OUTPUT FORMAT ━━━━━━━━━━━━
Return ONLY a JSON object matching this schema:
{{
  "sections": [
    {{
      "heading": "H2 section title",
      "key_points": ["specific point backed by source data", "..."],
      "estimated_words": 300
    }}
  ],
  "comparison": {{
    "heading": "Comparative Analysis heading",
    "alternatives": ["Alternative A", "Alternative B", "Alternative C"]
  }},
  "anti_recommendation": {{
    "heading": "When NOT to use heading",
    "focus": "primary failure scenario or scale limit to address"
  }},
  "tco_analysis": {{
    "heading": "TCO heading",
    "cost_categories": ["Licensing", "Infrastructure", "Training", "Maintenance", "Exit costs"]
  }}
}}

No preamble, no markdown fences. Output ONLY the JSON.
"""
    if user_direction:
        prompt += f"\n\n[User Direction]: {user_direction}"
    resp, _ = _call(client, prompt, _json_cfg(schema=OUTLINE_SCHEMA))
    return _parse_json(_extract_text(resp))
