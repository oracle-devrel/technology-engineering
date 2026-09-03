#!/usr/bin/env bash

# Start the Express API proxy first, then the Vite frontend.
set -Eeuo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "${SCRIPT_DIR}/../app" && pwd)"
BACKEND_PORT="${PORT:-3001}"
BACKEND_URL="http://127.0.0.1:${BACKEND_PORT}/health"
BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  local exit_code=$?
  trap - EXIT INT TERM

  for pid in "$FRONTEND_PID" "$BACKEND_PID"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "$pid" 2>/dev/null || true
    fi
  done

  wait "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" 2>/dev/null || true
  exit "$exit_code"
}

trap cleanup EXIT INT TERM

cd "$FRONTEND_DIR"

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required. Install Node.js 18 or later, then try again." >&2
  exit 1
fi

if [[ ! -d node_modules ]]; then
  echo "Dependencies are not installed. Run 'npm ci' in $FRONTEND_DIR first." >&2
  exit 1
fi

echo "Starting backend on port ${BACKEND_PORT}..."
npm run server &
BACKEND_PID=$!

for _ in {1..30}; do
  if curl --fail --silent --show-error "$BACKEND_URL" >/dev/null 2>&1; then
    echo "Backend is ready. Starting frontend on http://localhost:5173..."
    npm run dev &
    FRONTEND_PID=$!
    wait "$FRONTEND_PID"
    exit $?
  fi

  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    echo "Backend stopped before it became ready." >&2
    wait "$BACKEND_PID"
    exit 1
  fi

  sleep 1
done

echo "Backend did not become ready within 30 seconds: ${BACKEND_URL}" >&2
exit 1
