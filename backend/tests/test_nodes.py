"""
backend/tests/test_nodes.py — Unit tests for all HITL and exec node logic.

HITL nodes: `interrupt()` is patched to return a resume dict directly,
bypassing LangGraph's pause/resume mechanism. This lets us test the
approve / regenerate / feedback branching in isolation.

Exec nodes: `asyncio.to_thread` is patched with an async shim so the
underlying tool functions (also patched) are called synchronously.
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.graph.nodes import (
    node_draft,
    node_hitl_draft,
    node_hitl_final,
    node_hitl_outline,
    node_hitl_titles,
    node_hitl_topics,
    node_outline,
    node_titles,
    node_topics,
)


# ── helpers ────────────────────────────────────────────────────────

async def _to_thread_shim(fn, *args, **kwargs):
    """Runs the (mocked) sync tool function directly in the async test context."""
    return fn(*args, **kwargs)


# ── HITL 1a: node_hitl_topics ─────────────────────────────────────

class TestHitlTopics:
    async def test_approve_returns_topic(self):
        topic = {"title": "eBPF Observability", "description": "Desc", "trend_signal": "Hot"}
        resume = {"human_action": "approve", "topic": topic}
        state = {"topics": [topic]}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_topics(state)

        assert result["human_action"] == "approve"
        assert result["topic"] == topic

    async def test_regenerate_captures_feedback(self):
        resume = {"human_action": "regenerate", "human_feedback": "Focus on cloud-native"}
        state = {"topics": []}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_topics(state)

        assert result["human_action"] == "regenerate"
        assert result["human_feedback"] == "Focus on cloud-native"

    async def test_regenerate_without_feedback_defaults_to_empty(self):
        resume = {"human_action": "regenerate"}
        state = {"topics": []}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_topics(state)

        assert result["human_feedback"] == ""


# ── HITL 1b: node_hitl_titles ─────────────────────────────────────

class TestHitlTitles:
    async def test_approve_returns_title(self):
        title = {"title": "How eBPF Changes Everything", "angle": "Deep dive",
                 "primary_keyword": "ebpf", "seo_rationale": "High intent"}
        resume = {"human_action": "approve", "title": title}
        state = {"titles": [title]}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_titles(state)

        assert result["human_action"] == "approve"
        assert result["title"] == title

    async def test_regenerate_captures_feedback(self):
        resume = {"human_action": "regenerate", "human_feedback": "More technical angle"}
        state = {"titles": []}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_titles(state)

        assert result["human_action"] == "regenerate"
        assert result["human_feedback"] == "More technical angle"


# ── HITL 2: node_hitl_outline ─────────────────────────────────────

class TestHitlOutline:
    def _sample_outline(self):
        return {
            "sections": [{"heading": "S1", "key_points": ["P1"], "estimated_words": 300}],
            "comparison": {"heading": "Comp", "alternatives": ["A"]},
            "anti_recommendation": {"heading": "Anti", "focus": "Small scale"},
            "tco_analysis": {"heading": "TCO", "cost_categories": ["Licensing"]},
        }

    async def test_approve_uses_edited_outline(self):
        original = self._sample_outline()
        edited = {**original, "sections": [{"heading": "Edited S1", "key_points": ["P1"], "estimated_words": 300}]}
        resume = {"human_action": "approve", "edited_outline": edited}
        state = {"outline": original}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_outline(state)

        assert result["outline"]["sections"][0]["heading"] == "Edited S1"

    async def test_approve_without_edit_uses_original(self):
        original = self._sample_outline()
        resume = {"human_action": "approve"}
        state = {"outline": original}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_outline(state)

        assert result["outline"] == original

    async def test_regenerate_captures_feedback(self):
        resume = {"human_action": "regenerate", "human_feedback": "Add migration section"}
        state = {"outline": self._sample_outline()}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_outline(state)

        assert result["human_action"] == "regenerate"
        assert result["human_feedback"] == "Add migration section"


# ── HITL 3: node_hitl_draft ───────────────────────────────────────

class TestHitlDraft:
    def _sample_draft(self):
        return {
            "article_title": "Test Article",
            "executive_summary": "Summary here",
            "sections": [{"heading": "S1", "content": "Content"}],
        }

    async def test_approve_without_edit(self):
        resume = {"human_action": "approve"}
        state = {"draft": self._sample_draft(), "actual_writer": "claude", "fallback_reason": ""}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_draft(state)

        assert result["human_action"] == "approve"
        assert "draft" not in result  # no edited_draft → state unchanged

    async def test_approve_with_edited_draft(self):
        original = self._sample_draft()
        edited = {**original, "article_title": "Edited Title"}
        resume = {"human_action": "approve", "edited_draft": edited}
        state = {"draft": original, "actual_writer": "claude", "fallback_reason": ""}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_draft(state)

        assert result["human_action"] == "approve"
        assert result["draft"]["article_title"] == "Edited Title"

    async def test_regenerate_with_feedback(self):
        resume = {"human_action": "regenerate", "human_feedback": "Strengthen citations"}
        state = {"draft": self._sample_draft(), "actual_writer": "claude", "fallback_reason": ""}

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_draft(state)

        assert result["human_action"] == "regenerate"
        assert result["human_feedback"] == "Strengthen citations"


# ── HITL 4: node_hitl_final ───────────────────────────────────────

class TestHitlFinal:
    def _sample_state(self):
        return {
            "draft": {"article_title": "Final Article", "executive_summary": "S",
                      "sections": [{"heading": "S1", "content": "C"}]},
            "qa_checks": [{"category": "Structure", "check": "Has title", "passed": True, "note": ""}],
            "rubric_scores": {"Clarity": 8.0},
            "rerun_strategies": [],
            "hero_image_url": "https://example.com/image.jpg",
            "qa_rerun_count": 0,
        }

    async def test_approve_sets_final_post(self):
        resume = {"human_action": "approve"}
        state = self._sample_state()

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_final(state)

        assert result["human_action"] == "approve"
        assert result["final_post"] == state["draft"]

    async def test_regenerate_increments_rerun_count(self):
        strategy = {"name": "strengthen_evidence", "label": "Strengthen Evidence",
                    "guidance": "Add more citations", "icon": "🔍", "description": "Desc"}
        resume = {
            "human_action": "regenerate",
            "selected_strategy": strategy,
            "human_feedback": "Especially the TCO section",
        }
        state = self._sample_state()

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_final(state)

        assert result["human_action"] == "regenerate"
        assert result["qa_rerun_count"] == 1  # incremented from 0
        assert result["selected_strategy"] == strategy
        assert result["human_feedback"] == "Especially the TCO section"

    async def test_regenerate_feedback_only(self):
        resume = {"human_action": "regenerate", "human_feedback": "Make it shorter"}
        state = self._sample_state()

        with patch("backend.graph.nodes.interrupt", return_value=resume):
            result = await node_hitl_final(state)

        assert result["human_action"] == "regenerate"
        assert result["selected_strategy"] is None
        assert result["human_feedback"] == "Make it shorter"


# ── Exec node: node_topics ────────────────────────────────────────

class TestNodeTopics:
    async def test_passes_user_direction_and_clears_feedback(self):
        sample_topics = [{"title": "T", "description": "D", "trend_signal": "S"}]
        mock_fetch = MagicMock(return_value=sample_topics)
        state = {"category": "AI", "human_feedback": "enterprise focus"}

        with (
            patch("backend.graph.nodes.fetch_topics", mock_fetch),
            patch("asyncio.to_thread", side_effect=_to_thread_shim),
        ):
            result = await node_topics(state)

        assert result["topics"] == sample_topics
        assert result["human_feedback"] == ""  # cleared after use
        # Verify user_direction was forwarded
        call_kwargs = mock_fetch.call_args
        assert call_kwargs[0][2] == "enterprise focus"  # third positional arg

    async def test_empty_feedback_still_clears(self):
        mock_fetch = MagicMock(return_value=[])
        state = {"category": "AI", "human_feedback": ""}

        with (
            patch("backend.graph.nodes.fetch_topics", mock_fetch),
            patch("asyncio.to_thread", side_effect=_to_thread_shim),
        ):
            result = await node_topics(state)

        assert result["human_feedback"] == ""
