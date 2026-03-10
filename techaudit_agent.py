#!/usr/bin/env python3
from __future__ import annotations
"""
╔══════════════════════════════════════════════════════════════════╗
║       TechAudit Content Architect  v2.0                         ║
║  Strict, evidence-based AI technical writing agent              ║
║  Model : gemini-2.5-pro      |  Search : google_search          ║
╚══════════════════════════════════════════════════════════════════╝
"""

import streamlit as st
from google import genai
from google.genai import types
import os, json, re, time, requests, textwrap, hashlib
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlparse

try:
    import anthropic as _anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# ══════════════════════════════════════════════════════════════════
# 1 · PAGE CONFIG
# ══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="TechAudit Content Architect",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════
# 2 · GLOBAL STYLES
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
/* ── Base ──────────────────────────────────────────────────────── */
[data-testid="stApp"]        { background:#0a0e1a; color:#e2e8f0; }
[data-testid="stSidebar"]    { background:#0f1629!important;
                               border-right:1px solid #1e293b; }
.block-container             { padding-top:1.5rem; }
h1,h2,h3,h4                 { color:#f1f5f9; }

/* ── Header ────────────────────────────────────────────────────── */
.main-header {
  background:linear-gradient(135deg,#0f0c29 0%,#302b63 55%,#24243e 100%);
  border:1px solid rgba(99,102,241,.3); border-radius:16px;
  padding:2.5rem 2rem; text-align:center; margin-bottom:1.8rem;
  box-shadow:0 20px 60px rgba(99,102,241,.15);
}
.main-header h1 { font-size:2rem; font-weight:800;
  letter-spacing:-.02em; margin:0; color:#f1f5f9; }
.main-header p  { color:#94a3b8; font-size:.95rem; margin:.5rem 0 0; }

/* ── Step Progress Bar ─────────────────────────────────────────── */
.step-row {
  display:flex; align-items:center; gap:.4rem;
  background:#0f1629; border:1px solid #1e293b;
  border-radius:12px; padding:.9rem 1.4rem;
  margin-bottom:2rem; overflow-x:auto;
}
.step-item  { display:flex; align-items:center; gap:.45rem;
              white-space:nowrap; }
.step-dot   { width:26px; height:26px; border-radius:50%;
              display:flex; align-items:center; justify-content:center;
              font-size:.72rem; font-weight:700;
              background:#1e293b; color:#64748b;
              border:2px solid #334155; flex-shrink:0; }
.step-dot.active { background:#6366f1; color:#fff;
                   border-color:#818cf8;
                   box-shadow:0 0 12px rgba(99,102,241,.5); }
.step-dot.done   { background:#059669; color:#fff; border-color:#34d399; }
.step-label      { font-size:.78rem; color:#64748b; }
.step-label.active { color:#a5b4fc; font-weight:600; }
.step-connector  { flex:1; min-width:16px; height:1px; background:#1e293b; }

/* ── Generic card ──────────────────────────────────────────────── */
.card {
  background:#0f1629; border:1px solid #1e293b;
  border-radius:14px; padding:1.4rem;
  margin-bottom:.9rem; transition:all .2s;
}
.card:hover { border-color:#334155;
  transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(0,0,0,.3); }

/* ── Source card ───────────────────────────────────────────────── */
.source-card {
  background:#0f1629; border:1px solid #1e293b;
  border-radius:10px; padding:1.1rem; margin-bottom:.7rem;
}
.source-badge {
  display:inline-block;
  background:rgba(99,102,241,.15); color:#818cf8;
  border:1px solid rgba(99,102,241,.3);
  border-radius:6px; padding:.15rem .55rem;
  font-size:.68rem; font-weight:700; margin-bottom:.45rem;
}
.source-date { font-size:.7rem; color:#64748b; }

/* ── NotebookLM panel ──────────────────────────────────────────── */
.notebooklm-panel {
  background:linear-gradient(135deg,rgba(6,78,59,.2),rgba(5,150,105,.1));
  border:1px solid rgba(52,211,153,.25);
  border-radius:12px; padding:1.4rem; margin:1.4rem 0;
}
.notebooklm-panel h4 { color:#34d399; margin:0 0 .6rem; font-size:.95rem; }

/* ── Article ───────────────────────────────────────────────────── */
.executive-summary {
  background:linear-gradient(135deg,rgba(99,102,241,.1),rgba(168,85,247,.1));
  border-left:4px solid #6366f1; border-radius:0 12px 12px 0;
  padding:1.5rem; margin-bottom:2rem; font-style:italic;
  line-height:1.9; color:#cbd5e1;
}
.article-h2 {
  font-size:1.35rem; font-weight:700; color:#e2e8f0;
  border-bottom:2px solid rgba(99,102,241,.3);
  padding-bottom:.45rem; margin:2.2rem 0 1rem;
}
.article-p  { line-height:1.85; color:#cbd5e1; margin-bottom:.9rem; }
.chart-hint {
  background:rgba(15,23,42,.9); border:1px dashed #334155;
  border-radius:8px; padding:.9rem; margin:.8rem 0;
  font-size:.8rem; color:#64748b;
}
.chart-hint span { color:#a5b4fc; font-weight:600; }

/* ── Anti-rec & TCO boxes ──────────────────────────────────────── */
.anti-rec-box {
  background:rgba(220,38,38,.08); border-left:4px solid #dc2626;
  border-radius:0 12px 12px 0; padding:1.4rem; margin:1.4rem 0;
}
.tco-box {
  background:rgba(245,158,11,.08); border-left:4px solid #f59e0b;
  border-radius:0 12px 12px 0; padding:1.4rem; margin:1.4rem 0;
}

/* ── Quality audit ─────────────────────────────────────────────── */
.audit-row {
  display:flex; align-items:flex-start; gap:.7rem;
  padding:.55rem 1rem; border-radius:8px; margin:.25rem 0;
  font-size:.85rem;
}
.audit-pass { background:rgba(5,150,105,.1); }
.audit-fail { background:rgba(220,38,38,.1); }
.audit-icon { font-size:1rem; flex-shrink:0; margin-top:.1rem; }

/* ── Meta code block ───────────────────────────────────────────── */
.meta-block {
  background:#020617; border:1px solid #1e293b;
  border-radius:12px; padding:1.4rem;
  font-family:'JetBrains Mono','Fira Code',monospace;
  font-size:.78rem; color:#94a3b8; white-space:pre-wrap;
}

/* ── Comparison table ──────────────────────────────────────────── */
.cmp-table { width:100%; border-collapse:collapse; margin:1rem 0; }
.cmp-table th { background:#1e293b; color:#a5b4fc; padding:.7rem 1rem;
                text-align:left; font-size:.82rem; }
.cmp-table td { padding:.65rem 1rem; border-bottom:1px solid #1e293b;
                font-size:.83rem; color:#cbd5e1; vertical-align:top; }
.cmp-table tr:hover td { background:rgba(99,102,241,.05); }

/* ── Buttons ───────────────────────────────────────────────────── */
.stButton > button {
  background:linear-gradient(135deg,#6366f1,#7c3aed)!important;
  color:#fff!important; border:none!important;
  border-radius:10px!important; font-weight:600!important;
  font-size:.88rem!important; padding:.6rem 1.4rem!important;
  width:100%; transition:all .3s!important;
}
.stButton > button:hover {
  transform:translateY(-2px)!important;
  box-shadow:0 8px 24px rgba(99,102,241,.4)!important;
}
div[data-testid="stVerticalBlock"] .reset-btn > button {
  background:#1e293b!important; border:1px solid #334155!important;
}

/* ── Selectbox ─────────────────────────────────────────────────── */
.stSelectbox > div > div {
  background:#0f1629!important; border:1px solid #334155!important;
  border-radius:8px!important; color:#e2e8f0!important;
}

/* ── Progress / spinner ────────────────────────────────────────── */
.stSpinner > div { border-top-color:#6366f1!important; }

/* ── QA Score Panel ────────────────────────────────────────────── */
.qa-score-header {
  background:#0f1629; border:1px solid #1e293b; border-radius:14px;
  padding:1.6rem; margin-bottom:1.5rem; display:flex;
  align-items:center; gap:1.5rem; flex-wrap:wrap;
}
.qa-score-circle {
  width:72px; height:72px; border-radius:50%;
  display:flex; align-items:center; justify-content:center;
  font-size:1.3rem; font-weight:800; flex-shrink:0;
  border:3px solid currentColor;
}
.qa-score-circle.green { color:#34d399; background:rgba(52,211,153,.1); }
.qa-score-circle.yellow { color:#fbbf24; background:rgba(251,191,36,.1); }
.qa-score-circle.red  { color:#f87171; background:rgba(248,113,113,.1); }
.qa-grade-label { font-size:1.1rem; font-weight:700; }
.qa-grade-label.green { color:#34d399; }
.qa-grade-label.yellow { color:#fbbf24; }
.qa-grade-label.red   { color:#f87171; }
.qa-bar-wrap { flex:1; min-width:180px; }
.qa-bar-bg {
  height:10px; background:#1e293b; border-radius:99px;
  overflow:hidden; margin-top:.4rem;
}
.qa-bar-fill { height:100%; border-radius:99px; transition:width .4s; }
.qa-category-header {
  font-size:.8rem; font-weight:700; color:#64748b;
  text-transform:uppercase; letter-spacing:.08em;
  margin:1.2rem 0 .4rem; padding-bottom:.3rem;
  border-bottom:1px solid #1e293b;
}
/* Source-accept overrides */
.src-declined { opacity:.45; filter:grayscale(.6); }
.src-accepted { border-left-color:#34d399!important; }
/* Checkbox label tweak */
.stCheckbox label { font-size:.82rem!important; color:#94a3b8!important; }
.stCheckbox label span { vertical-align:middle; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 3 · CONSTANTS
# ══════════════════════════════════════════════════════════════════
CATEGORIES = [
    "AI Performance Engineering",
    "GPU Computing & Hardware",
    "High-Performance Networking",
    "Robotics & Edge Computing",
]

MODEL_REASONING = "gemini-2.5-pro"
MODEL_FALLBACK   = "gemini-2.5-flash"

# Claude (article writing)
CLAUDE_MODEL    = "claude-opus-4-6"
CLAUDE_FALLBACK = "claude-sonnet-4-6"

STEPS = [
    ("1", "Category"),
    ("2", "Topics"),
    ("3", "Titles"),
    ("4", "Research"),
    ("5", "Article"),
]

# Rubric scoring criteria: (name, target_score out of 10)
RUBRIC_CRITERIA = [
    ("Technical depth",     8.5),
    ("Clarity & structure", 8.0),
    ("Original insight",    7.0),
    ("Evidence & rigor",    6.5),
    ("Practical usefulness",8.0),
    ("Writing quality",     8.5),
]

# ── Competitor data paths & session key ──────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPETITORS_DATA_PATH = os.path.join(BASE_DIR, "data", "competitors_data.json")
DEFAULT_COMPETITORS_PATH = os.path.join(BASE_DIR, "data", "default_competitors.json")
COMPETITORS_SS_KEY = "competitors_data_cache"

# ── Competitors per category ─────────────────────────────────────
COMPETITORS_BY_CATEGORY: dict[str, dict[str, dict]] = {
    "AI Performance Engineering": {
        "nvidia_tech":  {"name": "NVIDIA Technical Blog", "blog_url": "https://developer.nvidia.com/blog/",       "tier": 1},
        "anyscale":     {"name": "Anyscale Blog",          "blog_url": "https://www.anyscale.com/blog",            "tier": 1},
        "together_ai":  {"name": "Together AI Blog",       "blog_url": "https://www.together.ai/blog",             "tier": 1},
        "huggingface":  {"name": "Hugging Face Blog",      "blog_url": "https://huggingface.co/blog",              "tier": 1},
        "mosaicml":     {"name": "MosaicML (Databricks)",  "blog_url": "https://www.databricks.com/blog",          "tier": 2},
        "alphasignal":  {"name": "AlphaSignal",            "blog_url": "https://alphasignal.ai/",                  "tier": 2},
    },
    "GPU Computing & Hardware": {
        "nextplatform": {"name": "The Next Platform",  "blog_url": "https://www.nextplatform.com/",        "tier": 1},
        "servethehome": {"name": "ServeTheHome (STH)", "blog_url": "https://www.servethehome.com/",        "tier": 1},
        "semianalysis": {"name": "SemiAnalysis",       "blog_url": "https://www.semianalysis.com/",        "tier": 1},
        "intel_dev":    {"name": "Intel Developer Zone","blog_url": "https://www.intel.com/content/www/us/en/developer/articles/technical/",  "tier": 1},
        "amd_gpuopen":  {"name": "AMD GPUOpen",        "blog_url": "https://gpuopen.com/",                 "tier": 2},
    },
    "High-Performance Networking": {
        "cloudflare":      {"name": "Cloudflare Blog",          "blog_url": "https://blog.cloudflare.com/",        "tier": 1},
        "meta_engineering":{"name": "Meta Engineering Blog",    "blog_url": "https://engineering.fb.com/",         "tier": 1},
        "cisco_tech":      {"name": "Cisco Tech Blog",          "blog_url": "https://blogs.cisco.com/",            "tier": 1},
        "kentik":          {"name": "Kentik Blog",              "blog_url": "https://www.kentik.com/blog/",        "tier": 2},
        "packet_pushers":  {"name": "Packet Pushers",           "blog_url": "https://packetpushers.net/",          "tier": 2},
    },
    "Robotics & Edge Computing": {
        "ieee_spectrum":   {"name": "IEEE Spectrum Robotics",   "blog_url": "https://spectrum.ieee.org/topic/robotics/",          "tier": 1},
        "boston_dynamics": {"name": "Boston Dynamics Blog",     "blog_url": "https://bostondynamics.com/blog/",                   "tier": 1},
        "nvidia_robotics": {"name": "NVIDIA Robotics Blog",     "blog_url": "https://developer.nvidia.com/blog/category/robotics/","tier": 1},
        "arm_newsroom":    {"name": "Arm Newsroom (Technical)", "blog_url": "https://newsroom.arm.com/",                          "tier": 2},
        "standard_bots":   {"name": "Standard Bots Blog",      "blog_url": "https://standardbots.com/blog/",                     "tier": 2},
        "dell_edge":       {"name": "Dell Technologies Blog",   "blog_url": "https://www.dell.com/en-us/blog/",                   "tier": 2},
    },
}


def _validate_competitor_config() -> None:
    """Validate COMPETITORS_BY_CATEGORY keys match CATEGORIES exactly."""
    missing = set(CATEGORIES) - set(COMPETITORS_BY_CATEGORY.keys())
    extra   = set(COMPETITORS_BY_CATEGORY.keys()) - set(CATEGORIES)
    if missing or extra:
        raise ValueError(
            f"COMPETITORS_BY_CATEGORY key mismatch — "
            f"missing: {missing}, extra: {extra}"
        )

# ══════════════════════════════════════════════════════════════════
# 4 · SESSION STATE
# ══════════════════════════════════════════════════════════════════
def _init():
    defaults = {
        "step":               1,
        "category":           None,
        "topics":             [],
        "topic":              None,
        "titles":             [],
        "title":              None,
        "sources":            [],
        "sources_confirmed":  False,
        "accepted_sources":   [],
        "notebooklm_context": "",
        "article":            None,
        "metadata":           None,
        "audit":              [],
        "qa_checks":          [],
        "qa_rerun_count":     0,
        "qa_rerun_strategy":  None,    # selected strategy dict from 3-option UI
        "hero_image_bytes":   None,    # server-side downloaded hero image bytes
        "model_used":         MODEL_REASONING,
        "claude_model_used":  CLAUDE_MODEL,
        "actual_writer":      "",      # "claude" | "gemini" | "gemini_fallback"
        "fallback_reason":    "",      # human-readable reason for fallback
        "gen_error":          "",
        "rubric_scores":      None,   # dict {criterion: score} from score_article_rubric()
        COMPETITORS_SS_KEY:   None,   # competitors data cache (session_state 1st layer)
        "collection_in_progress": False,  # prevent duplicate button clicks
        "competitive_context":    "",     # build_competitive_context() result — reuse on re-run/QA retry
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()

# ══════════════════════════════════════════════════════════════════
# 5 · GEMINI CLIENT
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


@st.cache_resource
def get_anthropic_client(api_key: str):
    if not ANTHROPIC_AVAILABLE or not api_key:
        return None
    return _anthropic.Anthropic(api_key=api_key)


def _search_cfg() -> types.GenerateContentConfig:
    """GenerateContentConfig with Google Search grounding."""
    return types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.4,
    )


def _json_cfg(schema: dict | None = None) -> types.GenerateContentConfig:
    """GenerateContentConfig for structured JSON output (no search)."""
    cfg = dict(
        response_mime_type="application/json",
        temperature=0.5,
    )
    if schema:
        cfg["response_schema"] = schema
    return types.GenerateContentConfig(**cfg)


def _plain_cfg() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(temperature=0.6)


def _extract_text(resp) -> str:
    """
    Safely pull text from a Gemini response.
    Tries resp.text first (works for most cases), then walks all parts
    skipping 'thought' parts (gemini-2.5 thinking tokens).
    Raises ValueError only if truly no text is found anywhere.
    """
    # Fast path
    try:
        if resp.text:
            return resp.text
    except Exception:
        pass

    # Walk candidates → parts, skip thought/code-execution parts
    try:
        parts = resp.candidates[0].content.parts or []
        for part in parts:
            # Skip thinking tokens (gemini-2.5 internal reasoning)
            if getattr(part, "thought", False):
                continue
            t = getattr(part, "text", None)
            if t:
                return t
    except Exception:
        pass

    # Describe finish reason if available for better diagnostics
    try:
        reason = str(resp.candidates[0].finish_reason)
    except Exception:
        reason = "unknown"

    raise ValueError(
        f"Model returned no usable text (finish_reason={reason}). "
        "This is a known intermittent behaviour of Google Search grounding — "
        "the request will be retried automatically."
    )


def _extract_text_safe(resp) -> str | None:
    """Like _extract_text but returns None instead of raising."""
    try:
        return _extract_text(resp)
    except ValueError:
        return None


def _call_search(client, prompt: str):
    """
    Run a prompt with Google Search grounding.
    If the grounded response contains no text (a known intermittent issue),
    silently retry with plain JSON mode — which always produces text.
    Returns the response object from whichever attempt succeeded.
    """
    resp = _call(client, prompt, _search_cfg())
    if _extract_text_safe(resp) is not None:
        return resp
    # No text from grounded response — fall back to JSON mode (no search tool)
    return _call(client, prompt, _json_cfg())


def _parse_json(text: str | None) -> list | dict:
    """
    Robust JSON extraction from model output.
    Handles: markdown fences, mixed prose + JSON (grounding adds footnotes),
    trailing commas, and unescaped characters in string values.

    Strategy:
      1. Strip markdown fences and try direct parse.
      2. Walk the text to find the outermost balanced [ ] or { } block.
      3. Apply light repair (trailing commas, JS-style comments) and retry.
    """
    if not text:
        raise ValueError("Empty response — model returned no content.")

    # ── Step 1: fence strip + direct attempt ──────────────────────
    clean = re.sub(r"^```(?:json)?\s*", "", text.strip(), flags=re.M)
    clean = re.sub(r"\s*```\s*$", "", clean.strip(), flags=re.M)
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        pass

    # ── Step 2: extract outermost balanced bracket block ──────────
    def _extract_balanced(src: str, open_ch: str, close_ch: str) -> str | None:
        start = src.find(open_ch)
        if start == -1:
            return None
        depth, in_str, esc, i = 0, False, False, start
        while i < len(src):
            ch = src[i]
            if esc:
                esc = False
            elif ch == "\\" and in_str:
                esc = True
            elif ch == '"':
                in_str = not in_str
            elif not in_str:
                if ch == open_ch:
                    depth += 1
                elif ch == close_ch:
                    depth -= 1
                    if depth == 0:
                        return src[start : i + 1]
            i += 1
        return None

    for open_ch, close_ch in [("[", "]"), ("{", "}")]:
        block = _extract_balanced(clean, open_ch, close_ch)
        if block is None:
            continue
        # Try raw
        try:
            return json.loads(block)
        except json.JSONDecodeError:
            pass
        # ── Step 3: light repair ──────────────────────────────────
        repaired = block
        # Remove trailing commas before ] or }
        repaired = re.sub(r",\s*([}\]])", r"\1", repaired)
        # Strip JS-style single-line comments
        repaired = re.sub(r"(?<!:)//[^\n\"]*", "", repaired)
        # Replace curly apostrophes / smart quotes
        repaired = repaired.replace("\u2018", "'").replace("\u2019", "'")
        repaired = repaired.replace("\u201c", '"').replace("\u201d", '"')
        try:
            return json.loads(repaired)
        except json.JSONDecodeError:
            pass

    raise ValueError(
        f"Could not parse JSON from model response.\n"
        f"First 300 chars of response:\n{text[:300]}"
    )


def _call(client, prompt: str, cfg, model=None) -> types.GenerateContentResponse:
    m = model or st.session_state.model_used
    try:
        return client.models.generate_content(model=m, contents=prompt, config=cfg)
    except Exception as e:
        if MODEL_FALLBACK not in str(m):
            st.session_state.model_used = MODEL_FALLBACK
            return client.models.generate_content(
                model=MODEL_FALLBACK, contents=prompt, config=cfg
            )
        raise e

# ══════════════════════════════════════════════════════════════════
# 5b · COMPETITOR DATA (collection, validation, storage)
# ══════════════════════════════════════════════════════════════════
import logging as _logging

_comp_log = _logging.getLogger("competitor_data")
if not _comp_log.handlers:
    _h = _logging.StreamHandler()
    _h.setFormatter(_logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))
    _comp_log.addHandler(_h)
    _comp_log.setLevel(_logging.INFO)


class CompetitorDataError(Exception):
    """Base error for competitor data operations."""


class SchemaValidationError(CompetitorDataError):
    """Raised when competitor data fails schema validation."""


class DataLoadingError(CompetitorDataError):
    """Raised when competitor data cannot be loaded from any source."""


class GeminiAPIError(CompetitorDataError):
    """Raised when Gemini API call fails during competitor collection."""


def validate_url_format(url: str) -> bool:
    """Validate URL format only — no network requests, no blocking."""
    if not url or not isinstance(url, str):
        return False
    try:
        result = urlparse(url)
        return all([result.scheme in ("http", "https"), result.netloc])
    except Exception:
        return False


def dedup_articles(articles_list: list[dict]) -> list[dict]:
    """Remove duplicate articles by URL, then sort by date descending."""
    seen_urls: set[str] = set()
    deduped: list[dict] = []
    for article in articles_list:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(article)
    deduped.sort(key=lambda a: a.get("date") or "", reverse=True)
    return deduped


def validate_competitors_schema(data: dict) -> None:
    """Validate competitors data structure. Raises SchemaValidationError on failure."""
    if "schema_version" not in data:
        raise SchemaValidationError("Missing schema_version")

    for category, cat_data in data.items():
        if category == "schema_version":
            continue
        if not isinstance(cat_data, dict) or "competitors" not in cat_data:
            raise SchemaValidationError(f"Category '{category}' missing 'competitors'")

        for comp_name, competitor in cat_data["competitors"].items():
            for field in ("name", "blog_url", "articles"):
                if field not in competitor:
                    raise SchemaValidationError(f"Competitor '{comp_name}' missing '{field}'")

            for idx, article in enumerate(competitor["articles"]):
                for field in ("title", "url", "date", "relevance"):
                    if field not in article:
                        raise SchemaValidationError(f"Article {idx} in '{comp_name}' missing '{field}'")


def migrate_competitors_schema(data: dict) -> Optional[dict]:
    """Migrate competitors data between schema versions."""
    version = data.get("schema_version", "1.0")
    if version == "1.0":
        return data
    st.warning(f"Unknown schema version: {version}. Re-collect in Step 4.")
    return None


def save_competitors_data(data: dict) -> None:
    """Always save to session_state, file only when possible."""
    st.session_state[COMPETITORS_SS_KEY] = data
    try:
        os.makedirs(os.path.dirname(COMPETITORS_DATA_PATH), exist_ok=True)
        with open(COMPETITORS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        _comp_log.info("Saved competitors data to %s", COMPETITORS_DATA_PATH)
    except (IOError, OSError) as e:
        _comp_log.warning("File save skipped (Cloud?): %s", e)


def load_competitors_data() -> Optional[dict]:
    """1st: session_state → 2nd: file → 3rd: default fallback."""
    # 1st: session_state
    cached = st.session_state.get(COMPETITORS_SS_KEY)
    if cached is not None:
        return cached

    # 2nd: local file
    try:
        with open(COMPETITORS_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _comp_log.info("Loaded competitors from %s", COMPETITORS_DATA_PATH)
        data = migrate_competitors_schema(data)
        if data is None:
            raise DataLoadingError("Schema migration failed — unknown version")
        validate_competitors_schema(data)
        st.session_state[COMPETITORS_SS_KEY] = data
        return data
    except FileNotFoundError:
        _comp_log.info("No competitors file at %s", COMPETITORS_DATA_PATH)
    except json.JSONDecodeError as e:
        _comp_log.error("Invalid JSON in %s: %s", COMPETITORS_DATA_PATH, e)
        st.warning("Competitor data file has invalid JSON. Re-collect in Step 4.")
    except SchemaValidationError as e:
        _comp_log.error("Schema validation failed for %s: %s", COMPETITORS_DATA_PATH, e)
        st.warning(f"Competitor data format error: {e}")
    except DataLoadingError as e:
        _comp_log.error("Data loading error: %s", e)
        st.warning(str(e))
    except (IOError, PermissionError) as e:
        _comp_log.error("File access error %s: %s", COMPETITORS_DATA_PATH, e)
        st.warning("Unable to read competitor data file.")

    # 3rd: default fallback
    try:
        with open(DEFAULT_COMPETITORS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        _comp_log.info("Loaded default competitors from %s", DEFAULT_COMPETITORS_PATH)
        data = migrate_competitors_schema(data)
        if data is None:
            return None
        validate_competitors_schema(data)
        st.session_state[COMPETITORS_SS_KEY] = data
        return data
    except FileNotFoundError:
        _comp_log.warning("No default competitors file at %s", DEFAULT_COMPETITORS_PATH)
    except json.JSONDecodeError as e:
        _comp_log.error("Invalid JSON in default file: %s", e)
    except SchemaValidationError as e:
        _comp_log.error("Default file schema error: %s", e)
    except Exception as e:
        _comp_log.error("Unexpected error loading defaults: %s", e)
    return None


def fetch_articles_for_competitor(
    client: genai.Client, comp_key: str, comp_data: dict, category: str
) -> list[dict]:
    """Fetch articles using Gemini + Google Search grounding."""
    blog_url = comp_data.get("blog_url", "")
    current_year = datetime.now().year

    prompt = f"""
Find the 3 most recent technical articles from {comp_data['name']}:
Blog: {blog_url}

Category: {category}

Return ONLY a JSON array (no markdown, no wrapping):
[
  {{
    "title": "Article Title",
    "url": "https://exact-url",
    "date": "YYYY-MM-DD",
    "relevance": "Why it matches {category}"
  }}
]

Requirements:
- URLs in valid http/https format
- Dates in YYYY-MM-DD format only
- Published in {current_year - 1}-{current_year}
- Max 3 articles per company
- No "company" field
"""

    try:
        resp = _call_search(client, prompt)
        text = _extract_text(resp)
        articles = _parse_json(text)
        if not isinstance(articles, list):
            _comp_log.warning("Non-list response for %s, got %s", comp_key, type(articles).__name__)
            return []
        _comp_log.info("Fetched %d articles for %s", len(articles), comp_key)
        return articles
    except (ValueError, json.JSONDecodeError) as e:
        _comp_log.error("Parse error for %s: %s", comp_key, e)
        st.warning(f"Could not parse articles for {comp_data.get('name', comp_key)}. Skipping.")
        return []
    except Exception as e:
        _comp_log.error("Gemini API error for %s: %s", comp_key, e)
        raise GeminiAPIError(f"API call failed for {comp_key}: {e}") from e


def collect_competitor_articles() -> tuple[int, int] | None:
    """Collect articles for current category using Gemini + Google Search."""
    try:
        category = st.session_state.get("category", "")

        if not category:
            st.warning("No category selected. Please complete Step 1 first.")
            return None

        _validate_competitor_config()
        _comp_log.info("Starting collection for category: %s", category)

        all_data = load_competitors_data()
        if all_data is None:
            all_data = {"schema_version": "1.0"}

        if category not in all_data:
            all_data[category] = {
                "metadata": {
                    "category": category,
                    "generated_date": datetime.now().strftime("%Y-%m-%d"),
                    "collected_timestamp": datetime.now().isoformat() + "Z",
                    "source": "ai_deep_research",
                },
                "competitors": {},
            }

        api_key = st.session_state.get("_api_key") or os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
        if not api_key:
            st.warning("Gemini API key not set. Enter it in the sidebar or set GOOGLE_GENERATIVE_AI_API_KEY.")
            return None
        client = get_client(api_key)

        if category not in COMPETITORS_BY_CATEGORY:
            raise CompetitorDataError(f"No competitors defined for category: {category}")

        competitors = COMPETITORS_BY_CATEGORY[category]
        failed_comps: list[str] = []

        for comp_key, comp_data in competitors.items():
            try:
                articles = fetch_articles_for_competitor(
                    client, comp_key, comp_data, category
                )

                validated_articles = [
                    a for a in articles
                    if validate_url_format(a.get("url", ""))
                ]
                filtered_count = len(articles) - len(validated_articles)
                if filtered_count > 0:
                    _comp_log.info("Filtered %d invalid URLs for %s", filtered_count, comp_key)

                deduped_articles = dedup_articles(validated_articles)

                if comp_key not in all_data[category]["competitors"]:
                    all_data[category]["competitors"][comp_key] = {
                        "name": comp_data.get("name", ""),
                        "blog_url": comp_data.get("blog_url", ""),
                        "tier": comp_data.get("tier", 2),
                        "editable": False,
                        "articles": [],
                    }

                all_data[category]["competitors"][comp_key]["articles"] = deduped_articles

            except GeminiAPIError as e:
                _comp_log.error("API error for %s: %s", comp_key, e)
                failed_comps.append(comp_data.get("name", comp_key))
                st.warning(f"API error for {comp_data.get('name', comp_key)}. Skipping.")
                continue
            except Exception as e:
                _comp_log.error("Unexpected error for %s: %s", comp_key, e)
                failed_comps.append(comp_data.get("name", comp_key))
                st.warning(f"Failed to collect for {comp_data.get('name', comp_key)}: {str(e)}")
                continue

        if failed_comps and len(failed_comps) == len(competitors):
            st.error("All competitor collections failed. Check API key and try again.")
            return None

        validate_competitors_schema(all_data)
        save_competitors_data(all_data)

        cat_data = all_data.get(category, {})
        companies_count = len(cat_data.get("competitors", {}))
        articles_count = sum(
            len(c.get("articles", []))
            for c in cat_data.get("competitors", {}).values()
        )
        _comp_log.info("Collection complete: %d companies, %d articles", companies_count, articles_count)
        if failed_comps:
            st.warning(f"Partial collection — skipped: {', '.join(failed_comps)}")
        return companies_count, articles_count

    except SchemaValidationError as e:
        _comp_log.error("Schema validation after collection: %s", e)
        st.error(f"Data format error after collection: {e}")
        return None
    except CompetitorDataError as e:
        _comp_log.error("Competitor data error: %s", e)
        st.error(str(e))
        return None
    except Exception as e:
        _comp_log.error("Unexpected collection error: %s", e)
        st.error(f"Collection failed: {str(e)}")
        return None


def load_competitors_for_category(category: str, available_data: Optional[dict] = None) -> Optional[dict]:
    """Load competitors matching article category — case-insensitive exact match."""
    if not available_data:
        return None
    if "schema_version" not in available_data:
        return None
    for cat_key in available_data:
        if cat_key != "schema_version" and cat_key.lower() == category.lower():
            return available_data[cat_key]
    return None


def build_competitive_context(category: str, data: Optional[dict]) -> str:
    """Generate competitor context block for injection into article generation prompt."""
    if not data:
        return ""

    cat_data = load_competitors_for_category(category, data)
    if not cat_data:
        return ""

    competitor_lines: list[str] = []
    for comp in cat_data.get("competitors", {}).values():
        name = comp.get("name", "")
        articles = comp.get("articles", [])
        if articles:
            titles = [f'  - "{a.get("title", "")}"' for a in articles[:2]]
            competitor_lines.append(f"**{name}**:")
            competitor_lines.extend(titles)

    if not competitor_lines:
        return ""

    lines = ["## Competitive Landscape (for differentiation only)\n"]
    lines.append("Competitors already covering this space:\n")
    lines.extend(competitor_lines)
    lines.append(
        "\nInstruction: Write from a distinct angle not covered above. "
        "Avoid duplicating their exact topics. Focus on unique insights, "
        "different benchmarks, or underexplored sub-problems."
    )
    return "\n".join(lines)


def render_competitors_dashboard(category: str, category_data: dict) -> None:
    """Render competitive analysis dashboard inside Step 5 tab."""
    st.markdown("### Competitive Analysis")
    metadata = category_data.get("metadata", {})
    collected = metadata.get("collected_timestamp", "N/A")

    competitors = category_data.get("competitors", {})
    total_articles = sum(len(c.get("articles", [])) for c in competitors.values())

    st.markdown(
        f'<p style="color:#64748b;font-size:.82rem">'
        f'Category: <strong>{category}</strong> &nbsp;|&nbsp; '
        f'Competitors: {len(competitors)} &nbsp;|&nbsp; '
        f'Articles: {total_articles} &nbsp;|&nbsp; '
        f'Collected: {collected}</p>',
        unsafe_allow_html=True,
    )

    if not competitors:
        st.info("No competitor data available for this category.")
        return

    # Sort by tier (1 first), then name
    sorted_comps = sorted(
        competitors.values(),
        key=lambda c: (c.get("tier", 99), c.get("name", "")),
    )

    # ── Competitors table ──────────────────────────────────────
    st.markdown("#### Competitors")
    table_rows = [
        {
            "Company": c.get("name", ""),
            "Tier": c.get("tier", "—"),
            "Articles": len(c.get("articles", [])),
            "Blog": c.get("blog_url", ""),
        }
        for c in sorted_comps
    ]
    st.dataframe(
        table_rows,
        column_config={
            "Company": st.column_config.TextColumn(width="large"),
            "Tier": st.column_config.NumberColumn(width="small"),
            "Articles": st.column_config.NumberColumn(width="small"),
            "Blog": st.column_config.LinkColumn(width="medium"),
        },
        hide_index=True,
        use_container_width=True,
    )

    # ── Articles accordion (sorted by tier, CLOSED by default) ─
    st.markdown("#### Competitor Articles")
    for comp in sorted_comps:
        name = comp.get("name", "")
        articles = comp.get("articles", [])
        # Articles already sorted by dedup_articles() during collection;
        # defensive re-sort only if loaded from file/default
        sorted_articles = sorted(
            articles, key=lambda a: a.get("date") or "", reverse=True
        )
        with st.expander(f"{name} ({len(sorted_articles)} articles)", expanded=False):
            if not sorted_articles:
                st.caption("No articles collected.")
            else:
                for a in sorted_articles:
                    url = a.get("url", "")
                    title_text = a.get("title", "Untitled")
                    date = a.get("date", "—")
                    relevance = a.get("relevance", "")
                    link = f"[{title_text}]({url})" if url else title_text
                    st.markdown(
                        f"**{link}**  \n"
                        f"Published: {date} &nbsp;|&nbsp; Relevance: {relevance}"
                    )

# ══════════════════════════════════════════════════════════════════
# 6 · IMAGE GENERATION  (Pollinations.ai — no key required)
# ══════════════════════════════════════════════════════════════════
def pollinations_url(prompt: str, w: int = 1200, h: int = 630, seed: int = 42) -> str:
    """Return a Pollinations.ai Flux image URL (no API key needed)."""
    enc = quote(prompt[:400])
    return (
        f"https://image.pollinations.ai/prompt/{enc}"
        f"?width={w}&height={h}&model=flux&nologo=true&enhance=true&seed={seed}"
    )


def _seed(text: str) -> int:
    return int(hashlib.md5(text.encode()).hexdigest(), 16) % 100_000

# ══════════════════════════════════════════════════════════════════
# 7 · WORKFLOW HELPERS
# ══════════════════════════════════════════════════════════════════

# ── Step 2: trending topics ────────────────────────────────────
def fetch_topics(client, category: str) -> list[dict]:
    prompt = f"""
You are a senior technical analyst. Using Google Search, identify EXACTLY 5 highly-specific,
trending technical topics within "{category}" based on 2025-2026 data (conferences, papers,
benchmark announcements, product launches).

Return ONLY a JSON array of 5 objects:
[
  {{"title": "<concise topic name>", "description": "<2-sentence technical rationale, cite data point or event>", "trend_signal": "<what makes it trending in 2025-2026>"}},
  ...
]
Strict: no markdown wrappers, pure JSON only.
"""
    resp = _call_search(client, prompt)
    return _parse_json(_extract_text(resp))


# ── Step 3: SEO/AEO title optimization ────────────────────────
def fetch_titles(client, topic: dict) -> list[dict]:
    prompt = f"""
You are an SEO strategist specializing in AEO (Answer Engine Optimization) for technical content.
Given the topic below, generate EXACTLY 5 article titles — each with a distinct technical angle.

Topic: {topic['title']}
Description: {topic['description']}

Requirements per title:
- Optimized for Google's AI Overviews and featured snippets
- Contains a primary keyword (measurable/quantitative angle preferred)
- 55–70 characters
- Distinct angle: e.g. benchmark-focused, cost-analysis, architectural deep-dive, failure-case, comparative

Return JSON array only:
[
  {{
    "title": "<full article title>",
    "angle": "<one of: benchmark | cost-analysis | architecture | failure-case | comparative>",
    "primary_keyword": "<exact keyword string>",
    "seo_rationale": "<1-sentence reason this title wins in SERPs/AEO>"
  }},
  ...5 items...
]
"""
    resp = _call(client, prompt, _json_cfg())
    return _parse_json(_extract_text(resp))


# ── Step 4: deep research — 8 high-authority sources ──────────
def deep_research(client, title: str) -> tuple[list[dict], str]:
    """
    Returns (sources_list, notebooklm_context_text).
    Uses Google Search grounding to find real, verifiable sources.
    """
    prompt = f"""
You are a technical research auditor. Using Google Search, find EXACTLY 8 high-authority sources
for the following article title. Sources MUST be published between 2023 and 2026.

Article Title: "{title}"

Authority tiers (you MUST cover all):
- Tier 1 (2 sources): Peer-reviewed papers (arXiv, IEEE, ACM, Nature)
- Tier 2 (2 sources): Official vendor whitepapers or technical documentation
- Tier 3 (2 sources): Tier-1 tech journalism (The Register, Ars Technica, AnandTech, Tom's Hardware, IEEE Spectrum)
- Tier 4 (2 sources): Independent benchmarks or audit reports (MLCommons, SPEC, Phoronix, TPC)

For each source return:
{{
  "id": 1,
  "title": "<exact article/paper title>",
  "url": "<full URL>",
  "publisher": "<publisher/venue>",
  "date": "<YYYY-MM or YYYY>",
  "tier": "<Tier 1|2|3|4>",
  "snippet": "<2-sentence key finding or claim from this source>",
  "key_data_point": "<specific number, metric, or fact from this source>"
}}

Return ONLY a JSON array of 8 objects.
"""
    resp = _call_search(client, prompt)
    sources = _parse_json(_extract_text(resp))

    # Extract any real grounding citations from the API response
    real_urls: list[str] = []
    try:
        for chunk in resp.candidates[0].grounding_metadata.grounding_chunks:
            if chunk.web and chunk.web.uri:
                real_urls.append(chunk.web.uri)
    except Exception:
        pass

    # Annotate sources with "verified" flag if URL appears in grounding
    for src in sources:
        src["grounded"] = any(
            src.get("url", "").split("/")[2] in u for u in real_urls
        )

    # Simulate NotebookLM context synthesis
    context = _build_notebooklm_context(client, title, sources)
    return sources, context


def _build_notebooklm_context(client, title: str, sources: list[dict]) -> str:
    """Synthesize a NotebookLM-style cross-reference knowledge base."""
    sources_text = "\n".join(
        f"[{s['id']}] ({s['tier']}) {s['title']} ({s['date']}) — {s['snippet']} KEY DATA: {s.get('key_data_point','N/A')}"
        for s in sources
    )
    prompt = f"""
You are simulating Google NotebookLM's deep contextual understanding layer.
Given 8 research sources for the article "{title}", produce a structured knowledge synthesis:

SOURCES:
{sources_text}

Produce a concise knowledge synthesis (400–500 words) that:
1. Identifies 3 consensus findings across ≥3 sources
2. Flags 2 conflicting claims between sources (with source IDs)
3. Lists 3 critical knowledge gaps NOT covered by these sources
4. Extracts the 5 most important quantitative data points with source IDs
5. Rates overall evidence strength: STRONG / MODERATE / WEAK with justification

Format as plain prose with labeled sections. This will be injected as context for article generation.
"""
    resp = _call(client, prompt, _plain_cfg())
    return _extract_text(resp)


# ── Step 5: Article generation ─────────────────────────────────
ARTICLE_SCHEMA = {
    "type": "object",
    "properties": {
        "article_title":       {"type": "string"},
        "executive_summary":   {"type": "string"},
        "sections": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "heading":        {"type": "string"},
                    "content":        {"type": "string"},
                    "chart_suggestion": {"type": "string"},
                    "image_prompt":   {"type": "string"},
                },
            },
        },
        "comparison": {
            "type": "object",
            "properties": {
                "heading":      {"type": "string"},
                "alternatives": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name":     {"type": "string"},
                            "pros":     {"type": "string"},
                            "cons":     {"type": "string"},
                            "tco_note": {"type": "string"},
                            "best_for": {"type": "string"},
                        },
                    },
                },
                "content": {"type": "string"},
            },
        },
        "anti_recommendation": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        "tco_analysis": {
            "type": "object",
            "properties": {
                "heading": {"type": "string"},
                "content": {"type": "string"},
            },
        },
        "conclusion":   {"type": "string"},
        "references":   {"type": "array", "items": {"type": "string"}},
        "metadata": {
            "type": "object",
            "properties": {
                "seo_slug":        {"type": "string"},
                "meta_description": {"type": "string"},
                "title_tag":       {"type": "string"},
                "word_count":      {"type": "integer"},
            },
        },
        "quality_audit": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "check":  {"type": "string"},
                    "passed": {"type": "boolean"},
                    "note":   {"type": "string"},
                },
            },
        },
    },
}


def generate_article(client, title: str, sources: list[dict], context: str, competitive_context: str = "") -> dict:
    sources_block = "\n".join(
        f"[{s['id']}] {s['title']} ({s['publisher']}, {s['date']}) | {s['snippet']} | KEY DATA: {s.get('key_data_point','')}"
        for s in sources
    )

    prompt = f"""
You are the world's most rigorous technical content auditor writing for a senior engineering audience.
Produce a complete article JSON adhering to every rule below.

━━━━━━━━━━━━ ARTICLE TITLE ━━━━━━━━━━━━
{title}

━━━━━━━━━━━━ NOTEBOOKLM CONTEXT (cross-reference this) ━━━━━━━━━━━━
{context}

━━━━━━━━━━━━ VERIFIED SOURCES (cite as [1]–[8]) ━━━━━━━━━━━━
{sources_block}

━━━━━━━━━━━━ STRICT CONTENT RULES ━━━━━━━━━━━━
WORD COUNT      : 1,000–1,500 words total (executive summary + all sections + comparison + anti-rec + tco + conclusion).
EXECUTIVE SUMMARY: Exactly 100 words. No bullets. Opening paragraph that captures the full argument.
PARAGRAPHS      : No bullet points anywhere. Use 2–3 sentence paragraphs for scannability.
EVIDENCE        : Every quantitative claim MUST include: value, source [N], methodology/test-condition, and independent-vs-vendor label.
                  Include at least 3 perspectives per major claim.
CRITICAL ANALYSIS: Address vendor lock-in, hidden infrastructure/training costs, and performance limitations.
                  Include conservative AND optimistic estimates side-by-side.
ANTI-RECOMMENDATION: Explain precisely when engineers should AVOID this technology (failure scenarios, scale limits, alternative-is-better situations).
TCO ANALYSIS    : Cover licensing, infrastructure, training/onboarding, maintenance, and exit costs over a 3-year horizon.
COMPARISON      : Compare 2–3 direct alternatives on: latency, throughput, cost/unit, vendor-lock-in risk, maturity.
ACRONYMS        : Define every acronym on first use. Example: "FP8 (8-bit floating-point)".
PHYSICAL LIMITS : Address thermal envelope, power budget, or scaling bottleneck relevant to the topic.

━━━━━━━━━━━━ OUTPUT SCHEMA ━━━━━━━━━━━━
Return a single JSON object (no markdown fences) with these keys:

article_title        : string  — final optimized title
executive_summary    : string  — exactly 100 words, paragraph form
sections             : array of objects, each with:
  heading            : H2 text
  content            : 3–4 paragraphs of body text (no bullets)
  chart_suggestion   : specific chart type + axes + what it should visualize
  image_prompt       : detailed Flux/Stable-Diffusion prompt for a professional technical illustration
comparison           : object with heading, alternatives (array), content
anti_recommendation  : object with heading, content
tco_analysis         : object with heading, content
conclusion           : string — 1 strong closing paragraph
references           : array of formatted citation strings [1]–[8]
metadata             : object with seo_slug, meta_description (≤155 chars), title_tag, word_count
quality_audit        : array of 4 objects (check, passed, note) verifying:
  1. All numbers cited with methodology + independent validation
  2. All acronyms defined at first use
  3. Physical constraints (thermal/power/scaling) addressed
  4. No repetition — themes consolidated

Output ONLY the JSON. No preamble, no explanation.
"""
    if competitive_context:
        prompt += f"\n\n{competitive_context}"
    resp = _call(client, prompt, _json_cfg())
    return _parse_json(_extract_text(resp))


# ── Claude article generation ───────────────────────────────────
def generate_article_claude(
    anthropic_client,
    title: str,
    accepted_sources: list[dict],
    all_sources: list[dict],
    context: str,
    qa_feedback: str = "",
    competitive_context: str = "",
) -> dict:
    """Generate the full article using Claude. Falls back to error dict on failure."""

    # Separate accepted vs. declined for the prompt
    accepted_ids = {s.get("id") for s in accepted_sources}
    declined = [s for s in all_sources if s.get("id") not in accepted_ids]

    primary_block = "\n".join(
        f"[{s['id']}] {s['title']} ({s['publisher']}, {s['date']})\n"
        f"    Snippet: {s['snippet']}\n"
        f"    Key data: {s.get('key_data_point','')}"
        for s in accepted_sources
    )
    supp_block = (
        "\n".join(
            f"[{s['id']}] {s['title']} — context only, do NOT cite"
            for s in declined
        )
        if declined else "None"
    )
    qa_note = (
        f"\n\nPREVIOUS DRAFT FAILED THESE QA CHECKS — fix them in this version:\n{qa_feedback}"
        if qa_feedback else ""
    )

    prompt = f"""You are the world's most rigorous technical content auditor writing for senior engineers.
Produce a complete article as a single JSON object following every rule below.{qa_note}

━━━━━━━━━━━━ ARTICLE TITLE ━━━━━━━━━━━━
{title}

━━━━━━━━━━━━ NOTEBOOKLM CONTEXT ━━━━━━━━━━━━
{context}

━━━━━━━━━━━━ PRIMARY SOURCES — CITE THESE (accepted by editor) ━━━━━━━━━━━━
{primary_block}

━━━━━━━━━━━━ SUPPLEMENTARY CONTEXT — DO NOT CITE ━━━━━━━━━━━━
{supp_block}

━━━━━━━━━━━━ STRICT CONTENT RULES ━━━━━━━━━━━━
WORD COUNT       : 1,000–1,500 words total.
EXECUTIVE SUMMARY: Exactly 100 words. Paragraph form. No bullets.
PARAGRAPHS       : NO bullet points anywhere. 2–3 sentence paragraphs only.
EVIDENCE         : Every quantitative claim must include value + [sourceN] + methodology/test condition + (VENDOR CLAIM) or (INDEPENDENT).
                   Include ≥3 perspectives per major claim.
CRITICAL ANALYSIS: Address vendor lock-in, hidden infra/training costs, scaling limits.
                   Pair conservative estimates with optimistic ones.
ANTI-REC         : Explain exactly when NOT to use this technology (failure thresholds, scale limits, better alternatives exist).
TCO              : Cover licensing, infra, training/onboarding, maintenance, exit costs over 3 years.
COMPARISON       : 2–3 direct alternatives on latency, throughput, $/unit, lock-in risk, maturity.
ACRONYMS         : Define every acronym on first use, e.g. "FP8 (8-bit floating-point)".
PHYSICAL LIMITS  : Explicitly address thermal envelope, power budget, or scaling bottleneck.

━━━━━━━━━━━━ OUTPUT SCHEMA ━━━━━━━━━━━━
Return ONE JSON object — no markdown fences, no preamble:

{{
  "article_title": "final optimized title string",
  "executive_summary": "exactly 100 words paragraph",
  "sections": [
    {{
      "heading": "H2 text",
      "content": "3-4 paragraphs no bullets",
      "chart_suggestion": "chart type + axes + what to visualize",
      "image_prompt": "detailed Flux prompt for technical illustration"
    }}
  ],
  "comparison": {{
    "heading": "string",
    "alternatives": [
      {{"name":"string","pros":"string","cons":"string","tco_note":"string","best_for":"string"}}
    ],
    "content": "analysis paragraph"
  }},
  "anti_recommendation": {{"heading":"string","content":"paragraph"}},
  "tco_analysis":        {{"heading":"string","content":"paragraph"}},
  "conclusion": "strong closing paragraph",
  "references": ["[1] formatted citation", "..."],
  "metadata": {{
    "seo_slug": "kebab-case",
    "meta_description": "≤155 chars",
    "title_tag": "SEO title",
    "word_count": 1200
  }},
  "quality_audit": [
    {{"check":"All numbers cited with methodology","passed":true,"note":"..."}},
    {{"check":"All acronyms defined at first use","passed":true,"note":"..."}},
    {{"check":"Physical constraints addressed","passed":true,"note":"..."}},
    {{"check":"No repetition — themes consolidated","passed":true,"note":"..."}}
  ]
}}

Output ONLY the JSON. Nothing else."""

    if competitive_context:
        prompt += f"\n\n{competitive_context}"

    model = CLAUDE_MODEL
    for attempt in range(2):
        try:
            msg = anthropic_client.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            raw = msg.content[0].text
            result = _parse_json(raw)
            st.session_state.claude_model_used = model
            return result
        except Exception as e:
            if attempt == 0 and CLAUDE_FALLBACK not in model:
                model = CLAUDE_FALLBACK
                continue
            raise e


# ── Programmatic QA (10-gate, independent of model self-report) ──
def run_comprehensive_qa(art: dict) -> list[dict]:
    """Run 10 programmatic quality checks on the generated article."""
    checks: list[dict] = []

    # Collect all prose
    exec_sum = art.get("executive_summary", "")
    body_parts = [s.get("content", "") for s in art.get("sections", [])]
    cmp_content  = art.get("comparison", {}).get("content", "")
    tco_content  = art.get("tco_analysis", {}).get("content", "")
    anti_content = art.get("anti_recommendation", {}).get("content", "")
    conclusion   = art.get("conclusion", "")
    all_text = " ".join(filter(None, [exec_sum, *body_parts, cmp_content, tco_content, anti_content, conclusion]))
    body_text = " ".join(body_parts)

    def add(category: str, check: str, passed: bool, note: str):
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
    phys_kw = ["thermal","power","watt","TDP","cooling","heat","bottleneck",
               "bandwidth","latency","scaling limit","memory wall","bandwidth-bound"]
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
        f"Clean" if not bullets else f"{len(bullets)} bullet(s) detected")

    return checks


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
        resp = _call(client, prompt, _json_cfg())
        text = _extract_text(resp)
        scores = _parse_json(text)
        # Ensure all criteria are present with float values
        result = {}
        for name, _ in RUBRIC_CRITERIA:
            result[name] = float(scores.get(name, 0.0))
        return result
    except Exception:
        return {name: 0.0 for name, _ in RUBRIC_CRITERIA}


# ══════════════════════════════════════════════════════════════════
# 8 · UI COMPONENT HELPERS
# ══════════════════════════════════════════════════════════════════

def render_header():
    st.markdown("""
<div class="main-header">
  <h1>⚙️ TechAudit Content Architect</h1>
  <p>Strict, evidence-based AI technical writing &nbsp;·&nbsp;
     <strong>Research:</strong> gemini-2.5-pro &nbsp;·&nbsp;
     <strong>Writing:</strong> claude-opus-4-6 &nbsp;·&nbsp;
     Google Search grounded</p>
</div>
""", unsafe_allow_html=True)


def render_steps(current: int):
    parts = []
    for i, (num, label) in enumerate(STEPS, start=1):
        cls = "active" if i == current else ("done" if i < current else "")
        icon = "✓" if i < current else num
        parts.append(f"""
<div class="step-item">
  <div class="step-dot {cls}">{icon}</div>
  <span class="step-label {cls}">{label}</span>
</div>""")
        if i < len(STEPS):
            parts.append('<div class="step-connector"></div>')

    st.markdown(f'<div class="step-row">{"".join(parts)}</div>', unsafe_allow_html=True)


def render_source_card(src: dict, idx: int):
    verified_badge = (
        '<span class="source-badge" style="background:rgba(5,150,105,.15);color:#34d399;border-color:rgba(52,211,153,.3)">✓ GROUNDED</span> '
        if src.get("grounded") else ""
    )
    st.markdown(f"""
<div class="source-card">
  <span class="source-badge">SOURCE [{src['id']}] · {src['tier']}</span>
  {verified_badge}<span class="source-date">📅 {src.get('date','')}</span>
  <h4 style="margin:.4rem 0 .3rem;font-size:.95rem;color:#e2e8f0">{src['title']}</h4>
  <p style="font-size:.78rem;color:#64748b;margin:0 0 .4rem">
    🏛 {src.get('publisher','')} &nbsp;·&nbsp;
    🔗 <a href="{src.get('url','#')}" target="_blank" style="color:#818cf8">{src.get('url','')[:60]}…</a>
  </p>
  <p style="font-size:.82rem;color:#94a3b8;margin:0 0 .3rem;line-height:1.6">{src.get('snippet','')}</p>
  <p style="font-size:.78rem;color:#a5b4fc;margin:0">
    📊 <strong>Key data:</strong> {src.get('key_data_point','—')}
  </p>
</div>
""", unsafe_allow_html=True)




def render_article(art: dict):
    article_title = art.get("article_title", "")

    # ── Executive summary ─────────────────────────────────────────
    st.markdown(f"""
<div class="executive-summary">
  <strong style="color:#a5b4fc;font-style:normal">Executive Summary</strong><br><br>
  {art.get('executive_summary','')}
</div>""", unsafe_allow_html=True)

    # ── Body sections — full-width image above each section ───────
    for sec in art.get("sections", []):
        heading = sec.get("heading", "")
        st.markdown(f'<div class="article-h2">{heading}</div>', unsafe_allow_html=True)

        # Section body paragraphs
        for para in sec.get("content", "").split("\n\n"):
            if para.strip():
                st.markdown(f'<p class="article-p">{para.strip()}</p>',
                            unsafe_allow_html=True)

        # Chart hint
        if sec.get("chart_suggestion"):
            st.markdown(
                f'<div class="chart-hint">📊 <span>Suggested visualization:</span>'
                f' {sec["chart_suggestion"]}</div>',
                unsafe_allow_html=True,
            )

    # ── Comparison section ────────────────────────────────────────
    cmp = art.get("comparison", {})
    if cmp:
        cmp_heading = cmp.get("heading", "Comparative Analysis")
        st.markdown(f'<div class="article-h2">{cmp_heading}</div>', unsafe_allow_html=True)
        alts = cmp.get("alternatives", [])
        if alts:
            rows_html = []
            for a in alts:
                if isinstance(a, dict):
                    rows_html.append(
                        f"<tr><td><strong>{a.get('name','—')}</strong></td>"
                        f"<td>✅ {a.get('pros','—')}</td>"
                        f"<td>⚠️ {a.get('cons','—')}</td>"
                        f"<td>{a.get('tco_note','—')}</td>"
                        f"<td><em>{a.get('best_for','—')}</em></td></tr>"
                    )
                elif isinstance(a, str):
                    rows_html.append(
                        f"<tr><td colspan='5' style='color:#94a3b8'>{a}</td></tr>"
                    )
            rows = "".join(rows_html)
            st.markdown(f"""
<table class="cmp-table">
  <thead><tr>
    <th>Solution</th><th>Pros</th><th>Cons</th><th>3-yr TCO Note</th><th>Best For</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>""", unsafe_allow_html=True)
        if cmp.get("content"):
            st.markdown(f'<p class="article-p">{cmp["content"]}</p>', unsafe_allow_html=True)

    # ── TCO analysis ──────────────────────────────────────────────
    tco = art.get("tco_analysis", {})
    if tco:
        tco_heading = tco.get("heading", "Total Cost of Operations")
        st.markdown(f"""
<div class="tco-box">
  <strong style="color:#fbbf24">💰 {tco_heading}</strong><br><br>
  <p class="article-p" style="margin:0">{tco.get('content','')}</p>
</div>""", unsafe_allow_html=True)

    # ── Anti-recommendation ───────────────────────────────────────
    anti = art.get("anti_recommendation", {})
    if anti:
        anti_heading = anti.get("heading", "When NOT to Use This")
        st.markdown(f"""
<div class="anti-rec-box">
  <strong style="color:#f87171">🚫 {anti_heading}</strong><br><br>
  <p class="article-p" style="margin:0">{anti.get('content','')}</p>
</div>""", unsafe_allow_html=True)

    # ── Conclusion ────────────────────────────────────────────────
    if art.get("conclusion"):
        st.markdown('<div class="article-h2">Conclusion</div>', unsafe_allow_html=True)
        st.markdown(f'<p class="article-p">{art["conclusion"]}</p>', unsafe_allow_html=True)

    # References
    refs = art.get("references", [])
    if refs:
        st.markdown('<div class="article-h2">References</div>', unsafe_allow_html=True)
        for r in refs:
            st.markdown(f'<p style="font-size:.8rem;color:#64748b;margin:.2rem 0">{r}</p>',
                        unsafe_allow_html=True)


def _generate_rerun_strategies(qa_checks: list[dict]) -> list[dict]:
    """Return 3 targeted regeneration strategy dicts based on which QA checks failed."""
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
    all_failed = [c for c in failed]
    strategies.append({
        "icon": "⚖️",
        "label": "Balanced Revision",
        "description": (
            f"Spread improvements evenly across all {len(failed_cats)} failing "
            f"categories ({len(all_failed)} total checks) with equal attention to each."
        ),
        "guidance": (
            "BALANCED REVISION — fix ALL failed checks proportionally:\n"
            + "\n".join(
                f"• [{c.get('category','?')}] {c['check']}"
                for c in all_failed
            )
            + "\nDo not sacrifice any category for another."
        ),
    })

    # Strategy C — structural rewrite or citation focus, whichever is more relevant
    struct_cats = {"Structure", "Content", "Writing Quality"}
    struct_checks = [
        c["check"] for c in failed if c.get("category") in struct_cats
    ]
    if struct_checks:
        strategies.append({
            "icon": "🔄",
            "label": "Structural Rewrite",
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
            "label": "Precision Citation Fix",
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


def render_quality_audit(qa_checks: list[dict], model_audit: list[dict] | None = None,
                          on_rerun=None, rubric_scores: dict | None = None):
    """
    Rich visual QA panel.
    qa_checks     — programmatic 10-gate checks from run_comprehensive_qa()
    model_audit   — 4-gate self-report from the AI (optional)
    on_rerun      — callable; if provided, shows a Re-generate button
    rubric_scores — dict {criterion: score} from score_article_rubric()
    """
    st.markdown("### 🔍 Publication Quality Audit")

    # ── Score summary ────────────────────────────────────────────
    total  = len(qa_checks)
    passed = sum(1 for c in qa_checks if c.get("passed"))
    pct    = int(passed / total * 100) if total else 0

    if pct >= 90:
        grade, color_cls, bar_color, grade_text = "A", "green", "#34d399", "PUBLICATION READY"
    elif pct >= 70:
        grade, color_cls, bar_color, grade_text = "B", "yellow", "#fbbf24", "MINOR REVISIONS NEEDED"
    else:
        grade, color_cls, bar_color, grade_text = "C", "red", "#f87171", "SIGNIFICANT ISSUES — RE-GENERATE"

    st.markdown(f"""
<div class="qa-score-header">
  <div class="qa-score-circle {color_cls}">{grade}</div>
  <div>
    <div class="qa-grade-label {color_cls}">{grade_text}</div>
    <div style="color:#64748b;font-size:.82rem;margin-top:.25rem">
      {passed} / {total} checks passed &nbsp;·&nbsp; {pct}%
    </div>
    <div class="qa-bar-wrap">
      <div class="qa-bar-bg">
        <div class="qa-bar-fill" style="width:{pct}%;background:{bar_color}"></div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Grouped checks ───────────────────────────────────────────
    categories: dict[str, list[dict]] = {}
    for item in qa_checks:
        cat = item.get("category", "Other")
        categories.setdefault(cat, []).append(item)

    for cat, items in categories.items():
        cat_pass = sum(1 for i in items if i.get("passed"))
        cat_total = len(items)
        cat_color = "#34d399" if cat_pass == cat_total else ("#fbbf24" if cat_pass > 0 else "#f87171")
        st.markdown(
            f'<div class="qa-category-header">'
            f'<span style="color:{cat_color}">■</span> &nbsp;{cat} '
            f'<span style="color:{cat_color};font-weight:600">{cat_pass}/{cat_total}</span></div>',
            unsafe_allow_html=True,
        )
        for item in items:
            icon = "✅" if item.get("passed") else "❌"
            cls  = "audit-pass" if item.get("passed") else "audit-fail"
            note = item.get("note", "")
            check = item.get("check", "")
            st.markdown(f"""
<div class="audit-row {cls}">
  <span class="audit-icon">{icon}</span>
  <div>
    <strong style="font-size:.83rem">{check}</strong>
    {"<br><span style='color:#94a3b8;font-size:.76rem'>" + note + "</span>" if note else ""}
  </div>
</div>""", unsafe_allow_html=True)

    # ── Rubric scoring ───────────────────────────────────────────
    if rubric_scores:
        st.markdown('<div class="qa-category-header"><span style="color:#a78bfa">■</span> &nbsp;Rubric Scores <span style="color:#64748b;font-size:.72rem">— AI evaluation (target / 10)</span></div>',
                    unsafe_allow_html=True)
        rubric_failed = []
        for name, target in RUBRIC_CRITERIA:
            score = rubric_scores.get(name, 0.0)
            passed = score >= target
            if not passed:
                rubric_failed.append((name, score, target))
            bar_pct = int(score / 10 * 100)
            bar_color = "#34d399" if passed else "#f87171"
            icon = "✅" if passed else "❌"
            cls = "audit-pass" if passed else "audit-fail"
            st.markdown(f"""
<div class="audit-row {cls}" style="flex-direction:column;gap:.4rem">
  <div style="display:flex;align-items:center;gap:.6rem;width:100%">
    <span class="audit-icon">{icon}</span>
    <strong style="font-size:.83rem;flex:1">{name}</strong>
    <span style="font-size:.85rem;font-weight:700;color:{bar_color}">{score:.1f}</span>
    <span style="font-size:.75rem;color:#64748b">/ target {target}</span>
  </div>
  <div style="background:#1e293b;border-radius:99px;height:6px;width:100%;margin-left:1.6rem">
    <div style="width:{bar_pct}%;height:100%;border-radius:99px;background:{bar_color};transition:width .4s"></div>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Model self-audit ─────────────────────────────────────────
    if model_audit:
        st.markdown('<div class="qa-category-header"><span style="color:#818cf8">■</span> &nbsp;Model Self-Report (Claude) <span style="color:#64748b;font-size:.72rem">— informational</span></div>',
                    unsafe_allow_html=True)
        for item in model_audit:
            icon = "✅" if item.get("passed") else "⚠️"
            cls  = "audit-pass" if item.get("passed") else "audit-fail"
            note = item.get("note", "")
            check = item.get("check", "")
            st.markdown(f"""
<div class="audit-row {cls}" style="opacity:.85">
  <span class="audit-icon">{icon}</span>
  <div>
    <strong style="font-size:.83rem">{check}</strong>
    {"<br><span style='color:#94a3b8;font-size:.76rem'>" + note + "</span>" if note else ""}
  </div>
</div>""", unsafe_allow_html=True)

    # ── Re-generate with strategy selection ──────────────────────
    rubric_failed_labels = []
    if rubric_scores:
        rubric_failed_labels = [
            f"{name} (score {rubric_scores.get(name, 0):.1f} < target {target})"
            for name, target in RUBRIC_CRITERIA
            if rubric_scores.get(name, 0) < target
        ]
    needs_rerun = pct < 90 or bool(rubric_failed_labels)
    if on_rerun and needs_rerun:
        failed_labels = [c["check"] for c in qa_checks if not c.get("passed")]
        all_failed = failed_labels + rubric_failed_labels
        st.markdown("---")
        issues_str = f"{len(failed_labels)} gate(s) failed" if failed_labels else ""
        if rubric_failed_labels:
            issues_str += (" · " if issues_str else "") + f"{len(rubric_failed_labels)} rubric criterion below target"
        st.markdown(
            f'<p style="color:#94a3b8;font-size:.85rem">⚠️ {issues_str}. '
            f'Choose a regeneration strategy below:</p>',
            unsafe_allow_html=True,
        )
        rerun_count = st.session_state.get("qa_rerun_count", 0)
        if rerun_count < 2:
            strategies = _generate_rerun_strategies(qa_checks)
            selected_strategy = st.session_state.get("qa_rerun_strategy")
            selected_label = selected_strategy["label"] if selected_strategy else None

            cols = st.columns(len(strategies))
            for i, (col, strat) in enumerate(zip(cols, strategies)):
                is_selected = selected_label == strat["label"]
                border_color = "#6366f1" if is_selected else "#1e293b"
                bg_color = "rgba(99,102,241,.12)" if is_selected else "#0f1629"
                check_mark = " ✓" if is_selected else ""
                col.markdown(f"""
<div style="background:{bg_color};border:2px solid {border_color};border-radius:12px;
     padding:1rem;cursor:pointer;transition:all .2s;min-height:130px">
  <div style="font-size:1.5rem;margin-bottom:.4rem">{strat['icon']}</div>
  <div style="font-weight:700;color:#f1f5f9;font-size:.88rem;margin-bottom:.4rem">
    {strat['label']}{check_mark}
  </div>
  <div style="color:#94a3b8;font-size:.75rem;line-height:1.45">{strat['description']}</div>
</div>""", unsafe_allow_html=True)
                btn_label = "✓ Selected" if is_selected else "Select"
                btn_type = "primary" if is_selected else "secondary"
                if col.button(btn_label, key=f"qa_strat_{i}", type=btn_type):
                    st.session_state.qa_rerun_strategy = strat
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)
            if selected_strategy:
                _strat_label = selected_strategy['label']
                if st.button(
                    f"🔁 Regenerate with '{_strat_label}' (attempt {rerun_count + 1}/2)",
                    key="qa_rerun_btn",
                    type="primary",
                ):
                    on_rerun(all_failed, selected_strategy["guidance"])
            else:
                st.info("Select a strategy above, then click Regenerate.")
        else:
            st.warning("Maximum re-generate attempts reached. Review and export the current draft, or start a new article.")
    elif not needs_rerun:
        st.success("All critical gates passed and rubric targets met — article is ready for publication review.")


def render_metadata(meta: dict):
    st.markdown("### 🏷 SEO / AEO Metadata")
    st.markdown(f"""
<div class="meta-block">
TITLE TAG        : {meta.get('title_tag','')}
SEO SLUG         : /{meta.get('seo_slug','')}
META DESCRIPTION : {meta.get('meta_description','')}
WORD COUNT EST.  : ~{meta.get('word_count',0):,} words
RESEARCH MODEL   : {st.session_state.model_used}  (Gemini — search &amp; sources)
WRITING MODEL    : {st.session_state.get('claude_model_used', CLAUDE_MODEL)}  (Claude — article)
GENERATED AT     : {datetime.now().strftime('%Y-%m-%d %H:%M UTC')}
</div>""", unsafe_allow_html=True)


def render_export_buttons(art: dict):
    md = _article_to_markdown(art)
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("⬇ Download Markdown", md, "article.md", "text/markdown")
    with col2:
        st.download_button(
            "⬇ Download JSON",
            json.dumps(art, indent=2),
            "article.json",
            "application/json",
        )

    st.markdown("#### 📋 Copy Full Article Text")
    escaped = md.replace("`", "\\`").replace("$", "\\$")
    import streamlit.components.v1 as components
    components.html(f"""
<button onclick="navigator.clipboard.writeText(`{escaped}`).then(()=>{{
    this.textContent='✅ Copied!';
    setTimeout(()=>this.textContent='📋 Copy to Clipboard',2000);
}})"
style="background:#6366f1;color:#fff;border:none;border-radius:10px;padding:.6rem 1.4rem;
font-size:.9rem;font-weight:600;cursor:pointer;width:100%">
📋 Copy to Clipboard
</button>
""", height=55)


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
        lines.append(f"\n## {cmp.get('heading','Comparative Analysis')}\n")
        lines.append(cmp.get("content", ""))
    tco = art.get("tco_analysis", {})
    if tco:
        lines.append(f"\n## {tco.get('heading','TCO Analysis')}\n")
        lines.append(tco.get("content", ""))
    anti = art.get("anti_recommendation", {})
    if anti:
        lines.append(f"\n## {anti.get('heading','When NOT to Use')}\n")
        lines.append(anti.get("content", ""))
    if art.get("conclusion"):
        lines.append(f"\n## Conclusion\n{art['conclusion']}")
    meta = art.get("metadata", {})
    if meta:
        lines.append(f"\n---\n**SEO Slug:** `/{meta.get('seo_slug','')}`")
        lines.append(f"**Meta Description:** {meta.get('meta_description','')}")
    refs = art.get("references", [])
    if refs:
        lines.append("\n## References\n" + "\n".join(refs))
    return "\n".join(lines)

# ══════════════════════════════════════════════════════════════════
# 9 · SIDEBAR
# ══════════════════════════════════════════════════════════════════
def render_sidebar():
    st.sidebar.markdown("## ⚙️ Configuration")

    api_key = st.sidebar.text_input(
        "Gemini API Key  *(research)*",
        type="password",
        value=os.environ.get("GEMINI_API_KEY", ""),
        help="Used for Steps 1–4 (topic search, source gathering). Get one at aistudio.google.com",
    )
    if api_key:
        st.session_state["_api_key"] = api_key

    anthropic_key = st.sidebar.text_input(
        "Anthropic API Key  *(article writing)*",
        type="password",
        value=os.environ.get("ANTHROPIC_API_KEY", ""),
        help=f"Used for Step 5 article generation ({CLAUDE_MODEL}). Get one at console.anthropic.com",
    )
    if anthropic_key:
        st.session_state["_anthropic_key"] = anthropic_key

    if not ANTHROPIC_AVAILABLE:
        st.sidebar.warning("`anthropic` package not installed. Run `pip install anthropic` then restart.")
    elif not anthropic_key:
        st.sidebar.info("ℹ️ No Anthropic key — article will fall back to Gemini.")

    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Research:** `{st.session_state.model_used}`")
    st.sidebar.markdown(f"**Writing:** `{st.session_state.get('claude_model_used', CLAUDE_MODEL)}`")
    st.sidebar.markdown(f"**Step:** {st.session_state.step} / 5")

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Workflow Overview")
    for i, (_, label) in enumerate(STEPS, 1):
        done  = st.session_state.step > i
        curr  = st.session_state.step == i
        icon  = "✅" if done else ("🔵" if curr else "⬜")
        st.sidebar.markdown(f"{icon} **Step {i}** — {label}")

    st.sidebar.markdown("---")
    with st.sidebar:
        if st.button("🔄 Reset Workflow", key="reset"):
            for k in list(st.session_state.keys()):
                if k != "_api_key":
                    del st.session_state[k]
            _init()
            st.rerun()

    st.sidebar.markdown("---")
    st.sidebar.markdown("""
<small style="color:#475569">
<strong>Evidence Standards</strong><br>
✔ Independent + vendor claims separated<br>
✔ TCO over 3-year horizon<br>
✔ Anti-recommendation scenarios<br>
✔ Physical constraint analysis<br>
✔ 4-gate quality audit<br>
✔ SEO/AEO metadata
</small>
""", unsafe_allow_html=True)

    return api_key, anthropic_key

# ══════════════════════════════════════════════════════════════════
# 10 · STEP RENDERERS
# ══════════════════════════════════════════════════════════════════

def step_1_category(client):
    """Category selection — no API call."""
    st.markdown("## Step 1 · Select a Domain")
    st.markdown('<p style="color:#94a3b8">Choose the broad technical domain for your article.</p>',
                unsafe_allow_html=True)

    cols = st.columns(2)
    for i, cat in enumerate(CATEGORIES):
        icons = ["🤖", "🖥️", "🌐", "🦾"]
        with cols[i % 2]:
            st.markdown(f"""
<div class="card" style="border-left:3px solid #6366f1;cursor:pointer">
  <div style="font-size:1.6rem">{icons[i]}</div>
  <h4 style="margin:.4rem 0 .2rem">{cat}</h4>
</div>""", unsafe_allow_html=True)
            if st.button(f"Select →", key=f"cat_{i}"):
                st.session_state.category = cat
                st.session_state.step = 2
                with st.spinner(f"Searching 2025-2026 trends in {cat}…"):
                    st.session_state.topics = fetch_topics(client, cat)
                st.rerun()


def step_2_topics():
    """Display 5 trending topics for selection."""
    st.markdown(f"## Step 2 · Trending Topics in *{st.session_state.category}*")
    st.markdown('<p style="color:#94a3b8">Based on 2025–2026 data · Google Search grounded</p>',
                unsafe_allow_html=True)

    for i, t in enumerate(st.session_state.topics):
        st.markdown(f"""
<div class="card">
  <h4 style="margin:0 0 .4rem;color:#a5b4fc">{i+1}. {t['title']}</h4>
  <p style="color:#94a3b8;font-size:.85rem;margin:0 0 .3rem">{t['description']}</p>
  <p style="color:#6366f1;font-size:.78rem;margin:0">📈 {t.get('trend_signal','')}</p>
</div>""", unsafe_allow_html=True)
        if st.button(f"Select Topic {i+1}", key=f"topic_{i}"):
            st.session_state.topic = t
            st.session_state.step = 3
            with st.spinner("Generating SEO/AEO-optimized titles…"):
                st.session_state.titles = fetch_titles(
                    st.session_state._client, t
                )
            st.rerun()


def step_3_titles():
    """Display 5 SEO/AEO-optimized title angles."""
    st.markdown(f"## Step 3 · Title Optimization")
    st.markdown(
        f'<p style="color:#94a3b8">Topic: <strong style="color:#e2e8f0">{st.session_state.topic["title"]}</strong></p>',
        unsafe_allow_html=True,
    )

    angle_colors = {
        "benchmark":      "#6366f1",
        "cost-analysis":  "#f59e0b",
        "architecture":   "#10b981",
        "failure-case":   "#ef4444",
        "comparative":    "#8b5cf6",
    }

    for i, t in enumerate(st.session_state.titles):
        angle = t.get("angle", "")
        color = angle_colors.get(angle.lower(), "#64748b")
        st.markdown(f"""
<div class="card" style="border-left:3px solid {color}">
  <span style="background:rgba(99,102,241,.12);color:{color};border-radius:6px;
    padding:.15rem .5rem;font-size:.7rem;font-weight:700">{angle.upper()}</span>
  <h4 style="margin:.4rem 0 .2rem;color:#e2e8f0">{t['title']}</h4>
  <p style="color:#64748b;font-size:.78rem;margin:0 0 .2rem">
    🔑 <strong>Keyword:</strong> {t.get('primary_keyword','—')}
  </p>
  <p style="color:#94a3b8;font-size:.78rem;margin:0">{t.get('seo_rationale','')}</p>
</div>""", unsafe_allow_html=True)
        if st.button(f"Choose Title {i+1}", key=f"title_{i}"):
            st.session_state.title = t
            st.session_state.step = 4
            with st.spinner("Conducting deep research — searching 8 high-authority sources…"):
                srcs, ctx = deep_research(
                    st.session_state._client, t["title"]
                )
                st.session_state.sources = srcs
                st.session_state.notebooklm_context = ctx
            st.rerun()


def step_4_research():
    """Source curation with accept/decline checkboxes + NotebookLM panel."""
    title = st.session_state.title["title"]
    sources = st.session_state.sources

    st.markdown("## Step 4 · Source Curation & Research Audit")
    st.markdown(
        f'<p style="color:#94a3b8">Article: <em>{title}</em></p>',
        unsafe_allow_html=True,
    )

    # ── Per-source accept / decline ─────────────────────────────
    st.markdown("### 📚 Curate Your Sources")
    st.markdown(
        '<p style="color:#64748b;font-size:.84rem">'
        'Check each source you want included. Unchecked sources are excluded from '
        'the article knowledge base. All sources are accepted by default.</p>',
        unsafe_allow_html=True,
    )

    col_a, col_b = st.columns(2)
    for i, src in enumerate(sources):
        src_id  = src.get("id", i + 1)
        col     = col_a if i % 2 == 0 else col_b
        with col:
            # Acceptance checkbox — persists in session_state via key
            accepted = st.checkbox(
                f"**Accept** Source [{src_id}] &nbsp;·&nbsp; {src.get('tier','')}",
                value=st.session_state.get(f"src_accept_{src_id}", True),
                key=f"src_accept_{src_id}",
            )
            # Source card with visual accepted / declined overlay
            border = "#34d399" if accepted else "#ef4444"
            opacity = "1" if accepted else "0.42"
            status_badge = (
                '<span class="source-badge" '
                'style="background:rgba(52,211,153,.15);color:#34d399;'
                'border-color:rgba(52,211,153,.3)">✓ ACCEPTED</span>'
                if accepted else
                '<span class="source-badge" '
                'style="background:rgba(248,113,113,.1);color:#f87171;'
                'border-color:rgba(248,113,113,.3)">✗ DECLINED</span>'
            )
            verified_badge = (
                '<span class="source-badge" '
                'style="background:rgba(5,150,105,.15);color:#34d399;'
                'border-color:rgba(52,211,153,.3)">🔗 GROUNDED</span> '
                if src.get("grounded") else ""
            )
            st.markdown(f"""
<div class="source-card" style="border-left:3px solid {border};opacity:{opacity};
     transition:opacity .25s,border-color .25s">
  {status_badge}
  <span class="source-badge">SOURCE [{src_id}] · {src.get('tier','')}</span>
  {verified_badge}
  <span class="source-date">📅 {src.get('date','')}</span>
  <h4 style="margin:.4rem 0 .3rem;font-size:.93rem;color:#e2e8f0">{src.get('title','')}</h4>
  <p style="font-size:.76rem;color:#64748b;margin:0 0 .35rem">
    🏛 {src.get('publisher','')} &nbsp;·&nbsp;
    🔗 <a href="{src.get('url','#')}" target="_blank" style="color:#818cf8">
    {src.get('url','')[:55]}…</a>
  </p>
  <p style="font-size:.8rem;color:#94a3b8;margin:0 0 .3rem;line-height:1.6">
    {src.get('snippet','')}
  </p>
  <p style="font-size:.76rem;color:#a5b4fc;margin:0">
    📊 <strong>Key data:</strong> {src.get('key_data_point','—')}
  </p>
</div>
""", unsafe_allow_html=True)

    # ── Tally accepted ──────────────────────────────────────────
    accepted_sources = [
        src for i, src in enumerate(sources)
        if st.session_state.get(f"src_accept_{src.get('id', i+1)}", True)
    ]
    n_acc = len(accepted_sources)
    n_tot = len(sources)

    # Tally bar
    bar_w   = int(n_acc / n_tot * 100) if n_tot else 0
    bar_col = "#34d399" if n_acc >= 5 else ("#fbbf24" if n_acc >= 2 else "#f87171")
    st.markdown(f"""
<div style="background:#0f1629;border:1px solid #1e293b;border-radius:10px;
     padding:1rem 1.4rem;margin:1.2rem 0;display:flex;align-items:center;gap:1.2rem;flex-wrap:wrap">
  <div style="font-size:1.4rem;font-weight:800;color:{bar_col}">{n_acc}</div>
  <div>
    <div style="color:#e2e8f0;font-size:.88rem;font-weight:600">
      {n_acc} of {n_tot} sources accepted</div>
    <div style="background:#1e293b;border-radius:99px;height:6px;width:180px;
         margin-top:.35rem;overflow:hidden">
      <div style="height:100%;width:{bar_w}%;background:{bar_col};border-radius:99px"></div>
    </div>
  </div>
  {"<div style='color:#f87171;font-size:.82rem'>Accept at least 1 source to proceed.</div>" if n_acc == 0 else ""}
</div>
""", unsafe_allow_html=True)

    # ── NotebookLM synthesis ────────────────────────────────────
    st.markdown("""
<div class="notebooklm-panel">
  <h4>🧠 NotebookLM Context Synthesis</h4>
  <p style="font-size:.8rem;color:#64748b;margin:0 0 .5rem">
    Cross-referenced knowledge base built from all gathered sources —
    injected as context for article generation.
  </p>
</div>""", unsafe_allow_html=True)
    with st.expander("View full context synthesis →", expanded=False):
        st.markdown(
            f'<div style="background:#020617;border-radius:8px;padding:1rem;'
            f'font-size:.82rem;color:#94a3b8;line-height:1.7;">'
            f'{st.session_state.notebooklm_context.replace(chr(10),"<br>")}</div>',
            unsafe_allow_html=True,
        )

    # ── Competitor Collection Button ─────────────────────────────
    collect_button = st.button(
        "📥 Collect Competitor Articles",
        disabled=st.session_state.get("collection_in_progress", False),
    )
    if collect_button and not st.session_state.get("collection_in_progress", False):
        st.session_state.collection_in_progress = True
        try:
            with st.spinner("🔍 AI collecting articles..."):
                result = collect_competitor_articles()
            if result is not None:
                companies, articles = result
                st.success(f"Competitor data collected! {companies} companies, {articles} articles")
            else:
                st.info("Don't worry - you can try again later or skip for now")
        except Exception as e:
            st.warning(f"Collection failed: {str(e)}")
            st.info("Don't worry - you can try again later or skip for now")
        finally:
            st.session_state.collection_in_progress = False

    # ── Generate button ─────────────────────────────────────────
    st.markdown("---")
    anthropic_client = st.session_state.get("_anthropic_client")
    writer_label = (
        f"Claude ({st.session_state.get('claude_model_used', CLAUDE_MODEL)})"
        if anthropic_client else
        f"Gemini ({MODEL_REASONING}) — add Anthropic key in sidebar for Claude"
    )
    st.markdown(
        f'<p style="color:#64748b;font-size:.83rem">✍️ Writer: <strong style="color:#a5b4fc">{writer_label}</strong></p>',
        unsafe_allow_html=True,
    )

    btn_disabled = n_acc == 0
    if not btn_disabled:
        if st.button(f"🚀 Generate Article with {n_acc} Accepted Source{'s' if n_acc != 1 else ''}"):
            st.session_state.accepted_sources = accepted_sources
            st.session_state.sources_confirmed = True
            st.session_state.step = 5
            st.session_state.qa_rerun_count = 0
            competitors_data = load_competitors_data()
            competitive_ctx = build_competitive_context(
                st.session_state.get("category", ""), competitors_data
            )
            st.session_state.competitive_context = competitive_ctx
            _do_generate(title, accepted_sources, qa_feedback="", competitive_context=competitive_ctx)
            st.rerun()
    else:
        st.button("🚀 Generate Article", disabled=True)


_CREDIT_ERRORS = (
    "credit balance is too low",
    "insufficient_quota",
    "billing",
    "payment",
    "upgrade or purchase",
    "402",
)

def _is_credit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(k in msg for k in _CREDIT_ERRORS)


def _do_generate(title: str, accepted_sources: list[dict], qa_feedback: str = "", competitive_context: str = ""):
    """
    Article generation with smart fallback:
      1. Claude (if Anthropic key present)           → best writing quality
      2. Gemini 2.5 Pro (auto-fallback on any error) → uses same NotebookLM context
    Hallucination prevention is maintained in both paths via:
      - Strict citation rules [N] in prompt
      - NotebookLM context injected as grounding
      - Accepted-source whitelist enforced
    """
    anthropic_client = st.session_state.get("_anthropic_client")
    art = None

    # ── Attempt 1: Claude ────────────────────────────────────────
    if anthropic_client:
        spinner_msg = f"✍️ Claude ({st.session_state.get('claude_model_used', CLAUDE_MODEL)}) is writing…"
        with st.spinner(spinner_msg):
            try:
                art = generate_article_claude(
                    anthropic_client,
                    title,
                    accepted_sources,
                    st.session_state.sources,
                    st.session_state.notebooklm_context,
                    qa_feedback=qa_feedback,
                    competitive_context=competitive_context,
                )
                st.session_state.actual_writer   = "claude"
                st.session_state.fallback_reason = ""
            except Exception as exc:
                if _is_credit_error(exc):
                    # Credit depleted — fall through to Gemini
                    st.session_state.fallback_reason = (
                        f"Anthropic credit balance too low — article written by Gemini ({MODEL_REASONING}) instead. "
                        f"Add credits at console.anthropic.com/billing to use Claude next time."
                    )
                else:
                    # Non-billing Claude error — still try Gemini as safety net
                    st.session_state.fallback_reason = (
                        f"Claude error ({str(exc)[:120]}) — automatically fell back to Gemini."
                    )

    # ── Attempt 2: Gemini (primary when no Anthropic key, or fallback) ──
    if art is None:
        writer_label = (
            "Gemini (fallback)" if st.session_state.fallback_reason
            else f"Gemini ({MODEL_REASONING})"
        )
        with st.spinner(f"✍️ Writing with {writer_label}…"):
            try:
                art = generate_article(
                    st.session_state._client,
                    title,
                    accepted_sources,
                    st.session_state.notebooklm_context,
                    competitive_context=competitive_context,
                )
                st.session_state.actual_writer = (
                    "gemini_fallback" if st.session_state.fallback_reason else "gemini"
                )
            except Exception as exc2:
                st.session_state.gen_error = str(exc2)
                return

    # ── Commit results ───────────────────────────────────────────
    st.session_state.article   = art
    st.session_state.metadata  = art.get("metadata", {})
    st.session_state.audit     = art.get("quality_audit", [])
    st.session_state.qa_checks = run_comprehensive_qa(art)
    st.session_state.gen_error = ""
    with st.spinner("📊 Scoring article on rubric criteria…"):
        st.session_state.rubric_scores = score_article_rubric(
            st.session_state._client, art
        )

    # ── Download 1 hero image server-side (avoids browser CSP blocks) ─
    hero_prompt = (
        f"cinematic wide-angle technical illustration for: {title}, "
        "dark background, indigo and cyan glow, professional tech photography style, "
        "high detail, 8k, no text"
    )
    img_url = pollinations_url(hero_prompt, w=1400, h=500, seed=_seed(title))
    try:
        with st.spinner("🖼 Generating hero image…"):
            r = requests.get(img_url, timeout=35)
        st.session_state.hero_image_bytes = r.content if r.status_code == 200 else None
    except Exception:
        st.session_state.hero_image_bytes = None


def step_5_article():
    """Render generated article + quality audit with re-generate support."""
    title = st.session_state.title["title"]

    # ── Generation error ─────────────────────────────────────────
    if st.session_state.gen_error:
        st.error(f"Generation error: {st.session_state.gen_error}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("← Back to Sources"):
                st.session_state.step = 4
                st.rerun()
        with col2:
            if st.button("🔁 Retry Generation"):
                _do_generate(
                    title, st.session_state.accepted_sources,
                    competitive_context=st.session_state.get("competitive_context", ""),
                )
                st.rerun()
        return

    # ── Article not yet generated (shouldn't happen, safety net) ─
    art = st.session_state.article
    if not art:
        st.info("Generating article…")
        _do_generate(
            title, st.session_state.accepted_sources,
            competitive_context=st.session_state.get("competitive_context", ""),
        )
        st.rerun()
        return

    # ── Hero banner (server-side cached bytes from _do_generate) ─
    hero_bytes = st.session_state.get("hero_image_bytes")
    if hero_bytes:
        st.image(hero_bytes, use_container_width=True)

    # ── Fallback banner ───────────────────────────────────────────
    fallback_reason = st.session_state.get("fallback_reason", "")
    if fallback_reason:
        st.warning(f"⚠️ {fallback_reason}")

    # ── Model badges ──────────────────────────────────────────────
    research_m    = st.session_state.get("model_used", MODEL_REASONING)
    actual_writer = st.session_state.get("actual_writer", "")
    if actual_writer == "claude":
        writing_m     = st.session_state.get("claude_model_used", CLAUDE_MODEL)
        writer_color  = "rgba(168,85,247,.15)"
        writer_border = "rgba(168,85,247,.3)"
        writer_text   = "#c084fc"
        writer_icon   = "✍️"
    elif actual_writer == "gemini_fallback":
        writing_m     = f"{MODEL_REASONING} (fallback)"
        writer_color  = "rgba(245,158,11,.1)"
        writer_border = "rgba(245,158,11,.3)"
        writer_text   = "#fbbf24"
        writer_icon   = "⚡"
    else:
        writing_m     = MODEL_REASONING
        writer_color  = "rgba(99,102,241,.15)"
        writer_border = "rgba(99,102,241,.3)"
        writer_text   = "#818cf8"
        writer_icon   = "✍️"

    st.markdown(f"""
<div style="display:flex;gap:.6rem;margin:.6rem 0 1.2rem;flex-wrap:wrap">
  <span style="background:rgba(99,102,241,.15);color:#818cf8;border:1px solid rgba(99,102,241,.3);
    border-radius:6px;padding:.2rem .7rem;font-size:.75rem;font-weight:600">
    🔍 Research: {research_m}
  </span>
  <span style="background:{writer_color};color:{writer_text};border:1px solid {writer_border};
    border-radius:6px;padding:.2rem .7rem;font-size:.75rem;font-weight:600">
    {writer_icon} Writing: {writing_m}
  </span>
  <span style="background:rgba(52,211,153,.1);color:#34d399;border:1px solid rgba(52,211,153,.25);
    border-radius:6px;padding:.2rem .7rem;font-size:.75rem;font-weight:600">
    📚 Sources: {len(st.session_state.accepted_sources)} accepted
  </span>
</div>
""", unsafe_allow_html=True)

    st.markdown(f"## {art.get('article_title', title)}")

    # ── Tabs ──────────────────────────────────────────────────────
    tab_article, tab_audit, tab_meta, tab_export, tab_competitors = st.tabs(
        ["📄 Article", "🔍 Quality Audit", "🏷 Metadata", "⬇ Export", "📊 Competitors"]
    )

    with tab_article:
        render_article(art)

    with tab_audit:
        qa_checks    = st.session_state.qa_checks
        model_audit  = st.session_state.audit

        def handle_rerun(failed_labels: list[str], strategy_guidance: str = ""):
            st.session_state.qa_rerun_count += 1
            st.session_state.qa_rerun_strategy = None   # reset selection for next round
            feedback = strategy_guidance or (
                "Failed checks to fix:\n" + "\n".join(f"• {l}" for l in failed_labels)
            )
            _do_generate(
                title, st.session_state.accepted_sources, qa_feedback=feedback,
                competitive_context=st.session_state.get("competitive_context", ""),
            )
            st.rerun()

        render_quality_audit(
            qa_checks,
            model_audit=model_audit,
            on_rerun=handle_rerun,
            rubric_scores=st.session_state.get("rubric_scores"),
        )

    with tab_meta:
        render_metadata(st.session_state.metadata or {})

    with tab_export:
        st.markdown("### Export Article")
        render_export_buttons(art)

    with tab_competitors:
        competitors_data = load_competitors_data()
        category = st.session_state.get("category", "")
        if competitors_data:
            matched = load_competitors_for_category(category, competitors_data)
            if matched:
                render_competitors_dashboard(category, matched)
            else:
                st.warning(f"No competitors for '{category}'")
                avail = [k for k in competitors_data if k != "schema_version"]
                if avail:
                    sel = st.selectbox("Select category to view:", avail)
                    render_competitors_dashboard(sel, competitors_data[sel])
        else:
            st.info("No competitor data yet. Use Step 4 to collect.")

    # ── Bottom actions ────────────────────────────────────────────
    st.markdown("---")
    col_back, col_new, _ = st.columns([1, 1, 2])
    with col_back:
        if st.button("← Back to Sources"):
            st.session_state.step = 4
            st.rerun()
    with col_new:
        if st.button("🔄 New Article"):
            for k in list(st.session_state.keys()):
                if k not in ("_api_key", "_client", "_anthropic_client"):
                    del st.session_state[k]
            _init()
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# 11 · MAIN ROUTER
# ══════════════════════════════════════════════════════════════════
def main():
    render_header()

    # Sidebar — get API keys
    api_key, anthropic_key = render_sidebar()

    if not api_key:
        st.warning(
            "👈 Please enter your **Gemini API Key** in the sidebar to begin.\n\n"
            "Get one free at [aistudio.google.com](https://aistudio.google.com)."
        )
        st.stop()

    # Build & cache clients
    client = get_client(api_key)
    st.session_state._client = client

    if anthropic_key and ANTHROPIC_AVAILABLE:
        st.session_state._anthropic_client = get_anthropic_client(anthropic_key)
    else:
        st.session_state._anthropic_client = None

    # Step progress bar
    render_steps(st.session_state.step)

    # Route to correct step
    s = st.session_state.step
    if s == 1:
        step_1_category(client)
    elif s == 2:
        step_2_topics()
    elif s == 3:
        step_3_titles()
    elif s == 4:
        step_4_research()
    elif s == 5:
        step_5_article()
    else:
        st.session_state.step = 1
        st.rerun()


if __name__ == "__main__":
    main()
