"""
backend/tests/test_utils.py — Unit tests for _parse_json and _extract_text.
No mocking needed: these are pure-Python or operate on simple mock objects.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from backend.tools.utils import _extract_text, _parse_json


# ── _parse_json ───────────────────────────────────────────────────

class TestParseJson:
    def test_clean_array(self):
        result = _parse_json('[{"key": "value"}]')
        assert result == [{"key": "value"}]

    def test_clean_object(self):
        result = _parse_json('{"name": "test", "count": 3}')
        assert result == {"name": "test", "count": 3}

    def test_strips_markdown_fences(self):
        text = '```json\n[{"title": "A"}]\n```'
        result = _parse_json(text)
        assert result == [{"title": "A"}]

    def test_strips_plain_fences(self):
        text = '```\n{"key": "val"}\n```'
        result = _parse_json(text)
        assert result == {"key": "val"}

    def test_trailing_comma_in_object(self):
        result = _parse_json('[{"key": "value",}]')
        assert result == [{"key": "value"}]

    def test_trailing_comma_in_array(self):
        # Pure array input — no outer object that could confuse bracket-first extraction
        result = _parse_json('["a", "b",]')
        assert result == ["a", "b"]

    def test_json_embedded_in_prose(self):
        text = 'Here is the data:\n[{"id": 1}]\nThat is all.'
        result = _parse_json(text)
        assert result == [{"id": 1}]

    def test_curly_brace_json_in_prose(self):
        # Object without inner arrays so `{` block is extracted correctly
        text = 'Output:\n{"name": "test", "count": 5}\nDone.'
        result = _parse_json(text)
        assert result == {"name": "test", "count": 5}

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="Empty response"):
            _parse_json("")

    def test_none_raises(self):
        with pytest.raises(ValueError, match="Empty response"):
            _parse_json(None)

    def test_unparseable_raises(self):
        with pytest.raises(ValueError):
            _parse_json("this is not json at all and has no brackets")

    def test_curly_quotes_repaired(self):
        # Models sometimes output \u201c/\u201d instead of plain quotes
        text = '{"key": \u201cvalue\u201d}'
        result = _parse_json(text)
        assert result == {"key": "value"}


# ── _extract_text ─────────────────────────────────────────────────

class TestExtractText:
    def test_from_text_attribute(self):
        resp = MagicMock()
        resp.text = "hello world"
        assert _extract_text(resp) == "hello world"

    def test_falls_back_to_parts(self):
        part = MagicMock()
        part.thought = False
        part.text = "from parts"

        resp = MagicMock()
        type(resp).text = property(lambda self: (_ for _ in ()).throw(Exception("no text")))
        resp.candidates[0].content.parts = [part]

        assert _extract_text(resp) == "from parts"

    def test_skips_thought_parts(self):
        thought_part = MagicMock()
        thought_part.thought = True
        thought_part.text = "internal reasoning"

        real_part = MagicMock()
        real_part.thought = False
        real_part.text = "actual output"

        resp = MagicMock()
        type(resp).text = property(lambda self: (_ for _ in ()).throw(Exception("no text")))
        resp.candidates[0].content.parts = [thought_part, real_part]

        assert _extract_text(resp) == "actual output"

    def test_raises_when_no_text_anywhere(self):
        resp = MagicMock()
        type(resp).text = property(lambda self: (_ for _ in ()).throw(Exception("no text")))
        resp.candidates[0].content.parts = []
        resp.candidates[0].finish_reason = "MAX_TOKENS"

        with pytest.raises(ValueError):
            _extract_text(resp)
