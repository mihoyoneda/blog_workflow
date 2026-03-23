"""
backend/tools/qa.py — Programmatic QA, rubric scoring, and rerun strategy generation.
Extracted from techaudit_agent.py (L899-1005, L1159-1249, L1474-1503).
All Streamlit dependencies removed.
"""

from __future__ import annotations

import re

from backend.config import RUBRIC_CRITERIA
from backend.tools.utils import (
    _call,
    _extract_text,
    _json_cfg,
    _parse_json,
)


# ── Article → Markdown (for rubric scoring) ──────────────────────

def _article_to_markdown(art: dict) -> str:
    lines = [f"# {art.get('article_title', '')}\n"]
    lines.append(f"> **Executive Summary**\n>\n> {art.get('executive_summary', '')}\n")
    for sec in art.get("sections", []):
        lines.append(f"\n## {sec['heading']}\n")
        lines.append(sec.get("content", ""))
        if sec.get("chart_suggestion"):
            lines.append(f"\n*📊 Chart: {sec['chart_suggestion']}*\n")
    cmp = art.get("comparison", {})
    if cmp:
        lines.append(f"\n## {cmp.get('heading', 'Comparative Analysis')}\n")
        lines.append(cmp.get("content", ""))
    tco = art.get("tco_analysis", {})
    if tco:
        lines.append(f"\n## {tco.get('heading', 'TCO Analysis')}\n")
        lines.append(tco.get("content", ""))
    anti = art.get("anti_recommendation", {})
    if anti:
        lines.append(f"\n## {anti.get('heading', 'When NOT to Use')}\n")
        lines.append(anti.get("content", ""))
    if art.get("conclusion"):
        lines.append(f"\n## Conclusion\n{art['conclusion']}")
    meta = art.get("metadata", {})
    if meta:
        lines.append(f"\n---\n**SEO Slug:** `/{meta.get('seo_slug', '')}`")
        lines.append(f"**Meta Description:** {meta.get('meta_description', '')}")
    refs = art.get("references", [])
    if refs:
        lines.append("\n## References\n" + "\n".join(refs))
    return "\n".join(lines)


# ── Programmatic QA (10-gate) ────────────────────────────────────

def run_comprehensive_qa(art: dict) -> list[dict]:
    """Run 10 programmatic quality checks on the generated article."""
    checks: list[dict] = []

    exec_sum = art.get("executive_summary", "")
    body_parts = [s.get("content", "") for s in art.get("sections", [])]
    cmp_content  = art.get("comparison", {}).get("content", "")
    tco_content  = art.get("tco_analysis", {}).get("content", "")
    anti_content = art.get("anti_recommendation", {}).get("content", "")
    conclusion   = art.get("conclusion", "")
    all_text = " ".join(filter(None, [exec_sum, *body_parts, cmp_content, tco_content, anti_content, conclusion]))
    body_text = " ".join(body_parts)

    def add(category: str, check: str, passed: bool, note: str) -> None:
        checks.append({"category": category, "check": check, "passed": passed, "note": note})

    # ── Structure ────────────────────────────────────────────────
    wc = len(all_text.split())
    add("Structure", "Word count: 1,000–1,500 words",
        1000 <= wc <= 1600,
        f"Detected ~{wc:,} words")

    exec_wc = len(exec_sum.split())
    add("Structure", "Executive summary ~100 words (±20)",
        80 <= exec_wc <= 120,
        f"{exec_wc} words detected — target 80–120")

    n_sections = len(art.get("sections", []))
    add("Structure", "At least 3 body sections present",
        n_sections >= 3,
        f"{n_sections} section(s) found")

    # ── Evidence ─────────────────────────────────────────────────
    citations = re.findall(r'\[\d+\]', body_text + cmp_content + tco_content + anti_content)
    add("Evidence", "Source citations [N] present in body (≥3)",
        len(citations) >= 3,
        f"{len(citations)} citation reference(s) detected")

    quant_cited = re.findall(
        r'(\d[\d,.]*\s*(?:%|ms|µs|ns|GB|TB|PB|W|kW|MHz|GHz|TFLOPS|TOPS|tokens|fps|x|×)[^[]{0,80}\[\d+\])',
        all_text)
    add("Evidence", "Quantitative claims paired with citations (≥3)",
        len(quant_cited) >= 3,
        f"{len(quant_cited)} cited numeric claim(s) detected")

    # ── Critical Analysis ─────────────────────────────────────────
    alts = art.get("comparison", {}).get("alternatives", [])
    n_alts = sum(1 for a in alts if isinstance(a, dict))
    add("Critical Analysis", "Comparison section with ≥2 alternatives",
        n_alts >= 2,
        f"{n_alts} alternative(s) found")

    add("Critical Analysis", "Anti-recommendation section present (>50 words)",
        len(anti_content.split()) > 50,
        f"{len(anti_content.split())} words in anti-rec section")

    add("Critical Analysis", "TCO analysis present (>50 words)",
        len(tco_content.split()) > 50,
        f"{len(tco_content.split())} words in TCO section")

    # ── Technical Depth ───────────────────────────────────────────
    phys_kw = ["thermal", "power", "watt", "TDP", "cooling", "heat", "bottleneck",
               "bandwidth", "latency", "scaling limit", "memory wall", "bandwidth-bound"]
    found_phys = [kw for kw in phys_kw if kw.lower() in all_text.lower()]
    add("Technical Depth", "Physical constraints addressed (thermal/power/scaling)",
        len(found_phys) >= 2,
        f"Keywords: {', '.join(found_phys[:4]) or 'none detected'}")

    # ── Clarity ───────────────────────────────────────────────────
    acronym_defs = re.findall(r'[A-Z]{2,}[0-9]*\s*\(', all_text)
    add("Clarity", "Acronyms defined on first use (ABC (…) pattern)",
        len(acronym_defs) >= 1,
        f"{len(acronym_defs)} definition(s): {', '.join(set(d.strip() for d in acronym_defs[:3]))}")

    # ── Style ─────────────────────────────────────────────────────
    bullets = re.findall(r'(?:^|\n)\s*[-•*]\s', all_text)
    add("Style", "No bullet points — paragraph format only",
        len(bullets) == 0,
        "Clean" if not bullets else f"{len(bullets)} bullet(s) detected")

    return checks


# ── Rubric scoring ───────────────────────────────────────────────

def score_article_rubric(client, art: dict) -> dict:
    """Ask Gemini to score the article on RUBRIC_CRITERIA, each 0.0–10.0."""
    full_text = _article_to_markdown(art)
    criteria_list = "\n".join(f'"{name}"' for name, _ in RUBRIC_CRITERIA)
    prompt = f"""You are a rigorous editorial evaluator. Score the following technical article on each criterion below.
Return ONLY a valid JSON object where keys are the exact criterion names and values are float scores between 0.0 and 10.0.

Criteria:
{criteria_list}

Article (truncated to first 4000 chars):
{full_text[:4000]}"""
    try:
        resp, _ = _call(client, prompt, _json_cfg())
        text = _extract_text(resp)
        scores = _parse_json(text)
        result = {}
        for name, _ in RUBRIC_CRITERIA:
            result[name] = float(scores.get(name, 0.0))
        return result
    except Exception:
        return {name: 0.0 for name, _ in RUBRIC_CRITERIA}


# ── Rerun strategy generation ────────────────────────────────────

def _generate_rerun_strategies(qa_checks: list[dict]) -> list[dict]:
    """Return up to 3 targeted regeneration strategy dicts based on which QA checks failed."""
    failed = [c for c in qa_checks if not c.get("passed")]
    if not failed:
        return []

    # Group failures by category
    failed_cats: dict[str, list[str]] = {}
    for c in failed:
        cat = c.get("category", "Other")
        failed_cats.setdefault(cat, []).append(c["check"])

    strategies = []

    # Strategy A — deep fix on worst category
    top_cat = max(failed_cats, key=lambda k: len(failed_cats[k]))
    top_checks = failed_cats[top_cat]
    strategies.append({
        "icon": "🎯",
        "label": f"Deep Fix: {top_cat}",
        "name": "Deep Fix",
        "description": (
            f"Concentrate entirely on {top_cat}. "
            f"Fix {len(top_checks)} failing check(s): "
            + ", ".join(top_checks[:3])
            + ("…" if len(top_checks) > 3 else ".")
        ),
        "guidance": (
            f"PRIORITY FIX — '{top_cat}' category has the most failures.\n"
            + "\n".join(f"• {ch}" for ch in top_checks)
            + "\nImprove these maximally while keeping the rest intact."
        ),
    })

    # Strategy B — balanced revision across all categories
    all_failed = list(failed)
    strategies.append({
        "icon": "⚖️",
        "label": "Balanced Revision",
        "name": "Balanced Revision",
        "description": (
            f"Spread improvements evenly across all {len(failed_cats)} failing "
            f"categories ({len(all_failed)} total checks) with equal attention to each."
        ),
        "guidance": (
            "BALANCED REVISION — fix ALL failed checks proportionally:\n"
            + "\n".join(
                f"• [{c.get('category', '?')}] {c['check']}"
                for c in all_failed
            )
            + "\nDo not sacrifice any category for another."
        ),
    })

    # Strategy C — structural rewrite or citation focus
    struct_cats = {"Structure", "Content", "Writing Quality"}
    struct_checks = [c["check"] for c in failed if c.get("category") in struct_cats]
    if struct_checks:
        strategies.append({
            "icon": "🔄",
            "label": "Structural Rewrite or Citation Fix",
            "name": "Structural Rewrite or Citation Fix",
            "description": (
                "Rewrite the article structure from scratch — preserve research facts "
                "but reorganize content flow and section order entirely."
            ),
            "guidance": (
                "STRUCTURAL REWRITE requested:\n"
                "• Rewrite the executive summary with sharper, more specific claims\n"
                "• Reorder body sections for stronger logical progression\n"
                "• Open each section with a concrete topic sentence backed by a cited data point\n"
                f"Also fix: {', '.join(struct_checks[:5])}"
            ),
        })
    else:
        strategies.append({
            "icon": "📚",
            "label": "Structural Rewrite or Citation Fix",
            "name": "Structural Rewrite or Citation Fix",
            "description": (
                "Focus on evidence quality: every factual claim must carry a [N] citation, "
                "and all accepted sources must be used."
            ),
            "guidance": (
                "CITATION & EVIDENCE FOCUS:\n"
                "• Add [N] inline citation after every factual claim\n"
                "• All accepted sources must be cited at least once\n"
                "• Label vendor claims [VENDOR] and independent analysis [INDEPENDENT]\n"
                f"Also address: {', '.join(c['check'] for c in all_failed[:5])}"
            ),
        })

    return strategies[:3]
