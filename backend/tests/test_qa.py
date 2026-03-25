"""
backend/tests/test_qa.py — Tests for QA tools (pure Python functions + mocked AI).

_article_to_markdown, run_comprehensive_qa, _generate_rerun_strategies are all
pure functions with no external dependencies — no mocking required.
score_article_rubric requires a mocked Gemini client.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from backend.tools.qa import (
    _article_to_markdown,
    _generate_rerun_strategies,
    run_comprehensive_qa,
    score_article_rubric,
)


# ── Fixtures ─────────────────────────────────────────────────────

def _minimal_article() -> dict:
    """Minimal valid article dict that passes most QA checks."""
    return {
        "article_title": "GPU Memory Bandwidth Bottlenecks",
        "executive_summary": (
            "Modern GPUs face bandwidth (BW) constraints that limit throughput. "
            "This analysis examines thermal, power, and scaling limits "
            "in H100 [1], A100 [2], and MI300X [3] architectures. "
            "Bandwidth-bound workloads suffer 30% latency [1] at peak load. "
            "Understanding TDP and cooling constraints is essential. "
            "Memory wall effects now dominate at 400 GB/s scale [2]."
        ),
        "sections": [
            {
                "heading": "Memory Architecture",
                "content": (
                    "HBM3 delivers 3.35 TB/s bandwidth [1]. "
                    "Thermal design power (TDP) is 700W [2]. "
                    "Cooling systems handle heat dissipation [3]."
                ),
            },
            {
                "heading": "Bottleneck Analysis",
                "content": (
                    "Memory wall effects constrain scaling [1]. "
                    "Power delivery limits burst performance [2]. "
                    "Bandwidth-bound models see 2.5× slowdown [3]."
                ),
                "chart_suggestion": "Bandwidth vs Compute chart",
            },
            {
                "heading": "Performance Benchmarks",
                "content": (
                    "H100 achieves 3.35 TB/s vs A100 2 TB/s [1]. "
                    "Latency drops 40ms under sustained load [2]. "
                    "TDP scales linearly with frequency [3]."
                ),
            },
        ],
        "comparison": {
            "heading": "Comparative Analysis",
            "content": "H100 vs A100 vs MI300X comparison.",
            "alternatives": [
                {"name": "A100", "score": 8},
                {"name": "MI300X", "score": 9},
                {"name": "H100", "score": 10},
            ],
        },
        "tco_analysis": {
            "heading": "TCO Analysis",
            "content": (
                "Total cost of ownership analysis requires carefully evaluating power consumption, "
                "cooling infrastructure, and hardware amortization over the full deployment lifetime. "
                "H100 clusters consume 700W TDP per card, requiring significant and costly cooling. "
                "A three-year TCO for a 100-card cluster easily exceeds $5M when including power, "
                "cooling, networking, and operational overhead costs for enterprise deployments. "
                "Organizations must weigh these substantial infrastructure costs against productivity gains."
            ),
        },
        "anti_recommendation": {
            "heading": "When NOT to Use",
            "content": (
                "GPU clusters are inappropriate for latency-sensitive applications "
                "requiring sub-millisecond response times in production environments. "
                "CPU-based inference pipelines are more cost-effective for batch sizes under 8. "
                "Small language models under 7B parameters show better total cost of ownership "
                "on modern high-core-count CPUs without specialized accelerator hardware. "
                "Power-constrained edge environments should evaluate ARM-based accelerators instead "
                "of data-center GPUs, as the power envelope difference is significant."
            ),
        },
        "conclusion": "GPU memory bandwidth remains the primary scaling bottleneck.",
        "metadata": {
            "seo_slug": "gpu-memory-bandwidth",
            "meta_description": "Analysis of GPU memory bandwidth constraints.",
        },
        "references": ["[1] NVIDIA H100 spec", "[2] AMD MI300X spec", "[3] Google TPUv4 spec"],
    }


# ── _article_to_markdown ──────────────────────────────────────────

class TestArticleToMarkdown:
    def test_includes_title(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "# GPU Memory Bandwidth Bottlenecks" in md

    def test_includes_executive_summary(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "Executive Summary" in md
        assert "bandwidth" in md.lower()

    def test_includes_section_headings(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "## Memory Architecture" in md
        assert "## Bottleneck Analysis" in md

    def test_includes_chart_suggestion(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "Bandwidth vs Compute chart" in md

    def test_includes_comparison(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "Comparative Analysis" in md

    def test_includes_tco_analysis(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "TCO Analysis" in md

    def test_includes_anti_recommendation(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "When NOT to Use" in md

    def test_includes_conclusion(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "Conclusion" in md

    def test_includes_metadata(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "gpu-memory-bandwidth" in md

    def test_includes_references(self):
        art = _minimal_article()
        md = _article_to_markdown(art)
        assert "References" in md
        assert "NVIDIA H100 spec" in md

    def test_empty_article_does_not_crash(self):
        md = _article_to_markdown({})
        assert isinstance(md, str)

    def test_no_comparison_section(self):
        art = _minimal_article()
        del art["comparison"]
        md = _article_to_markdown(art)
        assert isinstance(md, str)

    def test_no_tco_section(self):
        art = _minimal_article()
        del art["tco_analysis"]
        md = _article_to_markdown(art)
        assert isinstance(md, str)

    def test_no_anti_recommendation(self):
        art = _minimal_article()
        del art["anti_recommendation"]
        md = _article_to_markdown(art)
        assert isinstance(md, str)


# ── run_comprehensive_qa ─────────────────────────────────────────

class TestRunComprehensiveQA:
    def test_returns_list_of_dicts(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        assert isinstance(checks, list)
        assert all(isinstance(c, dict) for c in checks)

    def test_returns_eleven_checks(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        assert len(checks) == 11

    def test_each_check_has_required_keys(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        for c in checks:
            assert "category" in c
            assert "check" in c
            assert "passed" in c
            assert "note" in c

    def test_word_count_check_passes_for_adequate_article(self):
        art = _minimal_article()
        # Add ~1000 words to ensure total lands in the 1000-1600 word range
        filler = (
            "GPU memory bandwidth constraints fundamentally limit the throughput of "
            "modern transformer workloads when operating at scale in production environments. "
        ) * 50
        art["sections"][0]["content"] += filler
        checks = run_comprehensive_qa(art)
        wc_check = next(c for c in checks if "Word count" in c["check"])
        assert wc_check["passed"] is True

    def test_word_count_check_fails_for_short_article(self):
        art = _minimal_article()
        art["executive_summary"] = "Short."
        art["sections"] = [{"heading": "H", "content": "Short."}]
        art["comparison"] = {}
        art["tco_analysis"] = {}
        art["anti_recommendation"] = {}
        art["conclusion"] = ""
        checks = run_comprehensive_qa(art)
        wc_check = next(c for c in checks if "Word count" in c["check"])
        assert wc_check["passed"] is False

    def test_citations_check_passes_with_citations(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        cit_check = next(c for c in checks if "Source citations" in c["check"])
        assert cit_check["passed"] is True

    def test_citations_check_fails_without_citations(self):
        art = _minimal_article()
        for sec in art["sections"]:
            sec["content"] = "No citations here at all."
        art["comparison"]["content"] = "No citations."
        art["tco_analysis"]["content"] = "No citations."
        art["anti_recommendation"]["content"] = "No citations here either."
        checks = run_comprehensive_qa(art)
        cit_check = next(c for c in checks if "Source citations" in c["check"])
        assert cit_check["passed"] is False

    def test_anti_rec_check_passes_for_long_section(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        anti_check = next(c for c in checks if "Anti-recommendation" in c["check"])
        assert anti_check["passed"] is True

    def test_tco_check_passes_for_long_section(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        tco_check = next(c for c in checks if "TCO analysis" in c["check"])
        assert tco_check["passed"] is True

    def test_bullet_check_passes_for_no_bullets(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        bullet_check = next(c for c in checks if "bullet" in c["check"].lower())
        assert bullet_check["passed"] is True

    def test_bullet_check_fails_when_bullets_present(self):
        art = _minimal_article()
        art["sections"][0]["content"] = "- Item A\n- Item B\n- Item C"
        checks = run_comprehensive_qa(art)
        bullet_check = next(c for c in checks if "bullet" in c["check"].lower())
        assert bullet_check["passed"] is False

    def test_alternatives_check_passes_with_enough_alternatives(self):
        art = _minimal_article()
        checks = run_comprehensive_qa(art)
        alt_check = next(c for c in checks if "alternatives" in c["check"].lower())
        assert alt_check["passed"] is True

    def test_alternatives_check_fails_with_too_few(self):
        art = _minimal_article()
        art["comparison"]["alternatives"] = [{"name": "only one"}]
        checks = run_comprehensive_qa(art)
        alt_check = next(c for c in checks if "alternatives" in c["check"].lower())
        assert alt_check["passed"] is False

    def test_sections_check_fails_with_too_few_sections(self):
        art = _minimal_article()
        art["sections"] = [{"heading": "Only One", "content": "Just one section."}]
        checks = run_comprehensive_qa(art)
        sec_check = next(c for c in checks if "body sections" in c["check"])
        assert sec_check["passed"] is False

    def test_empty_article_returns_all_failed(self):
        checks = run_comprehensive_qa({})
        assert all(not c["passed"] for c in checks if "Word count" in c["check"] or "sections" in c["check"])


# ── _generate_rerun_strategies ───────────────────────────────────

class TestGenerateRerunStrategies:
    def _all_pass_checks(self) -> list[dict]:
        return [
            {"category": "Structure", "check": "Word count", "passed": True, "note": "ok"},
            {"category": "Evidence", "check": "Citations", "passed": True, "note": "ok"},
        ]

    def _some_fail_checks(self) -> list[dict]:
        return [
            {"category": "Structure", "check": "Word count check", "passed": False, "note": "low"},
            {"category": "Evidence", "check": "Source citations", "passed": False, "note": "missing"},
            {"category": "Structure", "check": "Section count", "passed": False, "note": "few"},
            {"category": "Clarity", "check": "Acronym defs", "passed": True, "note": "ok"},
        ]

    def test_returns_empty_when_all_pass(self):
        result = _generate_rerun_strategies(self._all_pass_checks())
        assert result == []

    def test_returns_up_to_3_strategies(self):
        result = _generate_rerun_strategies(self._some_fail_checks())
        assert len(result) <= 3

    def test_returns_list_of_dicts(self):
        result = _generate_rerun_strategies(self._some_fail_checks())
        assert isinstance(result, list)
        assert all(isinstance(s, dict) for s in result)

    def test_each_strategy_has_required_keys(self):
        result = _generate_rerun_strategies(self._some_fail_checks())
        for s in result:
            assert "icon" in s
            assert "label" in s
            assert "name" in s
            assert "description" in s
            assert "guidance" in s

    def test_deep_fix_strategy_targets_top_category(self):
        result = _generate_rerun_strategies(self._some_fail_checks())
        deep_fix = next((s for s in result if "Deep Fix" in s["name"]), None)
        assert deep_fix is not None
        # Structure has 2 failures, Evidence has 1 — Deep Fix should target Structure
        assert "Structure" in deep_fix["label"]

    def test_balanced_revision_strategy_present(self):
        result = _generate_rerun_strategies(self._some_fail_checks())
        balanced = next((s for s in result if "Balanced" in s["name"]), None)
        assert balanced is not None

    def test_structural_rewrite_strategy_present_when_structure_fails(self):
        checks = [
            {"category": "Structure", "check": "Word count", "passed": False, "note": "low"},
        ]
        result = _generate_rerun_strategies(checks)
        structural = next((s for s in result if "Structural" in s["name"]), None)
        assert structural is not None
        assert "Rewrite" in structural["label"]

    def test_citation_fix_strategy_when_no_structural_failures(self):
        checks = [
            {"category": "Technical Depth", "check": "Physical constraints", "passed": False, "note": "missing"},
        ]
        result = _generate_rerun_strategies(checks)
        citation = next((s for s in result if "Citation" in s["name"]), None)
        assert citation is not None


# ── score_article_rubric ─────────────────────────────────────────

class TestScoreArticleRubric:
    def test_returns_dict_on_success(self):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        scores_json = '{"Accuracy": 8.0, "Depth": 7.5}'
        with (
            patch("backend.tools.qa._call", return_value=(mock_resp, None)),
            patch("backend.tools.qa._extract_text", return_value=scores_json),
            patch("backend.tools.qa._parse_json", return_value={"Accuracy": 8.0, "Depth": 7.5}),
        ):
            result = score_article_rubric(mock_client, _minimal_article())
        assert isinstance(result, dict)

    def test_returns_zeros_on_exception(self):
        mock_client = MagicMock()
        with patch("backend.tools.qa._call", side_effect=Exception("API error")):
            result = score_article_rubric(mock_client, _minimal_article())
        assert isinstance(result, dict)
        assert all(v == 0.0 for v in result.values())
