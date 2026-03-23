"""
backend/graph/builder.py — LangGraph StateGraph assembly and compilation.
Assembles all 12 nodes with conditional routing for 7 HITL interrupt points.
"""

from __future__ import annotations

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, StateGraph

from backend.graph.nodes import (
    node_draft,
    node_hitl_draft,
    node_hitl_final,
    node_hitl_outline,
    node_hitl_sources,
    node_hitl_titles,
    node_hitl_topics,
    node_outline,
    node_qa,
    node_research,
    node_titles,
    node_topics,
)
from backend.graph.state import BlogState


# ── Routing functions ─────────────────────────────────────────────

def _route_hitl_topics(state: BlogState) -> str:
    """After HITL 1a: regenerate → re-fetch topics; approve → fetch titles."""
    if state.get("human_action") == "regenerate":
        return "topics"
    return "titles"


def _route_hitl_titles(state: BlogState) -> str:
    """After HITL 1b: regenerate → re-fetch titles (same topic); approve → research."""
    if state.get("human_action") == "regenerate":
        return "titles"
    return "research"


def _route_hitl_sources(state: BlogState) -> str:
    """After HITL 1c: regenerate → re-run research; approve → outline."""
    if state.get("human_action") == "regenerate":
        return "research"
    return "outline"


def _route_hitl_outline(state: BlogState) -> str:
    """After HITL 2: regenerate → re-generate outline; approve → draft."""
    if state.get("human_action") == "regenerate":
        return "outline"
    return "draft"


def _route_hitl_draft(state: BlogState) -> str:
    """After HITL 3: regenerate → re-generate draft; approve → QA."""
    if state.get("human_action") == "regenerate":
        return "draft"
    return "qa"


def _route_hitl_final(state: BlogState) -> str:
    """After HITL 4: regenerate → re-generate draft (Phase 3 restart); approve → END."""
    if state.get("human_action") == "regenerate":
        return "draft"
    return END


# ── Graph assembly ────────────────────────────────────────────────

def build_graph():
    """
    Build and compile the blog workflow StateGraph.

    Graph structure:
    ┌─ Phase 1 ──────────────────────────────────────────────────────────────┐
    │ topics → hitl_topics → titles → hitl_titles → research → hitl_sources │
    │    ↑         │ regenerate         ↑    │ regenerate       │ regenerate  │
    │    └─────────┘                    └────┘                  └─→ research  │
    └────────────────────────────────────────────────────────────────────────┘
         │ approve
         ↓
    outline → hitl_outline ──approve──→ draft → hitl_draft ──approve──→ qa → hitl_final ──approve──→ END
                  │ regenerate                   │ regenerate                  │ regenerate
                  └──→ outline                   └──→ draft                   └──→ draft
    """
    graph = StateGraph(BlogState)

    # Register all nodes
    graph.add_node("topics",       node_topics)
    graph.add_node("hitl_topics",  node_hitl_topics)
    graph.add_node("titles",       node_titles)
    graph.add_node("hitl_titles",  node_hitl_titles)
    graph.add_node("research",     node_research)
    graph.add_node("hitl_sources", node_hitl_sources)
    graph.add_node("outline",      node_outline)
    graph.add_node("hitl_outline", node_hitl_outline)
    graph.add_node("draft",        node_draft)
    graph.add_node("hitl_draft",   node_hitl_draft)
    graph.add_node("qa",           node_qa)
    graph.add_node("hitl_final",   node_hitl_final)

    # Entry point
    graph.set_entry_point("topics")

    # Phase 1 linear edges
    graph.add_edge("topics", "hitl_topics")
    graph.add_conditional_edges("hitl_topics", _route_hitl_topics, ["topics", "titles"])
    graph.add_edge("titles", "hitl_titles")
    graph.add_conditional_edges("hitl_titles", _route_hitl_titles, ["titles", "research"])
    graph.add_edge("research", "hitl_sources")
    graph.add_conditional_edges("hitl_sources", _route_hitl_sources, ["research", "outline"])

    # Phase 2
    graph.add_edge("outline", "hitl_outline")
    graph.add_conditional_edges("hitl_outline", _route_hitl_outline, ["outline", "draft"])

    # Phase 3
    graph.add_edge("draft", "hitl_draft")
    graph.add_conditional_edges("hitl_draft", _route_hitl_draft, ["draft", "qa"])

    # Phase 4
    graph.add_edge("qa", "hitl_final")
    graph.add_conditional_edges("hitl_final", _route_hitl_final, ["draft", END])

    checkpointer = InMemorySaver()
    return graph.compile(checkpointer=checkpointer)


# Module-level compiled graph — import this in stream.py
workflow_graph = build_graph()

# Node names for event filtering in SSE stream
NODE_NAMES: frozenset[str] = frozenset({
    "topics", "hitl_topics",
    "titles", "hitl_titles",
    "research", "hitl_sources",
    "outline", "hitl_outline",
    "draft", "hitl_draft",
    "qa", "hitl_final",
})
