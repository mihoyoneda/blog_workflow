"""
backend/tests/test_search.py — Tests for fetch_topics and fetch_titles.

Strategy: mock _call_search / _call to capture the prompt string, then assert
that [User Direction] is injected when user_direction is provided and absent otherwise.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.tools.search import fetch_titles, fetch_topics

SAMPLE_TOPICS_JSON = '[{"title": "Topic A", "description": "Desc A", "trend_signal": "Signal A"}]'
SAMPLE_TITLES_JSON = (
    '[{"title": "Title A", "angle": "Angle", '
    '"primary_keyword": "keyword", "seo_rationale": "rationale"}]'
)


def _make_resp(text: str) -> MagicMock:
    resp = MagicMock()
    resp.text = text
    return resp


# ── fetch_topics ──────────────────────────────────────────────────

class TestFetchTopics:
    def test_with_user_direction_injects_into_prompt(self):
        captured: dict = {}

        def mock_call_search(client, prompt):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TOPICS_JSON), "model"

        with patch("backend.tools.search._call_search", side_effect=mock_call_search):
            result = fetch_topics(MagicMock(), "AI Infrastructure", "Focus on enterprise cases")

        assert "[User Direction]: Focus on enterprise cases" in captured["prompt"]
        assert len(result) == 1
        assert result[0]["title"] == "Topic A"

    def test_without_user_direction_no_injection(self):
        captured: dict = {}

        def mock_call_search(client, prompt):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TOPICS_JSON), "model"

        with patch("backend.tools.search._call_search", side_effect=mock_call_search):
            result = fetch_topics(MagicMock(), "AI Infrastructure")

        assert "[User Direction]" not in captured["prompt"]
        assert len(result) == 1

    def test_empty_user_direction_treated_as_no_direction(self):
        captured: dict = {}

        def mock_call_search(client, prompt):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TOPICS_JSON), "model"

        with patch("backend.tools.search._call_search", side_effect=mock_call_search):
            fetch_topics(MagicMock(), "AI", "")

        assert "[User Direction]" not in captured["prompt"]

    def test_category_appears_in_prompt(self):
        captured: dict = {}

        def mock_call_search(client, prompt):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TOPICS_JSON), "model"

        with patch("backend.tools.search._call_search", side_effect=mock_call_search):
            fetch_topics(MagicMock(), "Kubernetes Networking")

        assert "Kubernetes Networking" in captured["prompt"]


# ── fetch_titles ──────────────────────────────────────────────────

class TestFetchTitles:
    def test_with_user_direction_injects_into_prompt(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TITLES_JSON), "model"

        topic = {"title": "eBPF Observability", "description": "Using eBPF for deep visibility"}
        with patch("backend.tools.search._call", side_effect=mock_call):
            result = fetch_titles(MagicMock(), topic, "More technical, less clickbait")

        assert "[User Direction]: More technical, less clickbait" in captured["prompt"]
        assert len(result) == 1
        assert result[0]["title"] == "Title A"

    def test_without_user_direction_no_injection(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TITLES_JSON), "model"

        topic = {"title": "eBPF Observability", "description": "Desc"}
        with patch("backend.tools.search._call", side_effect=mock_call):
            fetch_titles(MagicMock(), topic)

        assert "[User Direction]" not in captured["prompt"]

    def test_topic_name_appears_in_prompt(self):
        captured: dict = {}

        def mock_call(client, prompt, cfg):
            captured["prompt"] = prompt
            return _make_resp(SAMPLE_TITLES_JSON), "model"

        topic = {"title": "Wasm on the Edge", "description": "WebAssembly runtimes at the edge"}
        with patch("backend.tools.search._call", side_effect=mock_call):
            fetch_titles(MagicMock(), topic)

        assert "Wasm on the Edge" in captured["prompt"]
