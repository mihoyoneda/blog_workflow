"""
backend/graph/state.py — LangGraph state definition for the blog workflow.
Mirrors all session fields from techaudit_agent.py _init() (L270-298).
"""

from __future__ import annotations

from typing import TypedDict


class BlogState(TypedDict, total=False):
    # ── Input ────────────────────────────────────────────────────
    category: str

    # ── Phase 1: Research ────────────────────────────────────────
    topics: list[dict]          # fetch_topics() results — 5 topics
    topic: dict                 # user-selected topic {title, description, trend_signal}
    titles: list[dict]          # fetch_titles() results — 5 titles
    title: dict                 # user-selected title {title, angle, primary_keyword, seo_rationale}
    search_results: list        # deep_research() results — 8 sources (= all_sources)
    notebooklm_context: str     # _build_notebooklm_context() result
    accepted_sources: list      # user-approved sources (⊆ search_results)

    # ── Phase 2: Outline ─────────────────────────────────────────
    outline: dict               # generate_outline() result

    # ── Phase 3: Draft ───────────────────────────────────────────
    draft: dict                 # generate_article / generate_article_claude output JSON
    actual_writer: str          # "claude" | "gemini" | "gemini_fallback"
    fallback_reason: str        # Gemini fallback reason (empty = no fallback)

    # ── Phase 4: QA & Final ──────────────────────────────────────
    qa_checks: list             # run_comprehensive_qa() results (10 checks)
    rubric_scores: dict | None  # score_article_rubric() results {criterion: score}
    rerun_strategies: list      # _generate_rerun_strategies() results (up to 3)
    hero_image_url: str         # pollinations_url() (proxy endpoint serves it)
    final_post: dict            # user-approved final article

    # ── HITL control ─────────────────────────────────────────────
    current_phase: int          # 1–4
    human_feedback: str         # free-text feedback from HITL 3 (DraftEditor)
    human_action: str           # "approve" | "edit" | "regenerate"
    selected_strategy: dict | None  # strategy from HITL 4 (FinalApproval), takes priority over human_feedback

    # ── Execution metadata ────────────────────────────────────────
    qa_rerun_count: int         # number of QA re-runs
    model_used: str             # actual Gemini model name
    claude_model_used: str      # actual Claude model name
    gen_error: str              # generation error message (empty = success)
