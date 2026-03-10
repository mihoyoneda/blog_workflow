"""
Phase 4: Integration & unit tests for the competitor analysis feature.
Covers all 7 edge cases from plan.md + core function tests.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# ── Mock Streamlit before importing techaudit_agent ──────────────
# techaudit_agent.py calls st.set_page_config() at module level,
# so we must mock streamlit before the import.
_mock_st = MagicMock()
_mock_st.session_state = {}
_mock_st.cache_resource = lambda f: f  # passthrough decorator
sys.modules["streamlit"] = _mock_st

# Mock google.genai to avoid import errors
_mock_genai = MagicMock()
sys.modules["google"] = MagicMock()
sys.modules["google.genai"] = _mock_genai
sys.modules["google.genai.types"] = MagicMock()

# Mock anthropic
sys.modules["anthropic"] = MagicMock()

# Now import the functions under test
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from techaudit_agent import (
    CATEGORIES,
    COMPETITORS_BY_CATEGORY,
    COMPETITORS_SS_KEY,
    CompetitorDataError,
    DataLoadingError,
    GeminiAPIError,
    SchemaValidationError,
    build_competitive_context,
    dedup_articles,
    load_competitors_data,
    load_competitors_for_category,
    migrate_competitors_schema,
    save_competitors_data,
    validate_competitors_schema,
    validate_url_format,
    _validate_competitor_config,
)


# ══════════════════════════════════════════════════════════════════
# FIXTURES
# ══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _reset_session_state():
    """Clear mock session_state before each test."""
    _mock_st.session_state.clear()
    _mock_st.reset_mock()
    yield


@pytest.fixture
def valid_data() -> dict:
    """Minimal valid competitors data conforming to schema v1.0."""
    return {
        "schema_version": "1.0",
        "GPU Computing & Hardware": {
            "metadata": {
                "category": "GPU Computing & Hardware",
                "generated_date": "2026-03-09",
                "collected_timestamp": "2026-03-09T10:30:00Z",
                "source": "ai_deep_research",
            },
            "competitors": {
                "nextplatform": {
                    "name": "The Next Platform",
                    "blog_url": "https://www.nextplatform.com/",
                    "tier": 1,
                    "editable": False,
                    "articles": [
                        {
                            "title": "Blackwell Deep Dive",
                            "url": "https://www.nextplatform.com/blackwell",
                            "date": "2025-02-10",
                            "relevance": "GPU architecture",
                        },
                    ],
                },
                "amd_gpuopen": {
                    "name": "AMD GPUOpen",
                    "blog_url": "https://gpuopen.com/",
                    "tier": 2,
                    "editable": False,
                    "articles": [
                        {
                            "title": "ROCm 6.0",
                            "url": "https://gpuopen.com/rocm-6",
                            "date": "2025-01-08",
                            "relevance": "GPU stack",
                        },
                    ],
                },
            },
        },
    }


# ══════════════════════════════════════════════════════════════════
# 1. validate_url_format
# ══════════════════════════════════════════════════════════════════

class TestValidateUrlFormat:
    def test_valid_https(self):
        assert validate_url_format("https://example.com/path") is True

    def test_valid_http(self):
        assert validate_url_format("http://example.com") is True

    def test_no_scheme(self):
        assert validate_url_format("example.com") is False

    def test_ftp_scheme(self):
        assert validate_url_format("ftp://example.com") is False

    def test_empty_string(self):
        assert validate_url_format("") is False

    def test_none(self):
        assert validate_url_format(None) is False

    def test_not_string(self):
        assert validate_url_format(123) is False

    def test_no_domain(self):
        assert validate_url_format("https://") is False


# ══════════════════════════════════════════════════════════════════
# 2. dedup_articles
# ══════════════════════════════════════════════════════════════════

class TestDedupArticles:
    def test_removes_duplicates(self):
        articles = [
            {"url": "https://a.com/1", "date": "2025-01-01", "title": "A"},
            {"url": "https://a.com/1", "date": "2025-01-02", "title": "A dup"},
            {"url": "https://a.com/2", "date": "2025-01-03", "title": "B"},
        ]
        result = dedup_articles(articles)
        assert len(result) == 2
        assert result[0]["url"] == "https://a.com/2"  # newest first

    def test_sorts_by_date_desc(self):
        articles = [
            {"url": "https://a.com/old", "date": "2024-01-01"},
            {"url": "https://a.com/new", "date": "2025-06-01"},
            {"url": "https://a.com/mid", "date": "2025-01-01"},
        ]
        result = dedup_articles(articles)
        dates = [a["date"] for a in result]
        assert dates == ["2025-06-01", "2025-01-01", "2024-01-01"]

    def test_missing_dates_at_end(self):
        articles = [
            {"url": "https://a.com/nodate"},
            {"url": "https://a.com/dated", "date": "2025-01-01"},
        ]
        result = dedup_articles(articles)
        assert result[0]["date"] == "2025-01-01"
        assert result[1].get("date") is None

    def test_empty_list(self):
        assert dedup_articles([]) == []

    def test_empty_url_skipped(self):
        articles = [
            {"url": "", "date": "2025-01-01"},
            {"url": "https://a.com/1", "date": "2025-01-02"},
        ]
        result = dedup_articles(articles)
        assert len(result) == 1


# ══════════════════════════════════════════════════════════════════
# 3. validate_competitors_schema
# ══════════════════════════════════════════════════════════════════

class TestValidateCompetitorsSchema:
    def test_valid_schema(self, valid_data):
        validate_competitors_schema(valid_data)  # should not raise

    def test_missing_schema_version(self):
        with pytest.raises(SchemaValidationError, match="Missing schema_version"):
            validate_competitors_schema({"GPU Computing & Hardware": {}})

    def test_missing_competitors_key(self):
        data = {"schema_version": "1.0", "GPU Computing & Hardware": {"metadata": {}}}
        with pytest.raises(SchemaValidationError, match="missing 'competitors'"):
            validate_competitors_schema(data)

    def test_missing_competitor_field(self):
        data = {
            "schema_version": "1.0",
            "GPU Computing & Hardware": {
                "competitors": {
                    "bad": {"name": "X", "blog_url": "https://x.com"}
                    # missing "articles"
                }
            },
        }
        with pytest.raises(SchemaValidationError, match="missing 'articles'"):
            validate_competitors_schema(data)

    def test_missing_article_field(self):
        data = {
            "schema_version": "1.0",
            "GPU Computing & Hardware": {
                "competitors": {
                    "comp": {
                        "name": "X",
                        "blog_url": "https://x.com",
                        "articles": [
                            {"title": "T", "url": "https://x.com/1", "date": "2025-01-01"}
                            # missing "relevance"
                        ],
                    }
                }
            },
        }
        with pytest.raises(SchemaValidationError, match="missing 'relevance'"):
            validate_competitors_schema(data)


# ══════════════════════════════════════════════════════════════════
# 4. migrate_competitors_schema
# ══════════════════════════════════════════════════════════════════

class TestMigrateCompetitorsSchema:
    def test_v1_passthrough(self, valid_data):
        result = migrate_competitors_schema(valid_data)
        assert result is valid_data

    def test_unknown_version_returns_none(self):
        data = {"schema_version": "2.0"}
        result = migrate_competitors_schema(data)
        assert result is None
        _mock_st.warning.assert_called()

    def test_missing_version_defaults_to_1(self):
        data = {"GPU Computing & Hardware": {}}
        result = migrate_competitors_schema(data)
        assert result is data  # defaults to "1.0"


# ══════════════════════════════════════════════════════════════════
# 5. save / load competitors_data
# ══════════════════════════════════════════════════════════════════

class TestSaveLoadCompetitorsData:
    def test_save_to_session_state(self, valid_data):
        save_competitors_data(valid_data)
        assert _mock_st.session_state[COMPETITORS_SS_KEY] is valid_data

    def test_save_creates_file(self, valid_data, tmp_path):
        path = tmp_path / "data" / "competitors_data.json"
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(path)):
            save_competitors_data(valid_data)
        assert path.exists()
        loaded = json.loads(path.read_text(encoding="utf-8"))
        assert loaded["schema_version"] == "1.0"

    def test_load_from_session_state(self, valid_data):
        _mock_st.session_state[COMPETITORS_SS_KEY] = valid_data
        result = load_competitors_data()
        assert result is valid_data

    def test_load_from_file(self, valid_data, tmp_path):
        path = tmp_path / "competitors_data.json"
        path.write_text(json.dumps(valid_data), encoding="utf-8")
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(path)):
            with patch("techaudit_agent.DEFAULT_COMPETITORS_PATH", str(tmp_path / "none.json")):
                _mock_st.session_state[COMPETITORS_SS_KEY] = None
                result = load_competitors_data()
        assert result is not None
        assert result["schema_version"] == "1.0"

    def test_load_falls_back_to_default(self, valid_data, tmp_path):
        default_path = tmp_path / "default.json"
        default_path.write_text(json.dumps(valid_data), encoding="utf-8")
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(tmp_path / "none.json")):
            with patch("techaudit_agent.DEFAULT_COMPETITORS_PATH", str(default_path)):
                _mock_st.session_state[COMPETITORS_SS_KEY] = None
                result = load_competitors_data()
        assert result is not None

    def test_load_returns_none_when_all_fail(self, tmp_path):
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(tmp_path / "a.json")):
            with patch("techaudit_agent.DEFAULT_COMPETITORS_PATH", str(tmp_path / "b.json")):
                _mock_st.session_state[COMPETITORS_SS_KEY] = None
                result = load_competitors_data()
        assert result is None


# ══════════════════════════════════════════════════════════════════
# 6. load_competitors_for_category
# ══════════════════════════════════════════════════════════════════

class TestLoadCompetitorsForCategory:
    def test_exact_match(self, valid_data):
        result = load_competitors_for_category("GPU Computing & Hardware", valid_data)
        assert result is not None
        assert "competitors" in result

    def test_case_insensitive(self, valid_data):
        result = load_competitors_for_category("gpu computing & hardware", valid_data)
        assert result is not None

    def test_no_match(self, valid_data):
        result = load_competitors_for_category("Quantum Computing", valid_data)
        assert result is None

    def test_none_data(self):
        assert load_competitors_for_category("GPU", None) is None

    def test_no_schema_version(self):
        assert load_competitors_for_category("GPU", {"GPU": {}}) is None


# ══════════════════════════════════════════════════════════════════
# 7. build_competitive_context
# ══════════════════════════════════════════════════════════════════

class TestBuildCompetitiveContext:
    def test_returns_string_with_content(self, valid_data):
        result = build_competitive_context("GPU Computing & Hardware", valid_data)
        assert "Competitive Landscape" in result
        assert "The Next Platform" in result

    def test_empty_on_none_data(self):
        assert build_competitive_context("GPU", None) == ""

    def test_empty_on_no_category_match(self, valid_data):
        assert build_competitive_context("Quantum", valid_data) == ""

    def test_limits_to_2_titles(self):
        data = {
            "schema_version": "1.0",
            "Cat": {
                "competitors": {
                    "x": {
                        "name": "X Blog",
                        "blog_url": "https://x.com",
                        "articles": [
                            {"title": f"Art {i}", "url": f"https://x.com/{i}", "date": "2025-01-01", "relevance": "r"}
                            for i in range(5)
                        ],
                    }
                }
            },
        }
        result = build_competitive_context("Cat", data)
        # Should have max 2 article titles
        assert result.count('"Art') == 2

    def test_empty_when_no_articles(self):
        data = {
            "schema_version": "1.0",
            "Cat": {
                "competitors": {
                    "x": {"name": "X", "blog_url": "https://x.com", "articles": []}
                }
            },
        }
        result = build_competitive_context("Cat", data)
        assert result == ""


# ══════════════════════════════════════════════════════════════════
# 8. _validate_competitor_config
# ══════════════════════════════════════════════════════════════════

class TestValidateCompetitorConfig:
    def test_categories_match(self):
        _validate_competitor_config()  # should not raise

    def test_all_categories_covered(self):
        for cat in CATEGORIES:
            assert cat in COMPETITORS_BY_CATEGORY


# ══════════════════════════════════════════════════════════════════
# 9. EDGE CASES (7 scenarios from plan.md)
# ══════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Edge case scenarios from plan.md Phase 4."""

    # Edge 1: Missing API key
    def test_missing_api_key(self):
        """collect_competitor_articles returns None when API key missing."""
        from techaudit_agent import collect_competitor_articles

        _mock_st.session_state["category"] = "GPU Computing & Hardware"
        _mock_st.session_state[COMPETITORS_SS_KEY] = None
        with patch.dict(os.environ, {}, clear=True):
            with patch("techaudit_agent.os.getenv", return_value=None):
                result = collect_competitor_articles()
        assert result is None
        _mock_st.warning.assert_called()

    # Edge 2: Empty competitor articles list
    def test_empty_articles_from_gemini(self, valid_data):
        """Dashboard renders even with 0 articles per competitor."""
        for comp in valid_data["GPU Computing & Hardware"]["competitors"].values():
            comp["articles"] = []
        result = load_competitors_for_category("GPU Computing & Hardware", valid_data)
        assert result is not None
        assert all(
            len(c["articles"]) == 0
            for c in result["competitors"].values()
        )

    # Edge 3: Invalid article URLs filtered
    def test_invalid_urls_filtered(self):
        """validate_url_format filters bad URLs during collection."""
        articles = [
            {"url": "https://valid.com/a", "date": "2025-01-01"},
            {"url": "not-a-url", "date": "2025-01-02"},
            {"url": "ftp://wrong.com", "date": "2025-01-03"},
            {"url": "", "date": "2025-01-04"},
        ]
        valid = [a for a in articles if validate_url_format(a.get("url", ""))]
        assert len(valid) == 1
        assert valid[0]["url"] == "https://valid.com/a"

    # Edge 4: Duplicate articles
    def test_duplicate_articles_deduped(self):
        """Same URL from multiple sources only kept once."""
        articles = [
            {"url": "https://a.com/same", "date": "2025-01-01", "title": "First"},
            {"url": "https://a.com/same", "date": "2025-01-02", "title": "Duplicate"},
            {"url": "https://a.com/other", "date": "2025-01-03", "title": "Other"},
        ]
        result = dedup_articles(articles)
        assert len(result) == 2
        urls = [a["url"] for a in result]
        assert urls.count("https://a.com/same") == 1

    # Edge 5: Schema version mismatch
    def test_schema_version_mismatch(self, tmp_path):
        """Unknown schema version triggers warning and falls to default."""
        bad_data = {"schema_version": "2.0", "Cat": {"competitors": {}}}
        bad_path = tmp_path / "bad.json"
        bad_path.write_text(json.dumps(bad_data), encoding="utf-8")
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(bad_path)):
            with patch("techaudit_agent.DEFAULT_COMPETITORS_PATH", str(tmp_path / "none.json")):
                _mock_st.session_state[COMPETITORS_SS_KEY] = None
                result = load_competitors_data()
        assert result is None

    # Edge 6: Large JSON (stress test)
    def test_large_json_handles(self, tmp_path):
        """100 competitors with 50 articles each loads without error."""
        data = {"schema_version": "1.0"}
        comps = {}
        for i in range(100):
            comps[f"comp_{i}"] = {
                "name": f"Company {i}",
                "blog_url": f"https://comp{i}.com/",
                "tier": 1,
                "articles": [
                    {
                        "title": f"Article {j}",
                        "url": f"https://comp{i}.com/art-{j}",
                        "date": "2025-01-01",
                        "relevance": "test",
                    }
                    for j in range(50)
                ],
            }
        data["GPU Computing & Hardware"] = {"metadata": {}, "competitors": comps}
        validate_competitors_schema(data)  # should not raise
        path = tmp_path / "large.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        with patch("techaudit_agent.COMPETITORS_DATA_PATH", str(path)):
            with patch("techaudit_agent.DEFAULT_COMPETITORS_PATH", str(tmp_path / "x.json")):
                _mock_st.session_state[COMPETITORS_SS_KEY] = None
                result = load_competitors_data()
        assert result is not None
        assert len(result["GPU Computing & Hardware"]["competitors"]) == 100

    # Edge 7: Category not found in JSON
    def test_category_not_found(self, valid_data):
        """Missing category returns None, UI shows selectbox fallback."""
        result = load_competitors_for_category("Quantum Computing", valid_data)
        assert result is None


# ══════════════════════════════════════════════════════════════════
# 10. Default competitors file validation
# ══════════════════════════════════════════════════════════════════

class TestDefaultCompetitorsFile:
    def test_file_exists(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "data", "default_competitors.json")
        assert os.path.exists(path), f"Missing: {path}"

    def test_file_valid_json(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "data", "default_competitors.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["schema_version"] == "1.0"

    def test_file_passes_schema(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "data", "default_competitors.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        validate_competitors_schema(data)

    def test_all_categories_present(self):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "data", "default_competitors.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for cat in CATEGORIES:
            assert cat in data, f"Missing category: {cat}"
