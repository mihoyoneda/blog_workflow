#!/usr/bin/env bash
# setup.sh — Validate environment and install all dependencies
# Usage: bash scripts/setup.sh
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
fail() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo "═══════════════════════════════════════"
echo "   Blog Workflow — Setup & Validation"
echo "═══════════════════════════════════════"

# ── 1. Node.js ────────────────────────────────────────────────
if ! command -v node &>/dev/null; then
  fail "Node.js not found. Install from https://nodejs.org/ (v18+)"
fi
NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
[ "$NODE_VER" -lt 18 ] && fail "Node.js 18+ required (found: $(node -v))"
ok "Node.js $(node -v)"

# ── 2. Python ─────────────────────────────────────────────────
PYTHON=""
for cmd in python3 python; do
  if command -v "$cmd" &>/dev/null; then
    VER=$("$cmd" -c 'import sys; print(sys.version_info.minor + sys.version_info.major * 10)')
    [ "$VER" -ge 39 ] && PYTHON="$cmd" && break
  fi
done
[ -z "$PYTHON" ] && fail "Python 3.9+ not found. Install from https://www.python.org/"
ok "Python $($PYTHON --version)"

# ── 3. .env file ──────────────────────────────────────────────
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    warn ".env not found — copying from .env.example"
    cp .env.example .env
    warn "Edit .env and add your GEMINI_API_KEY before starting"
  else
    fail ".env file missing. Create it with GEMINI_API_KEY=..."
  fi
else
  grep -q "GEMINI_API_KEY" .env || fail ".env exists but GEMINI_API_KEY is missing"
  ok ".env file"
fi

# ── 4. Frontend ───────────────────────────────────────────────
echo ""
echo "Installing frontend dependencies..."
npm install
ok "Frontend dependencies installed"

# ── 5. Backend venv ───────────────────────────────────────────
echo ""
echo "Setting up Python virtual environment..."
if [ ! -d .venv ]; then
  $PYTHON -m venv .venv
  ok "Created .venv"
else
  ok ".venv already exists"
fi

# Activate and install
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q
pip install -r backend/requirements-dev.txt -q
ok "Backend dependencies installed"

# ── Done ──────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════"
ok "Setup complete!"
echo ""
echo "Next steps:"
echo "  Terminal 1:  npm run dev"
echo "  Terminal 2:  source .venv/bin/activate && uvicorn backend.main:app --reload --port 3001"
echo ""
echo "  Run tests:   npm test"
echo "               pytest"
echo "═══════════════════════════════════════"
