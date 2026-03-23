# TechBlog Automator — Changelog & Getting Started Guide

## Recent Changes (2026-03-23)

### Frontend Rewrite: Workflow API + SSE Integration
- **`src/lib/api.ts`** — Complete rewrite: 4 old REST endpoints replaced with 3 workflow-based functions
  - `startWorkflow(category)` → `POST /api/workflow/start` (returns thread_id)
  - `resumeWorkflow(thread_id, response)` → `POST /api/workflow/resume` (sends HITL feedback)
  - `getWorkflowState(thread_id)` → `GET /api/workflow/state/{thread_id}` (polling fallback)
- **`src/App.tsx`** — Complete rewrite as useReducer workflow controller
  - Action-based state management (`WORKFLOW_STARTED`, `PHASE_START`, `PROGRESS`, `HITL_WAITING`, `HITL_RESUMED`, `COMPLETE`, `ERROR`, `RESET`)
  - SSE subscription via `subscribeWorkflow()` with typed event handlers
  - Automatic HITL component routing (6 components based on `hitlStep`)
  - ConnectionBanner integration for SSE reconnection feedback
  - WorkflowProgress header with phase/step indicator
  - Framer Motion animations for screen transitions
- **Test fixes** — Updated FinalApproval.test.tsx and DraftEditor.test.tsx for type safety
- **Build verification** — Full TypeScript build passes ✅

### What Changed in Frontend Architecture

| Aspect | Before (v1) | After (v2) |
|--------|------------|-----------|
| **State management** | `useState` with 5 steps | `useReducer` with 8 actions |
| **API communication** | 4 simple REST endpoints | 3 workflow-based endpoints + SSE streaming |
| **Real-time updates** | None (request-response only) | SSE events: `phase_start`, `progress`, `hitl_waiting`, `complete`, `error` |
| **HITL components** | Not integrated | Auto-routed based on `hitlStep` (6 components) |
| **Session recovery** | None | Thread ID persists across SSE reconnects |
| **Error handling** | Basic try-catch | Full error state + reconnection logic with exponential backoff |

---

## Previous Changes (2026-03-20)

### SSE Error Recovery
- `src/lib/sse.ts` — Exponential-backoff reconnection (1s → 2s → 4s → 8s → 16s, max 5 retries)
- `src/components/common/ConnectionBanner.tsx` — Reconnecting/reconnected status banner UI
- `src/App.tsx` — `connBanner` state integration with `onReconnecting`/`onReconnected` callbacks
- Terminal SSE events (`hitl_waiting`, `complete`, `error`) close intentionally without triggering retry

### Markdown Export (FinalApproval)
- `draftToMarkdown()` — Converts `DraftArticle` to Markdown with optional YAML frontmatter
- Clipboard copy (`navigator.clipboard.writeText`) with "Copied!" feedback (2s timeout)
- `.md` file download via Blob + anchor click pattern (slug from metadata or title)

### Test Infrastructure
- **Frontend (Vitest)**: 39 tests across 4 HITL component test files
  - `vitest.config.ts` — jsdom environment, v8 coverage provider
  - `src/test/setup.ts` — `@testing-library/jest-dom` setup
  - Tests: TopicSelect (8), OutlineEditor (7), DraftEditor (11), FinalApproval (13)
- **Backend (pytest)**: 52 tests across 5 test modules
  - `pytest.ini` — `asyncio_mode = auto`
  - `backend/requirements-dev.txt` — pytest + pytest-asyncio
  - `backend/tests/conftest.py` — shared fixtures (client patching, in-memory SQLite)
  - Tests: utils (15), search (7), outline (4), nodes (16), workflow_api (9)

---

## Table of Contents

1. [What Changed: v1 → v2](#what-changed-v1--v2)
2. [Architecture](#architecture)
3. [Workflow](#workflow)
4. [Tech Stack](#tech-stack)
5. [Getting Started (Installation & Running)](#getting-started-installation--running)

---

## What Changed: v1 → v2

| Item | v1 | v2 |
|------|----|----|
| Backend | Express.js (`server.js`) | Python FastAPI (`backend/main.py`) |
| Workflow engine | None (simple API call chain) | **LangGraph** (per-phase state management + checkpointing) |
| Main AI model | Gemini 2.5 Flash (Express) | Gemini 2.5 Pro (FastAPI) |
| QA AI | Run separately in Streamlit (`techaudit_agent.py`) | Integrated as **Phase 4** node — Claude runs automatically |
| User interaction | 5-step linear wizard (forward only) | **7 HITL checkpoints** (review, edit, or re-run at every step) |
| Real-time communication | REST API (request-response) | **SSE** (Server-Sent Events) — live progress streaming |
| Session recovery | None (page refresh resets everything) | LangGraph checkpointer — **restores session after browser refresh** |
| Streamlit | Primary QA tool | Legacy (kept for reference); core logic ported to FastAPI |
| Outline generation | None (topic → article directly) | **New Phase 2** — AI generates a structured outline; human edits before drafting |
| Regeneration strategies | None | On QA failure, choose from 3 strategies: Deep Fix / Balanced Revision / Structural Rewrite |
| Hero image | Generated in Streamlit only | Auto-generated in Phase 4, served via proxy endpoint |

---

## Architecture

### v1

```
React (Vite :5173)
    │
    └── REST API ──→ Express.js (server.js :3001) ──→ Gemini 2.5 Flash
                                                        (Google Search Grounding)

Separate app:
    Streamlit ──→ Gemini 2.5 Pro + Claude
    (techaudit_agent.py)
```

### v2

```
React (Vite :5173)
    │
    ├── SSE (live stream) ──→ FastAPI (backend/main.py :3001)
    │                                │
    │                                └── LangGraph graph
    │                                        ├── Phase 1: Search (Gemini 2.5 Pro + Google Grounding)
    │                                        │   ├── HITL 1a: Topic selection
    │                                        │   ├── HITL 1b: Title selection
    │                                        │   └── HITL 1c: Source approval
    │                                        ├── Phase 2: Outline generation (Gemini)
    │                                        │   └── HITL 2: Outline editing
    │                                        ├── Phase 3: Article draft (Claude first → Gemini fallback)
    │                                        │   └── HITL 3: Draft review
    │                                        └── Phase 4: QA + final approval (Claude)
    │                                            └── HITL 4: Publish approval
    │
    └── REST API ──→ POST /start, POST /resume, GET /state
```

---

## Workflow

### v1: 5-step linear wizard

```
Select category → Select topic → Select theme → Review research → Article complete
(each step is one-way — no going back, no re-running)
```

### v2: 4 Phases + 7 HITL checkpoints

```
Enter category
    ↓
[Phase 1 — Search & Research]
    → Generate 5 topics    → ⏸ HITL 1a: Pick a topic   (can re-search)
    → Generate 5 titles    → ⏸ HITL 1b: Pick a title   (can regenerate)
    → Research 8 sources   → ⏸ HITL 1c: Approve sources (can re-search)
    ↓
[Phase 2 — Outline Generation]  ← New in v2
    → Generate outline     → ⏸ HITL 2: Add/remove/reorder sections (can regenerate)
    ↓
[Phase 3 — Article Draft]
    → Write with Claude (auto-fallback to Gemini if credits exhausted)
    → ⏸ HITL 3: Edit directly or request regeneration
    ↓
[Phase 4 — QA & Final Approval]
    → Claude runs automated quality check + rubric scoring (6 criteria)
    → Hero image auto-generated
    → ⏸ HITL 4: Review QA results, pick a regeneration strategy or approve for publishing
    ↓
[Published]
```

**Key differences from v1:**
- Every HITL step supports **going back and re-running** (v1 was forward-only)
- Phase 1 gates topic → title → source sequentially, preventing wasted API calls
- Phase 4 offers 3 targeted regeneration strategies when QA fails

---

## Tech Stack

### Backend

| Item | v1 | v2 |
|------|----|----|
| Language / framework | Node.js / Express.js | Python / FastAPI |
| Workflow | None | LangGraph (StateGraph + MemorySaver checkpointer) |
| Real-time | None (polling) | SSE (`sse-starlette`) |
| Article generation AI | Gemini 2.5 Flash | Claude first → Gemini 2.5 Pro fallback |
| Search AI | Gemini 2.5 Flash + Google Grounding | Gemini 2.5 Pro + Google Grounding |
| QA AI | Run separately in Streamlit | Claude (built into Phase 4 node) |
| State persistence | None (stateless per request) | LangGraph checkpointer (in-memory; SQLite/Postgres for production) |
| Entry point | `node server.js` | `uvicorn backend.main:app --reload --port 3001` |

### Frontend

| Item | v1 | v2 |
|------|----|----|
| State management | `useState` (single App.tsx file) | `useReducer` + split components |
| API communication | `fetch` (REST) | SSE (`EventSource`) + REST |
| UI structure | All steps in one App.tsx | Split into focused components (`hitl/`, `common/`) |
| New components | — | `TopicSelect`, `TitleSelect`, `SourceReview`, `OutlineEditor`, `DraftEditor`, `FinalApproval`, `WorkflowProgress`, `PhasePanel` |

### Python dependencies (new in v2)

```
langgraph>=0.4        # Workflow orchestrator
fastapi>=0.115        # API server (replaces Express)
uvicorn[standard]     # ASGI server
google-genai>=1.10.0  # Gemini API
anthropic>=0.40.0     # Claude API
sse-starlette         # SSE streaming
httpx                 # Async HTTP for image proxy
python-dotenv         # Environment variables
pydantic>=2.0         # Data validation
```

---

## Tool & Graph Architecture

### Tool Modules (`backend/tools/`)

#### `search.py` — Search & Research
| Function | Description |
|---|---|
| `fetch_topics(client, category)` | Fetches 5 trending technical topics for a category using Google Search Grounding |
| `fetch_titles(client, topic)` | Generates 5 SEO-optimized article title options for a topic |
| `deep_research(client, title)` | Collects 8 high-authority sources (Tier 1–4) with grounding verification |
| `_build_notebooklm_context(client, title, sources)` | Synthesizes 8 sources into a knowledge base (consensus, conflicts, gaps, key data points) |

#### `outline.py` — Outline Generation _(new in v2)_
| Function | Description |
|---|---|
| `generate_outline(client, title, search_results, notebooklm_context)` | Generates a structured JSON outline: `sections[]`, `comparison`, `anti_recommendation`, `tco_analysis` |

#### `article.py` — Article Generation
| Function | Description |
|---|---|
| `generate_article(client, title, sources, context)` | Generates article using Gemini (primary or fallback) |
| `generate_article_claude(anthropic_client, title, accepted_sources, all_sources, context, qa_feedback)` | Generates article using Claude with Sonnet fallback; supports QA feedback injection |
| `do_generate(...)` | Orchestrator: Claude first → Gemini fallback on credit error. Returns `GenerationResult` |

`GenerationResult` fields: `article`, `actual_writer`, `fallback_reason`, `model_used`, `claude_model_used`, `gen_error`

#### `qa.py` — Quality Assurance
| Function | Description |
|---|---|
| `run_comprehensive_qa(art)` | Runs 10 programmatic quality checks across Structure / Evidence / Critical Analysis / Technical Depth / Style |
| `score_article_rubric(client, art)` | Gemini scores the article on each rubric criterion (0.0–10.0) |
| `_generate_rerun_strategies(qa_checks)` | Returns up to 3 targeted regeneration strategies based on failed checks |
| `_article_to_markdown(art)` | Converts article JSON to Markdown for rubric scoring input |

**10 QA Checks:**

| Category | Check |
|---|---|
| Structure | Word count 1,000–1,500 |
| Structure | Executive summary ~100 words (±20) |
| Structure | At least 3 body sections |
| Evidence | Source citations `[N]` ≥ 3 |
| Evidence | Quantitative claims paired with citations ≥ 3 |
| Critical Analysis | Comparison section with ≥ 2 alternatives |
| Critical Analysis | Anti-recommendation section > 50 words |
| Critical Analysis | TCO analysis section > 50 words |
| Technical Depth | Physical constraints addressed (thermal/power/scaling) ≥ 2 keywords |
| Style | No bullet points — paragraph format only |

**3 Regeneration Strategies (on QA failure):**
- 🎯 **Deep Fix** — concentrate entirely on the category with the most failures
- ⚖️ **Balanced Revision** — spread fixes evenly across all failing categories
- 🔄 **Structural Rewrite / Citation Fix** — full structural rewrite if structure fails; citation strengthening otherwise

#### `image.py` — Hero Image
| Function | Description |
|---|---|
| `hero_image_url(title)` | Returns a Pollinations.ai Flux hero image URL for the article title (1400×500px, dark/indigo/cyan style) |
| `pollinations_url(prompt, w, h, seed)` | Builds a Pollinations.ai URL from a prompt (no API key required) |
| `_seed(text)` | MD5-based deterministic seed from title text |

---

### LangGraph Graph (`backend/graph/`)

12 nodes total: **6 exec nodes** + **6 HITL nodes**, organized into 4 phases.

#### Node Map

| Phase | Exec Node | HITL Node | Tools Called |
|---|---|---|---|
| 1 — Research | `topics` | `hitl_topics` | `fetch_topics()` + Google Search |
| 1 — Research | `titles` | `hitl_titles` | `fetch_titles()` |
| 1 — Research | `research` | `hitl_sources` | `deep_research()` → `_build_notebooklm_context()` |
| 2 — Outline _(new)_ | `outline` | `hitl_outline` | `generate_outline()` |
| 3 — Draft | `draft` | `hitl_draft` | `do_generate()` → Claude / Gemini |
| 4 — QA & Final | `qa` | `hitl_final` | `run_comprehensive_qa()` · `score_article_rubric()` · `_generate_rerun_strategies()` · `hero_image_url()` |

#### Flow & Regeneration Loops

```
topics → ⏸hitl_topics →approve→ titles → ⏸hitl_titles →approve→ research → ⏸hitl_sources
  ↑ regen ┘                        ↑ regen ┘                         ↑ regen ┘
           →approve→ outline → ⏸hitl_outline →approve→ draft → ⏸hitl_draft →approve→ qa → ⏸hitl_final →approve→ END
                        ↑ regen ┘                        ↑ regen ┘                    ↑ regen (→ draft) ┘
```

Each HITL node uses LangGraph `interrupt()` to pause the graph and wait for a `Command(resume=...)` from the frontend.

#### Routing Logic

| HITL Node | `approve` → | `regenerate` → |
|---|---|---|
| `hitl_topics` | `titles` | `topics` (re-fetch topic list) |
| `hitl_titles` | `research` | `titles` (same topic, new titles) |
| `hitl_sources` | `outline` | `research` (re-collect 8 sources) |
| `hitl_outline` | `draft` | `outline` (regenerate outline) |
| `hitl_draft` | `qa` | `draft` (regenerate with feedback / strategy) |
| `hitl_final` | `END` | `draft` (regenerate with QA strategy) |

#### Implementation Notes
- All nodes are `async def`; synchronous tool calls are wrapped in `asyncio.to_thread()` to avoid blocking the event loop
- `node_draft` injects `selected_strategy.guidance` (from HITL 4) or `human_feedback` (from HITL 3) as `qa_feedback` into `do_generate()`
- `node_qa` runs QA, rubric scoring, strategy generation, and hero image URL in a single node to allow independent re-execution
- Checkpointer: `MemorySaver` (dev) — replace with `SqliteSaver` or `PostgresSaver` for production

---

## Getting Started (Installation & Running)

### Prerequisites

- **Node.js** 18+ ([nodejs.org](https://nodejs.org))
- **Python** 3.11+ ([python.org](https://python.org))
- **Gemini API key** (free — [Google AI Studio](https://aistudio.google.com/app/apikey))
- **Anthropic API key** (optional — [console.anthropic.com](https://console.anthropic.com); used for Phase 3 article generation. Without it, Gemini handles generation automatically)

---

### Step 1: Navigate to the project

```bash
cd blog_workflow
```

---

### Step 2: Create the environment file

Create a `.env` file inside `blog_workflow/`:

```
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

> `ANTHROPIC_API_KEY` is optional. Without it, article generation falls back to Gemini and everything still works.

---

### Step 3: Install frontend dependencies

```bash
# Run from blog_workflow/
npm install
```

---

### Step 4: Set up Python virtual environment and install backend

```bash
# Run from blog_workflow/

# Create virtual environment (once only)
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install packages
pip install -r backend/requirements.txt
```

---

### Step 5: Run both servers (two terminals required)

**Terminal 1 — Frontend (Vite)**
```bash
# From blog_workflow/ — no virtual environment needed
npm run dev
# → opens at http://localhost:5173
```

**Terminal 2 — Backend v2 (FastAPI + LangGraph)**
```bash
# From blog_workflow/ — activate virtual environment first
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

uvicorn backend.main:app --reload --port 3001
# → API server running at http://localhost:3001
```

---

### Verify it's running

- Frontend: `http://localhost:5173`
- Backend health check: `http://localhost:3001/health`

---

### Directory overview

```
blog_workflow/
├── .env                    ← Create this yourself (API keys)
├── package.json            ← npm dependencies (frontend + legacy Express server)
├── backend/                ← New in v2: Python FastAPI + LangGraph
│   ├── requirements.txt    ← pip dependencies
│   ├── main.py             ← FastAPI entry point
│   ├── config.py           ← Model constants, rubric criteria
│   ├── clients.py          ← Gemini/Claude client singletons
│   ├── store.py            ← In-memory session store
│   ├── tools/              ← AI tool functions (search, article, QA, image)
│   ├── graph/              ← LangGraph graph definition
│   └── api/                ← FastAPI routers
├── src/                    ← React frontend
│   ├── App.tsx             ← v2 main app (workflow flow controller)
│   ├── lib/
│   │   ├── api.ts          ← REST API client
│   │   └── sse.ts          ← SSE client
│   ├── components/
│   │   ├── hitl/           ← 7 HITL UI components
│   │   └── common/         ← Shared components
│   └── types/workflow.ts   ← TypeScript type definitions
└── package.json            ← npm dependencies (frontend only)
```

---

### FAQ

**Q. What happens if I don't have `ANTHROPIC_API_KEY`?**
Phase 3 article generation automatically falls back to Gemini 2.5 Pro. Everything works fine.

**Q. Does a page refresh lose my progress?**
v2 uses LangGraph checkpointing to preserve session state. However, the current development build uses in-memory storage — restarting the server will reset all sessions.
