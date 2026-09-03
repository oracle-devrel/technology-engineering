#!/usr/bin/env bash
# Run the sentiment-intelligence backend (FastAPI, port 4060) and frontend
# (Vite, port 3060). Installs dependencies first and verifies them before
# starting either service. Ctrl+C stops both.
#
# This script lives in scripts/; the project root is its parent directory, so it
# can be launched from anywhere (e.g. ./scripts/run.sh or from inside scripts/).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
VENV_DIR="$BACKEND_DIR/.venv"

BACKEND_PORT=4060
FRONTEND_PORT=3060

log() { printf '\n[run.sh] %s\n' "$*"; }
die() { printf '[run.sh] ERROR: %s\n' "$*" >&2; exit 1; }

# Kill anything already listening on the given port so a stale instance never
# blocks a fresh start. Sends SIGTERM, then SIGKILL for any survivors.
free_port() {
    local port="$1"
    command -v lsof >/dev/null 2>&1 || {
        log "lsof not found; skipping port $port cleanup."
        return 0
    }

    local pids
    pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    [ -z "$pids" ] && return 0

    log "Port $port in use by PID(s): $pids — stopping them."
    # shellcheck disable=SC2086
    kill $pids 2>/dev/null || true
    sleep 1

    pids="$(lsof -ti tcp:"$port" -sTCP:LISTEN 2>/dev/null || true)"
    if [ -n "$pids" ]; then
        log "PID(s) still running on port $port: $pids — force killing."
        # shellcheck disable=SC2086
        kill -9 $pids 2>/dev/null || true
    fi
}

# ---------------------------------------------------------------------------
# Prerequisites
# ---------------------------------------------------------------------------
command -v python3 >/dev/null 2>&1 || die "python3 is not installed or not on PATH."
command -v npm >/dev/null 2>&1 || die "npm is not installed or not on PATH (Node.js 18+ required)."

# ---------------------------------------------------------------------------
# Backend setup
# ---------------------------------------------------------------------------
log "Setting up backend..."

if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment at $VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

VENV_PY="$VENV_DIR/bin/python"
[ -x "$VENV_PY" ] || die "Virtual environment python not found at $VENV_PY."

log "Installing Python dependencies..."
"$VENV_PY" -m pip install --quiet --upgrade pip
"$VENV_PY" -m pip install --quiet -r "$BACKEND_DIR/requirements.txt"

log "Verifying Python dependencies..."
"$VENV_PY" -c "import fastapi, uvicorn" \
    || die "Backend dependency verification failed (fastapi/uvicorn not importable)."

if [ ! -f "$BACKEND_DIR/.env" ]; then
    log "Creating backend/.env from .env.example (edit it with real credentials)."
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
fi

# ---------------------------------------------------------------------------
# Frontend setup
# ---------------------------------------------------------------------------
log "Setting up frontend..."

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    log "Installing npm dependencies (npm ci)..."
    (cd "$FRONTEND_DIR" && npm ci)
else
    log "node_modules already present, skipping npm ci."
fi

log "Verifying npm dependencies..."
(cd "$FRONTEND_DIR" && npm ls vite react >/dev/null 2>&1) \
    || die "Frontend dependency verification failed (vite/react missing). Try removing frontend/node_modules and re-running."

# ---------------------------------------------------------------------------
# Free the ports (kill any already-running instances)
# ---------------------------------------------------------------------------
log "Ensuring ports $BACKEND_PORT and $FRONTEND_PORT are free..."
free_port "$BACKEND_PORT"
free_port "$FRONTEND_PORT"

# ---------------------------------------------------------------------------
# Run both services
# ---------------------------------------------------------------------------
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
    log "Shutting down..."
    [ -n "$FRONTEND_PID" ] && kill "$FRONTEND_PID" 2>/dev/null || true
    [ -n "$BACKEND_PID" ] && kill "$BACKEND_PID" 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

log "Starting backend on http://localhost:$BACKEND_PORT ..."
(cd "$BACKEND_DIR" && "$VENV_PY" main.py) &
BACKEND_PID=$!

log "Starting frontend on http://localhost:$FRONTEND_PORT ..."
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

log "Backend PID: $BACKEND_PID | Frontend PID: $FRONTEND_PID"
log "Press Ctrl+C to stop both services."

# Exit if either service dies; cleanup trap stops the survivor.
wait -n "$BACKEND_PID" "$FRONTEND_PID"
