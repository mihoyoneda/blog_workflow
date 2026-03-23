"""
backend/graph/nodes.py — All LangGraph node implementations (12 nodes: 6 exec + 6 HITL).
All nodes are async def for compatibility with graph.astream_events().
Synchronous tool calls are wrapped in asyncio.to_thread() to avoid blocking the event loop.
HITL nodes use interrupt() — the graph pauses and waits for Command(resume=...).
"""

from __future__ import annotations

import asyncio

from langgraph.types import interrupt

from backend.clients import gemini_client, anthropic_client
from backend.graph.state import BlogState
from backend.tools.article import do_generate
from backend.tools.image import hero_image_url
from backend.tools.outline import generate_outline
from backend.tools.qa import _generate_rerun_strategies, run_comprehensive_qa, score_article_rubric
from backend.tools.search import deep_research, fetch_titles, fetch_topics


# ════════════════════════════════════════════════════════════════
# Phase 1 — Research (3 exec nodes + 3 HITL nodes)
# ════════════════════════════════════════════════════════════════

async def node_topics(state: BlogState) -> dict:
    """Fetch 5 trending topics for the selected category."""
    user_direction = state.get("human_feedback", "")
    topics = await asyncio.to_thread(fetch_topics, gemini_client, state["category"], user_direction)
    return {"topics": topics, "current_phase": 1, "human_feedback": ""}


async def node_hitl_topics(state: BlogState) -> dict:
    """
    HITL 1a — pause for user to select a topic.
    interrupt() payload: {node, topics}
    resume value: HITLResponse dict from frontend via Command(resume=...)
    """
    resume = interrupt({"node": "hitl_topics", "topics": state["topics"]})
    action = resume.get("human_action", "approve")
    if action == "regenerate":
        return {"human_action": "regenerate", "human_feedback": resume.get("human_feedback", "")}
    return {
        "topic": resume["topic"],
        "human_action": "approve",
    }


async def node_titles(state: BlogState) -> dict:
    """Fetch 5 title options for the selected topic."""
    user_direction = state.get("human_feedback", "")
    titles = await asyncio.to_thread(fetch_titles, gemini_client, state["topic"], user_direction)
    return {"titles": titles, "human_feedback": ""}


async def node_hitl_titles(state: BlogState) -> dict:
    """
    HITL 1b — pause for user to select a title.
    interrupt() payload: {node, titles}
    resume value: HITLResponse dict
    """
    resume = interrupt({"node": "hitl_titles", "titles": state["titles"]})
    action = resume.get("human_action", "approve")
    if action == "regenerate":
        return {"human_action": "regenerate", "human_feedback": resume.get("human_feedback", "")}
    return {
        "title": resume["title"],
        "human_action": "approve",
    }


async def node_research(state: BlogState) -> dict:
    """Deep-research 8 authoritative sources for the selected title."""
    title_text = state["title"]["title"]
    sources, context = await asyncio.to_thread(deep_research, gemini_client, title_text)
    return {
        "search_results": sources,
        "notebooklm_context": context,
    }


async def node_hitl_sources(state: BlogState) -> dict:
    """
    HITL 1c — pause for user to review and approve/decline sources.
    interrupt() payload: {node, search_results, notebooklm_context}
    Declined sources remain in search_results (used as supplementary context by Claude).
    """
    resume = interrupt({
        "node": "hitl_sources",
        "search_results": state["search_results"],
        "notebooklm_context": state["notebooklm_context"],
    })
    action = resume.get("human_action", "approve")
    if action == "regenerate":
        return {"human_action": "regenerate"}
    accepted = resume.get("accepted_sources", state["search_results"])
    return {
        "accepted_sources": accepted,
        "human_action": "approve",
    }


# ════════════════════════════════════════════════════════════════
# Phase 2 — Outline (1 exec node + 1 HITL node)
# ════════════════════════════════════════════════════════════════

async def node_outline(state: BlogState) -> dict:
    """Generate a structured article outline from research results."""
    title_text = state["title"]["title"]
    user_direction = state.get("human_feedback", "")
    outline = await asyncio.to_thread(
        generate_outline,
        gemini_client,
        title_text,
        state["search_results"],
        state.get("notebooklm_context", ""),
        user_direction,
    )
    return {"outline": outline, "current_phase": 2, "human_feedback": ""}


async def node_hitl_outline(state: BlogState) -> dict:
    """
    HITL 2 — pause for user to review/edit the outline.
    interrupt() payload: {node, outline}
    """
    resume = interrupt({"node": "hitl_outline", "outline": state["outline"]})
    action = resume.get("human_action", "approve")
    if action == "regenerate":
        return {"human_action": "regenerate", "human_feedback": resume.get("human_feedback", "")}
    edited = resume.get("edited_outline") or state["outline"]
    return {
        "outline": edited,
        "human_action": "approve",
    }


# ════════════════════════════════════════════════════════════════
# Phase 3 — Draft (1 exec node + 1 HITL node)
# ════════════════════════════════════════════════════════════════

async def node_draft(state: BlogState) -> dict:
    """
    Generate the article draft using Claude→Gemini fallback orchestration.
    qa_feedback: selected_strategy.guidance (HITL 4) takes priority over human_feedback (HITL 3).
    """
    strategy_guidance = (state.get("selected_strategy") or {}).get("guidance", "")
    human_fb = state.get("human_feedback", "")
    qa_feedback = "\n\n".join(filter(None, [strategy_guidance, human_fb]))

    title_text = state["title"]["title"]
    result = await asyncio.to_thread(
        do_generate,
        gemini_client,
        anthropic_client,
        title_text,
        state.get("accepted_sources", state.get("search_results", [])),
        state.get("search_results", []),
        state.get("notebooklm_context", ""),
        qa_feedback,
    )

    return {
        "draft": result.article,
        "actual_writer": result.actual_writer,
        "fallback_reason": result.fallback_reason,
        "model_used": result.model_used,
        "claude_model_used": result.claude_model_used,
        "gen_error": result.gen_error,
        "current_phase": 3,
        "selected_strategy": None,
        "human_feedback": "",
    }


async def node_hitl_draft(state: BlogState) -> dict:
    """
    HITL 3 — pause for user to review the draft.
    Options: approve or regenerate (with human_feedback).
    Direct text editing is not supported in the current UI — edited_draft is unused.
    interrupt() payload: {node, draft, actual_writer, fallback_reason}
    """
    resume = interrupt({
        "node": "hitl_draft",
        "draft": state["draft"],
        "actual_writer": state.get("actual_writer", ""),
        "fallback_reason": state.get("fallback_reason", ""),
    })
    action = resume.get("human_action", "approve")

    if action == "regenerate":
        return {
            "human_action": "regenerate",
            "human_feedback": resume.get("human_feedback", ""),
            "selected_strategy": resume.get("selected_strategy"),
        }

    edited = resume.get("edited_draft")
    if edited:
        return {"human_action": "approve", "draft": edited}
    return {"human_action": "approve"}


# ════════════════════════════════════════════════════════════════
# Phase 4 — QA & Final (1 exec node + 1 HITL node)
# ════════════════════════════════════════════════════════════════

async def node_qa(state: BlogState) -> dict:
    """
    Run QA, rubric scoring, rerun strategy generation, and hero image URL generation.
    Separated from node_draft to allow independent re-execution.
    """
    draft = state["draft"]

    # run_comprehensive_qa and _generate_rerun_strategies are CPU-bound (regex only) —
    # still run in thread to be safe and consistent.
    qa_checks = await asyncio.to_thread(run_comprehensive_qa, draft)
    rubric_scores = await asyncio.to_thread(score_article_rubric, gemini_client, draft)
    rerun_strategies = _generate_rerun_strategies(qa_checks)  # pure Python, fast
    image_url = hero_image_url(state["title"]["title"])       # pure Python, fast

    return {
        "qa_checks": qa_checks,
        "rubric_scores": rubric_scores,
        "rerun_strategies": rerun_strategies,
        "hero_image_url": image_url,
        "current_phase": 4,
        "qa_rerun_count": state.get("qa_rerun_count", 0),
    }


async def node_hitl_final(state: BlogState) -> dict:
    """
    HITL 4 — pause for user to approve publication or request regeneration with a strategy.
    interrupt() payload: {node, qa_checks, rubric_scores, rerun_strategies, hero_image_url, draft}
    """
    resume = interrupt({
        "node": "hitl_final",
        "qa_checks": state["qa_checks"],
        "rubric_scores": state.get("rubric_scores"),
        "rerun_strategies": state.get("rerun_strategies", []),
        "hero_image_url": state.get("hero_image_url", ""),
        "draft": state["draft"],
    })
    action = resume.get("human_action", "approve")

    if action == "regenerate":
        return {
            "human_action": "regenerate",
            "selected_strategy": resume.get("selected_strategy"),
            "human_feedback": resume.get("human_feedback", ""),
            "qa_rerun_count": state.get("qa_rerun_count", 0) + 1,
        }

    return {
        "human_action": "approve",
        "final_post": state["draft"],
    }
