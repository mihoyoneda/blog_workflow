# Deployment Guide

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 18+ | `node --version` |
| Python | 3.9+ | `python3 --version` |

## Quick Setup

```bash
# macOS / Linux
bash scripts/setup.sh

# Windows (Git Bash)
bash scripts/setup.sh

# Windows (Command Prompt) — manual steps below
```

## Manual Setup

### 1. Environment variables

```bash
cp .env.example .env
# Edit .env — add your GEMINI_API_KEY
```

### 2. Frontend

```bash
npm install
```

### 3. Backend

```bash
# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate

# Windows
python -m venv .venv
.venv\Scripts\activate

pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

## Running the app

Open **two terminals** from the `blog_workflow/` directory:

**Terminal 1 — Frontend:**
```bash
npm run dev
# → http://localhost:5173
```

**Terminal 2 — Backend:**
```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn backend.main:app --reload --port 3001
# → http://localhost:3001/docs
```

## Running tests

```bash
# Frontend (39 tests)
npm test

# Frontend with coverage report
npm run test:coverage

# Backend (52 tests, coverage ≥80% enforced)
pytest

# Both
npm test && pytest
```

## Pre-deployment checklist

- [ ] `npm test` — all frontend tests pass
- [ ] `pytest` — all backend tests pass, coverage ≥ 80%
- [ ] `npm run build` — production build succeeds
- [ ] `npm run lint` — no ESLint errors
- [ ] `.env` contains valid `GEMINI_API_KEY`
- [ ] Both servers start without errors
- [ ] Full workflow runs end-to-end in browser

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python: command not found` | Use `python3` instead |
| Port 5173 in use | `npm run dev -- --port 5174` |
| Port 3001 in use | `uvicorn backend.main:app --reload --port 3002` |
| `ModuleNotFoundError` | Re-activate venv, then `pip install -r backend/requirements.txt` |
| CORS error in browser | Ensure backend is running on port 3001 |
| `npm test` fails — vitest not found | Run `npm install` first |
| `pytest --cov` fails | Run `pip install -r backend/requirements-dev.txt` |
