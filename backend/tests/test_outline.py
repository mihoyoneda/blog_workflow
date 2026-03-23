"""
backend/tests/test_outline.py — Tests for generate_outline.

Verifies user_direction injection and that the parsed result contains
expected keys from the outline schema.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.tools.outline import generate_outline

SAMPLE_OUTLINE_JSON = """{
  "sections": [
    {"heading": "Section 1", "key_points": ["Point A", "Point B"], "estimated_words": 300}
  ],
  "comparison": {"heading": "Comparison", "alternatives": ["Alt A", "Alt B"]},
  "anti_recommendation": {"heading": "When NOT to Use", "focus": "Small teams"},
  "tco_analysis": {"heading": "TCO", "cost_categories": ["Licensing", "Infra"]}
}"""


def _make_resp(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


class TestGenerateOutline:
    def test_with_user_direction_injects_into_prompt(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_OUTLINE_JSON), "model"

        with patch("backend.tools.outline._call", side_effect=mock_call):
            result = generate_outline(
                MagicMock(),
                "Benchmarking LLM Inference Engines",
                [],
                "Some context here",
                "Add a cost comparison section",
            )

        assert "[User Direction]: Add a cost comparison section" in captured["prompt"]
        assert "sections" in result
        assert len(result["sections"]) == 1

    def test_without_user_direction_no_injection(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_OUTLINE_JSON), "model"

        with patch("backend.tools.outline._call", side_effect=mock_call):
            result = generate_outline(
                MagicMock(),
                "Benchmarking LLM Inference Engines",
                [],
                "",
            )

        assert "[User Direction]" not in captured["prompt"]
        assert "comparison" in result
        assert "anti_recommendation" in result
        assert "tco_analysis" in result

    def test_article_title_appears_in_prompt(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_OUTLINE_JSON), "model"

        with patch("backend.tools.outline._call", side_effect=mock_call):
            generate_outline(MagicMock(), "My Unique Title", [], "")

        assert "My Unique Title" in captured["prompt"]

    def test_sources_summary_appears_in_prompt(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_OUTLINE_JSON), "model"

        sources = [
            {"id": 1, "tier": "Tier 1", "title": "arXiv Paper", "snippet": "Key finding here"}
        ]
        with patch("backend.tools.outline._call", side_effect=mock_call):
            generate_outline(MagicMock(), "Title", sources, "")

        assert "arXiv Paper" in captured["prompt"]
