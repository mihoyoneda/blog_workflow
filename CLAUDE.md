# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repo is a **v2 AI-powered tech blog generation tool** built with:

- **Frontend** — React/TypeScript (Vite) with Tailwind CSS v4
- **Backend** — Python FastAPI + LangGraph (4-phase workflow with 7 Human-in-the-Loop checkpoints)
- **AI** — Gemini 2.5 Pro (search, outline, article fallback) + Claude (article generation, QA)

The workflow goes: category → topic select → title select → source approval → outline edit → draft review → QA + final approval → published article.

---

## 🚀 Getting Started (First-Time Setup)

### ✅ Prerequisites

Before you start, ensure you have:

- **Node.js 18+** — Check: `node --version`
  - ✅ Tested with Node.js 18.17.0+, 20.x
- **Python 3.9+** — Check: `python --version` or `python3 --version`
  - ✅ Tested with Python 3.9, 3.10, 3.11, 3.12
  - **⚠️ Windows users:** If `python` doesn't work, use `python3` instead
- **Git** — For version control
- **API Keys** (required):
  - `GEMINI_API_KEY` — [Get from Google AI Studio](https://aistudio.google.com/app/apikeys) *(required)*
  - `ANTHROPIC_API_KEY` (optional) — [Get from Anthropic Console](https://console.anthropic.com/)

**Not installed?**
- [Install Node.js](https://nodejs.org/) (LTS recommended)
- [Install Python](https://www.python.org/downloads/) (3.9+)

**Quick pre-flight check:**
```bash
node --version      # Should show v18+ or v20+
python --version    # Should show 3.9+
# (If above fails, try: python3 --version)
```

### 1️⃣ Clone and Navigate to Project

```bash
# Navigate to the project directory
cd blog_workflow

# Verify you're in the right place
ls -la | grep package.json
```

### 2️⃣ Set Up Environment Variables

You **must** create a `.env` file in the current directory (you should already be in `blog_workflow/`) with your API keys.

**Option A: Using Command Line (Recommended)**

```bash
# On Windows (Command Prompt):
(
echo GEMINI_API_KEY=your_actual_gemini_key
echo ANTHROPIC_API_KEY=your_actual_anthropic_key
) > .env

# On macOS/Linux:
echo "GEMINI_API_KEY=your_actual_gemini_key" > .env
echo "ANTHROPIC_API_KEY=your_actual_anthropic_key" >> .env

# Verify the file was created:
cat .env  # macOS/Linux: or 'type .env' on Windows
```

**Option B: Manual Creation**

1. Open `blog_workflow/` in your file explorer
2. Create a new file named `.env` (note the leading dot)
3. Add these lines:
```
GEMINI_API_KEY=your_actual_gemini_key
ANTHROPIC_API_KEY=your_actual_anthropic_key
```
4. Save and close

**Get your API keys:**
- 🔑 `GEMINI_API_KEY` — [Get from Google AI Studio](https://aistudio.google.com/app/apikeys) *(required)*
- 🔑 `ANTHROPIC_API_KEY` — [Get from Anthropic Console](https://console.anthropic.com/) *(optional but recommended)*

> **⚠️ Important:** `ANTHROPIC_API_KEY` is optional — article generation falls back to Gemini automatically if absent. But having it allows faster generation and better quality.
>
> **🔒 Never commit `.env`** — It's already in `.gitignore`

### 3️⃣ Set Up Frontend (Terminal 1)

```bash
# From blog_workflow/ directory
# Note: npm install may take 2-5 minutes depending on your internet speed
npm install

# Start the development server (runs on http://localhost:5173)
npm run dev
```

**Expected output:**
```
VITE v5.0.0  ready in 150 ms

➜  Local:   http://localhost:5173/
➜  Press q to quit
```

✅ **Success:** Open http://localhost:5173 in your browser.

### 4️⃣ Set Up Backend (Terminal 2, in blog_workflow/)

**⚠️ Important:** This must run in a **separate terminal window** from the frontend. Keep Terminal 1 (frontend) running!

```bash
# Make sure you're in blog_workflow/ directory (you should be from initial setup)
# Create Python virtual environment
# If 'python' doesn't work, replace with 'python3'
python -m venv .venv

# Activate the virtual environment
# ➤ Windows (Command Prompt — RECOMMENDED):
.venv\Scripts\activate
# ➤ Windows (PowerShell):
.venv\Scripts\Activate.ps1
# If above fails with "cannot be loaded" error, try:
# 1. Run in Command Prompt instead (.venv\Scripts\activate)
# 2. Or grant execution permission (requires admin):
#    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
# ➤ macOS/Linux:
source .venv/bin/activate

# Verify activation — prompt should show (.venv) at the start of your prompt
# Then install dependencies
# Note: These commands run from blog_workflow/ directory
pip install --upgrade pip
# Note: Install from backend/requirements.txt (not root requirements.txt)
pip install -r backend/requirements.txt

# Start the FastAPI server (runs on http://localhost:3001)
# Note: This creates workflow_sessions.db automatically on first run
uvicorn backend.main:app --reload --port 3001
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:3001 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Application startup complete
```

✅ **Success:** Backend is ready.
- `workflow_sessions.db` is created automatically to store workflow sessions
- Backend API: http://localhost:3001
- API Documentation: http://localhost:3001/docs
- Frontend should now be able to connect (check Terminal 1's browser for any errors)

### 5️⃣ Verify Everything Works

**Both servers must be running simultaneously!**

| Step | What to Check | Expected Result | URL |
|------|---------------|-----------------|-----|
| 1️⃣ **Frontend** | Browser loads | Welcome page or workflow form | http://localhost:5173 |
| 2️⃣ **Backend API** | API documentation | Swagger UI with endpoints | http://localhost:3001/docs |
| 3️⃣ **Connection** | Create blog post | No CORS errors in console | Start workflow in UI |

**Quick health check:**

Option 1: Use your browser (works everywhere):
- Open http://localhost:5173 in your browser (frontend)
- Open http://localhost:3001/docs in your browser (backend API docs)

Option 2: Command line (Linux/macOS only):
```bash
# In a new terminal (with venv activated):
curl http://localhost:3001/docs  # Should return HTML (backend is running)
curl http://localhost:5173       # Should return HTML (frontend is running)
```

**If something is wrong:**
- ❌ Frontend loads but backend is unreachable → Check Backend Terminal for errors
- ❌ Backend starts but frontend can't connect → Restart both servers
- ❌ Port already in use → See "🔧 Troubleshooting" section

---

## 🔧 Troubleshooting

### Python Command Not Found

**Problem:** `python: command not found` or `python is not recognized`

**Solution:**
```bash
# Try python3 instead of python
python3 --version

# If that works, use python3 for all subsequent commands:
python3 -m venv .venv
# Note: Run this from blog_workflow/ directory
python3 -m pip install -r backend/requirements.txt
uvicorn backend.main:app --reload --port 3001
```

**On Windows:** If neither `python` nor `python3` work:
1. Uninstall and reinstall Python from https://www.python.org/downloads/
2. ✅ Check "Add Python to PATH" during installation
3. Close and reopen Command Prompt/PowerShell
4. Try `python --version` again

---

### npm install Fails

**Problem:** `npm ERR!` or dependency conflict errors during `npm install`

**Why this happens:**
- npm cache may be corrupted or outdated
- Node.js version incompatibility with package versions
- Internet connection interruption while downloading packages
- Platform-specific dependency conflicts (macOS/Windows/Linux differences)
- Insufficient disk space for node_modules (~500MB)

**Solution:**
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and package-lock.json
rm -rf node_modules package-lock.json  # macOS/Linux
# OR on Windows (Command Prompt):
rmdir /s /q node_modules
del package-lock.json

# Verify Node.js version (should be 18+)
node --version

# Try installing again
npm install
```

**If still failing:**
- Update npm: `npm install -g npm@latest`
- Check Node.js version: Must be 18+ (download from https://nodejs.org/)
- Check internet connection — npm needs to download dependencies

---

### Port Already in Use

If you see `Address already in use` error:

**For port 5173 (Frontend):**
```bash
# Find process using port 5173
# Windows:
netstat -ano | findstr :5173
# macOS/Linux:
lsof -i :5173

# Kill the process (replace PID with actual process ID)
# Windows: taskkill /PID {PID} /F
# macOS/Linux: kill -9 {PID}

# Or just use a different port:
npm run dev -- --port 5174
```

**For port 3001 (Backend):**
```bash
uvicorn backend.main:app --reload --port 3002
```

### ModuleNotFoundError / pip install fails

```bash
# Make sure you activated the venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Verify the prompt shows (.venv)
# Then reinstall:
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### `.env` File Issues

**Problem:** `GEMINI_API_KEY not found` or API key errors

**Step 1: Verify .env file exists**
```bash
# From blog_workflow/ directory:
cat .env          # macOS/Linux
type .env         # Windows

# Should show:
# GEMINI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

**Step 2: If file is missing or empty**
```bash
# Recreate it (replace with your actual keys):
echo "GEMINI_API_KEY=your_actual_key_here" > .env
echo "ANTHROPIC_API_KEY=your_actual_key_here" >> .env

# Verify:
cat .env  # Should show both keys
```

**Step 3: Verify file is in correct location**
```bash
# From blog_workflow/ directory:
ls -la .env       # macOS/Linux
dir .env          # Windows

# Should show: .env exists in blog_workflow/ root (not in backend/ or src/)
```

**Step 4: Restart backend**
```bash
# Stop backend (Ctrl+C in Terminal 2)
# Restart it:
uvicorn backend.main:app --reload --port 3001
```

### Frontend can't connect to Backend (CORS error)

1. Ensure backend is running on port 3001
2. Check browser console for error details
3. Restart both servers (Ctrl+C in each terminal, then run again)

---

### Backend Starts But API Returns 401/403 Errors

**Problem:** Backend runs but API calls fail with authentication errors

**Solution:**
```bash
# Verify .env file has valid keys
cat .env  # macOS/Linux: or 'type .env' on Windows

# Check if keys are correct (should not be empty)
# Keys should look like: GEMINI_API_KEY=AIzaSy...

# Test your API keys:
# 1. Gemini API key:
#    Visit https://aistudio.google.com/app/apikeys
#    Verify the key is ACTIVE and not ROTATED

# 2. Anthropic API key (if using):
#    Visit https://console.anthropic.com/
#    Verify the key is ACTIVE

# Restart backend after updating keys
# Stop backend (Ctrl+C in Terminal 2)
uvicorn backend.main:app --reload --port 3001
```

**If problem persists:**
- Check you're using correct API keys (not accidentally pasted extra spaces)
- Check API keys haven't been rotated in the provider console
- Check rate limits aren't exceeded on your API accounts

---

### Tests Failing

**Problem:** `npm test` or `pytest` fails

**Frontend tests (npm test):**
```bash
# Make sure all dependencies are installed
npm install

# Run tests in verbose mode to see what's failing
npm test -- --reporter=verbose

# Or run a specific test file
npm test TopicSelect.test.tsx
```

**Backend tests (pytest):**
```bash
# Make sure venv is activated
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Make sure dev dependencies are installed
pip install -r backend/requirements-dev.txt

# Run tests in verbose mode
pytest -v

# Run a specific test file
pytest backend/tests/test_utils.py -v
```

**Common issues:**
- ❌ `ModuleNotFoundError` → Reinstall dev dependencies: `pip install -r backend/requirements-dev.txt`
- ❌ `No module named 'pytest'` → Make sure venv is activated
- ❌ `npm test` shows "No tests found" → Check node_modules is present: `npm install`

---

## 📚 Development Commands

### Frontend

```bash
# From blog_workflow/ directory

npm run dev          # Start dev server (http://localhost:5173)
npm run build        # Build for production
npm run lint         # Run ESLint
npm test             # Run tests (Vitest)
npm run test:watch   # Run tests in watch mode
npm run test:coverage  # Run tests with coverage
```

### Backend

```bash
# From blog_workflow/ directory, with venv activated

# Development server with auto-reload
uvicorn backend.main:app --reload --port 3001

# Run tests
pip install -r backend/requirements-dev.txt  # First time only
pytest

# Run tests with coverage
pytest --cov=backend
```

---

## 🔬 Advanced Topics & Architecture

> **Note:** This section is for understanding how the application works. You don't need to read this to get started.

## Architecture

### Data Flow

```
React (Vite :5173)
    │
    ├── SSE ──→ GET /api/workflow/stream/{thread_id}   ← sole graph execution entry point
    ├── POST    /api/workflow/start                    ← creates thread_id, stores initial input
    └── POST    /api/workflow/resume                   ← stores HITL response for SSE reconnect
                        │
                    FastAPI (:3001)
                        │
                    LangGraph graph
                        ├── node_topics    → HITL 1a (topic select)
                        ├── node_titles    → HITL 1b (title select)
                        ├── node_research  → HITL 1c (source approval)
                        ├── node_outline   → HITL 2  (outline edit)
                        ├── node_draft     → HITL 3  (draft review)
                        ├── node_qa        → HITL 4  (final approval)
                        └── END
```

### SSE + HITL cycle

1. `POST /start` → `{thread_id}`
2. `GET /stream/{thread_id}` → SSE opens, `astream_events()` runs the graph
3. `GraphInterrupt` → SSE yields `hitl_waiting` → stream closes
4. `POST /resume` → HITL response stored in `pending_resumes`
5. `GET /stream/{thread_id}` → SSE reopens, graph resumes with `Command(resume=...)`
6. Repeat until `complete`

### SSE Error Recovery

`src/lib/sse.ts` implements exponential-backoff reconnection:
- On network error: retries 1s → 2s → 4s → 8s → 16s (max 5 attempts)
- `ConnectionBanner` component shows reconnecting/reconnected status below the header
- Terminal events (`hitl_waiting`, `complete`, `error`) close intentionally — no retry
- After 5 failed attempts, falls back to error state with "please refresh" message

### Key Tech Choices

- **LangGraph** `interrupt()` + `MemorySaver` checkpointer — HITL pause/resume and session persistence
- **`graph.astream_events(version="v2")`** is the only execution path — never mix with `ainvoke()`
- **`backend/store.py`** holds `pending_inputs` / `pending_resumes` dicts shared between `workflow.py` and `stream.py`
- **Tailwind CSS v4** via `@tailwindcss/vite` plugin (no `postcss.config.js`)
- **Framer Motion** `AnimatePresence` with `mode="wait"` for transitions
- **KaTeX** renders LaTeX math (`remark-math` + `rehype-katex`)
- Article generation: Claude first → Gemini fallback on credit exhaustion (`_is_credit_error`)
- Hero image stored as URL in `BlogState`, not bytes — avoids checkpointer bloat; served via `/api/image/hero/{thread_id}` proxy

## Directory Structure

```
blog_workflow/
├── backend/
│   ├── main.py          # FastAPI entry point
│   ├── config.py        # Model constants, RUBRIC_CRITERIA
│   ├── clients.py       # Gemini/Claude singletons
│   ├── store.py         # pending_inputs / pending_resumes
│   ├── tools/           # AI tool functions (search, outline, article, qa, image, utils)
│   ├── graph/
│   │   ├── state.py     # BlogState TypedDict
│   │   ├── nodes.py     # All phase + HITL nodes (async def)
│   │   └── builder.py   # StateGraph assembly + compile
│   └── api/
│       ├── workflow.py  # POST /start, /resume, GET /state
│       ├── stream.py    # GET /stream/{thread_id} — SSE
│       ├── image_proxy.py
│       └── health.py
├── src/
│   ├── App.tsx          # Workflow controller (useReducer)
│   ├── lib/
│   │   ├── api.ts       # startWorkflow, resumeWorkflow, getWorkflowState
│   │   └── sse.ts       # EventSource wrapper
│   ├── components/
│   │   ├── hitl/        # TopicSelect, TitleSelect, SourceReview, OutlineEditor, DraftEditor, FinalApproval
│   │   └── common/      # MarkdownPreview, FeedbackInput, ConnectionBanner
│   ├── test/setup.ts    # Vitest setup (@testing-library/jest-dom)
│   └── types/workflow.ts
├── vitest.config.ts     # Vitest config (jsdom, v8 coverage)
├── pytest.ini           # pytest config (asyncio_mode=auto)
└── package.json
```

## Testing

### Frontend Tests (Vitest)

```bash
# From blog_workflow/ directory

npm test               # Run all tests once
npm run test:watch     # Run tests in watch mode (re-runs on file change)
npm run test:coverage  # Run tests and show coverage report
```

**Test files** (`src/components/hitl/`):
- `TopicSelect.test.tsx` — selection, regeneration, disabled state
- `OutlineEditor.test.tsx` — heading/key point editing, feedback
- `DraftEditor.test.tsx` — preview/edit mode, approve/regenerate
- `FinalApproval.test.tsx` — QA display, copy/download, strategy selection

**Coverage:** 39 tests across 4 HITL components

### Backend Tests (pytest)

```bash
# From blog_workflow/ directory, with venv activated

# First time: install dev dependencies
pip install -r backend/requirements-dev.txt

# Run all tests
pytest

# Run with coverage report
pytest --cov=backend

# Run specific test file
pytest backend/tests/test_utils.py

# Run in verbose mode
pytest -v
```

**Test files** (`backend/tests/`):
- `test_utils.py` — `_parse_json`, `_extract_text`
- `test_search.py` — `fetch_topics`, `fetch_titles`, user direction injection
- `test_outline.py` — `generate_outline`, prompt verification
- `test_nodes.py` — all HITL and exec nodes (interrupt/resume cycle)
- `test_workflow_api.py` — API endpoints (start, resume, state)

**Coverage:** 52 tests across 5 modules

---

## 📋 Quick Reference Cheat Sheet

### Initial Setup (One-time)

```bash
# Navigate to project root
cd blog_workflow

# Add API keys to .env (create the file with your keys)

# Install frontend dependencies (may take 2-5 minutes)
npm install

# Set up Python virtual environment
python -m venv .venv

# Activate venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt
```

### Daily Development

**⚠️ Important: Open TWO separate terminal windows**

**Terminal 1 (Frontend) — Start this FIRST:**
```bash
# (You should already be in blog_workflow/ from initial setup)
npm run dev

# Expected:
# ➜  Local:   http://localhost:5173/
# ➜  Press q to quit
```

**Terminal 2 (Backend) — Start this SECOND:**
```bash
# Navigate to blog_workflow/ (if using a fresh terminal)
cd blog_workflow

# Activate venv (only needed once per terminal session)
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Start backend
uvicorn backend.main:app --reload --port 3001

# Expected:
# INFO:     Uvicorn running on http://127.0.0.1:3001
# INFO:     Application startup complete
```

**✅ Ready to use:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:3001/docs

### Important URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | React app |
| Backend API | http://localhost:3001 | FastAPI |
| API Docs | http://localhost:3001/docs | Swagger UI |
| Health Check | http://localhost:3001/health | Backend status (returns `{"status": "ok"}`) |

### Common Tasks

```bash
# Run frontend tests
npm test

# Run backend tests with venv activated
pytest --cov=backend

# Build for production
npm run build

# Check code quality
npm run lint
```

---

## 🍎 macOS User Guide

> Complete setup guide optimized for macOS (Intel and Apple Silicon M1/M2/M3)

### Prerequisites for macOS

**Check your Mac:**
```bash
# Check CPU type (Intel vs Apple Silicon)
uname -m
# Result: x86_64 (Intel) or arm64 (Apple Silicon)

# Check current shell
echo $SHELL
# Newer Macs: /bin/zsh
# Older Macs: /bin/bash
```

### Installation via Homebrew (Recommended)

Homebrew makes installation much easier on macOS:

```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Add Homebrew to your PATH if using Apple Silicon
# (add these lines to ~/.zshrc or ~/.bash_profile)
# export PATH="/opt/homebrew/bin:$PATH"

# Install Node.js (includes npm)
brew install node

# Install Python
brew install python

# Verify installations
node --version    # Should show v18+
python3 --version # Should show 3.9+
npm --version     # Should show 8+
```

### Apple Silicon (M1/M2/M3) Specific Notes

If you're using Apple Silicon Mac:

```bash
# Most packages work fine on M1/M2/M3, but some may need ARM64 versions
# If you encounter "No matching architecture" errors:

# 1. Check if package is available for ARM64
npm install --verbose

# 2. If dependencies fail, try Rosetta emulation
# Open Terminal → Get Info → Check "Open using Rosetta"

# 3. Or use architecture-specific Python:
arch -arm64 python3 -m venv .venv
```

### Full macOS Setup (Copy & Paste)

```bash
# 1. Navigate to project
cd blog_workflow

# 2. Create .env file
cat > .env << EOF
GEMINI_API_KEY=your_actual_gemini_key
ANTHROPIC_API_KEY=your_actual_anthropic_key
EOF

# 3. Verify .env was created
cat .env

# 4. Install frontend (Terminal 1)
npm install
npm run dev

# 5. In a NEW terminal (Terminal 2)
# Create Python venv
python3 -m venv .venv

# Activate venv
source .venv/bin/activate

# Install backend dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt

# Start backend
uvicorn backend.main:app --reload --port 3001
```

### Common macOS Issues

**Issue: "command not found: python3"**
```bash
# Python may not be installed via Homebrew
brew install python

# Or check if it's in a different location
which python3
```

**Issue: "Permission denied" on .venv scripts**
```bash
# Make scripts executable (shouldn't be necessary, but try if needed)
chmod +x .venv/bin/activate
```

**Issue: M1 Mac - "No module named '_bz2'"**
```bash
# This is a known issue with some Python packages on M1
# Reinstall Python via Homebrew:
brew install python@3.11
python3.11 -m venv .venv
```

**Issue: Port already in use on macOS**
```bash
# Find process using port 5173
lsof -i :5173

# Kill the process (replace PID with actual number)
kill -9 <PID>

# Or use different port
npm run dev -- --port 5174
```

**Issue: npm cache issues (macOS specific)**
```bash
# Clear npm cache
npm cache clean --force

# If still failing, also clear Homebrew cache
brew cleanup
```

### Shell Configuration (zsh vs bash)

Modern macOS uses **zsh** by default. If you want to use bash:

```bash
# Check current shell
echo $SHELL

# Switch to bash (macOS Catalina+)
chsh -s /bin/bash

# Or use zsh
chsh -s /bin/zsh
```

**Add to ~/.zshrc or ~/.bash_profile if needed:**
```bash
# Add Homebrew to PATH (Apple Silicon)
export PATH="/opt/homebrew/bin:$PATH"

# Python path (if needed)
export PATH="/usr/local/opt/python@3.11/bin:$PATH"
```

### Recommended macOS Development Tools

```bash
# Install Xcode Command Line Tools (required by some packages)
xcode-select --install

# Install Git (if not already installed)
brew install git

# Verify Git
git --version
```

---

## ❓ Need Help?

### Common Issues Quick Map

| Issue | See Section |
|-------|-------------|
| `python: command not found` | "Python Command Not Found" troubleshooting |
| Port 5173 or 3001 already in use | "Port Already in Use" troubleshooting |
| `.env` file not found or empty | ".env File Issues" troubleshooting |
| Backend can't start | "ModuleNotFoundError / pip install fails" |
| Frontend can't connect to Backend | "Frontend can't connect to Backend (CORS error)" |
| Tests failing | See "Testing" section |
| Questions about how it works | See "Architecture" section |

### Still stuck?

1. **Check Terminal output** — Most errors include helpful messages
2. **Restart both servers** — Often fixes connection issues
3. **Verify prerequisites** — Run `node --version`, `python --version`
4. **Check `.env` file** — Ensure it exists and has API keys
5. **Check ports** — Ensure 5173 and 3001 are not already in use
