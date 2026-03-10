# Blog Workflow - Competitive Analysis Feature Implementation Plan

**Last Updated**: 2026-03-09
**Status**: Planning (No Implementation Yet)
**Version**: 2.18 (Import & UI Pass — urlparse import clarified, UI wireframe corrected, stale pandas/mock-data references removed)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Current System Context](#current-system-context)
3. [Revised Architecture](#revised-architecture)
4. [System Architecture](#system-architecture)
5. [Data Structure](#data-structure)
6. [UI Design](#ui-design)
7. [Implementation Checklist](#implementation-checklist)
8. [Article Collection Guidelines](#article-collection-guidelines)
9. [Competitive Context Injection](#competitive-context-injection-step-5-article-generation-enhancement)
10. [Error Handling](#error-handling)
11. [Performance Optimization](#performance-optimization)
12. [Risk Management](#risk-management)
13. [Timeline & Resources](#timeline--resources)

---

## Project Overview

### Objective
Add competitive awareness feature showing competitor blogs and articles alongside generated articles.

### Key Features
1. **Data Collection Button** (Step 4) - Collect competitor articles once
2. **Analysis Dashboard** (Step 5) - Simple display of competitors and their articles

### Approach
- **Simplified**: Display only (no scoring/comparison)
- **Data-driven**: One-time collection in Step 4, reuse in Step 5
- **Fast**: Minimal implementation focused on core features

---

## Current System Context

### Existing Components

**techaudit_agent.py (Streamlit App)**
- Step 1: Category selection
- Step 2: Topic generation
- Step 3: Title generation
- Step 4: Research & source gathering ← **NEW: Add [📥 Collect Competitor Articles] button here**
- Step 5: Article generation ← **NEW: Add [📊 Competitors] tab here (tab style, not button)**

**Key Technologies**
- Python, Streamlit, Google Gemini (new SDK: `from google import genai`)
- JSON for data storage
- ~~Pandas for Excel~~ → Excel Export removed (outside Phase 1.0 scope)

> ⚠️ **Category Name Caution**: Must match the actual `CATEGORIES` constant (techaudit_agent.py:235) exactly.
> ```
> "AI Performance Engineering"
> "GPU Computing & Hardware"        ← NOT "GPU Computing"
> "High-Performance Networking"     ← 4th category that was missing from the plan
> "Robotics & Edge Computing"
> ```

---

## Revised Architecture

### New User Flow

```
STEP 4: RESEARCH PHASE (Existing)
┌──────────────────────────────────────────┐
│ Deep Research Complete                   │
├──────────────────────────────────────────┤
│ [Gather Research Sources] (existing)     │
│ [📥 Collect Competitor Articles] (NEW)   │
└──────────────────────────────────────────┘
              ↓ (Button Click → Collect once only)
        Gemini + Google Search Grounding
              ↓
        ✅ competitors_data collected
        (session_state 1st layer + file 2nd layer, Cloud compatible)

═════════════════════════════════════════════

STEP 5: ARTICLE GENERATION (Existing)
┌──────────────────────────────────────────┐
│ Article Generation Complete              │
├──────────────────────────────────────────┤
│ [📄 Article] [🔍 Quality Audit] [🏷 Metadata] [⬇ Export] [📊 Competitors] ← NEW tab added
├──────────────────────────────────────────┤
│ (Auto-load when tab clicked — no button) │
│                                          │
│  When 📊 Competitors tab selected:       │
│  └─ Call load_competitors_data()         │
│  └─ Render render_competitors_dashboard()│
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ COMPETITIVE ANALYSIS DASHBOARD           │
│ - Competitors List (table)               │
│ - Their Articles (accordion, CLOSED)     │
└──────────────────────────────────────────┘
```

### Key Difference from Original Plan
- ❌ No competitor scoring (simple display only)
- ❌ No improvement recommendations
- ✅ One-time data collection (reusable)
- ✅ Simple, fast implementation

---

## System Architecture

### Technology Stack

```
Backend (Python/Streamlit):
├─ streamlit          (UI rendering)
├─ json               (Data storage)
└─ urllib.parse       (URL format validation — forbidden to use requests)

Data Storage:
├─ st.session_state   (1st: Cloud compatible, persistent in session)
├─ competitors_data.json    (2nd: local file backup)
└─ /data/default_competitors.json (3rd: default value fallback)

Language: All English
```

### File Structure & Configuration

**Secrets Configuration**

> ⑪ `[gemini]` section not needed: new SDK uses only `os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")`.
> Gemini model names are managed by code constants (`MODEL_REASONING`, `MODEL_FALLBACK`).

> ⚠️ **secrets.toml path section not used**: actual code uses absolute paths based on `BASE_DIR` directly
> (`COMPETITORS_DATA_PATH`, `DEFAULT_COMPETITORS_PATH` constants). st.secrets path reading not needed.
> → `.streamlit/secrets.toml` should be used only for API keys and sensitive values.

```
.streamlit/secrets.toml (local) or Streamlit Cloud:

# [paths] section not needed — code uses BASE_DIR absolute path constants directly
# [defaults] section not needed — same reason

# No sections needed (API keys managed via environment variables)
# GOOGLE_GENERATIVE_AI_API_KEY is read via os.getenv() (secrets.toml not needed)
```

**Path Configuration** (Absolute Paths)

```python
# Use absolute paths for cross-platform compatibility
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COMPETITORS_DATA_PATH = os.path.join(BASE_DIR, "data", "competitors_data.json")
DEFAULT_COMPETITORS_PATH = os.path.join(BASE_DIR, "data", "default_competitors.json")
COMPETITORS_SS_KEY = "competitors_data_cache"
```

**Gemini API Configuration**

> ⚠️ Actual code uses new SDK (`from google import genai`). Mixing with old SDK (`google.generativeai`) is prohibited.

```python
# New SDK (same pattern as actual techaudit_agent.py)
from google import genai
from google.genai import types

# ④ get_competitor_client() wrapper not needed — call app's get_client(api_key) directly
# get_client() is cached by @st.cache_resource (techaudit_agent.py:306)
# Usage pattern:
#   api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
#   if not api_key:
#       st.warning("⚠️ GOOGLE_GENERATIVE_AI_API_KEY not set.")
#       return None  # ← Unified to None (False returns True in is not None check → TypeError)
#   client = get_client(api_key)

# ✅ _competitor_search_cfg() not needed — verification complete
# _call_search(client, prompt) signature check result: config built-in (techaudit_agent.py:388)
# → _search_cfg() is called internally, so no need to pass config externally
# → fetch_articles_for_competitor() only needs to call _call_search(client, prompt)
```

**File Structure**

```
blog_workflow/
├── techaudit_agent.py              (MODIFIED)
│   ├─ step_4_research()
│   │  ├─ + collect_competitor_articles() (NEW — called from Step 4 button)
│   │
│   ├─ step_5_article()
│   │  ├─ + render_competitors_dashboard() (NEW — called inside 📊 Competitors tab, not button)
│   │
│   ├─ + save_competitors_data()         (NEW func — define in Phase 0 first)
│   ├─ + load_competitors_data()         (NEW func — define in Phase 0 first)
│   ├─ + migrate_competitors_schema()    (NEW func)
│   ├─ + validate_competitors_schema()   (NEW func)
│   ├─ + _validate_competitor_config()   (NEW func — ⑤ replace assert)
│   ├─ + validate_url_format()           (NEW func — urlparse only, no requests)
│   ├─ + dedup_articles()                (NEW func)
│   ├─ + load_competitors_for_category() (NEW func)
│   ├─ + build_competitive_context()     (NEW func — ⑧ context injection)
│   ├─ + _do_generate() signature modification   (② add competitive_context: str = "")
│   ├─ + generate_article_claude() signature modification (add competitive_context: str = "" + prompt injection)
│   └─ + generate_article() signature modification        (add competitive_context: str = "" + prompt injection)
│
├── .streamlit/
│   └─ secrets.toml                 (NEW - Config file)
│
└── data/
    ├─ competitors_data.json        (NEW - User-collected)
    └─ default_competitors.json     (NEW - Fallback)
```


---

## Data Structure

### competitors_data.json (Category-Based)

> ⚠️ Top-level keys must match `CATEGORIES` constant exactly:
> `"AI Performance Engineering"` / `"GPU Computing & Hardware"` / `"High-Performance Networking"` / `"Robotics & Edge Computing"`

```json
{
  "schema_version": "1.0",

  "GPU Computing & Hardware": {
    "metadata": {
      "category": "GPU Computing & Hardware",
      "generated_date": "2026-03-09",
      "collected_timestamp": "2026-03-09T10:30:00Z",
      "source": "ai_deep_research"
    },
    "competitors": {
      "nextplatform": {
        "name": "The Next Platform",
        "blog_url": "https://www.nextplatform.com/",
        "tier": 1,
        "editable": false,
        "articles": [
          {
            "title": "Blackwell Architecture Deep Dive",
            "url": "https://www.nextplatform.com/blackwell-arch",
            "date": "2025-02-10",
            "relevance": "GPU architecture"
          }
        ]
      },
      "servethehome": { "name": "ServeTheHome (STH)", "blog_url": "https://www.servethehome.com/", "tier": 1, "editable": false, "articles": [ ... ] },
      "semianalysis": { "name": "SemiAnalysis",       "blog_url": "https://www.semianalysis.com/",  "tier": 1, "editable": false, "articles": [ ... ] },
      "intel_dev":    { "name": "Intel Developer Zone","blog_url": "https://www.intel.com/...",      "tier": 1, "editable": false, "articles": [ ... ] },
      "amd_gpuopen":  { "name": "AMD GPUOpen",         "blog_url": "https://gpuopen.com/",           "tier": 2, "editable": false, "articles": [ ... ] }
    }
  },

  "AI Performance Engineering": {
    "metadata": { "category": "AI Performance Engineering", "generated_date": "2026-03-09", ... },
    "competitors": {
      "nvidia_tech":  { "name": "NVIDIA Technical Blog", "tier": 1, "articles": [ ... ] },
      "anyscale":     { "name": "Anyscale Blog",          "tier": 1, "articles": [ ... ] },
      "together_ai":  { "name": "Together AI Blog",       "tier": 1, "articles": [ ... ] },
      "huggingface":  { "name": "Hugging Face Blog",      "tier": 1, "articles": [ ... ] },
      "mosaicml":     { "name": "MosaicML (Databricks)",  "tier": 2, "articles": [ ... ] },
      "alphasignal":  { "name": "AlphaSignal",            "tier": 2, "articles": [ ... ] }
    }
  },

  "High-Performance Networking": {
    "metadata": { "category": "High-Performance Networking", ... },
    "competitors": {
      "cloudflare":       { "name": "Cloudflare Blog",       "tier": 1, "articles": [ ... ] },
      "meta_engineering": { "name": "Meta Engineering Blog", "tier": 1, "articles": [ ... ] },
      "cisco_tech":       { "name": "Cisco Tech Blog",       "tier": 1, "articles": [ ... ] },
      "kentik":           { "name": "Kentik Blog",           "tier": 2, "articles": [ ... ] },
      "packet_pushers":   { "name": "Packet Pushers",        "tier": 2, "articles": [ ... ] }
    }
  },

  "Robotics & Edge Computing": {
    "metadata": { "category": "Robotics & Edge Computing", ... },
    "competitors": {
      "ieee_spectrum":   { "name": "IEEE Spectrum Robotics",  "tier": 1, "articles": [ ... ] },
      "boston_dynamics": { "name": "Boston Dynamics Blog",    "tier": 1, "articles": [ ... ] },
      "nvidia_robotics": { "name": "NVIDIA Robotics Blog",    "tier": 1, "articles": [ ... ] },
      "arm_newsroom":    { "name": "Arm Newsroom (Technical)","tier": 2, "articles": [ ... ] },
      "standard_bots":   { "name": "Standard Bots Blog",     "tier": 2, "articles": [ ... ] },
      "dell_edge":       { "name": "Dell Technologies Blog",  "tier": 2, "articles": [ ... ] }
    }
  }
}
```
> ⚠️ The above keys must match `COMPETITORS_BY_CATEGORY` constant and `default_competitors.json` exactly.

**Key Features**:
- ✅ schema_version: "1.0" (backward compatibility)
- ✅ Category-based structure (flexible)
- ✅ editable: false for Phase 1 (locked)
- ✅ source field (tracks how data was collected)
- ✅ relevance field (why article matches)
- ✅ Each category has own metadata & collection timestamp

---

## UI Design

### Step 4: Data Collection Interface

```
Deep Research Complete

[Gather Research Sources] (Existing button)
[📥 Collect Competitor Articles] (NEW button - distinct from Step 5)

─ After clicking "Collect Competitor Articles" ─

⏳ 🔍 AI collecting articles...   (st.spinner)

✅ Competitor data collected! 5 companies, 12 articles   (st.success — single line)

OR

ℹ️ Don't worry - you can try again later or skip for now   (st.info — result is None)

OR

⚠️ Collection failed: {error message}   (st.warning — exception)
```

### Step 5: Dashboard Layout

(Rendered inside 📊 Competitors tab — no separate button)

```
[📄 Article] [🔍 Quality Audit] [🏷 Metadata] [⬇ Export] [📊 Competitors]  ← Dashboard shown when tab selected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 COMPETITIVE ANALYSIS
Category: GPU Computing & Hardware

1️⃣ COMPETITORS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
┌──────────────────────┬──────┬───────┐
│ Company              │ Tier │ Blog  │
├──────────────────────┼──────┼───────┤
│ The Next Platform    │  1   │[Link] │
│ ServeTheHome (STH)   │  1   │[Link] │
│ SemiAnalysis         │  1   │[Link] │
│ Intel Developer Zone │  1   │[Link] │
│ AMD GPUOpen          │  2   │[Link] │
└──────────────────────┴──────┴───────┘

2️⃣ COMPETITOR ARTICLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

▼ The Next Platform (2 articles)
  ├─ 📄 Blackwell Architecture Deep Dive
  │   URL: https://www.nextplatform.com/...
  │   Published: 2025-02-10
  │   Relevance: GPU architecture
  │
  └─ 📄 HPC Accelerator Benchmark 2025
      URL: https://www.nextplatform.com/...
      Published: 2025-01-20

▼ ServeTheHome (STH) (2 articles)
  ├─ 📄 NVIDIA H200 vs H100 Server Review
  │   Published: 2025-02-05
  └─ 📄 AMD MI300X Datacenter Analysis
      Published: 2025-01-15

▼ SemiAnalysis (1 article)
  └─ 📄 GPU Supply Chain 2025 Outlook
      Published: 2025-02-01

▼ Intel Developer Zone (0 articles)
▼ AMD GPUOpen (0 articles)
```

### UI Element Distinction

```
STEP 4: [📥 Collect Competitor Articles] (Button)
  Purpose: Collect data once
  Action: Gemini + Google Search → JSON saved
  Output: competitors_data.json + session_state
  Icon: 📥 (download/import)
  Location: Right after NotebookLM expander, before Generate Article button

STEP 5: [📊 Competitors] (Tab — not button)
  Purpose: Display collected data
  Action: load_competitors_data() called automatically when tab clicked
  Output: Dashboard on screen (no additional click needed)
  Location: Added at end of existing tab list
  ⚠️ Button approach forbidden — integrate as tab style
```

---

## Implementation Checklist

### Phase 0: Competitor Data Collection (Step 4 button) - 60 minutes

**Strategy**: Method A - Gemini AI + Google Search Grounding (new SDK pattern)

**Imports & Setup**:
```python
from __future__ import annotations
import json
import os
from datetime import datetime   # ← Import class directly, not module (enables datetime.now())
# time not needed — exponential backoff uses _call() internal logic
from typing import Optional
from urllib.parse import urlparse   # remove requests — replace with urlparse
from google import genai            # new SDK (old SDK import google.generativeai forbidden)
from google.genai import types      # new SDK
import streamlit as st
# Reuse app internal helpers: get_client(), _call_search(), _extract_text(), _parse_json()
```

**Python Version**: Python 3.10+ recommended.

```
[ ] ⚠️ Implementation order caution: define validate_competitors_schema() first
    > collect_competitor_articles() calls validate_competitors_schema() internally
    > This function appears in Phase 1 checklist but must be written first in Phase 0.
    > → Phase 1 checklist item validate_competitors_schema() is pre-implemented in Phase 0.

[ ] Add 3 session keys to _init() (techaudit_agent.py:270 defaults dictionary)
    > ⚠️ Skipping this causes KeyError in load_competitors_data() and Step 4 button
    [ ] "competitors_data_cache": None    # Key corresponding to COMPETITORS_SS_KEY
    [ ] "collection_in_progress": False   # Used to disable Step 4 button
    [ ] "competitive_context":    ""      # Result of build_competitive_context() — reused on re-run/QA retry

    ```python
    # Add to _init() defaults dictionary (after existing "rubric_scores" item)
    "competitors_data_cache":  None,   # Used by load/save_competitors_data()
    "collection_in_progress":  False,  # Prevent duplicate button clicks
    "competitive_context":     "",     # Preserve build_competitive_context() result — reuse on re-run/QA retry
    ```

[ ] Define COMPETITORS_BY_CATEGORY constant (NEW — add to constants section in techaudit_agent.py)
    > This dictionary is a code constant referencing the same competitor list as default_competitors.json.
    > It determines which competitors collect_competitor_articles() runs AI searches for.
    > **Location**: Right after RUBRIC_CRITERIA constant, before _init() function (after techaudit_agent.py:266)

    ```python
    # Located after RUBRIC_CRITERIA (after techaudit_agent.py:266)
    COMPETITORS_BY_CATEGORY: dict[str, dict[str, dict]] = {
        # ── AI model acceleration · inference efficiency · MLOps ──────────────────────────
        "AI Performance Engineering": {
            "nvidia_tech":  {"name": "NVIDIA Technical Blog", "blog_url": "https://developer.nvidia.com/blog/",       "tier": 1},
            "anyscale":     {"name": "Anyscale Blog",          "blog_url": "https://www.anyscale.com/blog",            "tier": 1},
            "together_ai":  {"name": "Together AI Blog",       "blog_url": "https://www.together.ai/blog",             "tier": 1},
            "huggingface":  {"name": "Hugging Face Blog",      "blog_url": "https://huggingface.co/blog",              "tier": 1},
            "mosaicml":     {"name": "MosaicML (Databricks)",  "blog_url": "https://www.databricks.com/blog",          "tier": 2},
            "alphasignal":  {"name": "AlphaSignal",            "blog_url": "https://alphasignal.ai/",                  "tier": 2},
        },
        # ── Hardware architecture · chipsets · accelerators ────────────────────────────
        "GPU Computing & Hardware": {
            "nextplatform": {"name": "The Next Platform",  "blog_url": "https://www.nextplatform.com/",        "tier": 1},
            "servethehome": {"name": "ServeTheHome (STH)", "blog_url": "https://www.servethehome.com/",        "tier": 1},
            "semianalysis": {"name": "SemiAnalysis",       "blog_url": "https://www.semianalysis.com/",        "tier": 1},
            "intel_dev":    {"name": "Intel Developer Zone","blog_url": "https://www.intel.com/content/www/us/en/developer/articles/technical/",  "tier": 1},
            "amd_gpuopen":  {"name": "AMD GPUOpen",        "blog_url": "https://gpuopen.com/",                 "tier": 2},
        },
        # ── Low-latency transmission · AI cluster networking · SDN ──────────────────────
        "High-Performance Networking": {
            "cloudflare":      {"name": "Cloudflare Blog",          "blog_url": "https://blog.cloudflare.com/",        "tier": 1},
            "meta_engineering":{"name": "Meta Engineering Blog",    "blog_url": "https://engineering.fb.com/",         "tier": 1},
            "cisco_tech":      {"name": "Cisco Tech Blog",          "blog_url": "https://blogs.cisco.com/",            "tier": 1},
            "kentik":          {"name": "Kentik Blog",              "blog_url": "https://www.kentik.com/blog/",        "tier": 2},
            "packet_pushers":  {"name": "Packet Pushers",           "blog_url": "https://packetpushers.net/",          "tier": 2},
        },
        # ── Physical AI · edge inference · collaborative robots ──────────────────────────
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
        """
        ⑤ Separated into function instead of module-level assert — prevents AssertionError on import.
        Called once on first entry to _init() or collect_competitor_articles().
        """
        missing = set(CATEGORIES) - set(COMPETITORS_BY_CATEGORY.keys())
        extra   = set(COMPETITORS_BY_CATEGORY.keys()) - set(CATEGORIES)
        if missing or extra:
            raise ValueError(
                f"COMPETITORS_BY_CATEGORY key mismatch — "
                f"missing: {missing}, extra: {extra}"
            )
    ```

    > ⑤ `_validate_competitor_config()` call point:
    > Last line of `_init()` function or on first entry to `collect_competitor_articles()`.
    > Module-level `assert` causes AssertionError on import — forbidden.

[ ] Create data/default_competitors.json (NEW)
    > ⚠️ **Dual maintenance caution**: Competitor list exists in both COMPETITORS_BY_CATEGORY constant and default_competitors.json.
    > Must update **both** when adding/changing competitors.
    > Phase 2 will review unifying to single source (JSON or constant).
    [ ] Pre-populate with 5 competitors per category (all 4 categories)
    [ ] Add 2-3 sample articles per competitor
    [ ] Match schema version 1.0
    [ ] Include all 4 categories: AI Performance Engineering, GPU Computing & Hardware,
        High-Performance Networking, Robotics & Edge Computing
    [ ] Use as fallback for testing

    Complete JSON structure with sample data:
    ```json
    {
      "schema_version": "1.0",

      "GPU Computing & Hardware": {
        "metadata": {
          "category": "GPU Computing & Hardware",
          "generated_date": "2026-03-09",
          "collected_timestamp": "2026-03-09T10:30:00Z",
          "source": "ai_deep_research"
        },
        "competitors": {
          "nextplatform": {
            "name": "The Next Platform",
            "blog_url": "https://www.nextplatform.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Blackwell Architecture Deep Dive", "url": "https://www.nextplatform.com/blackwell-arch", "date": "2025-02-10", "relevance": "GPU architecture"},
              {"title": "HPC Accelerator Benchmark 2025", "url": "https://www.nextplatform.com/hpc-benchmark-2025", "date": "2025-01-20", "relevance": "Performance benchmarks"}
            ]
          },
          "servethehome": {
            "name": "ServeTheHome (STH)",
            "blog_url": "https://www.servethehome.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "NVIDIA H200 vs H100 Server Review", "url": "https://www.servethehome.com/h200-review", "date": "2025-02-05", "relevance": "GPU hardware review"},
              {"title": "AMD MI300X Datacenter Analysis", "url": "https://www.servethehome.com/mi300x-analysis", "date": "2025-01-15", "relevance": "Accelerator comparison"}
            ]
          },
          "semianalysis": {
            "name": "SemiAnalysis",
            "blog_url": "https://www.semianalysis.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "GPU Supply Chain 2025 Outlook", "url": "https://www.semianalysis.com/gpu-supply-2025", "date": "2025-02-01", "relevance": "Semiconductor market"},
              {"title": "Wafer-Scale Engine Economics", "url": "https://www.semianalysis.com/wse-economics", "date": "2025-01-10", "relevance": "Chip architecture"}
            ]
          },
          "intel_dev": {
            "name": "Intel Developer Zone",
            "blog_url": "https://www.intel.com/content/www/us/en/developer/articles/technical/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "AMX Instruction Set for AI Workloads", "url": "https://intel.com/developer/amx-ai", "date": "2025-01-25", "relevance": "CPU+GPU hybrid"}
            ]
          },
          "amd_gpuopen": {
            "name": "AMD GPUOpen",
            "blog_url": "https://gpuopen.com/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "ROCm 6.0 Performance Improvements", "url": "https://gpuopen.com/rocm-6", "date": "2025-01-08", "relevance": "Open-source GPU stack"}
            ]
          }
        }
      },

      "AI Performance Engineering": {
        "metadata": {
          "category": "AI Performance Engineering",
          "generated_date": "2026-03-09",
          "collected_timestamp": "2026-03-09T10:30:00Z",
          "source": "ai_deep_research"
        },
        "competitors": {
          "nvidia_tech": {
            "name": "NVIDIA Technical Blog",
            "blog_url": "https://developer.nvidia.com/blog/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "TensorRT-LLM Optimization Guide", "url": "https://developer.nvidia.com/blog/tensorrt-llm", "date": "2025-02-12", "relevance": "Inference optimization"},
              {"title": "FlashAttention-3 CUDA Implementation", "url": "https://developer.nvidia.com/blog/flash-attention-3", "date": "2025-01-18", "relevance": "Attention efficiency"}
            ]
          },
          "anyscale": {
            "name": "Anyscale Blog",
            "blog_url": "https://www.anyscale.com/blog",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Scaling LLM Inference with Ray Serve", "url": "https://anyscale.com/blog/ray-serve-llm", "date": "2025-02-08", "relevance": "Distributed inference"},
              {"title": "Cost-Efficient Model Training at Scale", "url": "https://anyscale.com/blog/training-cost", "date": "2025-01-22", "relevance": "Training efficiency"}
            ]
          },
          "together_ai": {
            "name": "Together AI Blog",
            "blog_url": "https://www.together.ai/blog",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "FlashAttention-2 in Production", "url": "https://together.ai/blog/flashattention-prod", "date": "2025-02-03", "relevance": "Attention mechanisms"},
              {"title": "Inference Cost Reduction 70%", "url": "https://together.ai/blog/inference-cost", "date": "2025-01-14", "relevance": "Cost optimization"}
            ]
          },
          "huggingface": {
            "name": "Hugging Face Blog",
            "blog_url": "https://huggingface.co/blog",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Quantization Techniques for LLMs", "url": "https://huggingface.co/blog/quantization", "date": "2025-01-30", "relevance": "Model compression"}
            ]
          },
          "mosaicml": {
            "name": "MosaicML (Databricks)",
            "blog_url": "https://www.databricks.com/blog",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Efficient LLM Training with Composer", "url": "https://databricks.com/blog/composer-training", "date": "2025-01-05", "relevance": "Training efficiency"}
            ]
          },
          "alphasignal": {
            "name": "AlphaSignal",
            "blog_url": "https://alphasignal.ai/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Top AI Engineering Papers Jan 2025", "url": "https://alphasignal.ai/jan-2025", "date": "2025-02-01", "relevance": "Research curation"}
            ]
          }
        }
      },

      "Robotics & Edge Computing": {
        "metadata": {
          "category": "Robotics & Edge Computing",
          "generated_date": "2026-03-09",
          "collected_timestamp": "2026-03-09T10:30:00Z",
          "source": "ai_deep_research"
        },
        "competitors": {
          "ieee_spectrum": {
            "name": "IEEE Spectrum Robotics",
            "blog_url": "https://spectrum.ieee.org/topic/robotics/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Humanoid Robots in Manufacturing 2025", "url": "https://spectrum.ieee.org/humanoid-2025", "date": "2025-02-10", "relevance": "Humanoid robotics"},
              {"title": "Edge AI for Industrial Control", "url": "https://spectrum.ieee.org/edge-ai-control", "date": "2025-01-20", "relevance": "Industrial edge AI"}
            ]
          },
          "boston_dynamics": {
            "name": "Boston Dynamics Blog",
            "blog_url": "https://bostondynamics.com/blog/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Atlas Learning to Manipulate Objects", "url": "https://bostondynamics.com/blog/atlas-manipulation", "date": "2025-02-05", "relevance": "Robot manipulation"},
              {"title": "Spot Autonomy in Real Environments", "url": "https://bostondynamics.com/blog/spot-autonomy", "date": "2025-01-15", "relevance": "Autonomous navigation"}
            ]
          },
          "nvidia_robotics": {
            "name": "NVIDIA Robotics Blog",
            "blog_url": "https://developer.nvidia.com/blog/category/robotics/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "Isaac Sim 4.0 for Robot Training", "url": "https://developer.nvidia.com/blog/isaac-sim-4", "date": "2025-02-08", "relevance": "Simulation training"}
            ]
          },
          "arm_newsroom": {
            "name": "Arm Newsroom (Technical)",
            "blog_url": "https://newsroom.arm.com/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Cortex-M55 for Edge AI Inference", "url": "https://newsroom.arm.com/cortex-m55-ai", "date": "2025-01-28", "relevance": "Low-power edge chip"}
            ]
          },
          "standard_bots": {
            "name": "Standard Bots Blog",
            "blog_url": "https://standardbots.com/blog/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Cobot Deployment in SME Factories", "url": "https://standardbots.com/blog/sme-cobot", "date": "2025-01-22", "relevance": "Industrial cobot"}
            ]
          },
          "dell_edge": {
            "name": "Dell Technologies Blog",
            "blog_url": "https://www.dell.com/en-us/blog/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Micro LLM Deployment at Edge", "url": "https://dell.com/blog/micro-llm-edge", "date": "2025-01-18", "relevance": "Edge infrastructure"}
            ]
          }
        }
      },

      "High-Performance Networking": {
        "metadata": {
          "category": "High-Performance Networking",
          "generated_date": "2026-03-09",
          "collected_timestamp": "2026-03-09T10:30:00Z",
          "source": "ai_deep_research"
        },
        "competitors": {
          "cloudflare": {
            "name": "Cloudflare Blog",
            "blog_url": "https://blog.cloudflare.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "HTTP/3 Performance at Scale", "url": "https://blog.cloudflare.com/http3-perf", "date": "2025-02-10", "relevance": "Protocol optimization"},
              {"title": "QUIC Adoption Metrics 2025", "url": "https://blog.cloudflare.com/quic-2025", "date": "2025-01-25", "relevance": "Next-gen transport"}
            ]
          },
          "meta_engineering": {
            "name": "Meta Engineering Blog",
            "blog_url": "https://engineering.fb.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "RoCE Network for 100k GPU Cluster", "url": "https://engineering.fb.com/roce-100k-gpu", "date": "2025-02-05", "relevance": "AI cluster networking"},
              {"title": "Distributed Training Network Design", "url": "https://engineering.fb.com/dist-training-net", "date": "2025-01-12", "relevance": "Training infrastructure"}
            ]
          },
          "cisco_tech": {
            "name": "Cisco Tech Blog",
            "blog_url": "https://blogs.cisco.com/",
            "tier": 1,
            "editable": false,
            "articles": [
              {"title": "AI-Ready Data Center Ethernet", "url": "https://blogs.cisco.com/ai-ethernet", "date": "2025-01-30", "relevance": "AI fabric design"}
            ]
          },
          "kentik": {
            "name": "Kentik Blog",
            "blog_url": "https://www.kentik.com/blog/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "Network Observability for GPU Clusters", "url": "https://kentik.com/blog/gpu-network-obs", "date": "2025-01-20", "relevance": "Network visibility"}
            ]
          },
          "packet_pushers": {
            "name": "Packet Pushers",
            "blog_url": "https://packetpushers.net/",
            "tier": 2,
            "editable": false,
            "articles": [
              {"title": "InfiniBand vs Ethernet for AI in 2025", "url": "https://packetpushers.net/infiniband-vs-ethernet", "date": "2025-02-01", "relevance": "AI network comparison"}
            ]
          }
        }
      }
    }
    ```

[ ] Gemini Client Setup (new SDK pattern — ④ call directly without wrapper)
    > ⚠️ Forbidden to create get_competitor_client() wrapper function — prevents duplicate clients
    > Call get_client(api_key) directly inside collect_competitor_articles()

    ```python
    # Old SDK forbidden: import google.generativeai as genai (X)
    # New SDK use: from google import genai (O)
    from google import genai
    from google.genai import types

    # ✅ _competitor_search_cfg() definition not needed — _call_search() has config built-in
    # (Verified from techaudit_agent.py:388: _call_search(client, prompt) signature, _search_cfg() called internally)

    # Calling pattern (inside collect_competitor_articles):
    #   api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
    #   if not api_key:
    #       st.warning("⚠️ GOOGLE_GENERATIVE_AI_API_KEY not set.")
    #       return None  # ← Unified to None (False returns True in is not None check → TypeError)
    #   client = get_client(api_key)   ← Cached by @st.cache_resource
    #   # Then reuse _call_search(client, prompt) (no need to pass config separately)
    ```

    [ ] Call app's existing get_client(api_key) directly (forbidden to create wrapper function)
    [ ] API key: Use only os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") (no duplicate st.secrets needed)
    [ ] Search grounding: Use _call_search(client, prompt) as-is — no separate config passing needed
    [ ] Fallback: App's existing _call() function auto-switches to MODEL_FALLBACK
    [ ] Exponential backoff: Leverage _call() internal logic (no separate implementation needed)

[ ] Add button in step_4_research() — ⑥ insertion location specified
    > **Insertion location**: Right after NotebookLM panel (st.expander) closes, before "Generate Article" button
    > Find that location in step_4_research() function and insert the block below:
    > ⚠️ **Below is abbreviated example for insertion guidance** — see Error Handling section for complete handler.
    > Use the `try/except/finally` version from Error Handling section in actual implementation.

    ```python
    # ── NotebookLM expander END ──────────────────────────────────
    # ── ⑥ NEW: Competitor Collection Button ─────────────────────
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
                st.success(f"✅ Competitor data collected! {companies} companies, {articles} articles")
            else:
                # st.error() already shown inside collect_competitor_articles()
                st.info("ℹ️ Don't worry - you can try again later or skip for now")
        except Exception as e:
            st.warning(f"⚠️ Collection failed: {str(e)}")
            st.info("ℹ️ Don't worry - you can try again later or skip for now")
        finally:
            st.session_state.collection_in_progress = False  # Always reset (even on exception)
    # ── Generate Article Button (existing) ───────────────────────────
    ```
    [ ] [📥 Collect Competitor Articles] button — after NotebookLM panel, before Generate Article

[ ] Implement validate_url_format() helper function
    > ⚠️ Forbidden to validate URL accessibility with requests: causes Streamlit main thread blocking
    > (5 competitors × 3 retries × 10sec timeout = worst case 150sec UI freeze)
    [ ] Validate only format with urlparse (no network requests)
    [ ] Check if scheme is http/https
    [ ] Check if netloc (domain) exists
    [ ] Filter only invalid URL formats

    from urllib.parse import urlparse  # ⚠️ Import addition needed — current techaudit_agent.py imports only quote (line 15)

    def validate_url_format(url: str) -> bool:
        """Validate URL format only — no network requests, no blocking."""
        if not url or not isinstance(url, str):
            return False
        try:
            result = urlparse(url)
            return all([result.scheme in ("http", "https"), result.netloc])
        except Exception:
            return False

[ ] Implement dedup_articles() function
    [ ] Track seen URLs in set
    [ ] Keep first occurrence only
    [ ] Sort by date descending (newest first), missing dates go to end

    def dedup_articles(articles_list: list[dict]) -> list[dict]:
        """Remove duplicate articles by URL, then sort by date descending."""
        seen_urls: set[str] = set()
        deduped: list[dict] = []
        for article in articles_list:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                deduped.append(article)
        # Sort by date descending (missing dates at end)
        deduped.sort(key=lambda a: a.get("date") or "", reverse=True)
        return deduped

[ ] ③ Define save_competitors_data() / load_competitors_data() first
    > ⚠️ These two functions are called internally by collect_competitor_articles()
    > Must be positioned **before** collect_competitor_articles().
    > See "Strategy 1" in Performance Optimization section for full implementation.
    > Phase 1 checklist load/save items are considered already implemented in Phase 0.

[ ] Implement collect_competitor_articles()
    Complete implementation with error handling:

    ```python
    def collect_competitor_articles() -> tuple[int, int] | None:
        """Collect articles for current article's category using Gemini + Google Search"""
        try:
            # ⚠️ Actual session key is "category" (see techaudit_agent.py:1591)
            # "article_category" key doesn't exist — relying on default fallback causes bug
            category = st.session_state.get("category", "")

            # ⑩ Early return for empty category — check before unnecessary config validation
            if not category:
                st.warning("⚠️ No category selected. Please complete Step 1 first.")
                return None  # ← Unified to None (False returns True in is not None check → TypeError)

            # ⑤ Validate COMPETITORS_BY_CATEGORY vs CATEGORIES key match (after category check)
            _validate_competitor_config()

            # Load or initialize competitors data
            all_data = load_competitors_data()
            if all_data is None:
                all_data = {"schema_version": "1.0"}

            if category not in all_data:
                all_data[category] = {
                    "metadata": {
                        "category": category,
                        "generated_date": datetime.now().strftime("%Y-%m-%d"),
                        "collected_timestamp": datetime.now().isoformat() + "Z",
                        "source": "ai_deep_research"
                    },
                    "competitors": {}
                }

            # ④ Call directly without wrapper (get_competitor_client() forbidden)
            api_key = os.getenv("GOOGLE_GENERATIVE_AI_API_KEY")
            if not api_key:
                # Predictable condition — st.warning + return None, not raise ValueError (UX)
                st.warning("⚠️ GOOGLE_GENERATIVE_AI_API_KEY not set.")
                return None
            client = get_client(api_key)  # @st.cache_resource — doesn't create new Client

            # Get competitors for this category from COMPETITORS_BY_CATEGORY
            if category not in COMPETITORS_BY_CATEGORY:
                raise ValueError(f"No competitors defined for category: {category}")

            competitors = COMPETITORS_BY_CATEGORY[category]

            # Collect articles for each competitor
            for comp_key, comp_data in competitors.items():
                try:
                    articles = fetch_articles_for_competitor(
                        client,       # Pass genai.Client (not old SDK's model object)
                        comp_key,
                        comp_data,
                        category
                    )

                    # URL format validation (no network requests — use validate_url_format)
                    validated_articles = [
                        a for a in articles
                        if validate_url_format(a.get("url", ""))
                    ]

                    # Deduplicate
                    deduped_articles = dedup_articles(validated_articles)

                    # Store in JSON structure
                    if comp_key not in all_data[category]["competitors"]:
                        all_data[category]["competitors"][comp_key] = {
                            "name": comp_data.get("name", ""),
                            "blog_url": comp_data.get("blog_url", ""),
                            "tier": comp_data.get("tier", 2),
                            "editable": False,
                            "articles": []
                        }

                    all_data[category]["competitors"][comp_key]["articles"] = deduped_articles

                except Exception as e:
                    st.warning(f"Failed to collect for {comp_key}: {str(e)}")
                    continue

            # Validate schema before saving
            validate_competitors_schema(all_data)

            # Save to session_state 1st layer + file 2nd layer (st.cache_data not needed)
            save_competitors_data(all_data)

            # Calculate count for success message
            cat_data = all_data.get(category, {})
            companies_count = len(cat_data.get("competitors", {}))
            articles_count = sum(
                len(c.get("articles", []))
                for c in cat_data.get("competitors", {}).values()
            )
            return companies_count, articles_count  # Return (int, int) — format message at call site

        except Exception as e:
            st.error(f"Collection error: {str(e)}")
            return None  # Return None on failure (call site checks for None)
        # ⚠️ collection_in_progress reset handled only in finally block at call site (button handler)
        # Forbidden to duplicate initialization inside function — single responsibility principle

    def fetch_articles_for_competitor(
        client: genai.Client, comp_key: str, comp_data: dict, category: str
    ) -> list[dict]:
        """Fetch articles using new SDK — client.models.generate_content() pattern."""
        blog_url = comp_data.get("blog_url", "")

        current_year = datetime.now().year  # Dynamic date (hardcoding forbidden)
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
            # New SDK pattern: client.models.generate_content() + GenerateContentConfig
            # Recommend reusing app's _call_search() + _extract_text() + _parse_json()
            resp = _call_search(client, prompt)          # Existing helper (search grounding + fallback)
            text = _extract_text(resp)                   # Existing helper (remove thinking token)
            articles = _parse_json(text)                 # Existing helper (robust JSON parsing)
            return articles if isinstance(articles, list) else []

        except Exception as e:
            st.warning(f"Gemini call failed for {comp_key}: {str(e)}")
            return []
    ```

[ ] Save with metadata
    [ ] Add collection_timestamp       (collected_timestamp field)
    [ ] Add source: "ai_deep_research" (source field)
    [ ] Add category: st.session_state.get("category") (category field, use dynamic value)
    > ⚠️ metadata field must match dictionary in implementation code exactly:
    > category / generated_date / collected_timestamp / source — only 4 fields. No prompt_version.

[ ] Auto-handle missing data
    [ ] If collection fails → collect_competitor_articles() returns None
        (default auto-load handled by load_competitors_data() 3rd fallback — forbidden to load directly here)
    [ ] If load_competitors_data() also fails → show st.warning() but continue
    [ ] User can retry in future runs
```

### Phase 1: Load & Display (Step 5 — 📊 Competitors tab) - 1 hour

```
[ ] Implement validate_competitors_schema() function
    > ⚠️ Needs to be defined first during Phase 0 — collect_competitor_articles() calls this function.
    > Write it first in file beginning (before save/load definition) during Phase 0 work.
    [ ] Check schema_version exists
    [ ] Validate each category has "competitors" key
    [ ] Validate each competitor has "name", "blog_url", "articles"
    [ ] Validate articles have "title", "url", "date", "relevance"
    [ ] Raise ValueError with specific field information on failure

    def validate_competitors_schema(data):
        """Validate competitors data structure"""
        if "schema_version" not in data:
            raise ValueError("Missing schema_version")

        for category, cat_data in data.items():
            if category == "schema_version":
                continue
            if "competitors" not in cat_data:
                raise ValueError(f"Category '{category}' missing 'competitors'")

            for comp_name, competitor in cat_data["competitors"].items():
                required = ["name", "blog_url", "articles"]
                for field in required:
                    if field not in competitor:
                        raise ValueError(f"Competitor '{comp_name}' missing '{field}'")

                for idx, article in enumerate(competitor["articles"]):
                    art_required = ["title", "url", "date", "relevance"]
                    for field in art_required:
                        if field not in article:
                            raise ValueError(f"Article {idx} in '{comp_name}' missing '{field}'")

[ ] Implement migrate_competitors_schema() function
    [ ] Check schema_version in loaded data
    [ ] If v1.0: return as-is (no migration needed)
    [ ] If unknown version (not v1.0): show st.warning() then return None
    [ ] Return None → load_competitors_data() handles as ValueError then tries default fallback
    > Currently only v1.0 supported. Add branches to this function when adding future versions.

    def migrate_competitors_schema(data):
        """Migrate competitors data between schema versions"""
        version = data.get("schema_version", "1.0")
        if version == "1.0":
            return data  # Current version, no migration needed
        else:
            # v1.1+: Currently undefined. Unknown versions return None
            # → load_competitors_data() handles as ValueError then tries default fallback
            st.warning(f"Unknown schema version: {version}. Re-collect in Step 4.")
            return None

[ ] load_competitors_data() / save_competitors_data()
    > ✅ Pre-implemented in Phase 0 (see Phase 0 checklist item ③)
    > See "Strategy 1" in Performance Optimization section for full implementation
    > This item is only for verification after Phase 0 completion:
    [ ] Verify session_state 1st → file 2nd → default 3rd fallback order
    [ ] Verify migrate_competitors_schema() + validate_competitors_schema() calls
    [ ] Verify None-checks

[ ] Implement load_competitors_for_category(category: str, available_data: dict | None) -> dict | None
    [ ] Match article category to JSON category (case-insensitive exact match)
    [ ] If exact match not found, return None (UI handles selection)
    [ ] Separate data loading from UI logic
    [ ] Add proper type hints (Optional[dict] for Python 3.9 compat if needed)
    [ ] DO NOT use @st.cache_data (stateless lookup function)

    def load_competitors_for_category(category: str, available_data: Optional[dict] = None) -> Optional[dict]:
        """Load competitors matching article category - case-insensitive exact match"""
        if not available_data:
            return None

        if "schema_version" not in available_data:
            return None

        # Exact match (case-insensitive)
        for cat_key in available_data.keys():
            if cat_key != "schema_version" and cat_key.lower() == category.lower():
                return available_data[cat_key]

        # No match found - return None, UI will handle category selection
        return None

    # In Step 5, handle category mismatch separately:
    competitors_data = load_competitors_data()
    if competitors_data:
        matched_data = load_competitors_for_category(category, competitors_data)
        if not matched_data:
            st.warning(f"No competitors for '{category}'")
            # ⚠️ Must exclude "schema_version" key — including it makes it selectable in selectbox → error
            available = [k for k in competitors_data if k != "schema_version"]
            if available:
                selected_cat = st.selectbox("Select category:", available)
                matched_data = competitors_data[selected_cat]
                render_competitors_dashboard(selected_cat, matched_data)  # ← Must call

[ ] ⑧ Implement build_competitive_context(category: str, data: dict | None) -> str
    > See full implementation in Competitive Context Injection section
    [ ] If data is None or empty → return empty string "" (doesn't affect article generation)
    [ ] Call load_competitors_for_category() for category matching
    [ ] Include max 2 article titles per competitor
    [ ] Pass result to _do_generate(competitive_context=...) (links with ② Option A)
    [ ] Forbidden to call load_competitors_data() internally when calling alone — pass via data parameter

[ ] ② generate_article_claude() / generate_article() signature and prompt modification
    > ⚠️ Even if passing competitive_context to _do_generate(), these functions won't update unless modified
    > → competitive context won't be reflected in actual article generation prompt — forbidden to skip
    [ ] Add competitive_context: str = "" parameter to generate_article_claude()
    [ ] Add competitive_context: str = "" parameter to generate_article()
    [ ] Insert at end of prompt in both functions with pattern below:
        ```python
        if competitive_context:
            prompt += f"\n\n{competitive_context}"
        ```
    [ ] If competitive_context is empty string ("") → no prompt change (backward compatible)

[ ] Cache invalidation not needed (session_state based)
    > save_competitors_data() directly updates session_state[COMPETITORS_SS_KEY]
    > st.cache_data.clear() and competitors_updated flag no longer needed.
    > On next rerun load_competitors_data() immediately returns latest session_state value.

[ ] Add session state protection
    [ ] Initialize: st.session_state.collection_in_progress = False
    [ ] Check flag before API call
    [ ] Set True during collection, False after
    [ ] Disable button while collection_in_progress

    if "collection_in_progress" not in st.session_state:
        st.session_state.collection_in_progress = False

    collect_button = st.button(
        "📥 Collect Competitor Articles",
        disabled=st.session_state.collection_in_progress
    )

    if collect_button and not st.session_state.collection_in_progress:
        st.session_state.collection_in_progress = True
        try:
            with st.spinner("🔍 AI collecting articles..."):
                result = collect_competitor_articles()
            if result is not None:
                companies, articles = result
                st.success(f"✅ Competitor data collected! {companies} companies, {articles} articles")
            else:
                # st.error() already shown inside collect_competitor_articles()
                st.info("ℹ️ Don't worry - you can try again later or skip for now")
        except Exception as e:
            st.warning(f"⚠️ Collection failed: {str(e)}")  # st.warning not st.error (canonical)
            st.info("ℹ️ Don't worry - you can try again later or skip for now")
        finally:
            st.session_state.collection_in_progress = False

[ ] render_article() — ✅ Already exists, reuse (techaudit_agent.py:1064)
    > Verification complete: render_article(art: dict) signature. No separate extraction needed.
    [ ] Signature: render_article(art: dict) -> None  (art is article dict object)
    [ ] Call render_article(art) in tab_article block (keep existing code as-is)

[ ] Add dashboard in step_5_article() — ⑦ integrate as tab style
    > **Style**: Add `"📊 Competitors"` tab to `st.tabs()` not separate button
    > ✅ Actual tab verification complete (techaudit_agent.py:1983):
    >   Existing: ["📄 Article", "🔍 Quality Audit", "🏷 Metadata", "⬇ Export"]
    >   Modified: ["📄 Article", "🔍 Quality Audit", "🏷 Metadata", "⬇ Export", "📊 Competitors"]
    ```python
    # techaudit_agent.py:1983 — add 5th tab to existing 4 tabs
    tab_article, tab_audit, tab_meta, tab_export, tab_competitors = st.tabs(
        ["📄 Article", "🔍 Quality Audit", "🏷 Metadata", "⬇ Export", "📊 Competitors"]
    )
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
                    sel = st.selectbox("Select category:", avail)
                    render_competitors_dashboard(sel, competitors_data[sel])
        else:
            st.info("ℹ️ No competitor data yet. Use Step 4 to collect.")
    ```
    [ ] Add "📊 Competitors" tab at end of existing tab list (forbidden to use button style)

[ ] Implement render_competitors_dashboard(category: str, category_data: dict) -> None
    """Render dashboard with matched competitor data"""
    > ⚠️ **Parameter structure caution**: category_data is return value from load_competitors_for_category()
    > It's a full category dictionary ({"metadata": {...}, "competitors": {...}}).
    > When iterating competitors must use category_data.get("competitors", {}).items().
    > Using category_data.items() directly includes "metadata" key → error.

    [ ] Accept category_data parameter (not load from global)
    [ ] If None:
        └─ st.info("ℹ️ No competitor data collected")
        └─ Show article WITHOUT dashboard
        └─ Allow user to continue (don't st.stop())

    [ ] Display article info (title, category, generated date)
    [ ] Display competitors table — extract with category_data.get("competitors", {})
    [ ] Display articles in accordion (title, URL, date, relevance - start CLOSED)
    [ ] Sort articles by date (newest first, missing dates at end)
    [ ] Type hints: category: str, category_data: dict, return: None
```

### Phase 2: Error Handling (30 minutes)

```
[ ] Define custom error classes
    [ ] CompetitorDataError (parent)
    [ ] GeminiAPIError
    [ ] SchemaValidationError
    [ ] DataLoadingError

[ ] Add try-except blocks
    [ ] JSON file loading (FileNotFoundError, JSONDecodeError)
    [ ] File operations (IOError, PermissionError)
    [ ] Schema validation (SchemaValidationError)
    [ ] URL validation (ValueError, Exception)  # urlparse only — no TimeoutError/ConnectionError
    [ ] Gemini API calls (GeminiAPIError)

[ ] User-friendly messages
    [ ] "Competitor data file not found. Collect in Step 4 first."
    [ ] "Error loading competitor data. Invalid JSON."
    [ ] "Collection failed: {specific error}. Try again later or skip."
    [ ] "API rate limit exceeded. Wait a moment and try again."

[ ] Logging
    [ ] Log file paths (errors only, not all accesses)
    [ ] Log JSON parsing errors with details
    [ ] Log schema validation failures with field names
    [ ] Log API calls and failures
```

### Phase 3: Performance Optimization (30 minutes)

```
[ ] Caching Strategy (session_state based)
    [ ] Use session_state[COMPETITORS_SS_KEY] as 1st cache
    [ ] load_competitors_data(): session_state → file → default search order
    [ ] save_competitors_data(): immediately update session_state + async file save
    [ ] Forbidden to use @st.cache_data (conflicts with session_state)

[ ] UI Optimization
    [ ] Accordion items: start CLOSED by default
    [ ] Lazy load articles (only expand on click)
    [ ] Don't load all competitors at once
    [ ] Disable buttons during processing

[ ] Memory Efficiency
    [ ] Load JSON once, reuse
    [ ] Minimal data processing
    [ ] Use native Streamlit components for display
```

### Phase 4: Integration & Testing - 90 minutes

```
[ ] Integration Tests
    [ ] Step 4 button creates JSON file (competitors_data.json)
    [ ] Step 5 📊 Competitors tab displays dashboard when clicked
    [ ] Dashboard displays correctly
    [ ] No console errors
    [ ] Latest data reflected immediately when switching tabs after collect (session_state based)

[ ] Edge Cases (7 scenarios - 12 min each)
    1. [ ] Missing API key handling
       - GOOGLE_GENERATIVE_AI_API_KEY not set (environment variable not set)
       - os.getenv("GOOGLE_GENERATIVE_AI_API_KEY") returns None
       - Expected: st.warning() shown, collect_competitor_articles() returns None
       - ⚠️ Forbidden to use st.secrets — code uses only os.getenv()

    2. [ ] Empty competitor articles list
       - Gemini returns [] for all competitors
       - Expected: competitors shown but with "0 articles" message
       - Dashboard still renders

    3. [ ] Invalid article URLs
       - validate_url_format() returns False for some URLs (format error)
       - Expected: URLs filtered out, valid format ones only stored
       - Duplicates removed correctly

    4. [ ] Duplicate article handling
       - Same URL from multiple competitors or multiple calls
       - Expected: dedup_articles() keeps first occurrence only
       - Order preserved (by date)

    5. [ ] Schema version mismatch
       - competitors_data.json has schema_version "2.0" (unknown)
       - Expected: migrate_competitors_schema() returns None
       - load_competitors_data() catches ValueError → tries default fallback
       - if default_competitors.json also missing or fails → return None
       - UI shows info message: "No competitor data collected"

    6. [ ] Very large JSON files (1MB+)
       - 100+ competitors with 50+ articles each
       - Expected: load_competitors_data() still works via caching
       - No memory leaks, fast subsequent loads

    7. [ ] Category not found in JSON
       - article_category = "Quantum Computing" but JSON only has "GPU Computing"
       - Expected: load_competitors_for_category() returns None
       - UI shows selectbox: "Select category to view"
       - User can pick from available categories

[ ] User Testing
    [ ] Dashboard loads in <2 seconds (cached)
    [ ] Buttons respond immediately
    [ ] Accordion expand/collapse works
    [ ] Links are clickable and valid
    [ ] Category selection works correctly
    [ ] Articles sort correctly by date (newest first)
    [ ] No console errors during workflow
    [ ] Error messages are user-friendly
    [ ] Existing features (Steps 1-3) still work
```

---

## Article Collection Guidelines

### AI Prompt Template (Method A: Gemini + Google Search)

> **Calling strategy**: **1 API call per competitor** (per-competitor, individual call)
> - Max 6 calls per category × 4 categories = max 24 Gemini API calls
> - Same strategy as `fetch_articles_for_competitor()` implementation (not batch calling)
> - Advantage: individual failures don't affect other competitors (try/except per competitor)
> - Disadvantage: many API calls → only collect 1 category so actually max 6 calls

Below is prompt example that `fetch_articles_for_competitor()` generates for 1 competitor:

```
[Example of 1 competitor: The Next Platform / GPU Computing & Hardware]

Find the 3 most recent technical articles from The Next Platform:
Blog: https://www.nextplatform.com/

Category: GPU Computing & Hardware

Return ONLY a JSON array (no markdown, no wrapping):
[
  {
    "title": "Article Title",
    "url": "https://exact-url",
    "date": "YYYY-MM-DD",
    "relevance": "GPU optimization description"
  }
]

Requirements:
- URLs in valid http/https format
- Dates in YYYY-MM-DD format only
- Published in {current_year - 1}-{current_year}   ← dynamically generated
- Max 3 articles per company
- No "company" field
```

### Category-Specific Focus Keywords (for reference in prompt category field)

```
AI Performance Engineering:
  Focus: Model acceleration, inference efficiency, distributed training, cost optimization

GPU Computing & Hardware:
  Focus: GPU architecture, accelerator benchmarks, hardware performance tuning

High-Performance Networking:
  Focus: AI cluster networking, RDMA/RoCE, low-latency protocols, SDN

Robotics & Edge Computing:
  Focus: Physical AI, edge inference, humanoid robots, real-time control
```

---

## Competitive Context Injection (Step 5 article generation enhancement)

### Overview

Rather than just displaying competitor data, **inject context into Step 5 article generation prompt**.
Generative AI recognizes topics competitors are covering and writes from differentiated angles.

```
Existing flow:  Research → Article generation → (separate) display competitors
Improved flow:  Research + collect competitors → Article generation with competitor insights
```

### Implementation Method

```python
def build_competitive_context(category: str, data: dict | None) -> str:
    """
    Generate competitor context block for injection into Step 5 prompt.
    Accepts pre-loaded data argument to prevent duplicate loading.
    Returns empty string if no data (doesn't affect prompt).
    """
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
            titles = [f'  - "{a.get("title", "")}"' for a in articles[:2]]  # [3] defensive .get()
            competitor_lines.append(f"**{name}**:")
            competitor_lines.extend(titles)

    # [1] Return empty string if no actual competitor lines — prevent header+instruction only injection
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
```

### ② _do_generate() Modification Method (Option A — add parameter)

> **Option A**: Add `competitive_context: str = ""` parameter to `_do_generate()`.
> No signature change at existing call sites (backward compatible due to default="").

```python
# techaudit_agent.py:1817 — existing signature
# def _do_generate(title: str, accepted_sources: list[dict], qa_feedback: str = ""):

# ② Modified signature
def _do_generate(title: str, accepted_sources: list[dict], qa_feedback: str = "", competitive_context: str = ""):
    """
    competitive_context: return value from build_competitive_context().
    Empty string has no prompt effect.
    """
    # ── Attempt 1: Claude (keep existing arg order, add competitive_context only) ──
    art = generate_article_claude(
        anthropic_client,                        # existing
        title,                                   # existing
        accepted_sources,                        # existing
        st.session_state.sources,               # existing (all_sources)
        st.session_state.notebooklm_context,    # existing (context)
        qa_feedback=qa_feedback,                 # existing
        competitive_context=competitive_context, # ← NEW
    )

    # ── Attempt 2: Gemini (keep existing arg order, add competitive_context only) ──
    art = generate_article(
        st.session_state._client,               # existing
        title,                                   # existing
        accepted_sources,                        # existing
        st.session_state.notebooklm_context,    # existing (context)
        competitive_context=competitive_context, # ← NEW
    )
```

### Article Prompt Insertion Location

> ⚠️ **Calling location caution**: `_do_generate()` is called from
> **step_4_research() Generate Article button handler**, not step_5_article() (techaudit_agent.py:1793-1800).
> step_5_article() only displays already-generated article so doesn't call `_do_generate()` here.
> → `build_competitive_context()` calculation and `_do_generate()` modification both belong in step_4_research().

> ⚠️ `_do_generate()` has **4 call sites** in code. All must be modified:
> | Line | Location | Modification |
> |------|----------|--------|
> | 1797 | step_4_research() Generate button | Calculate then save + pass to session_state |
> | 1919 | step_5_article() Retry Generation button | Reuse from session_state |
> | 1927 | step_5_article() safety net call | Reuse from session_state |
> | 2000 | handle_rerun() QA re-run | Reuse from session_state |

```python
# ── [1797] step_4_research() Generate button handler ──────────────────────────────
# Calculate competitive_context and save to session_state (reuse in remaining call sites)
if st.button(f"🚀 Generate Article with {n_acc} Accepted Source{'s' if n_acc != 1 else ''}"):
    st.session_state.accepted_sources = accepted_sources
    st.session_state.sources_confirmed = True
    st.session_state.step = 5
    st.session_state.qa_rerun_count = 0
    # ← NEW: Calculate then save to session_state
    competitors_data = load_competitors_data()
    competitive_context = build_competitive_context(
        st.session_state.get("category", ""), competitors_data
    )
    st.session_state.competitive_context = competitive_context   # ← Save
    _do_generate(title, accepted_sources, qa_feedback="", competitive_context=competitive_context)
    st.rerun()

# ── [1919] step_5_article() Retry Generation button ──────────────────────────────
# Retry after gen_error — reuse from session_state
if st.button("🔁 Retry Generation"):
    _do_generate(
        title, st.session_state.accepted_sources,
        competitive_context=st.session_state.get("competitive_context", ""),  # ← NEW
    )
    st.rerun()

# ── [1927] step_5_article() safety net call ─────────────────────────────────────────
# Fallback when article is missing — reuse from session_state
_do_generate(
    title, st.session_state.accepted_sources,
    competitive_context=st.session_state.get("competitive_context", ""),      # ← NEW
)

# ── [2000] handle_rerun() QA re-run ─────────────────────────────────────────────
# QA re-run — keep qa_feedback, reuse from session_state
_do_generate(
    title, st.session_state.accepted_sources, qa_feedback=feedback,
    competitive_context=st.session_state.get("competitive_context", ""),      # ← NEW
)
```

### Conditions

- Article generation works normally **without** competitor data (optional enhancement)
- `build_competitive_context()` always safely returns empty string
- `competitive_context` calculated only on first generation (line 1797) — subsequent runs reuse session_state
- Only need to add context at end of `generate_article_claude()` / `generate_article()` prompt

---

## Error Handling & User Options

### Step 4: Competitor Collection (Simple Design)

```python
# Initialize session state protection
if "collection_in_progress" not in st.session_state:
    st.session_state.collection_in_progress = False

# Button disabled during collection
collect_button = st.button(
    "📥 Collect Competitor Articles",
    disabled=st.session_state.collection_in_progress
)

if collect_button and not st.session_state.collection_in_progress:
    st.session_state.collection_in_progress = True
    try:
        with st.spinner("🔍 AI collecting articles..."):
            result = collect_competitor_articles()
        # save_competitors_data() directly updates session_state internally — clear not needed
        if result is not None:
            companies, articles = result
            st.success(f"✅ Competitor data collected! {companies} companies, {articles} articles")
        else:
            st.info("ℹ️ Don't worry - you can try again later or skip for now")
    except Exception as e:
        st.warning(f"⚠️ Collection failed: {str(e)}")
        st.info("ℹ️ Don't worry - you can try again later or skip for now")
    finally:
        st.session_state.collection_in_progress = False

# Continue button always available
if st.button("Continue to Article Writing ➜"):
    st.session_state.step = 5
    st.rerun()
```

### Step 5: Graceful Missing Data Handling

```python
# ✅ Actual tab names verified (techaudit_agent.py:1983)
tab_article, tab_audit, tab_meta, tab_export, tab_competitors = st.tabs(
    ["📄 Article", "🔍 Quality Audit", "🏷 Metadata", "⬇ Export", "📊 Competitors"]
)

# ── tab_article ───────────────────────────────────────────────
with tab_article:
    render_article(art)  # Article always displayed (independent of competitor data) — art: dict

# ── tab_competitors ───────────────────────────────────────────
with tab_competitors:
    # Session state based so st.cache_data.clear() not needed
    competitors_data = load_competitors_data()

    # Competitive context already built before article generation (no rebuild needed here)

    if competitors_data:
        # ⚠️ Session key is "category" — NOT "article_category" (techaudit_agent.py:1591)
        category = st.session_state.get("category", "")
        matched_data = load_competitors_for_category(category, competitors_data)

        if matched_data:
            render_competitors_dashboard(category, matched_data)
        else:
            # Category mismatch - offer selection
            st.warning(f"No competitors for '{category}'")
            # ⚠️ Must exclude "schema_version" key
            available = [k for k in competitors_data if k != "schema_version"]
            if available:
                selected_cat = st.selectbox("Select category to view:", available)
                render_competitors_dashboard(selected_cat, competitors_data[selected_cat])
    else:
        # ❌ No data - show friendly message only
        st.info("""
        ℹ️ **No competitor data collected yet**

        Go back to **Step 4** to collect competitor data.
        """)
```

**Key Difference**:
- ❌ NOT forcing users to collect data
- ✅ Simple info message if missing
- ✅ Article ALWAYS displayed
- ✅ Export works with or without competitor data
- ✅ Users naturally flow through

### User-Friendly Messages

```
✅ Success:
  "✅ Competitor data collected! 5 companies, 12 articles"

⚠️ Warning:
  "⚠️ No competitor data for this category"
  "⚠️ Continuing without competitors"

ℹ️ Info:
  "ℹ️ Using default competitors for testing"
  "💡 Tip: Click article titles to read full posts"

❌ Error:
  "❌ Data format outdated. Recollect in Step 4"
  "❌ Unable to load competitors. Try again."
```


---

## Performance Optimization

### Strategy 1: Dual Storage (session_state 1st layer + file 2nd layer)

> ⚠️ Streamlit Cloud resets filesystem on restart.
> Relying on files alone loses data in Cloud environment.

```python
COMPETITORS_SS_KEY = "competitors_data_cache"

def save_competitors_data(data: dict) -> None:
    """Always save to session_state, file only when possible."""
    st.session_state[COMPETITORS_SS_KEY] = data
    try:
        os.makedirs(os.path.dirname(COMPETITORS_DATA_PATH), exist_ok=True)
        with open(COMPETITORS_DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except (IOError, OSError):
        pass  # Cloud environment — session_state alone is sufficient

def load_competitors_data() -> dict | None:
    """1st: session_state (fast, Cloud compatible) → 2nd: file → 3rd: default fallback"""
    # 1st: session_state
    # ⚠️ _init() initializes with None so use `is not None` check not `in` check
    # (`in` check with cached None returns True → file search bug)
    cached = st.session_state.get(COMPETITORS_SS_KEY)
    if cached is not None:
        return cached

    # 2nd: local file (when exists)
    try:
        with open(COMPETITORS_DATA_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data = migrate_competitors_schema(data)
        if data is None:
            raise ValueError("Migration failed")
        validate_competitors_schema(data)
        st.session_state[COMPETITORS_SS_KEY] = data  # Also cache in session_state
        return data
    except FileNotFoundError:
        pass
    except Exception as e:
        st.warning(f"Competitor data file load failed: {e}")

    # 3rd: default fallback
    try:
        with open(DEFAULT_COMPETITORS_PATH, encoding="utf-8") as f:
            data = json.load(f)
        data = migrate_competitors_schema(data)
        if data is None:
            return None
        validate_competitors_schema(data)
        st.session_state[COMPETITORS_SS_KEY] = data
        return data
    except Exception as e:
        st.error(f"Default data load failed: {e}")
        return None

# ✅ Result:
# - session_state: reused in all reruns within session (Streamlit Cloud compatible)
# - file: persists between sessions in local development
# - @st.cache_data removed → st.cache_data.clear() not needed after collect
```

### Strategy 2: Lazy UI Loading

```python
# Accordion items: CLOSED by default
# Only expand when user clicks
# Prevents loading all 100+ articles at once

with st.expander("▼ The Next Platform (3 articles)", expanded=False):
    # Render articles only when expanded
    render_articles_table(nextplatform_articles)
```

### Strategy 3: Memory Efficiency

```python
# Load JSON once
competitors_data = load_competitors_data()

# Reuse throughout dashboard
# Minimal filtering/processing
```


---

## Risk Management

### Potential Risks & Mitigation

#### Risk 1: Data Collection Failure
**Problem**: Gemini API call fails, no competitor articles collected
**Mitigation**:
- Fallback: `load_competitors_data()` 3rd fallback auto-loads `default_competitors.json`
- per-competitor try/except — rest of collection continues if 1 fails
- Logging: st.warning() shows failed competitors

#### Risk 2: techaudit_agent.py Gets Corrupted
**Problem**: Editing Streamlit app breaks existing functionality
**Mitigation**:
- Git commit BEFORE any changes
- Backup: `techaudit_agent.py.backup`
- Test each Phase immediately after implementation
- Rollback plan: Revert to previous git commit

#### Risk 3: File System Issues
**Problem**: competitors_data.json corrupted, deleted, or inaccessible
**Mitigation**:
- Store in /data/ directory (separate from code)
- Add file existence check at start
- Provide "Recollect" button if file invalid
- Logging: Track file access

#### Risk 3b: Competitor Data Loss from Session Timeout (New)
**Problem**: session_state 1st storage resets on browser close/session timeout.
Data disappears on reconnect in Streamlit Cloud.
**Mitigation**:
- If 2nd file save succeeds, auto-recover next session (load_competitors_data() tries file path)
- Local environment: complete recovery via file persistence
- Cloud environment: if file save fails → show "Recollect in Step 4" message
- Recommend showing users "Valid only during this session" message after collection

#### ~~Risk 4: Excel Generation Fails~~ (Removed)
> Excel Export removed from Phase 1.0 scope (see Line 57). Review after Phase 2.0.

#### Risk 4: Performance Degradation
**Problem**: Dashboard loads slowly with large dataset
**Mitigation**:
- Caching strategy (session_state 1st cache — forbidden to use @st.cache_data)
- Expandable/collapsed UI (lazy load)
- Pagination if needed (Phase 2)
- Monitor load time during testing

### Rollback Plan

```
If implementation breaks anything:

1. Immediate: git log --oneline
2. Identify last working commit
3. git checkout <commit-hash> techaudit_agent.py
4. Restart Streamlit
5. Verify functionality restored

OR

1. Use .backup file
   cp techaudit_agent.py.backup techaudit_agent.py
2. Restart
3. Identify what went wrong
4. Fix and retry
```

---

## Phase Architecture

### Phase 1.0 (This Implementation)

**Features**:
- ✅ AI-based competitor data collection (Step 4)
- ✅ Fixed competitors (non-editable)
- ✅ Category-based (GPU, AI, Robotics, etc.)
- ✅ Simple display dashboard (Step 5)
- ✅ User options (collect, default, skip)

**Timeline**: 3.5-4 hours (Sonnet 4.6)

### Phase 2.0 (Future Enhancement)

**Design**: Competitors Fixed, User Modifies via Code

**Phase 2 Philosophy**:
- ❌ No UI for editing (keep simple)
- ✅ Users modify competitors_data.json directly
- ✅ Re-run Streamlit to reload
- ✅ Add new categories as needed
- ✅ Keeps Phase 1 minimal & focused

**Planned Features**:
- ✅ Add new competitors
  - Edit competitors_data.json
  - Add new "company_key" entry
  - Include: name, blog_url, tier, articles

- ✅ Add new categories
  - Add new top-level key: "AI Performance Engineering"
  - Include: metadata, competitors

- ✅ Manual article updates
  - Edit articles array in JSON
  - Add/remove by modifying JSON directly
  - Restart Streamlit to reload

- ✅ Advanced Excel (Optional)
  - Multiple sheets
  - Formatting & colors
  - Charts/graphs

**Implementation Example** (for users):

```json
// Add new competitor to GPU Computing & Hardware
"GPU Computing & Hardware": {
  "competitors": {
    "nextplatform": { ... },
    "my_custom_competitor": {  // ← NEW
      "name": "Custom Blog Name",
      "blog_url": "https://custom-blog.com",
      "tier": 2,
      "articles": [
        {
          "title": "Custom Article",
          "url": "https://...",
          "date": "2025-03-06",
          "relevance": "GPU related"
        }
      ]
    }
  }
}
```

**Timeline**: 0 hours (no code implementation needed)

**User Instructions** (for Phase 2):
1. Manually edit data/competitors_data.json
2. Re-run Streamlit app
3. Data automatically reloads from cache
4. New competitors appear in dashboard

---

## Timeline & Resources

### Phase 1.0 Implementation Time

**Model Recommendations**:
```
Sonnet 4.6 (Recommended): 4-4.5 hours

  Phase 0 (AI Collection): 60 min
    └─ Gemini API setup, Google Search grounding
    └─ 3 categories × Gemini calls + dedup/validation

  Phase 1 (Load & Display): 1 hour
    └─ Dashboard rendering with matched competitors

  Phase 2 (Error Handling): 30 min
    └─ User options & graceful fallbacks

  Phase 3 (Performance): 30 min
    └─ Caching & lazy loading strategy

  Phase 4 (Testing & Edge Cases): 90 min
    └─ 7 edge cases, integration tests
    └─ Cache invalidation, competitor matching

  Buffer: 30 min

  TOTAL: 4-4.5 hours

Opus 4.6 (Fast): 3-3.5 hours
  └─ Same phases, 20% faster due to better reasoning
```

### Why This Architecture?

```
Phase 1 (Now):
- Simple, focused features
- AI-powered data collection
- User-friendly options
- Fast to implement

Phase 2 (Later):
- User customization
- Advanced features
- Build on solid base
- No time pressure
```

---

## Next Steps

### When Ready to Implement

1. **Approve Plan**
   - Review this plan.md
   - Confirm all changes vs original
   - Approve simplified approach

2. **Choose Model**
   - Option A: Sonnet 4.6 (3-4 hours) ← Recommended
   - Option B: Opus 4.6 (2-2.5 hours) ← If urgent

3. **Create Backup**
   - `cp techaudit_agent.py techaudit_agent.py.backup`
   - `git commit -m "backup before competitors feature"`

4. **Start Implementation**
   - Phase 0-4 in order
   - Test after each phase
   - Commit after each phase

5. **Deploy**
   - Final testing
   - Verify existing features still work
   - Document any new instructions

---

## Final Implementation Summary

### Key Features - Phase 1.0

| Feature | Status | Details |
|---------|--------|---------|
| **AI Data Collection** | ✅ | Gemini 2.5 Pro + Google Search grounding |
| **Category-Based** | ✅ | GPU, AI, Robotics, etc. |
| **Gemini Model** | ✅ | Primary: gemini-2.5-pro, Fallback: gemini-2.5-flash |
| **JSON Path** | ✅ | Via BASE_DIR absolute path constants (`COMPETITORS_DATA_PATH`) |
| **Schema Version** | ✅ | v1.0 with backward compatibility |
| **User Options** | ✅ | Collect / Default / Skip (not forced) |
| **Competitor Editing** | ⏳ | Phase 2.0 feature |
| **Article Relevance** | ✅ | Tracked in JSON without "company" wrapper |
| **Button Icons** | ✅ | 📥 (Step 4 button) / 📊 (Step 5 tab) |
| **Error Handling** | ✅ | Complete with 7 edge cases |
| **Performance** | ✅ | Caching, lazy loading, ~2sec dashboard load |
| **Code Examples** | ✅ | Complete implementations (not pseudocode) |

### Comparison: Original vs Final Plan

| Item | Original | Final Plan | Why |
|------|----------|-----------|-----|
| Competitor Scoring | ✅ Yes | ❌ No | Not needed for Phase 1 |
| Improvement Recs | ✅ Yes | ❌ No | Simplified scope |
| Data Collection | Manual | **AI-powered** | Automation! |
| Collection Location | Step 5 | **Step 4** | Logical separation |
| User Choice | Forced | **Optional** | Better UX |
| Editable Competitors | ❌ No | **Phase 2** | Phased approach |
| Excel Export | ✅ Yes | **❌ No** | Removed - not core feature |
| Time Estimate | 6-7 hours | **3.5-4 hours** | Focused scope |
| Complexity | High | **Low** | Easier to maintain |

---

**Status**: ✅ Planning Complete - Ready for Implementation

**Fixes Applied (v2.1 → v2.2)**:
1. ✅ Complete new SDK replacement: `from google import genai` + reuse `get_client()`
2. ✅ Synchronize category names: add `GPU Computing & Hardware`, `High-Performance Networking`
3. ✅ Replace URL validation: `requests` → `urlparse` (remove blocking)
4. ✅ Dual storage: session_state 1st + file 2nd (`save_competitors_data()`)
5. ✅ Competitor context injection: add `build_competitive_context(category, data)`
6. ✅ Fix session key: `article_category` → `category` (based on techaudit_agent.py:1591)
7. ✅ `load_competitors_data()` single version: remove @st.cache_data version, unify to session_state version
8. ✅ Add `COMPETITORS_BY_CATEGORY` constant definition (validate CATEGORIES match with assert)
9. ✅ Remove remaining `st.cache_data.clear()` (2 places — unnecessary with session_state basis)
10. ✅ `build_competitive_context()` signature: add data argument (prevent duplicate loading)
11. ✅ Technology Stack: `requests` → `urllib.parse`, specify 3-step storage
12. ✅ Secrets cleanup: remove `[gemini]` section (unnecessary in new SDK)
13. ✅ Date range update: `2024-2025` → `2025-2026`
14. ✅ `dedup_articles()` add type hints
15. ✅ Risk Management: add session timeout risk
16. ✅ Timeline: `Opus 4.5` → `Opus 4.6`
17. ✅ UI Mock-up / Phase 2 example category name fix (`GPU Computing` → `GPU Computing & Hardware`)

**v2.3 Changes (2026-03-09)**:
1. ✅ ② `_do_generate(competitive_context: str = "")` Option A signature and call pattern specify
2. ✅ ③ `save/load_competitors_data()` in Phase 0 specify defining **before** `collect_competitor_articles()`
3. ✅ ④ `get_competitor_client()` wrapper completely remove → replace with direct `get_client(api_key)` call
4. ✅ ⑤ module-level `assert` → replace with `_validate_competitor_config()` function
5. ✅ ⑥ Step 4 button insertion location specify (after NotebookLM, before Generate Article)
6. ✅ ⑦ Step 5 dashboard change from button style → `"📊 Competitors"` tab style
7. ✅ ⑧ Phase 1 checklist add `build_competitive_context()` implementation item
8. ✅ ⑨ Sample JSON `generated_date` / `collected_timestamp` → update to `2026-03-09`
9. ✅ ⑩ `collect_competitor_articles()` add early return for empty category(`if not category`)

**v2.6 Changes (2026-03-09 — Final Correctness Pass)**:
1. ✅ `collect_competitor_articles()` return value unify: early return `False` → `None` (prevent TypeError)
2. ✅ API key not set comment unify `return False` → `return None` to same
3. ✅ Data Structure JSON example competitor replace: colfax/penguin etc → nextplatform/servethehome etc (match actual constants)
4. ✅ Current System Context Step 5 description: "button" → "tab" specify
5. ✅ File Structure `render_competitors_dashboard()`: `(NEW button)` → `(NEW — called inside tab)`
6. ✅ Phase 1 section title: `Step 5 buttons` → `Step 5 — 📊 Competitors tab`
7. ✅ Integration Tests: `Step 5 button loads` → `Step 5 tab displays dashboard when clicked`
8. ✅ Edge Case 1: `st.secrets.get()` → `os.getenv()` modification + forbid explicitly
9. ✅ Competitive Context insertion location: remove `step_4_research() or` → clarify Step 5 only

**v2.7 Changes (2026-03-09 — UI Mock-up & Code Consistency Pass)**:
1. ✅ UI Design Step 5 Dashboard mock-up competitor replace: Colfax/Penguin etc → nextplatform/servethehome etc (reflect actual constants)
2. ✅ UI Design Step 5 header fix: `👁️ VIEW COMPETITIVE ANALYSIS` → `📊 COMPETITIVE ANALYSIS` + reflect tab entry style
3. ✅ Error Handling Step 5 code tab wrapping add: structure with `with tab_article:` / `with tab_competitors:` blocks
4. ✅ Phase 0 Imports remove `import time` (unused — exponential backoff handled inside `_call()`)
5. ✅ Step 4 success message mock-up unified to actual code format (multiline bullet → single line st.success)

**v2.8 Changes (2026-03-09 — Final Consistency Pass)**:
1. ✅ Strategy 2 expander example competitor replace: `Colfax Research` → `The Next Platform` (reflect actual constants)
2. ✅ Phase 2 JSON example key replace: `"colfax"` → `"nextplatform"` (reflect actual constants)
3. ✅ Final Summary table JSON Path fix: `Via st.secrets (Method 3)` → `Via BASE_DIR absolute path constants`
4. ✅ Final Summary table Button Icons fix: `📥 vs 👁️` → `📥 (Step 4 button) / 📊 (Step 5 tab)` (reflect tab style)
5. ✅ Error Handling Phase 2 URL validation exception type fix: `TimeoutError/ConnectionError` → `ValueError/Exception` (urlparse only)
6. ✅ Changelog order sort: move v2.7 items after v2.6 (v2.3 → v2.4 → v2.5 → v2.6 → v2.7 → v2.8 order)

**v2.9 Changes (2026-03-09 — Parameter & Handler Correctness Pass)**:
1. ✅ `render_competitors_dashboard()` parameter name fix: `competitors_dict` → `category_data` + add required comment for `.get("competitors", {})`
2. ✅ Phase 0 button handler `finally` block add: move `collection_in_progress = False` to finally (prevent permanent disable on exception)
3. ✅ Phase 0 button handler `else` branch add: show `st.info("ℹ️ Don't worry...")` when `result is None`
4. ✅ Phase 0 handler add warning comment: "Error Handling section version must be used"

**v2.10 Changes (2026-03-09 — Handler & Snippet Consistency Pass)**:
1. ✅ Key Technologies remove `Pandas for Excel` — Excel Export explicitly outside Phase 1.0 scope
2. ✅ Phase 1 button handler add `else: st.info(...)` — unify with canonical Error Handling version
3. ✅ Phase 1 button handler fix `st.error()` → `st.warning()` — all 3 places same message level
4. ✅ `load_competitors_for_category()` usage example add `render_competitors_dashboard()` call — prevent missing render after selectbox selection

**v2.11 Changes (2026-03-09 — Validation Call & Checklist Accuracy Pass)**:
1. ✅ `collect_competitor_articles()` code add `_validate_competitor_config()` call — clarify validation call missing from code despite being in notes
2. ✅ Phase 0 checklist remove `prompt_version: "1.0"` — non-existent field not in implementation code metadata dict. Specify actual 4 fields
3. ✅ Phase 0 auto-handle explanation fix — "auto-load default_competitors.json" → clarify `load_competitors_data()` 3rd fallback handles it, forbid direct load inside function

**v2.12 Changes (2026-03-09 — API Key & Edge Case Accuracy Pass)**:
1. ✅ `collect_competitor_articles()` API key not set handling fix: `raise ValueError` → `st.warning()` + `return None` (predictable condition — UX consistency, unify with Phase 0 comment and Edge Case 1 expected)
2. ✅ Edge Case 5 description fix: `load_competitors_data() returns None` → `catches ValueError → tries default fallback → returns None if default also fails` (clarify 3-step fallback flow)

**v2.13 Changes (2026-03-09 — Context Injection & Call Order Pass)**:
1. ✅ `build_competitive_context()` empty context injection bug fix: return `""` if no actual competitor lines after loop — prevent header+instruction only injection
2. ✅ `build_competitive_context()` fix `a["title"]` → `a.get("title", "")` defensive approach
3. ✅ `collect_competitor_articles()` `_validate_competitor_config()` call order fix: move after `if not category` check — skip unnecessary config validation if category not selected

**v2.14 Changes (2026-03-09 — Article Generator Signature Pass)**:
1. ✅ File Structure add `generate_article_claude()` / `generate_article()` modification items — specify below `_do_generate()`
2. ✅ Phase 1 checklist add `generate_article_claude()` / `generate_article()` signature + prompt injection items — prevent missing `competitive_context` reflection. Specify backward compatible pattern when empty string

**v2.5 Changes (2026-03-09 — UI Consistency & Logic Fixes)**:
1. ✅ Revised Architecture diagram update to tab style (remove button style)
2. ✅ Button Distinction → replace with UI element distinction section (reflect Step 5 tab style)
3. ✅ Phase 1 checklist selectbox — add `schema_version` key filter (prevent error on selection)
4. ✅ Remove `collection_in_progress` duplication — remove finally block inside function, manage only at call site
5. ✅ `collect_competitor_articles()` return value change: `True/False` → `(companies, articles) / None` (for number display)
6. ✅ Button handler 3 places success message update: include number format `"N companies, M articles"`
7. ✅ `migrate_competitors_schema()` checklist text fix — remove v1.1 support hint, match actual implementation
8. ✅ `_competitor_search_cfg()` add comment: needs verification before implementation (A/B scenario)
9. ✅ `secrets.toml [paths]` section explicitly not needed — BASE_DIR absolute path constants replace

**v2.4 Changes (2026-03-09 — Bug Fixes & Clarifications)**:
1. ✅ `datetime` import fix: `import datetime` → `from datetime import datetime` (prevent AttributeError)
2. ✅ `load_competitors_data()` 1st cache bug fix: `in` check → `is not None` check (prevent `_init()` None initialization conflict)
3. ✅ `dedup_articles()` add date sorting: sort by date descending after dedup (resolve spec-implementation mismatch)
4. ✅ `migrate_competitors_schema()` remove dead code: delete empty v1.1 branch, simplify unsupported version handling
5. ✅ `fetch_articles_for_competitor()` prompt date dynamicize: `"2025-2026"` → `{current_year-1}-{current_year}`
6. ✅ Article Collection Guidelines strategy clarify: resolve batch vs individual confusion (specify per-competitor 1 API call style)
7. ✅ `st.tabs()` add pre-implementation verification comment: specify actual tab name validation needed
8. ✅ `render_article()` verification items specify: clarify actions via A/B scenario
9. ✅ `default_competitors.json` add dual management warning: specify need to sync both

**Document Version**: 2.14 (Article Generator Signature Pass)
**Last Updated**: 2026-03-09
