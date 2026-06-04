#!/usr/bin/env bash
# Copyright (c) 2026 Oracle and/or its affiliates.
# SPDX-License-Identifier: UPL-1.0
set -euo pipefail

cd "$(dirname "$0")"

BACKEND_PORT="${BACKEND_PORT:-8002}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"
PYTHON=".venv/bin/python"

if [ ! -x "$PYTHON" ]; then
  echo "Python virtual environment was not found. Run ./setup.sh first."
  exit 1
fi

if [ ! -d "node_modules" ]; then
  echo "Node dependencies were not found. Run ./setup.sh first."
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm was not found. Install Node.js 20 or newer, then rerun ./setup.sh."
  exit 1
fi

export VITE_API_PROXY_TARGET="http://localhost:${BACKEND_PORT}"

echo "Starting FastAPI backend on http://127.0.0.1:${BACKEND_PORT}"
"$PYTHON" -m uvicorn backend.main:app --host 127.0.0.1 --port "$BACKEND_PORT" &
BACKEND_PID="$!"

cleanup() {
  if kill -0 "$BACKEND_PID" >/dev/null 2>&1; then
    echo "Stopping FastAPI backend..."
    kill "$BACKEND_PID" >/dev/null 2>&1 || true
  fi
}

trap cleanup EXIT INT TERM

echo "Starting Vite frontend on http://127.0.0.1:${FRONTEND_PORT}"
echo "Press Ctrl+C to stop both dev servers."
npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
