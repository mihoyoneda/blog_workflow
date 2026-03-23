"""
backend/tools/article.py — Article generation with Claude→Gemini fallback.
Extracted from techaudit_agent.py (L638-895, L1803-1903).
All st.session_state / st.spinner references removed.
QA and hero image generation are NOT included here — they live in qa.py and image.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from backend.config import CLAUDE_MODEL, CLAUDE_FALLBACK
from backend.tools.utils import (
    _call,
    _extract_text,
    _json_cfg,
    _parse_json,
)

# ── Article JSON schema (extracted from techaudit_agent.py L638) ─
ARTICLE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "article_title":     {"type": "string"},
        "executive_summary": {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading":          {"type": "string"},
                    "content":          {"type": "string"},
                    "chart_suggestion": {"type": "string"},
                    "image_prompt":     {"type": "string"},
                },
            },
        },
        "comparison": {
            "type": "object",
            "properties": {
                "heading":      {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":     {"type": "string"},
                            "pros":     {"type": "string"},
                            "cons":     {"type": "string"},
                            "tco_note": {"type": "string"},
                            "best_for": {"type": "string"},
                        },
                    },
                },
                "content": {"type": "string"},
            },
        },
        "anti_recommendation": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        "tco_analysis": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        "conclusion":   {"type": "string"},
        "references":   {"type": "array", "items": {"type": "string"}},
        "metadata": {
            "type": "object",
            "properties": {
                "seo_slug":         {"type": "string"},
                "meta_description": {"type": "string"},
                "title_tag":        {"type": "string"},
                "word_count":       {"type": "integer"},
            },
        },
        "quality_audit": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check":  {"type": "string"},
                    "passed": {"type": "boolean"},
                    "note":   {"type": "string"},
                },
            },
        },
    },
}


# ── Return type ───────────────────────────────────────────────────

@dataclass
class GenerationResult:
    article: dict
    actual_writer: str        # "claude" | "gemini" | "gemini_fallback"
    fallback_reason: str      # empty string = no fallback
    model_used: str           # actual Gemini model name used
    claude_model_used: str    # actual Claude model name used
    gen_error: str            # empty string = success
    metadata: dict = field(default_factory=dict)


# ── Credit error detection ───────────────────────────────────────

_CREDIT_ERRORS: tuple[str, ...] = (
    "credit balance is too low",
    "insufficient_quota",
    "billing",
    "payment",
    "upgrade or purchase",
    "402",
)


def _is_credit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in _CREDIT_ERRORS)


# ── Gemini article generation ────────────────────────────────────

def generate_article(client, title: str, sources: list[dict], context: str) -> dict:
    """Generate article using Gemini. `sources` should be accepted_sources."""
    sources_block = "\n".join(
        f"[{s['id']}] {s['title']} ({s['publisher']}, {s['date']}) | {s['snippet']} | KEY DATA: {s.get('key_data_point', '')}"
        for s in sources
    )

    prompt = f"""
You are the world's most rigorous technical content auditor writing for a senior engineering audience.
Produce a complete article JSON adhering to every rule below.

━━━━━━━━━━━━ ARTICLE TITLE ━━━━━━━━━━━━
{title}

━━━━━━━━━━━━ NOTEBOOKLM CONTEXT (cross-reference this) ━━━━━━━━━━━━
{context}

━━━━━━━━━━━━ VERIFIED SOURCES (cite as [1]–[8]) ━━━━━━━━━━━━
{sources_block}

━━━━━━━━━━━━ STRICT CONTENT RULES ━━━━━━━━━━━━
WORD COUNT      : 1,000–1,500 words total (executive summary + all sections + comparison + anti-rec + tco + conclusion).
EXECUTIVE SUMMARY: Exactly 100 words. No bullets. Opening paragraph that captures the full argument.
PARAGRAPHS      : No bullet points anywhere. Use 2–3 sentence paragraphs for scannability.
EVIDENCE        : Every quantitative claim MUST include: value, source [N], methodology/test-condition, and independent-vs-vendor label.
                  Include at least 3 perspectives per major claim.
CRITICAL ANALYSIS: Address vendor lock-in, hidden infrastructure/training costs, and performance limitations.
                  Include conservative AND optimistic estimates side-by-side.
ANTI-RECOMMENDATION: Explain precisely when engineers should AVOID this technology (failure scenarios, scale limits, alternative-is-better situations).
TCO ANALYSIS    : Cover licensing, infrastructure, training/onboarding, maintenance, and exit costs over a 3-year horizon.
COMPARISON      : Compare 2–3 direct alternatives on: latency, throughput, cost/unit, vendor-lock-in risk, maturity.
ACRONYMS        : Define every acronym on first use. Example: "FP8 (8-bit floating-point)".
PHYSICAL LIMITS : Address thermal envelope, power budget, or scaling bottleneck relevant to the topic.

━━━━━━━━━━━━ OUTPUT SCHEMA ━━━━━━━━━━━━
Return a single JSON object (no markdown fences) with these keys:

article_title        : string  — final optimized title
executive_summary    : string  — exactly 100 words, paragraph form
sections             : array of objects, each with:
  heading            : H2 text
  content            : 3–4 paragraphs of body text (no bullets)
  chart_suggestion   : specific chart type + axes + what it should visualize
  image_prompt       : detailed Flux/Stable-Diffusion prompt for a professional technical illustration
comparison           : object with heading, alternatives (array), content
anti_recommendation  : object with heading, content
tco_analysis         : object with heading, content
conclusion           : string — 1 strong closing paragraph
references           : array of formatted citation strings [1]–[8]
metadata             : object with seo_slug, meta_description (≤155 chars), title_tag, word_count
quality_audit        : array of 4 objects (check, passed, note) verifying:
  1. All numbers cited with methodology + independent validation
  2. All acronyms defined at first use
  3. Physical constraints (thermal/power/scaling) addressed
  4. No repetition — themes consolidated

Output ONLY the JSON. No preamble, no explanation.
"""
    resp, _ = _call(client, prompt, _json_cfg())
    return _parse_json(_extract_text(resp))


# ── Claude article generation ────────────────────────────────────

def generate_article_claude(
    anthropic_client,
    title: str,
    accepted_sources: list[dict],
    all_sources: list[dict],
    context: str,
    qa_feedback: str = "",
) -> dict:
    """
    Generate article using Claude. Falls back to claude-sonnet on first error.
    accepted_sources  — sources the editor approved (will be cited)
    all_sources       — all 8 search results (declined ones are supplementary context only)
    """
    accepted_ids = {s.get("id") for s in accepted_sources}
    declined = [s for s in all_sources if s.get("id") not in accepted_ids]

    primary_block = "\n".join(
        f"[{s['id']}] {s['title']} ({s['publisher']}, {s['date']})\n"
        f"    Snippet: {s['snippet']}\n"
        f"    Key data: {s.get('key_data_point', '')}"
        for s in accepted_sources
    )
    supp_block = (
        "\n".join(
            f"[{s['id']}] {s['title']} — context only, do NOT cite"
            for s in declined
        )
        if declined
        else "None"
    )
    qa_note = (
        f"\n\nPREVIOUS DRAFT FAILED THESE QA CHECKS — fix them in this version:\n{qa_feedback}"
        if qa_feedback
        else ""
    )

    prompt = f"""You are the world's most rigorous technical content auditor writing for senior engineers.
Produce a complete article as a single JSON object following every rule below.{qa_note}

━━━━━━━━━━━━ ARTICLE TITLE ━━━━━━━━━━━━
{title}

━━━━━━━━━━━━ NOTEBOOKLM CONTEXT ━━━━━━━━━━━━
{context}

━━━━━━━━━━━━ PRIMARY SOURCES — CITE THESE (accepted by editor) ━━━━━━━━━━━━
{primary_block}

━━━━━━━━━━━━ SUPPLEMENTARY CONTEXT — DO NOT CITE ━━━━━━━━━━━━
{supp_block}

━━━━━━━━━━━━ STRICT CONTENT RULES ━━━━━━━━━━━━
WORD COUNT       : 1,000–1,500 words total.
EXECUTIVE SUMMARY: Exactly 100 words. Paragraph form. No bullets.
PARAGRAPHS       : NO bullet points anywhere. 2–3 sentence paragraphs only.
EVIDENCE         : Every quantitative claim must include value + [sourceN] + methodology/test condition + (VENDOR CLAIM) or (INDEPENDENT).
                   Include ≥3 perspectives per major claim.
CRITICAL ANALYSIS: Address vendor lock-in, hidden infra/training costs, scaling limits.
                   Pair conservative estimates with optimistic ones.
ANTI-REC         : Explain exactly when NOT to use this technology (failure thresholds, scale limits, better alternatives exist).
TCO              : Cover licensing, infra, training/onboarding, maintenance, exit costs over 3 years.
COMPARISON       : 2–3 direct alternatives on latency, throughput, $/unit, lock-in risk, maturity.
ACRONYMS         : Define every acronym on first use, e.g. "FP8 (8-bit floating-point)".
PHYSICAL LIMITS  : Explicitly address thermal envelope, power budget, or scaling bottleneck.

━━━━━━━━━━━━ OUTPUT SCHEMA ━━━━━━━━━━━━
Return ONE JSON object — no markdown fences, no preamble:

{{
  "article_title": "final optimized title string",
  "executive_summary": "exactly 100 words paragraph",
  "sections": [
    {{
      "heading": "H2 text",
      "content": "3-4 paragraphs no bullets",
      "chart_suggestion": "chart type + axes + what to visualize",
      "image_prompt": "detailed Flux prompt for technical illustration"
    }}
  ],
  "comparison": {{
    "heading": "string",
    "alternatives": [
      {{"name":"string","pros":"string","cons":"string","tco_note":"string","best_for":"string"}}
    ],
    "content": "analysis paragraph"
  }},
  "anti_recommendation": {{"heading":"string","content":"paragraph"}},
  "tco_analysis":        {{"heading":"string","content":"paragraph"}},
  "conclusion": "strong closing paragraph",
  "references": ["[1] formatted citation", "..."],
  "metadata": {{
    "seo_slug": "kebab-case",
    "meta_description": "≤155 chars",
    "title_tag": "SEO title",
    "word_count": 1200
  }},
  "quality_audit": [
    {{"check":"All numbers cited with methodology","passed":true,"note":"..."}},
    {{"check":"All acronyms defined at first use","passed":true,"note":"..."}},
    {{"check":"Physical constraints addressed","passed":true,"note":"..."}},
    {{"check":"No repetition — themes consolidated","passed":true,"note":"..."}}
  ]
}}

Output ONLY the JSON. Nothing else."""

    model = CLAUDE_MODEL
    for attempt in range(2):
        try:
            msg = anthropic_client.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text
            return _parse_json(raw)
        except Exception as e:
            if attempt == 0 and CLAUDE_FALLBACK not in model:
                model = CLAUDE_FALLBACK
                continue
            raise e


# ── Fallback orchestration ───────────────────────────────────────

def do_generate(
    gemini_client,
    anthropic_client,
    title: str,
    accepted_sources: list[dict],
    all_sources: list[dict],
    notebooklm_context: str,
    qa_feedback: str = "",
) -> GenerationResult:
    """
    Article generation with smart Claude→Gemini fallback.
    Extracted from techaudit_agent.py _do_generate() (L1817-1903), state/spinner removed.

    Known limitation: generate_article() (Gemini) has no qa_feedback parameter.
    If Claude credit error triggers fallback, the regeneration strategy guidance
    will NOT be passed to Gemini — inherited structural limitation from v1.
    """
    art = None
    fallback_reason = ""
    actual_writer = ""
    claude_model_used = CLAUDE_MODEL
    model_used = ""

    # ── Attempt 1: Claude ─────────────────────────────────────────
    if anthropic_client is not None:
        try:
            art = generate_article_claude(
                anthropic_client,
                title,
                accepted_sources,
                all_sources,
                notebooklm_context,
                qa_feedback=qa_feedback,
            )
            actual_writer = "claude"
        except Exception as exc:
            if _is_credit_error(exc):
                fallback_reason = (
                    f"Anthropic credit balance too low — article written by Gemini instead. "
                    f"Add credits at console.anthropic.com/billing to use Claude next time."
                )
            else:
                fallback_reason = (
                    f"Claude error ({str(exc)[:120]}) — automatically fell back to Gemini."
                )

    # ── Attempt 2: Gemini (primary or fallback) ───────────────────
    if art is None:
        try:
            art = generate_article(
                gemini_client,
                title,
                accepted_sources,
                notebooklm_context,
            )
            actual_writer = "gemini_fallback" if fallback_reason else "gemini"
            model_used = "gemini"  # actual model tracked in _call internals
        except Exception as exc2:
            return GenerationResult(
                article={},
                actual_writer="",
                fallback_reason=fallback_reason,
                model_used="",
                claude_model_used=claude_model_used,
                gen_error=str(exc2),
            )

    return GenerationResult(
        article=art,
        actual_writer=actual_writer,
        fallback_reason=fallback_reason,
        model_used=model_used,
        claude_model_used=claude_model_used,
        gen_error="",
        metadata=art.get("metadata", {}),
    )
