"""
backend/tools/search.py — Topic/title/source search tools.
Extracted from techaudit_agent.py (L509-634), Streamlit dependencies removed.
All _call() callers unpack (response, actual_model) as required.
"""

from __future__ import annotations

from backend.tools.utils import (
    _call,
    _call_search,
    _extract_text,
    _json_cfg,
    _plain_cfg,
    _parse_json,
)


def fetch_topics(client, category: str, user_direction: str = "") -> list[dict]:
    """
    Fetch 5 trending technical topics for the given category using Google Search grounding.
    Returns list of dicts: {title, description, trend_signal}.
    """
    prompt = f"""
You are a senior technical analyst. Using Google Search, identify EXACTLY 5 highly-specific,
trending technical topics within "{category}" based on 2025-2026 data (conferences, papers,
benchmark announcements, product launches).

Return ONLY a JSON array of 5 objects:
[
  {{"title": "<concise topic name>", "description": "<2-sentence technical rationale, cite data point or event>", "trend_signal": "<what makes it trending in 2025-2026>"}},
  ...
]
No preamble, no explanation, no markdown fences.
"""
    if user_direction:
        prompt += f"\n\n[User Direction]: {user_direction}"
    resp, _ = _call_search(client, prompt)
    return _parse_json(_extract_text(resp))


def fetch_titles(client, topic: dict, user_direction: str = "") -> list[dict]:
    """
    Fetch 5 SEO-optimised article title options for the given topic.
    Returns list of dicts: {title, angle, primary_keyword, seo_rationale}.
    """
    topic_name = topic.get("title", str(topic))
    topic_desc = topic.get("description", "")

    prompt = f"""
You are an expert technical SEO strategist. Generate EXACTLY 5 article title options for the topic below.
Each title must be unique in angle and optimised for search intent.

Topic: {topic_name}
Description: {topic_desc}

Return ONLY a JSON array of 5 objects:
[
  {{
    "title": "<article title (60-80 chars)>",
    "angle": "<unique editorial angle — e.g. cost analysis, performance deep-dive, migration guide>",
    "primary_keyword": "<main SEO keyword phrase>",
    "seo_rationale": "<1-sentence why this ranks for the keyword>"
  }},
  ...
]
No preamble, no explanation, no markdown fences.
"""
    if user_direction:
        prompt += f"\n\n[User Direction]: {user_direction}"
    resp, _ = _call(client, prompt, _json_cfg())
    return _parse_json(_extract_text(resp))


def deep_research(client, title: str) -> tuple[list[dict], str]:
    """
    Find 8 high-authority sources for the given article title using Google Search grounding.
    Returns (sources_list, notebooklm_context_text).
    """
    prompt = f"""
You are a technical research auditor. Using Google Search, find EXACTLY 8 high-authority sources
for the following article title. Sources MUST be published between 2023 and 2026.

Article Title: "{title}"

Authority tiers (you MUST cover all):
- Tier 1 (2 sources): Peer-reviewed papers (arXiv, IEEE, ACM, Nature)
- Tier 2 (2 sources): Official vendor whitepapers or technical documentation
- Tier 3 (2 sources): Tier-1 tech journalism (The Register, Ars Technica, AnandTech, Tom's Hardware, IEEE Spectrum)
- Tier 4 (2 sources): Independent benchmarks or audit reports (MLCommons, SPEC, Phoronix, TPC)

For each source return:
{{
  "id": 1,
  "title": "<exact article/paper title>",
  "url": "<full URL>",
  "publisher": "<publisher/venue>",
  "date": "<YYYY-MM or YYYY>",
  "tier": "<Tier 1|2|3|4>",
  "snippet": "<2-sentence key finding or claim from this source>",
  "key_data_point": "<specific number, metric, or fact from this source>"
}}

Return ONLY a JSON array of 8 objects.
"""
    resp, _ = _call_search(client, prompt)
    sources = _parse_json(_extract_text(resp))

    # Annotate sources with grounding verification flag
    real_urls: list[str] = []
    try:
        for chunk in resp.candidates[0].grounding_metadata.grounding_chunks:
            if chunk.web and chunk.web.uri:
                real_urls.append(chunk.web.uri)
    except Exception:
        pass

    for src in sources:
        src["grounded"] = any(
            src.get("url", "").split("/")[2] in u for u in real_urls
        )

    context = _build_notebooklm_context(client, title, sources)
    return sources, context


def _build_notebooklm_context(client, title: str, sources: list[dict]) -> str:
    """Synthesize a NotebookLM-style cross-reference knowledge base from 8 sources."""
    sources_text = "\n".join(
        f"[{s['id']}] ({s['tier']}) {s['title']} ({s['date']}) — {s['snippet']} KEY DATA: {s.get('key_data_point', 'N/A')}"
        for s in sources
    )
    prompt = f"""
You are simulating Google NotebookLM's deep contextual understanding layer.
Given 8 research sources for the article "{title}", produce a structured knowledge synthesis:

SOURCES:
{sources_text}

Produce a concise knowledge synthesis (400–500 words) that:
1. Identifies 3 consensus findings across ≥3 sources
2. Flags 2 conflicting claims between sources (with source IDs)
3. Lists 3 critical knowledge gaps NOT covered by these sources
4. Extracts the 5 most important quantitative data points with source IDs
5. Rates overall evidence strength: STRONG / MODERATE / WEAK with justification

Format as plain prose with labeled sections. This will be injected as context for article generation.
"""
    resp, _ = _call(client, prompt, _plain_cfg())
    return _extract_text(resp)
